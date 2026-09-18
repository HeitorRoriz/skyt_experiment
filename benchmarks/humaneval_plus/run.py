"""Checkpointed HumanEval+ generation. No SKYT repair. No style contracts."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .analyze import analyze_records
from .cost import usd_for_usage, write_cost_ledger
from .dataset import load_evalplus_problems
from .generate import ApiSpendBlocked, generate_completion
from .manifest import MANIFEST, PILOT_TASK_IDS
from .provenance import attach_oracle, atomic_write_json, dump_jsonl, new_generation_record
from .sandbox import SandboxUnavailable, docker_available, evaluate_stitched, plus_cases_for_problem
from .stitch import stitch_solution

CHECKPOINT_EVERY_GENS = 5
SCORE_EVERY_CONFIGS = 4
CHECKPOINT_BOOTSTRAP = 200


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
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                # Power-loss can truncate the last line. Keep prior records.
                continue
    return records


def _config_complete(records: List[Dict[str, Any]], n: int) -> bool:
    indexes = {int(record.get("run_index", -1)) for record in records}
    return set(range(n)).issubset(indexes)


def _config_sameeval(records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if len(records) < 2:
        return None
    from benchmark.metrics import config_repeatability
    from benchmark.relation import fingerprint
    from benchmark.score import _is_certified

    ordered = sorted(records, key=lambda item: int(item.get("run_index", 0)))
    prints = [
        fingerprint(record.get("stitched_code") or "", flexible_naming=True)
        for record in ordered
    ]
    certified = [
        _is_certified(record, fp is not None) for record, fp in zip(ordered, prints)
    ]
    return config_repeatability(prints, certified)


def _write_checkpoint(
    out_dir: Path,
    *,
    payload: Dict[str, Any],
) -> None:
    atomic_write_json(out_dir / "checkpoint.json", payload)


def _score_complete_configs(out_dir: Path, n: int) -> Optional[Dict[str, Any]]:
    from benchmark.score import score_directory

    try:
        return score_directory(
            out_dir,
            out_dir,
            n_bootstrap=CHECKPOINT_BOOTSTRAP,
            skip_incomplete=True,
            require_n=n,
            report_filename="sameeval_checkpoint.json",
        )
    except Exception as exc:
        print(f"  checkpoint score skipped: {type(exc).__name__}: {exc}", flush=True)
        return None


def run_config(
    *,
    task_id: str,
    model: str,
    temperature: float,
    n: int,
    out_dir: Path,
    allow_api: bool,
    force: bool = False,
    restrict_to_pilot: bool = True,
    analyze: bool = True,
) -> Dict[str, Any]:
    if not allow_api:
        raise ApiSpendBlocked(
            "Refusing to call an LLM. Re-run with --allow-api after smoke tests pass."
        )
    if n < 2:
        raise ValueError("Need at least two generations")
    if restrict_to_pilot and task_id not in PILOT_TASK_IDS:
        raise ValueError(f"{task_id} is not a preregistered pilot task")
    if not docker_available():
        raise SandboxUnavailable("Docker is required to score HumanEval+")

    problems, dataset_md5 = load_evalplus_problems()
    problem = dict(problems[task_id])
    cache_dir = out_dir / "plus_cases"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{_safe_name(task_id, 'canon', 0.0)}.json"
    if cache_path.exists():
        problem["plus_cases"] = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        problem["plus_cases"] = plus_cases_for_problem(problem)
        cache_path.write_text(
            json.dumps(problem["plus_cases"]), encoding="utf-8"
        )
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
        if (run_index + 1) % CHECKPOINT_EVERY_GENS == 0 or (run_index + 1) == n:
            write_cost_ledger(out_dir)
            _write_checkpoint(
                out_dir,
                payload={
                    "schema": "sameeval-checkpoint-v1",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "task_id": task_id,
                    "model": model,
                    "temperature": temperature,
                    "run_index": run_index,
                    "n_this_config": len(records),
                    "n_target": n,
                    "jsonl": str(jsonl_path),
                    "config_complete": _config_complete(records, n),
                },
            )

    analysis = analyze_records(records) if analyze else None
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
        "n_base_passed": None if analysis is None else analysis["n_base_passed"],
        "n_plus_certified": None if analysis is None else analysis["n_plus_certified"],
        "consensus_index": None if analysis is None else analysis["consensus_index"],
        "usd_estimate": sum(
            usd_for_usage(model, record.get("usage")) or 0.0 for record in records
        ),
    }
    atomic_write_json(summary_path, summary)
    return summary


def all_evalplus_task_ids() -> List[str]:
    problems, _digest = load_evalplus_problems()
    ids = sorted(problems)
    if len(ids) != 164:
        raise ValueError(f"Expected 164 HumanEval+ tasks, got {len(ids)}")
    return ids


def incomplete_task_ids(
    out_dir: Path,
    *,
    n: int,
    task_ids: List[str],
    models: List[str],
    temperatures: List[float],
) -> List[str]:
    """Tasks that still lack a complete jsonl+summary on at least one config."""
    missing: List[str] = []
    for task_id in task_ids:
        for model in models:
            for temp in temperatures:
                stem = _safe_name(task_id, model, temp)
                jsonl_path = out_dir / f"{stem}.jsonl"
                summary_path = out_dir / f"{stem}_summary.json"
                if not (
                    _config_complete(_load_existing(jsonl_path), n)
                    and summary_path.exists()
                ):
                    missing.append(task_id)
                    break
            else:
                continue
            break
    return missing


def run_grid(
    *,
    task_ids: List[str],
    out_dir: Path,
    n: int,
    allow_api: bool,
    models: Optional[List[str]] = None,
    temperatures: Optional[List[float]] = None,
    restrict_to_pilot: bool = True,
    analyze: bool = True,
    force: bool = False,
    log_filename: str = "grid_progress.log",
    report_filename: str = "grid_report.json",
    schema: str = "skyt-humaneval-plus-grid-v1",
) -> Dict[str, Any]:
    if not allow_api:
        raise ApiSpendBlocked(
            "Refusing to call an LLM. Re-run with --allow-api after smoke tests pass."
        )
    models = list(models or MANIFEST["models"])
    # Claude first: OpenAI already rate-limited on this account.
    models = sorted(models, key=lambda name: (0 if name.startswith("claude-") else 1, name))
    temperatures = list(temperatures if temperatures is not None else MANIFEST["temperatures"])
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / log_filename
    configs = [
        (task_id, model, float(temp))
        for model in models
        for task_id in task_ids
        for temp in temperatures
    ]
    rows = []
    n_complete = 0

    def flush_grid(ledger: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            "schema": schema,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "n_configs": len(configs),
            "n_complete": n_complete,
            "n_tasks": len(task_ids),
            "n": n,
            "models": models,
            "temperatures": temperatures,
            "no_skyt_repair": True,
            "restrict_to_pilot": restrict_to_pilot,
            "analyze": analyze,
            "cost": ledger or write_cost_ledger(out_dir),
            "configs": rows,
        }
        atomic_write_json(out_dir / report_filename, payload)
        return payload

    for index, (task_id, model, temp) in enumerate(configs, start=1):
        line = f"[{index}/{len(configs)}] {task_id} {model} T={temp}"
        print(line, flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        jsonl_path = out_dir / f"{_safe_name(task_id, model, temp)}.jsonl"
        summary_path = out_dir / f"{_safe_name(task_id, model, temp)}_summary.json"
        if _config_complete(_load_existing(jsonl_path), n) and summary_path.exists():
            print("  SKIPPED complete", flush=True)
            try:
                prior = json.loads(summary_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                prior = {}
            rows.append(
                {
                    "task_id": task_id,
                    "model": model,
                    "temperature": temp,
                    "n_plus_certified": prior.get("n_plus_certified"),
                    "n_base_passed": prior.get("n_base_passed"),
                    "usd_estimate": prior.get("usd_estimate"),
                    "same_at_2": prior.get("same_at_2"),
                    "same_at_2_given_cert": prior.get("same_at_2_given_cert"),
                    "plus_pass": prior.get("plus_pass"),
                    "skipped": "complete",
                }
            )
            n_complete += 1
            continue
        try:
            summary = run_config(
                task_id=task_id,
                model=model,
                temperature=temp,
                n=n,
                out_dir=out_dir,
                allow_api=True,
                force=force,
                restrict_to_pilot=restrict_to_pilot,
                analyze=analyze,
            )
        except Exception as exc:
            err = type(exc).__name__
            detail = str(exc)[:300]
            print(f"  FAILED {err}: {detail}", flush=True)
            rows.append(
                {
                    "task_id": task_id,
                    "model": model,
                    "temperature": temp,
                    "error": err,
                }
            )
            write_cost_ledger(out_dir)
            flush_grid()
            continue
        sameeval = _config_sameeval(_load_existing(jsonl_path)) or {}
        rows.append(
            {
                "task_id": task_id,
                "model": model,
                "temperature": temp,
                "n_plus_certified": summary.get("n_plus_certified", sameeval.get("n_certified")),
                "n_base_passed": summary.get("n_base_passed"),
                "usd_estimate": summary.get("usd_estimate"),
                "same_at_2": sameeval.get("same_at_2"),
                "same_at_2_given_cert": sameeval.get("same_at_2_given_cert"),
                "plus_pass": sameeval.get("plus_pass"),
            }
        )
        n_complete += 1
        ledger = write_cost_ledger(out_dir)
        flush_grid(ledger)
        if n_complete % SCORE_EVERY_CONFIGS == 0:
            scored = _score_complete_configs(out_dir, n)
            if scored:
                print(
                    f"  SameEval checkpoint: {scored.get('n_complete_configs')} configs "
                    f"-> {out_dir / 'sameeval_checkpoint.json'}",
                    flush=True,
                )

    ledger = write_cost_ledger(out_dir)
    report = flush_grid(ledger)
    _score_complete_configs(out_dir, n)
    return report


def run_pilot(
    *,
    out_dir: Path,
    n: int,
    allow_api: bool,
    models: Optional[List[str]] = None,
    temperatures: Optional[List[float]] = None,
) -> Dict[str, Any]:
    report = run_grid(
        task_ids=list(PILOT_TASK_IDS),
        out_dir=out_dir,
        n=n,
        allow_api=allow_api,
        models=models,
        temperatures=temperatures,
        restrict_to_pilot=True,
        analyze=True,
        log_filename="pilot_progress.log",
        report_filename="pilot_report.json",
        schema="skyt-humaneval-plus-pilot-v1",
    )
    return report


def run_full(
    *,
    out_dir: Path,
    n: int,
    allow_api: bool,
    models: Optional[List[str]] = None,
    temperatures: Optional[List[float]] = None,
    force: bool = False,
    only_incomplete: bool = False,
) -> Dict[str, Any]:
    """164-task overlay at protocol N. New tree only. No SKYT analysis."""
    from benchmark.protect import assert_writable
    from benchmark.schema import FROZEN_PROTOCOL_N

    protocol_n = FROZEN_PROTOCOL_N
    if int(MANIFEST["n_full"]) != protocol_n:
        raise ValueError(
            f"experiment_manifest n_full={MANIFEST['n_full']} must equal "
            f"protocol N={protocol_n}"
        )
    if n != protocol_n:
        raise ValueError(
            f"Full HumanEval+ overlay uses protocol N={protocol_n} (SPEC OPEN 3 "
            f"settled). Got N={n}. The 30-task pilot stays N=10 in its own tree."
        )
    assert_writable(out_dir)
    if not allow_api:
        raise ApiSpendBlocked(
            "Refusing to call an LLM. Re-run with --allow-api after smoke tests pass."
        )
    models = list(models or MANIFEST["models"])
    models = sorted(models, key=lambda name: (0 if name.startswith("claude-") else 1, name))
    temperatures = [
        float(item)
        for item in (
            temperatures if temperatures is not None else MANIFEST["temperatures"]
        )
    ]
    task_ids = all_evalplus_task_ids()
    if only_incomplete:
        task_ids = incomplete_task_ids(
            out_dir,
            n=n,
            task_ids=task_ids,
            models=models,
            temperatures=temperatures,
        )
        print(f"Incomplete tasks ({len(task_ids)}): {task_ids}", flush=True)
        if not task_ids:
            from .cost import collect_cost

            return {
                "schema": "skyt-humaneval-plus-full-v1",
                "n_configs": 0,
                "n_complete": 0,
                "n_tasks": 164,
                "n": n,
                "cost": collect_cost(out_dir) if out_dir.exists() else {},
            }
    return run_grid(
        task_ids=task_ids,
        out_dir=out_dir,
        n=n,
        allow_api=allow_api,
        models=models,
        temperatures=temperatures,
        restrict_to_pilot=False,
        analyze=False,
        force=force,
        log_filename="full_progress.log",
        report_filename="full_report.json",
        schema="skyt-humaneval-plus-full-v1",
    )

