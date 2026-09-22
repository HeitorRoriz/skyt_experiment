"""Held-out SKYT with HumanEval base as the operational oracle.

Plus tests are stored for evaluation and are not used to pick a canon or to
roll back a repair. Writes a sibling tree; never overwrites the overlay or
the plus-operational held-out tree. No LLM. Requires Docker on cache misses.
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

from benchmarks.humaneval_plus.manifest import MANIFEST
from benchmarks.humaneval_plus.provenance import atomic_write_json, attach_oracle, sha256_text
from benchmarks.humaneval_plus.sandbox import (
    SandboxUnavailable,
    docker_available,
    evaluate_base_only,
    evaluate_stitched,
)
from benchmarks.humaneval_plus.run import (
    _config_complete,
    _load_existing,
    _safe_name,
    all_evalplus_task_ids,
)

from skyt.humaneval_heldout import (
    DEFAULT_N_SPLITS,
    DEFAULT_TRAIN_SIZE,
    HELDOUT_SEED,
    OVERLAY_SOURCE,
    _iter_configs,
    heldout_splits,
    select_train_canon,
)
from skyt.humaneval_repair import (
    CachedPlusOracle,
    EnhancedCodeTransformer,
    _load_plus_problem,
    _plus_oracle_fields,
    apply_certified_consensus_repair,
    humaneval_repair_contract,
)


ORACLE_SPLIT_OUT = (
    Path("outputs") / "benchmark" / "humaneval_plus_164_n20_skyt_heldout_oracle_split"
)
SCHEMA = "skyt-humaneval-plus-heldout-oracle-split-v1"


def _base_operational_payload(record: Dict[str, Any]) -> Dict[str, Any]:
    oracle = record.get("oracle") or {}
    base = bool(oracle.get("base_passed"))
    plus = oracle.get("plus_passed")
    return {
        "passed": base,
        "pass_rate": 1.0 if base else 0.0,
        "base_status": oracle.get("base_status"),
        "base_passed": base,
        "plus_status": oracle.get("plus_status"),
        "plus_passed": plus,
        "certified": bool(plus) if plus is not None else False,
    }


class CachedOperationalOracle(CachedPlusOracle):
    """Base tests only for pick / rollback. Plus is filled after SKYT commits."""

    def seed_from_record(self, code: str, record: Dict[str, Any]) -> None:
        self.cache[sha256_text(code or "")] = _base_operational_payload(record)

    def run_oracle_tests(
        self, code: str, contract: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        key = sha256_text(code or "")
        cached = self.cache.get(key)
        if cached is not None:
            self.n_hits += 1
            payload = dict(cached)
        else:
            self.n_misses += 1
            result = evaluate_base_only(code or "", self.problem)
            payload = {
                "passed": bool(result.get("base_passed")),
                "pass_rate": 1.0 if result.get("base_passed") else 0.0,
                "base_status": result.get("base_status"),
                "base_passed": bool(result.get("base_passed")),
                "plus_status": "not_run",
                "plus_passed": None,
                "certified": False,
            }
            self.cache[key] = dict(payload)
        payload["passed"] = bool(payload.get("base_passed"))
        payload["pass_rate"] = 1.0 if payload["passed"] else 0.0
        return payload


def attach_plus_evaluation(
    records: List[Dict[str, Any]],
    *,
    overlay_by_hash: Dict[str, Dict[str, Any]],
    problem: Dict[str, Any],
    eval_cache: Dict[str, Dict[str, Any]],
) -> None:
    """Fill EvalPlus plus_passed after SKYT has already committed the artifact."""
    for index, record in enumerate(records):
        oracle = record.get("oracle") or {}
        if oracle.get("plus_passed") is not None:
            continue
        code = record.get("stitched_code") or ""
        key = sha256_text(code)
        if key in overlay_by_hash:
            records[index] = attach_oracle(record, overlay_by_hash[key])
            continue
        if key not in eval_cache:
            eval_cache[key] = _plus_oracle_fields(evaluate_stitched(code, problem))
        records[index] = attach_oracle(record, eval_cache[key])


def dual_repeatability(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    ordered = sorted(records, key=lambda item: int(item.get("run_index", 0)))
    prints = [
        fingerprint(record.get("stitched_code") or "", flexible_naming=True)
        for record in ordered
    ]
    base_cert = [
        bool((record.get("oracle") or {}).get("base_passed")) and fp is not None
        for record, fp in zip(ordered, prints)
    ]
    plus_cert = [
        _is_certified(record, fp is not None) for record, fp in zip(ordered, prints)
    ]
    base = config_repeatability(prints, base_cert)
    plus = config_repeatability(prints, plus_cert)
    return {
        "same_at_2": base["same_at_2"],
        "same_at_2_given_cert": base["same_at_2_given_cert"],
        "base_pass": base["plus_pass"],
        "plus_pass": plus["plus_pass"],
        "plus_same_at_2": plus["same_at_2"],
        "plus_same_at_2_given_cert": plus["same_at_2_given_cert"],
        "n_base_certified": base["n_certified"],
        "n_plus_certified": plus["n_certified"],
        "u_statistic_pair_count": base["u_statistic_pair_count"],
        "relation_version": RELATION_VERSION,
    }


def _mean_field(rows: Sequence[Dict[str, Any]], key: str) -> Optional[float]:
    values = [row[key] for row in rows if row.get(key) is not None]
    if not values:
        return None
    return statistics.mean(float(value) for value in values)


def _prefix(prefix: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    keep = (
        "same_at_2",
        "same_at_2_given_cert",
        "base_pass",
        "plus_pass",
        "plus_same_at_2",
        "plus_same_at_2_given_cert",
        "n_base_certified",
        "n_plus_certified",
    )
    return {f"{prefix}_{name}": fields[name] for name in keep}


def oracle_split_config(
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
    max_transformation_level: int = 3,
) -> Dict[str, Any]:
    source_dir = source_dir.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    if source_dir == out_dir:
        raise ValueError("Refusing to overwrite the overlay source directory")
    if int(max_transformation_level) != 3 and out_dir == ORACLE_SPLIT_OUT.expanduser().resolve():
        raise ValueError(
            "Level ablation must write a sibling tree; refusing to overwrite "
            "the oracle-split headline directory"
        )
    assert_writable(out_dir)
    if n != FROZEN_PROTOCOL_N:
        raise ValueError(f"Oracle-split rewrite uses protocol N={FROZEN_PROTOCOL_N}")
    if train_size != n // 2:
        raise ValueError(f"train_size must be n//2={n // 2}")
    if not docker_available():
        raise SandboxUnavailable("Docker is required to score repaired HumanEval+")
    if EnhancedCodeTransformer is None:
        raise RuntimeError("EnhancedCodeTransformer import failed")

    stem = _safe_name(task_id, model, temperature)
    source_jsonl = source_dir / f"{stem}.jsonl"
    summary_path = out_dir / f"{stem}_oracle_split.json"
    raw = _load_existing(source_jsonl)
    if not _config_complete(raw, n):
        raise ValueError(f"{stem}: overlay source is incomplete")
    records = sorted(raw, key=lambda item: int(item["run_index"]))[:n]
    if not force and summary_path.exists():
        prior = json.loads(summary_path.read_text(encoding="utf-8"))
        if (
            prior.get("schema") == SCHEMA
            and int(prior.get("n_splits") or 0) == n_splits
            and int(prior.get("n") or 0) == n
            and int(prior.get("cv_seed") or 0) == seed
            and int(prior.get("max_transformation_level") or 3) == int(max_transformation_level)
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
    oracle = CachedOperationalOracle(problem)
    overlay_by_hash: Dict[str, Dict[str, Any]] = {}
    for record in records:
        oracle.seed_from_record(record.get("stitched_code") or "", record)
        overlay_by_hash[sha256_text(record.get("stitched_code") or "")] = (
            record.get("oracle") or {}
        )
    plus_eval_cache: Dict[str, Dict[str, Any]] = {}

    splits = heldout_splits(n, train_size, n_splits, seed)
    universe = set(range(n))
    canon_system = CanonSystem(str(out_dir / "canon" / stem))
    transformer = EnhancedCodeTransformer(canon_system, enable_agents=False)
    transformer.enable_agents = False

    split_rows: List[Dict[str, Any]] = []
    for split_id, train_tuple in enumerate(splits):
        train = list(train_tuple)
        test = sorted(universe - set(train))
        selected = select_train_canon(
            records, contract_dict, train, payload_fn=_base_operational_payload
        )
        test_records = [records[index] for index in test]
        pre = dual_repeatability(test_records)
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
                max_transformation_level=int(max_transformation_level),
            )
        )
        attach_plus_evaluation(
            repaired,
            overlay_by_hash=overlay_by_hash,
            problem=problem,
            eval_cache=plus_eval_cache,
        )
        post = dual_repeatability(repaired)
        split_rows.append(
            {
                "split_id": split_id,
                "train_indices": train,
                "test_indices": test,
                "canon_created": selected is not None,
                "consensus_index": None if selected is None else selected["index"],
                "n_transformed": n_transformed,
                "n_rolled_back": n_rolled_back,
                **_prefix("pre", pre),
                **_prefix("post", post),
            }
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema": SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "model": model,
        "temperature": temperature,
        "n": n,
        "train_size": train_size,
        "n_splits": len(splits),
        "cv_seed": seed,
        "repair_policy": "certified_consensus",
        "operational_oracle": "humaneval_base",
        "evaluation_oracle": "evalplus_plus",
        "max_transformation_level": int(max_transformation_level),
        "heldout": True,
        "relation_version": RELATION_VERSION,
        "source_jsonl": str(source_jsonl),
        "n_splits_with_canon": sum(1 for row in split_rows if row["canon_created"]),
        "n_transformed_mean": _mean_field(split_rows, "n_transformed"),
        "n_rolled_back_mean": _mean_field(split_rows, "n_rolled_back"),
        "oracle_cache_hits": oracle.n_hits,
        "oracle_cache_misses": oracle.n_misses,
        "pre_same_at_2": _mean_field(split_rows, "pre_same_at_2"),
        "post_same_at_2": _mean_field(split_rows, "post_same_at_2"),
        "pre_same_at_2_given_cert": _mean_field(
            split_rows, "pre_same_at_2_given_cert"
        ),
        "post_same_at_2_given_cert": _mean_field(
            split_rows, "post_same_at_2_given_cert"
        ),
        "pre_base_pass": _mean_field(split_rows, "pre_base_pass"),
        "post_base_pass": _mean_field(split_rows, "post_base_pass"),
        "pre_plus_pass": _mean_field(split_rows, "pre_plus_pass"),
        "post_plus_pass": _mean_field(split_rows, "post_plus_pass"),
        "splits": split_rows,
    }
    atomic_write_json(summary_path, summary)
    return summary


def oracle_split_grid(
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
    max_transformation_level: int = 3,
) -> Dict[str, Any]:
    source_dir = source_dir.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    if source_dir == out_dir:
        raise ValueError("Refusing to overwrite the overlay source directory")
    if int(max_transformation_level) != 3 and out_dir == ORACLE_SPLIT_OUT.expanduser().resolve():
        raise ValueError(
            "Level ablation must write a sibling tree; refusing to overwrite "
            "the oracle-split headline directory"
        )
    assert_writable(out_dir)
    if not docker_available():
        raise SandboxUnavailable("Docker is required")

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
    if limit:
        configs = configs[: int(limit)]
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []
    n_failed = 0
    for index, (cfg_task, cfg_model, cfg_temp) in enumerate(configs, start=1):
        print(
            f"[{index}/{len(configs)}] oracle-split {cfg_task} {cfg_model} T={cfg_temp}",
            flush=True,
        )
        try:
            summary = oracle_split_config(
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
                max_transformation_level=int(max_transformation_level),
            )
            rows.append(
                {
                    "task_id": summary["task_id"],
                    "model": summary["model"],
                    "temperature": summary["temperature"],
                    "pre_same_at_2": summary.get("pre_same_at_2"),
                    "post_same_at_2": summary.get("post_same_at_2"),
                    "pre_plus_pass": summary.get("pre_plus_pass"),
                    "post_plus_pass": summary.get("post_plus_pass"),
                    "pre_base_pass": summary.get("pre_base_pass"),
                    "post_base_pass": summary.get("post_base_pass"),
                    "n_splits_with_canon": summary.get("n_splits_with_canon"),
                    "oracle_cache_misses": summary.get("oracle_cache_misses"),
                }
            )
        except Exception as exc:  # noqa: BLE001 — grid must continue
            n_failed += 1
            rows.append(
                {
                    "task_id": cfg_task,
                    "model": cfg_model,
                    "temperature": cfg_temp,
                    "error": str(exc),
                }
            )
            print(f"  FAILED {exc}", flush=True)

    scored = [row for row in rows if "error" not in row]

    def _boot(field: str) -> Dict[str, Any]:
        usable = [row for row in scored if row.get(field) is not None]
        if not usable:
            return {"mean": None, "lower": None, "upper": None}
        return cluster_bootstrap_mean(
            [float(row[field]) for row in usable],
            [str(row["task_id"]) for row in usable],
            n_bootstrap=n_bootstrap,
            seed=BOOTSTRAP_SEED,
        )

    report = {
        "schema": "skyt-humaneval-plus-oracle-split-grid-v1",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "operational_oracle": "humaneval_base",
        "evaluation_oracle": "evalplus_plus",
        "n_configs": len(rows),
        "n_scored": len(scored),
        "n_failed_configs": n_failed,
        "pre_same_at_2": _boot("pre_same_at_2"),
        "post_same_at_2": _boot("post_same_at_2"),
        "pre_plus_pass": _boot("pre_plus_pass"),
        "post_plus_pass": _boot("post_plus_pass"),
        "pre_base_pass": _boot("pre_base_pass"),
        "post_base_pass": _boot("post_base_pass"),
        "out_dir": str(out_dir),
        "configs": rows,
    }
    atomic_write_json(out_dir / "oracle_split_report.json", report)
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", default=str(OVERLAY_SOURCE))
    parser.add_argument("--out-dir", default=str(ORACLE_SPLIT_OUT))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--task-id")
    parser.add_argument("--model")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--max-transformation-level", type=int, default=3)
    args = parser.parse_args()
    report = oracle_split_grid(
        source_dir=Path(args.source_dir),
        out_dir=Path(args.out_dir),
        limit=int(args.limit),
        task_id=args.task_id,
        model=args.model,
        temperature=args.temperature,
        force=bool(args.force),
        max_transformation_level=int(args.max_transformation_level),
    )
    print(
        json.dumps(
            {
                "n_scored": report["n_scored"],
                "n_failed_configs": report["n_failed_configs"],
                "post_same_at_2": (report.get("post_same_at_2") or {}).get("mean"),
                "post_plus_pass": (report.get("post_plus_pass") or {}).get("mean"),
                "out_dir": report["out_dir"],
            },
            indent=2,
        )
    )
