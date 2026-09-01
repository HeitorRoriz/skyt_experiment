"""Checkpointed HumanEval+ generation. No SKYT repair. No style contracts."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .analyze import analyze_records
from .dataset import load_evalplus_problems
from .generate import ApiSpendBlocked, generate_completion
from .manifest import MANIFEST, PILOT_TASK_IDS
from .provenance import attach_oracle, dump_jsonl, new_generation_record
from .sandbox import SandboxUnavailable, docker_available, evaluate_stitched
from .stitch import stitch_solution


def _safe_name(task_id: str, model: str, temperature: float) -> str:
    task = re.sub(r"[^A-Za-z0-9]+", "_", task_id).strip("_")
    model_part = re.sub(r"[^A-Za-z0-9]+", "_", model).strip("_")
    return f"{task}_{model_part}_temp{temperature}"


def _failed_oracle() -> Dict[str, Any]:
    return {
        "base_status": "fail",
        "base_passed": False,
        "plus_status": "fail",
        "plus_passed": False,
        "certified": False,
    }


def _load_existing(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def run_config(
    *,
    task_id: str,
    model: str,
    temperature: float,
    n: int,
    out_dir: Path,
    allow_api: bool,
    force: bool = False,
) -> Dict[str, Any]:
    if not allow_api:
        raise ApiSpendBlocked(
            "Refusing to call an LLM. Re-run with --allow-api after smoke tests pass."
        )
    if n < 2:
        raise ValueError("Need at least two generations")
    if task_id not in PILOT_TASK_IDS:
        raise ValueError(f"{task_id} is not a preregistered pilot task")
    if not docker_available():
        raise SandboxUnavailable("Docker is required to score HumanEval+")

    problems, dataset_md5 = load_evalplus_problems()
    problem = dict(problems[task_id])
    human = stitch_solution(
        problem["prompt"],
        problem["canonical_solution"],
        problem["entry_point"],
    )
    human_code = human["stitched_code"]

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = _safe_name(task_id, model, temperature)
    jsonl_path = out_dir / f"{stem}.jsonl"
    summary_path = out_dir / f"{stem}_summary.json"

    existing = [] if force else _load_existing(jsonl_path)
    by_index = {int(record["run_index"]): record for record in existing}
    records: List[Dict[str, Any]] = []
    max_tokens = int(MANIFEST["generation"]["max_tokens"])

    for run_index in range(n):
        if run_index in by_index:
            record = by_index[run_index]
            record["human_reference_code"] = human_code
            records.append(record)
            continue
        raw_response: Optional[str] = None
        usage: Dict[str, Any] = {}
        error: Optional[str] = None
        try:
            raw_response, usage = generate_completion(
                model=model,
                problem_prompt=problem["prompt"],
                temperature=temperature,
                max_tokens=max_tokens,
                allow_api=True,
            )
        except Exception as exc:  # Checkpoint the failure; do not leak secrets.
            error = type(exc).__name__
            if type(exc).__name__ == "APIConnectionError":
                error = "APIConnectionError:ssl_or_network"
        stitch = stitch_solution(
            problem["prompt"], raw_response or "", problem["entry_point"]
        )
        record = new_generation_record(
            task_id=task_id,
            model=model,
            temperature=temperature,
            run_index=run_index,
            problem_prompt=problem["prompt"],
            raw_response=raw_response,
            stitch=stitch,
            usage=usage,
            error=error,
        )
        record["human_reference_code"] = human_code
        record["repair_applied"] = False
        record["style_contract"] = None
        if error or not stitch.get("parse_ok") or not stitch.get("has_entry_point"):
            record = attach_oracle(record, _failed_oracle())
        else:
            oracle = evaluate_stitched(stitch["stitched_code"], problem)
            record = attach_oracle(record, oracle)
        records.append(record)
        dump_jsonl(jsonl_path, records)

    analysis = analyze_records(records)
    summary = {
        "schema": "skyt-humaneval-plus-summary-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "model": model,
        "temperature": temperature,
        "n": n,
        "dataset_md5": dataset_md5,
        "no_skyt_repair": True,
        "no_style_contracts": True,
        "jsonl": str(jsonl_path),
        "analysis": analysis,
        "n_base_passed": analysis["n_base_passed"],
        "n_plus_certified": analysis["n_plus_certified"],
        "consensus_index": analysis["consensus_index"],
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    return summary
