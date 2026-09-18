#!/usr/bin/env python3
"""Execute one HumanEval-style job inside the sandbox container.

No network. Do not read host environment secrets. Invoked as:
  python docker_worker.py /in/job.json /out/result.json
"""

from __future__ import annotations

import json
import multiprocessing
import signal
import sys
import time
import traceback
from typing import Any, Dict, Optional


def _jsonable(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (int, float, str, bool)) or value is None:
        return value
    return repr(value)


def _values_equal(got: Any, expected: Any, atol: float) -> bool:
    if isinstance(got, (int, float)) and isinstance(expected, (int, float)) and atol:
        return abs(float(got) - float(expected)) <= atol
    return got == expected


def _call_with_timeout(candidate, args, seconds: int = 2) -> Any:
    def _handler(signum, frame):
        raise TimeoutError("case timeout")

    signal.signal(signal.SIGALRM, _handler)
    signal.alarm(max(1, int(seconds)))
    try:
        return candidate(*args)
    finally:
        signal.alarm(0)


def _evaluate(job: Dict[str, Any], connection) -> None:
    try:
        code = job["code"]
        entry_point = job["entry_point"]
        namespace: Dict[str, Any] = {}
        exec(compile(code, "<solution>", "exec"), namespace, namespace)
        if entry_point not in namespace:
            connection.send(
                {
                    "status": "fail",
                    "passed": False,
                    "error": f"missing entry point {entry_point}",
                }
            )
            return

        candidate = namespace[entry_point]
        if job.get("mode") == "check":
            exec(compile(job["test"], "<test>", "exec"), namespace, namespace)
            namespace["check"](candidate)
            connection.send({"status": "pass", "passed": True, "error": None})
            return

        if job.get("mode") == "eval_inputs":
            outputs = []
            timed_out = 0
            case_seconds = int(job.get("case_timeout_seconds") or 2)
            for args in job.get("inputs") or []:
                try:
                    outputs.append(_jsonable(_call_with_timeout(candidate, args, case_seconds)))
                except TimeoutError:
                    timed_out += 1
                    outputs.append({"__timeout__": True})
            connection.send(
                {
                    "status": "pass",
                    "passed": True,
                    "outputs": outputs,
                    "timed_out_cases": timed_out,
                    "error": None,
                }
            )
            return

        details = []
        all_ok = True
        atol = float(job.get("atol") or 0.0)
        case_seconds = int(job.get("case_timeout_seconds") or 2)
        for case in job.get("cases") or []:
            try:
                got = _jsonable(
                    _call_with_timeout(candidate, case["args"], case_seconds)
                )
                ok = _values_equal(got, case["expected"], atol)
            except TimeoutError:
                ok = False
                got = "timeout"
            except Exception as exc:  # Isolated worker: capture every case.
                ok = False
                got = f"{type(exc).__name__}: {exc}"
            details.append({"ok": bool(ok), "got": repr(got)[:300]})
            all_ok = all_ok and bool(ok)
        connection.send(
            {
                "status": "pass" if all_ok else "fail",
                "passed": bool(all_ok),
                "details": details,
                "error": None if all_ok else "case failure",
            }
        )
    except Exception as exc:
        connection.send(
            {
                "status": "fail",
                "passed": False,
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc()[-2000:],
            }
        )
    finally:
        connection.close()


def main() -> int:
    job_path, result_path = sys.argv[1], sys.argv[2]
    with open(job_path, encoding="utf-8") as handle:
        job = json.load(handle)
    timeout = float(job.get("timeout_seconds", 10))
    context = multiprocessing.get_context("fork")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(target=_evaluate, args=(job, child), daemon=True)
    process.start()
    child.close()
    # Drain the pipe while waiting. HumanEval/14 all_prefixes (and similar)
    # returns large list payloads; if the parent only join()s, the child
    # blocks on send once the pipe buffer fills and the job looks idle
    # at 0% CPU until the wall timeout.
    result: Optional[Dict[str, Any]] = None
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        if parent.poll(min(0.5, remaining)):
            result = parent.recv()
            process.join(1)
            break
        if not process.is_alive():
            if parent.poll(0.1):
                result = parent.recv()
            break
    if process.is_alive():
        process.kill()
        process.join(1)
        if result is None:
            result = {"status": "timeout", "passed": False, "error": "timeout"}
    elif result is None:
        if parent.poll():
            result = parent.recv()
        else:
            result = {
                "status": "fail",
                "passed": False,
                "error": f"worker exit {process.exitcode}",
            }
    with open(result_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
