"""Replay SKYT repair on stored HumanEval+ generations. No LLM calls.

Certified Consensus pick, repair toward that form, Docker plus-oracle, rollback
if tests break. Writes a parallel tree; never overwrites the Table 1 pilot.
No style contracts: function_name is only the Level-3 replace-with-canon target.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.canon_selection import select_certified_consensus_canon
from src.canon_system import CanonSystem
from src.contract import Contract

from benchmarks.humaneval_plus.analyze import analyze_records
from benchmarks.humaneval_plus.dataset import load_evalplus_problems
from benchmarks.humaneval_plus.manifest import PILOT_TASK_IDS
from benchmarks.humaneval_plus.provenance import attach_oracle, dump_jsonl, sha256_text
from benchmarks.humaneval_plus.run import _config_complete, _load_existing, _safe_name
from benchmarks.humaneval_plus.sandbox import SandboxUnavailable, docker_available, evaluate_stitched


try:
    from agents.enhanced_transformer import EnhancedCodeTransformer
except ImportError:  # pragma: no cover
    EnhancedCodeTransformer = None


def humaneval_repair_contract(
    *,
    task_id: str,
    model: str,
    temperature: float,
    prompt: str,
    entry_point: str,
) -> Dict[str, Any]:
    """Minimal contract so CanonSystem/Contract.validate succeed.

    Not a style contract. ``function_name`` is the transformer’s replace-with-canon
    target (the HumanEval entry point).
    """
    return {
        "id": _safe_name(task_id, model, temperature),
        "task_intent": f"HumanEval+ {task_id}",
        "prompt": prompt,
        "language": "python",
        "contract_version": "heplus-repair-v1",
        "created_timestamp": "2026-09-02T00:00:00+00:00",
        "constraints": {
            "variable_naming": {"naming_policy": "flexible"},
            "function_name": entry_point,
        },
    }


def _oracle_payload(record: Dict[str, Any]) -> Dict[str, Any]:
    oracle = record.get("oracle") or {}
    certified = bool(oracle.get("certified"))
    return {
        "passed": certified,
        "pass_rate": 1.0 if certified else 0.0,
        "base_status": oracle.get("base_status"),
        "base_passed": oracle.get("base_passed"),
        "plus_status": oracle.get("plus_status"),
        "plus_passed": oracle.get("plus_passed"),
        "certified": certified,
    }


def _plus_oracle_fields(result: Dict[str, Any]) -> Dict[str, Any]:
    certified = bool(result.get("certified"))
    return {
        "passed": certified,
        "pass_rate": 1.0 if certified else 0.0,
        "base_status": result.get("base_status"),
        "base_passed": result.get("base_passed"),
        "plus_status": result.get("plus_status"),
        "plus_passed": result.get("plus_passed"),
        "certified": certified,
    }


class CachedPlusOracle:
    """Docker plus tests, keyed by code hash. Seeds from stored Table 1 oracles."""

    def __init__(self, problem: Dict[str, Any]):
        self.problem = problem
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.n_hits = 0
        self.n_misses = 0

    def seed_from_record(self, code: str, record: Dict[str, Any]) -> None:
        self.cache[sha256_text(code or "")] = _oracle_payload(record)

    def run_oracle_tests(self, code: str, contract: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        key = sha256_text(code or "")
        cached = self.cache.get(key)
        if cached is not None:
            self.n_hits += 1
            return dict(cached)
        self.n_misses += 1
        result = evaluate_stitched(code or "", self.problem)
        payload = _plus_oracle_fields(result)
        self.cache[key] = payload
        return dict(payload)


def _load_plus_problem(source_dir: Path, task_id: str) -> Dict[str, Any]:
    problems, _digest = load_evalplus_problems()
    problem = dict(problems[task_id])
    cache_path = source_dir / "plus_cases" / f"{_safe_name(task_id, 'canon', 0.0)}.json"
    if cache_path.exists():
        problem["plus_cases"] = json.loads(cache_path.read_text(encoding="utf-8"))
    return problem


def _paired_counts(pre: List[Dict[str, Any]], post: List[Dict[str, Any]]) -> Dict[str, int]:
    regressions = rescues = 0
    for before, after in zip(pre, post):
        pre_ok = bool((before.get("oracle") or {}).get("certified"))
        post_ok = bool((after.get("oracle") or {}).get("certified"))
        if pre_ok and not post_ok:
            regressions += 1
        if (not pre_ok) and post_ok:
            rescues += 1
    return {"n_regressions": regressions, "n_rescues": rescues}


def apply_certified_consensus_repair(
    *,
    records: List[Dict[str, Any]],
    selected: Optional[Dict[str, Any]],
    contract_dict: Dict[str, Any],
    oracle: CachedPlusOracle,
    canon_store: Path,
    consensus_index: Optional[int] = None,
    canon_system: Optional[CanonSystem] = None,
    transformer: Optional[Any] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int, int]:
    """Repair ``records`` toward a frozen Certified Consensus form.

    ``selected`` is None when the train (or in-sample) slice has no certified
    consensus: copy the records and skip the transformer. Does not change how
    the runtime picks a canon.
    """
    repaired_records: List[Dict[str, Any]] = []
    transform_rows: List[Dict[str, Any]] = []
    n_rolled_back = 0
    n_transformed = 0
    if selected is None:
        for record in records:
            updated = deepcopy(record)
            updated["stitched_code_pre"] = record.get("stitched_code")
            updated["oracle_pre"] = record.get("oracle")
            updated["repair_applied"] = False
            updated["repair_policy"] = "certified_consensus"
            updated["skipped_reason"] = "no_certified_consensus_canon"
            updated["rolled_back"] = False
            repaired_records.append(updated)
            transform_rows.append(
                {
                    "run_index": record.get("run_index"),
                    "transformation_needed": False,
                    "skipped_reason": "no_certified_consensus_canon",
                }
            )
        return repaired_records, transform_rows, n_transformed, n_rolled_back

    if EnhancedCodeTransformer is None:
        raise RuntimeError("EnhancedCodeTransformer import failed")
    codes = [record.get("stitched_code") or "" for record in records]
    if canon_system is None:
        canon_system = CanonSystem(str(canon_store))
    contract = Contract(contract_dict)
    canon_system.create_canon(
        contract,
        selected["code"],
        oracle_result=selected["oracle_result"],
        require_oracle_pass=True,
    )
    if transformer is None:
        transformer = EnhancedCodeTransformer(canon_system, enable_agents=False)
        transformer.enable_agents = False
    else:
        transformer.enable_agents = False
    contract_id = contract_dict["id"]
    index = selected["index"] if consensus_index is None else consensus_index
    for record, code in zip(records, codes):
        comparison = canon_system.compare_to_canon(contract_id, code, contract_dict)
        updated = deepcopy(record)
        updated["stitched_code_pre"] = code
        updated["oracle_pre"] = record.get("oracle")
        updated["repair_policy"] = "certified_consensus"
        updated["consensus_index"] = index
        if comparison.get("is_identical"):
            updated["repair_applied"] = False
            updated["rolled_back"] = False
            updated["skipped_reason"] = "already_consensus_form"
            repaired_records.append(updated)
            transform_rows.append(
                {
                    "run_index": record.get("run_index"),
                    "transformation_needed": False,
                    "final_distance": comparison.get("distance"),
                    "skipped_reason": "already_consensus_form",
                }
            )
            continue
        result = transformer.transform_to_canon(
            code,
            contract_id,
            contract=contract_dict,
            oracle_system=oracle,
        )
        candidate = result.get("transformed_code", code)
        post = oracle.run_oracle_tests(candidate, contract_dict)
        if result.get("rolled_back"):
            n_rolled_back += 1
        if candidate != code and not result.get("rolled_back"):
            n_transformed += 1
        updated["stitched_code"] = candidate
        updated = attach_oracle(updated, post)
        updated["repair_applied"] = candidate != code
        updated["rolled_back"] = bool(result.get("rolled_back"))
        updated["transformation_level"] = result.get("transformation_level")
        updated["transformations_applied"] = result.get("transformations_applied")
        repaired_records.append(updated)
        transform_rows.append(
            {
                "run_index": record.get("run_index"),
                "transformation_needed": True,
                "transformation_success": result.get("success"),
                "rolled_back": result.get("rolled_back"),
                "final_distance": result.get("final_distance"),
                "transformation_level": result.get("transformation_level"),
            }
        )
    return repaired_records, transform_rows, n_transformed, n_rolled_back


def repair_config(
    *,
    source_dir: Path,
    out_dir: Path,
    task_id: str,
    model: str,
    temperature: float,
    n: int = 10,
    force: bool = False,
) -> Dict[str, Any]:
    if source_dir.resolve() == out_dir.resolve():
        raise ValueError("Refusing to overwrite the Table 1 source directory")
    if not docker_available():
        raise SandboxUnavailable("Docker is required to score repaired HumanEval+")
    if EnhancedCodeTransformer is None:
        raise RuntimeError("EnhancedCodeTransformer import failed")

    stem = _safe_name(task_id, model, temperature)
    source_jsonl = source_dir / f"{stem}.jsonl"
    jsonl_path = out_dir / f"{stem}.jsonl"
    summary_path = out_dir / f"{stem}_summary.json"
    raw = _load_existing(source_jsonl)
    if not _config_complete(raw, n):
        raise ValueError(f"{stem}: Table 1 source is incomplete")
    records = sorted(raw, key=lambda item: int(item["run_index"]))[:n]
    if not force and _config_complete(_load_existing(jsonl_path), n) and summary_path.exists():
        return json.loads(summary_path.read_text(encoding="utf-8"))

    problem = _load_plus_problem(source_dir, task_id)
    entry_point = problem["entry_point"]
    contract_dict = humaneval_repair_contract(
        task_id=task_id,
        model=model,
        temperature=temperature,
        prompt=problem["prompt"],
        entry_point=entry_point,
    )
    codes = [record.get("stitched_code") or "" for record in records]
    oracle_results = [_oracle_payload(record) for record in records]
    selected = select_certified_consensus_canon(codes, contract_dict, oracle_results)

    oracle = CachedPlusOracle(problem)
    for code, record in zip(codes, records):
        oracle.seed_from_record(code, record)

    repaired_records, transform_rows, n_transformed, n_rolled_back = (
        apply_certified_consensus_repair(
            records=records,
            selected=selected,
            contract_dict=contract_dict,
            oracle=oracle,
            canon_store=out_dir / "canon" / stem,
            consensus_index=None if selected is None else selected["index"],
        )
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    dump_jsonl(jsonl_path, repaired_records)
    analysis = analyze_records(repaired_records)
    paired = _paired_counts(records, repaired_records)
    summary = {
        "schema": "skyt-humaneval-plus-repair-summary-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "model": model,
        "temperature": temperature,
        "n": n,
        "repair_policy": "certified_consensus",
        "no_skyt_repair": False,
        "no_style_contracts": True,
        "canon_created": selected is not None,
        "consensus_index": None if selected is None else selected["index"],
        "n_certified_pre": sum(
            1 for record in records if (record.get("oracle") or {}).get("certified")
        ),
        "n_transformed": n_transformed,
        "n_rolled_back": n_rolled_back,
        "oracle_cache_hits": oracle.n_hits,
        "oracle_cache_misses": oracle.n_misses,
        "source_jsonl": str(source_jsonl),
        "jsonl": str(jsonl_path),
        "analysis": analysis,
        "n_base_passed": analysis["n_base_passed"],
        "n_plus_certified": analysis["n_plus_certified"],
        **paired,
        "transforms": transform_rows,
    }
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary


def repair_pilot(
    *,
    source_dir: Path,
    out_dir: Path,
    n: int = 10,
    force: bool = False,
    limit: int = 0,
) -> Dict[str, Any]:
    if source_dir.resolve() == out_dir.resolve():
        raise ValueError("Refusing to overwrite the Table 1 source directory")
    models = ["claude-sonnet-4-5-20250929", "gpt-4o-mini"]
    temperatures = [0.0, 0.7]
    configs = [
        (task_id, model, float(temp))
        for model in models
        for task_id in PILOT_TASK_IDS
        for temp in temperatures
    ]
    rows = []
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "repair_progress.log"
    done = 0
    for index, (task_id, model, temp) in enumerate(configs, start=1):
        line = f"[{index}/{len(configs)}] {task_id} {model} T={temp}"
        print(line, flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        try:
            summary = repair_config(
                source_dir=source_dir,
                out_dir=out_dir,
                task_id=task_id,
                model=model,
                temperature=temp,
                n=n,
                force=force,
            )
        except Exception as exc:
            err = type(exc).__name__
            print(f"  FAILED {err}: {str(exc)[:300]}", flush=True)
            rows.append(
                {
                    "task_id": task_id,
                    "model": model,
                    "temperature": temp,
                    "error": err,
                }
            )
            done += 1
            if limit and done >= limit:
                break
            continue
        print(
            f"  plus={summary.get('n_plus_certified')} "
            f"reg={summary.get('n_regressions')} "
            f"rescue={summary.get('n_rescues')} "
            f"canon={summary.get('canon_created')}",
            flush=True,
        )
        rows.append(
            {
                "task_id": task_id,
                "model": model,
                "temperature": temp,
                "n_plus_certified": summary.get("n_plus_certified"),
                "n_regressions": summary.get("n_regressions"),
                "n_rescues": summary.get("n_rescues"),
                "canon_created": summary.get("canon_created"),
                "n_transformed": summary.get("n_transformed"),
                "n_rolled_back": summary.get("n_rolled_back"),
            }
        )
        done += 1
        if limit and done >= limit:
            break
    report = {
        "schema": "skyt-humaneval-plus-repair-pilot-v1",
        "n_configs": len(rows),
        "n": n,
        "repair_policy": "certified_consensus",
        "no_style_contracts": True,
        "source_dir": str(source_dir),
        "out_dir": str(out_dir),
        "n_regressions": sum(int(row.get("n_regressions") or 0) for row in rows if "error" not in row),
        "n_rescues": sum(int(row.get("n_rescues") or 0) for row in rows if "error" not in row),
        "n_failed_configs": sum(1 for row in rows if "error" in row),
        "configs": rows,
    }
    (out_dir / "repair_report.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    return report
