#!/usr/bin/env python3
"""Revalidate persisted repaired outputs in hard-timeout child processes.

Run this script inside a network-disabled, read-only container. It writes a
hash-bound cache consumed by ``gate0_pairwise_analysis.py``; original experiment
JSON files are never modified.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import io
import json
import multiprocessing
import os
import sys
import time
from typing import Any, Dict, Optional, Tuple

from gate0_pairwise_analysis import select_configs


CACHE_SCHEMA = "skyt-post-oracle-cache-v2"


def code_hash(code: str) -> str:
    return hashlib.sha256((code or "").encode("utf-8")).hexdigest()


def canonical_json_hash(value: Any) -> str:
    serialized = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _oracle_worker(code: str, contract: Dict[str, Any], connection) -> None:
    """Execute one oracle in a disposable process."""
    try:
        from src.oracle_system import OracleSystem

        with contextlib.redirect_stdout(io.StringIO()):
            with contextlib.redirect_stderr(io.StringIO()):
                result = OracleSystem().run_oracle_tests(
                    code or "", contract, timeout=5
                )
        connection.send({"status": "completed", "result": result})
    except BaseException as exc:  # Child must serialize every failure.
        try:
            connection.send({
                "status": "worker_error",
                "result": {
                    "passed": False,
                    "error": f"{type(exc).__name__}: {exc}",
                    "test_results": [],
                },
            })
        except BaseException:
            pass
    finally:
        connection.close()


def evaluate_isolated(
    code: str,
    contract: Dict[str, Any],
    hard_timeout: float,
) -> Dict[str, Any]:
    """Run one output with a process-level kill timeout."""
    context = multiprocessing.get_context(
        "fork" if sys.platform != "win32" else "spawn"
    )
    parent, child = context.Pipe(duplex=False)
    process = context.Process(
        target=_oracle_worker,
        args=(code, contract, child),
        daemon=True,
    )
    started = time.monotonic()
    process.start()
    child.close()
    process.join(hard_timeout)

    if process.is_alive():
        process.terminate()
        process.join(1)
        if process.is_alive() and hasattr(process, "kill"):
            process.kill()
            process.join(1)
        parent.close()
        return {
            "status": "hard_timeout",
            "duration_seconds": time.monotonic() - started,
            "result": {
                "passed": False,
                "error": f"Hard oracle timeout after {hard_timeout}s",
                "test_results": [],
            },
        }

    payload: Optional[Dict[str, Any]] = None
    if parent.poll():
        try:
            payload = parent.recv()
        except EOFError:
            payload = None
    parent.close()

    if payload is None:
        payload = {
            "status": "worker_exited_without_result",
            "result": {
                "passed": False,
                "error": (
                    "Oracle worker exited without returning a result "
                    f"(exit code {process.exitcode})"
                ),
                "test_results": [],
            },
        }
    payload["duration_seconds"] = time.monotonic() - started
    return payload


def build_cache(hard_timeout: float) -> Dict[str, Any]:
    configs, skipped = select_configs()
    cache: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    entries: Dict[str, Any] = {}
    evaluated = reused = 0

    for position, ((contract_id, model, temperature), (_, path, data)) in enumerate(
        sorted(configs.items()), start=1
    ):
        contract = data.get("contract") or {}
        contract_digest = canonical_json_hash(contract)
        oracle_results = []
        for code in data.get("repaired_outputs") or []:
            digest = code_hash(code or "")
            cache_key = (contract_id, contract_digest, digest)
            if cache_key not in cache:
                cache[cache_key] = evaluate_isolated(
                    code or "", contract, hard_timeout
                )
                evaluated += 1
            else:
                reused += 1
            execution = cache[cache_key]
            oracle_results.append({
                "output_sha256": digest,
                "status": execution["status"],
                "duration_seconds": execution["duration_seconds"],
                "result": execution["result"],
            })

        filename = os.path.basename(path)
        entries[filename] = {
            "contract_id": contract_id,
            "contract_sha256": contract_digest,
            "model": model,
            "temperature": temperature,
            "n_outputs": len(data.get("repaired_outputs") or []),
            "oracle_results": oracle_results,
        }
        print(
            f"[{position}/{len(configs)}] {contract_id} / {model} / "
            f"T={temperature}",
            file=sys.stderr,
            flush=True,
        )

    oracle_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "src",
        "oracle_system.py",
    )
    with open(oracle_path, "rb") as oracle_file:
        oracle_source_sha256 = hashlib.sha256(oracle_file.read()).hexdigest()

    return {
        "schema": CACHE_SCHEMA,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "python_version": sys.version,
        "oracle_source_sha256": oracle_source_sha256,
        "selected_configs": len(configs),
        "skipped_files": len(skipped),
        "unique_contract_code_pairs_evaluated": evaluated,
        "duplicate_outputs_reused": reused,
        "entries": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        required=True,
        help="Cache path. Mount only this file writable when sandboxing.",
    )
    parser.add_argument(
        "--hard-timeout",
        type=float,
        default=8.0,
        help="Parent-process timeout per unique output.",
    )
    parser.add_argument(
        "--sandbox-image",
        default="unknown",
        help="Immutable container image reference used for provenance.",
    )
    args = parser.parse_args()

    result = build_cache(args.hard_timeout)
    result["sandbox_image"] = args.sandbox_image
    with open(args.output, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")
    print(
        f"Wrote {args.output}: "
        f"{result['unique_contract_code_pairs_evaluated']} unique evaluations, "
        f"{result['duplicate_outputs_reused']} reused outputs",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
