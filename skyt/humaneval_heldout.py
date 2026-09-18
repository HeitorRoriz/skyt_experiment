"""Held-out SKYT rewrite on stored HumanEval+ overlay generations. No LLM calls.

Pick Certified Consensus on a train slice of 10, freeze that form, SKYT-repair
the held-out 10, then score fingerprint same@2 / same@2|cert on the rewritten
test slice. Mean over balanced splits (seed 20260723). Writes a parallel tree;
never overwrites the 164 overlay, Gate 0, or the 30-task pilot.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from benchmark.metrics import cluster_bootstrap_mean, config_repeatability
from benchmark.protect import assert_writable
from benchmark.relation import RELATION_VERSION, fingerprint
from benchmark.schema import BOOTSTRAP_SEED, DEFAULT_N_BOOTSTRAP, FROZEN_PROTOCOL_N
from benchmark.score import _is_certified
from src.canon_system import CanonSystem
from src.repeatability_protocol import _balanced_splits

from benchmarks.humaneval_plus.manifest import MANIFEST
from benchmarks.humaneval_plus.provenance import atomic_write_json
from benchmarks.humaneval_plus.run import (
    _config_complete,
    _load_existing,
    _safe_name,
    all_evalplus_task_ids,
)
from benchmarks.humaneval_plus.sandbox import SandboxUnavailable, docker_available

from skyt.humaneval_repair import (
    CachedPlusOracle,
    EnhancedCodeTransformer,
    _load_plus_problem,
    _oracle_payload,
    apply_certified_consensus_repair,
    humaneval_repair_contract,
    select_certified_consensus_canon,
)


HELDOUT_SEED = BOOTSTRAP_SEED
DEFAULT_TRAIN_SIZE = 10
DEFAULT_N_SPLITS = 20
OVERLAY_SOURCE = Path("outputs") / "benchmark" / "humaneval_plus_164_n20"
HELDOUT_OUT = Path("outputs") / "benchmark" / "humaneval_plus_164_n20_skyt_heldout"


def heldout_splits(
    n: int,
    train_size: int,
    n_splits: int,
    seed: int = HELDOUT_SEED,
) -> List[Tuple[int, ...]]:
    return _balanced_splits(n, train_size, n_splits, seed)


def fingerprint_repeatability(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    ordered = sorted(records, key=lambda item: int(item.get("run_index", 0)))
    prints = [
        fingerprint(record.get("stitched_code") or "", flexible_naming=True)
        for record in ordered
    ]
    certified = [
        _is_certified(record, fp is not None) for record, fp in zip(ordered, prints)
    ]
    analysis = config_repeatability(prints, certified)
    analysis["relation_version"] = RELATION_VERSION
    return analysis


def select_train_canon(
    records: Sequence[Dict[str, Any]],
    contract_dict: Dict[str, Any],
    train_indices: Sequence[int],
) -> Optional[Dict[str, Any]]:
    """Certified Consensus on the train slice only. Index is into ``records``."""
    train = [records[index] for index in train_indices]
    codes = [record.get("stitched_code") or "" for record in train]
    oracles = [_oracle_payload(record) for record in train]
    selected = select_certified_consensus_canon(codes, contract_dict, oracles)
    if selected is None:
        return None
    local = int(selected["index"])
    global_index = int(train_indices[local])
    return {
        **selected,
        "index": global_index,
        "train_index": local,
        "run_index": int(records[global_index].get("run_index", global_index)),
    }


def _metric_fields(analysis: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "same_at_2": analysis["same_at_2"],
        "same_at_2_given_cert": analysis["same_at_2_given_cert"],
        "plus_pass": analysis["plus_pass"],
        "n_certified": analysis["n_certified"],
        "u_statistic_pair_count": analysis["u_statistic_pair_count"],
        "u_statistic_certified_pair_count": analysis[
            "u_statistic_certified_pair_count"
        ],
    }


def _mean_field(rows: Sequence[Dict[str, Any]], key: str) -> Optional[float]:
    values = [row[key] for row in rows if row.get(key) is not None]
    if not values:
        return None
    return statistics.mean(float(value) for value in values)


def _prefix_metrics(prefix: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    return {f"{prefix}_{name}": value for name, value in fields.items()}


def heldout_config(
    *,
    source_dir: Path,
    out_dir: Path,
    task_id: str,
    model: str,
    temperature: float,
    n: int = FROZEN_PROTOCOL_N,
    train_size: int = DEFAULT_TRAIN_SIZE,
    n_splits: int = DEFAULT_N_SPLITS,
    seed: int = HELDOUT_SEED,
    force: bool = False,
) -> Dict[str, Any]:
    source_dir = source_dir.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    if source_dir == out_dir:
        raise ValueError("Refusing to overwrite the overlay source directory")
    assert_writable(out_dir)
    if n != FROZEN_PROTOCOL_N:
        raise ValueError(
            f"Held-out rewrite is the protocol N={FROZEN_PROTOCOL_N} overlay "
            f"(train {train_size} / test {n - train_size}). Got N={n}."
        )
    if train_size != n // 2:
        raise ValueError(
            f"Held-out train_size must be n//2={n // 2} (got {train_size})"
        )
    if n_splits <= 0:
        raise ValueError("n_splits must be positive")
    if not docker_available():
        raise SandboxUnavailable("Docker is required to score repaired HumanEval+")
    if EnhancedCodeTransformer is None:
        raise RuntimeError("EnhancedCodeTransformer import failed")

    stem = _safe_name(task_id, model, temperature)
    source_jsonl = source_dir / f"{stem}.jsonl"
    summary_path = out_dir / f"{stem}_heldout.json"
    raw = _load_existing(source_jsonl)
    if not _config_complete(raw, n):
        raise ValueError(f"{stem}: overlay source is incomplete")
    records = sorted(raw, key=lambda item: int(item["run_index"]))[:n]
    if not force and summary_path.exists():
        prior = json.loads(summary_path.read_text(encoding="utf-8"))
        if (
            prior.get("schema") == "skyt-humaneval-plus-heldout-summary-v1"
            and int(prior.get("n_splits") or 0) == n_splits
            and int(prior.get("n") or 0) == n
            and int(prior.get("cv_seed") or 0) == seed
        ):
            return prior

    problem = _load_plus_problem(source_dir, task_id)
    contract_dict = humaneval_repair_contract(
        task_id=task_id,
        model=model,
        temperature=temperature,
        prompt=problem["prompt"],
        entry_point=problem["entry_point"],
    )
    oracle = CachedPlusOracle(problem)
    for record in records:
        oracle.seed_from_record(record.get("stitched_code") or "", record)

    splits = heldout_splits(n, train_size, n_splits, seed)
    universe = set(range(n))
    canon_system = CanonSystem(str(out_dir / "canon" / stem))
    transformer = EnhancedCodeTransformer(canon_system, enable_agents=False)
    transformer.enable_agents = False

    split_rows: List[Dict[str, Any]] = []
    for split_id, train_tuple in enumerate(splits):
        train = list(train_tuple)
        test = sorted(universe - set(train))
        selected = select_train_canon(records, contract_dict, train)
        test_records = [records[index] for index in test]
        pre = fingerprint_repeatability(test_records)
        repaired, transform_rows, n_transformed, n_rolled_back = (
            apply_certified_consensus_repair(
                records=test_records,
                selected=selected,
                contract_dict=contract_dict,
                oracle=oracle,
                canon_store=out_dir / "canon" / stem,
                consensus_index=None if selected is None else selected["index"],
                canon_system=canon_system,
                transformer=transformer,
            )
        )
        post = fingerprint_repeatability(repaired)
        split_rows.append(
            {
                "split_id": split_id,
                "train_indices": train,
                "test_indices": test,
                "canon_created": selected is not None,
                "consensus_index": None if selected is None else selected["index"],
                "consensus_run_index": (
                    None if selected is None else selected.get("run_index")
                ),
                "n_transformed": n_transformed,
                "n_rolled_back": n_rolled_back,
                "n_already_consensus": sum(
                    1
                    for row in transform_rows
                    if row.get("skipped_reason") == "already_consensus_form"
                ),
                **_prefix_metrics("pre", _metric_fields(pre)),
                **_prefix_metrics("post", _metric_fields(post)),
            }
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema": "skyt-humaneval-plus-heldout-summary-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "model": model,
        "temperature": temperature,
        "n": n,
        "train_size": train_size,
        "heldout_test_size": n - train_size,
        "n_splits": len(splits),
        "cv_seed": seed,
        "repair_policy": "certified_consensus",
        "heldout": True,
        "in_sample": False,
        "no_style_contracts": True,
        "relation_version": RELATION_VERSION,
        "source_jsonl": str(source_jsonl),
        "n_splits_with_canon": sum(1 for row in split_rows if row["canon_created"]),
        "n_transformed_mean": _mean_field(split_rows, "n_transformed"),
        "n_rolled_back_mean": _mean_field(split_rows, "n_rolled_back"),
        "oracle_cache_hits": oracle.n_hits,
        "oracle_cache_misses": oracle.n_misses,
        "pre_same_at_2": _mean_field(split_rows, "pre_same_at_2"),
        "pre_same_at_2_given_cert": _mean_field(
            split_rows, "pre_same_at_2_given_cert"
        ),
        "pre_plus_pass": _mean_field(split_rows, "pre_plus_pass"),
        "post_same_at_2": _mean_field(split_rows, "post_same_at_2"),
        "post_same_at_2_given_cert": _mean_field(
            split_rows, "post_same_at_2_given_cert"
        ),
        "post_plus_pass": _mean_field(split_rows, "post_plus_pass"),
        "splits": split_rows,
    }
    atomic_write_json(summary_path, summary)
    return summary


def _bootstrap_metric(
    rows: Sequence[Dict[str, Any]],
    field: str,
    *,
    n_bootstrap: int,
) -> Dict[str, Any]:
    usable = [row for row in rows if row.get(field) is not None]
    if not usable:
        return {
            "mean": None,
            "lower": None,
            "upper": None,
            "n_defined": 0,
            "n_dropped": len(rows),
            "n_clusters": 0,
        }
    result = cluster_bootstrap_mean(
        [float(row[field]) for row in usable],
        [str(row["task_id"]) for row in usable],
        n_bootstrap=n_bootstrap,
        seed=BOOTSTRAP_SEED,
    )
    result["n_defined"] = len(usable)
    result["n_dropped"] = len(rows) - len(usable)
    return result


def _heldout_slice(
    rows: Sequence[Dict[str, Any]],
    *,
    model: str,
    temperature: Any,
    n_bootstrap: int,
    phase: str,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "phase": phase,
        "n_configs": len(rows),
        "n_tasks": len({row["task_id"] for row in rows}),
        "n": FROZEN_PROTOCOL_N,
        "heldout_test_size": DEFAULT_TRAIN_SIZE,
        "pilot_grid": False,
    }
    for name in ("same_at_2", "same_at_2_given_cert", "plus_pass"):
        clustered = _bootstrap_metric(rows, name, n_bootstrap=n_bootstrap)
        payload[name] = clustered["mean"]
        payload[f"{name}_ci95"] = (
            None
            if clustered["mean"] is None
            else [clustered["lower"], clustered["upper"]]
        )
        payload[f"{name}_n_defined"] = clustered["n_defined"]
        payload[f"{name}_n_dropped"] = clustered["n_dropped"]
        payload[f"{name}_n_clusters"] = clustered["n_clusters"]
        payload[f"{name}_pct"] = (
            None if clustered["mean"] is None else round(100.0 * clustered["mean"], 1)
        )
    return payload


def _phase_rows(rows: Sequence[Dict[str, Any]], phase: str) -> List[Dict[str, Any]]:
    prefix = f"{phase}_"
    out = []
    for row in rows:
        out.append(
            {
                "task_id": row["task_id"],
                "model": row["model"],
                "temperature": row["temperature"],
                "n": FROZEN_PROTOCOL_N,
                "same_at_2": row.get(f"{prefix}same_at_2"),
                "same_at_2_given_cert": row.get(f"{prefix}same_at_2_given_cert"),
                "plus_pass": row.get(f"{prefix}plus_pass"),
            }
        )
    return out


def _phase_report(
    rows: Sequence[Dict[str, Any]],
    *,
    phase: str,
    n_bootstrap: int,
) -> Dict[str, Any]:
    metric_rows = _phase_rows(rows, phase)
    groups: Dict[Tuple[str, float], List[Dict[str, Any]]] = {}
    for row in metric_rows:
        key = (str(row["model"]), float(row["temperature"]))
        groups.setdefault(key, []).append(row)
    slices = [
        _heldout_slice(
            groups[key],
            model=key[0],
            temperature=key[1],
            n_bootstrap=n_bootstrap,
            phase=phase,
        )
        for key in sorted(groups)
    ]
    return {
        "phase": phase,
        "all": _heldout_slice(
            metric_rows,
            model="both",
            temperature="both",
            n_bootstrap=n_bootstrap,
            phase=phase,
        ),
        "slices": slices,
    }


def _config_row(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "task_id": summary["task_id"],
        "model": summary["model"],
        "temperature": summary["temperature"],
        "n": summary["n"],
        "n_splits": summary["n_splits"],
        "n_splits_with_canon": summary.get("n_splits_with_canon"),
        "pre_same_at_2": summary.get("pre_same_at_2"),
        "pre_same_at_2_given_cert": summary.get("pre_same_at_2_given_cert"),
        "pre_plus_pass": summary.get("pre_plus_pass"),
        "post_same_at_2": summary.get("post_same_at_2"),
        "post_same_at_2_given_cert": summary.get("post_same_at_2_given_cert"),
        "post_plus_pass": summary.get("post_plus_pass"),
        "n_transformed_mean": summary.get("n_transformed_mean"),
        "n_rolled_back_mean": summary.get("n_rolled_back_mean"),
        "oracle_cache_misses": summary.get("oracle_cache_misses"),
    }


def _flush_report(
    *,
    out_dir: Path,
    source_dir: Path,
    rows: List[Dict[str, Any]],
    n: int,
    train_size: int,
    n_splits: int,
    seed: int,
    n_bootstrap: int,
    n_failed: int,
) -> Dict[str, Any]:
    scored = [row for row in rows if "error" not in row]
    report: Dict[str, Any] = {
        "schema": "skyt-humaneval-plus-heldout-grid-v1",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "n": n,
        "train_size": train_size,
        "heldout_test_size": n - train_size,
        "n_splits": n_splits,
        "cv_seed": seed,
        "n_bootstrap": n_bootstrap,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "relation_version": RELATION_VERSION,
        "repair_policy": "certified_consensus",
        "heldout": True,
        "in_sample": False,
        "source_dir": str(source_dir),
        "out_dir": str(out_dir),
        "n_configs": len(rows),
        "n_scored": len(scored),
        "n_failed_configs": n_failed,
        "pre": _phase_report(scored, phase="pre", n_bootstrap=n_bootstrap)
        if scored
        else None,
        "post": _phase_report(scored, phase="post", n_bootstrap=n_bootstrap)
        if scored
        else None,
        "configs": rows,
    }
    atomic_write_json(out_dir / "heldout_report.json", report)
    return report


def _iter_configs(
    *,
    task_ids: Sequence[str],
    models: Sequence[str],
    temperatures: Sequence[float],
    only_task_id: Optional[str],
    only_model: Optional[str],
    only_temperature: Optional[float],
) -> List[Tuple[str, str, float]]:
    models = sorted(models, key=lambda name: (0 if name.startswith("claude-") else 1, name))
    configs = [
        (task_id, model, float(temp))
        for model in models
        for task_id in task_ids
        for temp in temperatures
    ]
    if only_task_id:
        configs = [item for item in configs if item[0] == only_task_id]
    if only_model:
        configs = [item for item in configs if item[1] == only_model]
    if only_temperature is not None:
        configs = [item for item in configs if item[2] == float(only_temperature)]
    return configs


def heldout_grid(
    *,
    source_dir: Path,
    out_dir: Path,
    n: int = FROZEN_PROTOCOL_N,
    train_size: int = DEFAULT_TRAIN_SIZE,
    n_splits: int = DEFAULT_N_SPLITS,
    seed: int = HELDOUT_SEED,
    force: bool = False,
    limit: int = 0,
    task_id: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
) -> Dict[str, Any]:
    source_dir = source_dir.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    if source_dir == out_dir:
        raise ValueError("Refusing to overwrite the overlay source directory")
    assert_writable(out_dir)
    if not docker_available():
        raise SandboxUnavailable("Docker is required to score repaired HumanEval+")

    task_ids = all_evalplus_task_ids()
    models = list(MANIFEST["models"])
    temperatures = [float(item) for item in MANIFEST["temperatures"]]
    configs = _iter_configs(
        task_ids=task_ids,
        models=models,
        temperatures=temperatures,
        only_task_id=task_id,
        only_model=model,
        only_temperature=temperature,
    )
    if not configs:
        raise ValueError("No matching overlay configs")

    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "heldout_progress.log"
    rows: List[Dict[str, Any]] = []
    n_failed = 0
    done = 0
    report = _flush_report(
        out_dir=out_dir,
        source_dir=source_dir,
        rows=rows,
        n=n,
        train_size=train_size,
        n_splits=n_splits,
        seed=seed,
        n_bootstrap=n_bootstrap,
        n_failed=n_failed,
    )

    for index, (cfg_task, cfg_model, cfg_temp) in enumerate(configs, start=1):
        line = f"[{index}/{len(configs)}] {cfg_task} {cfg_model} T={cfg_temp}"
        print(line, flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
        try:
            summary = heldout_config(
                source_dir=source_dir,
                out_dir=out_dir,
                task_id=cfg_task,
                model=cfg_model,
                temperature=cfg_temp,
                n=n,
                train_size=train_size,
                n_splits=n_splits,
                seed=seed,
                force=force,
            )
        except Exception as exc:
            err = type(exc).__name__
            detail = str(exc)[:300]
            print(f"  FAILED {err}: {detail}", flush=True)
            rows.append(
                {
                    "task_id": cfg_task,
                    "model": cfg_model,
                    "temperature": cfg_temp,
                    "error": err,
                    "detail": detail,
                }
            )
            n_failed += 1
            done += 1
            report = _flush_report(
                out_dir=out_dir,
                source_dir=source_dir,
                rows=rows,
                n=n,
                train_size=train_size,
                n_splits=n_splits,
                seed=seed,
                n_bootstrap=n_bootstrap,
                n_failed=n_failed,
            )
            if limit and done >= limit:
                break
            continue
        row = _config_row(summary)
        print(
            f"  pre same@2={row.get('pre_same_at_2')} "
            f"post same@2={row.get('post_same_at_2')} "
            f"canon_splits={row.get('n_splits_with_canon')}/{summary.get('n_splits')} "
            f"docker_misses={row.get('oracle_cache_misses')}",
            flush=True,
        )
        rows.append(row)
        done += 1
        report = _flush_report(
            out_dir=out_dir,
            source_dir=source_dir,
            rows=rows,
            n=n,
            train_size=train_size,
            n_splits=n_splits,
            seed=seed,
            n_bootstrap=n_bootstrap,
            n_failed=n_failed,
        )
        if limit and done >= limit:
            break
    return report
