#!/usr/bin/env python3
"""Execute one HumanEval-style job inside the sandbox container.

No network. Do not read host environment secrets. Invoked as:
  python docker_worker.py /in/job.json /out/result.json
"""

from __future__ import annotations

import json
import multiprocessing
import sys
import traceback
from typing import Any, Dict


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
            for args in job.get("inputs") or []:
                outputs.append(_jsonable(candidate(*args)))
            connection.send(
                {
                    "status": "pass",
                    "passed": True,
                    "outputs": outputs,
                    "error": None,
                }
            )
            return

        details = []
        all_ok = True
        atol = float(job.get("atol") or 0.0)
        for case in job.get("cases") or []:
            try:
                got = _jsonable(candidate(*case["args"]))
                ok = _values_equal(got, case["expected"], atol)
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
    process.join(timeout)
    if process.is_alive():
        process.kill()
        process.join(1)
        result = {"status": "timeout", "passed": False, "error": "timeout"}
    elif parent.poll():
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
