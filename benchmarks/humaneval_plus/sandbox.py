"""Network-disabled Docker execution for generated Python.

Untrusted code is never exec'd on the host. EvalPlus's in-process checker is
not used on Windows (it reports timeout for every program).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .manifest import MANIFEST, PACKAGE_DIR
from .stitch import stitch_solution


WORKER_PATH = PACKAGE_DIR / "docker_worker.py"


class SandboxUnavailable(RuntimeError):
    """Docker is missing, not running, or refused the job."""


def docker_available() -> bool:
    docker = shutil.which("docker")
    if not docker:
        return False
    try:
        completed = subprocess.run(
            [docker, "info"],
            capture_output=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def _docker_bin() -> str:
    docker = shutil.which("docker")
    if not docker:
        raise SandboxUnavailable("docker executable not found")
    return docker


def run_sandboxed_job(job: Dict[str, Any]) -> Dict[str, Any]:
    """Run one job in an ephemeral, network-disabled container."""
    if not docker_available():
        raise SandboxUnavailable("Docker is not running")

    image = MANIFEST["sandbox"]["image"]
    timeout = int(job.get("timeout_seconds") or MANIFEST["sandbox"]["timeout_seconds"])
    job = dict(job)
    job["timeout_seconds"] = timeout

    docker = _docker_bin()
    with tempfile.TemporaryDirectory(prefix="heplus_") as tmp:
        tmp_path = Path(tmp)
        in_dir = tmp_path / "in"
        out_dir = tmp_path / "out"
        in_dir.mkdir()
        out_dir.mkdir()
        shutil.copy2(WORKER_PATH, in_dir / "docker_worker.py")
        (in_dir / "job.json").write_text(
            json.dumps(job), encoding="utf-8"
        )
        # Docker Desktop on Windows needs the real path, not a sandbox alias.
        in_mount = str(in_dir.resolve())
        out_mount = str(out_dir.resolve())
        command = [
            docker,
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,exec,nosuid,size=64m",
            "--memory",
            str(MANIFEST["sandbox"]["memory"]),
            "--cpus",
            str(MANIFEST["sandbox"]["cpus"]),
            "--pids-limit",
            str(MANIFEST["sandbox"]["pids_limit"]),
            "--security-opt",
            "no-new-privileges",
            "-v",
            f"{in_mount}:/in:ro",
            "-v",
            f"{out_mount}:/out:rw",
            "-w",
            "/in",
            image,
            "python",
            "/in/docker_worker.py",
            "/in/job.json",
            "/out/result.json",
        ]
        env = {
            "PATH": os.environ.get("PATH", ""),
            "SystemRoot": os.environ.get("SystemRoot", ""),
            "WINDIR": os.environ.get("WINDIR", ""),
        }
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                timeout=timeout + 30,
                check=False,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "passed": False,
                "error": "docker run timed out",
            }
        result_path = out_dir / "result.json"
        if completed.returncode != 0 and not result_path.exists():
            stderr = (completed.stderr or b"").decode("utf-8", "replace")[-1500:]
            raise SandboxUnavailable(
                f"docker run failed ({completed.returncode}): {stderr}"
            )
        if not result_path.exists():
            return {
                "status": "fail",
                "passed": False,
                "error": "sandbox produced no result",
                "stderr": (completed.stderr or b"").decode("utf-8", "replace")[-1500:],
            }
        with result_path.open(encoding="utf-8") as handle:
            return json.load(handle)


def _plus_input_too_expensive(args: Any) -> bool:
    """Drop plus inputs that explode naive recurrences (e.g. tri(n=1e6))."""
    if not isinstance(args, (list, tuple)):
        return False
    for arg in args:
        if isinstance(arg, bool):
            continue
        if isinstance(arg, int) and abs(arg) > 30:
            return True
    return False


def _eval_canonical_plus_inputs(
    code: str,
    entry_point: str,
    inputs: List[Any],
) -> List[Any]:
    """Run canonical plus inputs in Docker batches so a 60s wall clock cannot
    kill the whole extra-test suite (HumanEval/10, /14, /21, /38, /93, /113).
    """
    outputs: List[Any] = []
    remaining = list(inputs)
    batch_size = 80
    batch_timeout = max(int(MANIFEST["sandbox"]["timeout_seconds"]), 180)
    while remaining:
        batch = remaining[:batch_size]
        result = run_sandboxed_job(
            {
                "mode": "eval_inputs",
                "code": code,
                "entry_point": entry_point,
                "inputs": batch,
                "timeout_seconds": batch_timeout,
                "case_timeout_seconds": 1,
            }
        )
        got = result.get("outputs") or []
        if result.get("passed") and len(got) == len(batch):
            outputs.extend(got)
            remaining = remaining[len(batch) :]
            batch_size = 80
            continue
        if batch_size > 20:
            batch_size = max(20, batch_size // 2)
            continue
        outputs.extend([{"__timeout__": True} for _ in batch])
        remaining = remaining[len(batch) :]
        batch_size = 80
    return outputs


def plus_cases_for_problem(problem: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return args/expected pairs for HumanEval+ extras.

    Smoke fixtures already store ``plus_cases``. Official EvalPlus problems
    store ``plus_input`` only; expected values come from the canonical
    solution, executed in Docker.
    """
    existing = problem.get("plus_cases")
    if existing:
        return list(existing)
    inputs = [
        args
        for args in list(problem.get("plus_input") or [])
        if not _plus_input_too_expensive(args)
    ]
    if not inputs:
        return []
    stitch = stitch_solution(
        problem["prompt"],
        problem["canonical_solution"],
        problem["entry_point"],
    )
    if not stitch.get("parse_ok") or not stitch.get("has_entry_point"):
        raise SandboxUnavailable("canonical solution did not stitch")
    outputs = _eval_canonical_plus_inputs(
        stitch["stitched_code"], problem["entry_point"], inputs
    )
    if len(outputs) != len(inputs):
        raise SandboxUnavailable(
            f"canonical plus eval failed: expected {len(inputs)} outputs, got {len(outputs)}"
        )
    cases = []
    for args, expected in zip(inputs, outputs):
        if isinstance(expected, dict) and expected.get("__timeout__"):
            continue
        cases.append({"args": args, "expected": expected})
    if not cases:
        raise SandboxUnavailable("canonical plus eval timed out on every extra case")
    problem["plus_cases"] = cases
    return cases


def evaluate_stitched(
    code: str,
    problem: Dict[str, Any],
    *,
    timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """Score original HumanEval tests and extra plus cases separately."""
    timeout = timeout_seconds or int(MANIFEST["sandbox"]["timeout_seconds"])
    base_job = {
        "mode": "check",
        "code": code,
        "entry_point": problem["entry_point"],
        "test": problem["test"],
        "timeout_seconds": timeout,
    }
    base = run_sandboxed_job(base_job)
    plus_cases: List[Dict[str, Any]] = plus_cases_for_problem(problem)
    if plus_cases:
        plus_timeout = timeout
        if timeout_seconds is None:
            plus_timeout = max(timeout, min(180, 20 + len(plus_cases) // 5))
        plus = run_sandboxed_job(
            {
                "mode": "cases",
                "code": code,
                "entry_point": problem["entry_point"],
                "cases": plus_cases,
                "atol": problem.get("atol") or 0,
                "timeout_seconds": plus_timeout,
                "case_timeout_seconds": 2,
            }
        )
    else:
        plus = {
            "status": "skipped",
            "passed": None,
            "error": "no plus cases on this problem",
        }
    plus_passed = bool(base.get("passed")) and bool(plus.get("passed"))
    if plus.get("status") == "skipped":
        plus_passed = bool(base.get("passed"))
    return {
        "base_status": base.get("status"),
        "base_passed": bool(base.get("passed")),
        "plus_status": plus.get("status"),
        "plus_passed": plus_passed if plus.get("status") != "skipped" else None,
        "certified": plus_passed if plus.get("status") != "skipped" else bool(base.get("passed")),
        "base": base,
        "plus": plus,
    }
