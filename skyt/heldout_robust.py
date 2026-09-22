"""Held-out SKYT robustness: persist repairs, extra B splits. No LLM.

Replays Certified Consensus repair on stored overlay generations. Oracle
results are inherited when the repaired entry point matches a stored program
(typical Level-3 substitution). Writes a sibling tree; never overwrites the
frozen overlay, Gate 0, the 30-task pilot, or the B=20 held-out summaries.
"""

from __future__ import annotations

import json
import statistics
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from benchmark.protect import assert_writable
from benchmark.relation import RELATION_VERSION, fingerprint
from benchmark.schema import BOOTSTRAP_SEED, DEFAULT_N_BOOTSTRAP, FROZEN_PROTOCOL_N
from benchmark.score import _is_certified
from src.canon_system import CanonSystem

from benchmarks.humaneval_plus.manifest import MANIFEST
from benchmarks.humaneval_plus.provenance import atomic_write_json, attach_oracle
from benchmarks.humaneval_plus.run import (
    _config_complete,
    _load_existing,
    _safe_name,
    all_evalplus_task_ids,
)

from skyt.heldout_posthoc import _boot, _cell_rows
from skyt.humaneval_heldout import (
    HELDOUT_SEED,
    OVERLAY_SOURCE,
    _iter_configs,
    _metric_fields,
    _prefix_metrics,
    balanced_splits_ordered,
    fingerprint_repeatability,
    select_train_canon,
)
from skyt.humaneval_repair import (
    EnhancedCodeTransformer,
    _load_plus_problem,
    apply_certified_consensus_repair,
    humaneval_repair_contract,
)
from skyt.repair_memo import InheritPlusOracle, RepairMemo, preindex_level3
from skyt.zero_api_analysis import RULERS, _repeat


ROBUST_OUT = Path("outputs") / "benchmark" / "humaneval_plus_164_n20_skyt_heldout_robust"
DEFAULT_N_SPLITS = 500
B_TABLE = (20, 50, 100, 500)
PERSIST_PROGRAM_SPLITS = 20
SCHEMA = "skyt-humaneval-plus-heldout-robust-v1"
CELLS = [
    ("all", None, None),
    ("gpt-4o-mini T=0.0", "gpt-4o-mini", 0.0),
    ("gpt-4o-mini T=0.7", "gpt-4o-mini", 0.7),
    ("claude-sonnet-4-5-20250929 T=0.0", "claude-sonnet-4-5-20250929", 0.0),
    ("claude-sonnet-4-5-20250929 T=0.7", "claude-sonnet-4-5-20250929", 0.7),
]


def _mean_field(rows: Sequence[Dict[str, Any]], key: str) -> Optional[float]:
    values = [row[key] for row in rows if row.get(key) is not None]
    if not values:
        return None
    return statistics.mean(float(value) for value in values)


def _record_from_hit(record: Dict[str, Any], hit: Dict[str, Any]) -> Dict[str, Any]:
    updated = deepcopy(record)
    updated["stitched_code_pre"] = record.get("stitched_code")
    updated["oracle_pre"] = record.get("oracle")
    updated["repair_policy"] = "certified_consensus"
    updated["stitched_code"] = hit.get("stitched_code", record.get("stitched_code"))
    if hit.get("oracle") is not None:
        updated = attach_oracle(updated, hit["oracle"])
    updated["repair_applied"] = hit.get("repair_applied", False)
    updated["rolled_back"] = hit.get("rolled_back", False)
    updated["skipped_reason"] = hit.get("skipped_reason")
    updated["transformation_level"] = hit.get("transformation_level")
    return updated


def apply_repair_with_memo(
    *,
    records: List[Dict[str, Any]],
    selected: Optional[Dict[str, Any]],
    contract_dict: Dict[str, Any],
    oracle: InheritPlusOracle,
    canon_store: Path,
    canon_system: CanonSystem,
    transformer: Any,
    memo: RepairMemo,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int, int]:
    if selected is None:
        return apply_certified_consensus_repair(
            records=records,
            selected=None,
            contract_dict=contract_dict,
            oracle=oracle,
            canon_store=canon_store,
            consensus_index=None,
            canon_system=canon_system,
            transformer=transformer,
        )
    oracle.bind_canon(selected["code"], selected["oracle_result"])
    preindex_level3(
        oracle, records, selected["code"], contract_dict, selected["oracle_result"]
    )
    canon_code = selected["code"]
    repaired: List[Optional[Dict[str, Any]]] = [None] * len(records)
    transform_rows: List[Optional[Dict[str, Any]]] = [None] * len(records)
    pending: List[int] = []
    n_transformed = 0
    n_rolled_back = 0
    for index, record in enumerate(records):
        code = record.get("stitched_code") or ""
        hit = memo.get(code, canon_code)
        if hit is None:
            pending.append(index)
            continue
        item = _record_from_hit(record, hit)
        repaired[index] = item
        transform_rows[index] = hit.get("transform_row") or {
            "run_index": record.get("run_index"),
            "skipped_reason": hit.get("skipped_reason"),
            "rolled_back": hit.get("rolled_back"),
        }
        if item.get("repair_applied") and not item.get("rolled_back"):
            n_transformed += 1
        if item.get("rolled_back"):
            n_rolled_back += 1
    if pending:
        subset = [records[index] for index in pending]
        got, rows, extra_t, extra_b = apply_certified_consensus_repair(
            records=subset,
            selected=selected,
            contract_dict=contract_dict,
            oracle=oracle,
            canon_store=canon_store,
            consensus_index=selected["index"],
            canon_system=canon_system,
            transformer=transformer,
        )
        n_transformed += extra_t
        n_rolled_back += extra_b
        for item, row, index in zip(got, rows, pending):
            repaired[index] = item
            transform_rows[index] = row
            memo.put(
                item.get("stitched_code_pre") or records[index].get("stitched_code") or "",
                canon_code,
                {
                    "stitched_code": item.get("stitched_code"),
                    "oracle": item.get("oracle"),
                    "repair_applied": item.get("repair_applied"),
                    "rolled_back": item.get("rolled_back"),
                    "skipped_reason": item.get("skipped_reason"),
                    "transformation_level": item.get("transformation_level"),
                    "transform_row": row,
                },
            )
    return list(repaired), list(transform_rows), n_transformed, n_rolled_back


def _split_payload(
    *,
    split_id: int,
    train: Sequence[int],
    test: Sequence[int],
    selected: Optional[Dict[str, Any]],
    n_transformed: int,
    n_rolled_back: int,
    transform_rows: Sequence[Dict[str, Any]],
    pre: Dict[str, Any],
    post: Dict[str, Any],
    persist_programs: bool,
    repaired: Sequence[Dict[str, Any]],
    n_unresolved: int,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "split_id": split_id,
        "train_indices": list(train),
        "test_indices": list(test),
        "canon_created": selected is not None,
        "consensus_index": None if selected is None else selected["index"],
        "consensus_run_index": None if selected is None else selected.get("run_index"),
        "n_transformed": n_transformed,
        "n_rolled_back": n_rolled_back,
        "n_unresolved_oracle": n_unresolved,
        "n_already_consensus": sum(
            1
            for row in transform_rows
            if row.get("skipped_reason") == "already_consensus_form"
        ),
        **_prefix_metrics("pre", _metric_fields(pre)),
        **_prefix_metrics("post", _metric_fields(post)),
    }
    if persist_programs:
        payload["test_codes"] = [
            record.get("stitched_code") or "" for record in repaired
        ]
        payload["test_plus"] = [
            _is_certified(
                record,
                fingerprint(record.get("stitched_code") or "", flexible_naming=True)
                is not None,
            )
            for record in repaired
        ]
    return payload


def robust_config(
    *,
    source_dir: Path,
    out_dir: Path,
    task_id: str,
    model: str,
    temperature: float,
    n: int = FROZEN_PROTOCOL_N,
    train_size: int = 10,
    n_splits: int = DEFAULT_N_SPLITS,
    seed: int = HELDOUT_SEED,
    allow_docker: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    source_dir = source_dir.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    if source_dir == out_dir:
        raise ValueError("Refusing to overwrite the overlay source directory")
    assert_writable(out_dir)
    if n != FROZEN_PROTOCOL_N:
        raise ValueError(f"protocol N={FROZEN_PROTOCOL_N}")
    if EnhancedCodeTransformer is None:
        raise RuntimeError("EnhancedCodeTransformer import failed")

    stem = _safe_name(task_id, model, temperature)
    summary_path = out_dir / f"{stem}_robust.json"
    source_jsonl = source_dir / f"{stem}.jsonl"
    raw = _load_existing(source_jsonl)
    if not _config_complete(raw, n):
        raise ValueError(f"{stem}: overlay source is incomplete")
    records = sorted(raw, key=lambda item: int(item["run_index"]))[:n]
    if not force and summary_path.exists():
        prior = json.loads(summary_path.read_text(encoding="utf-8"))
        if (
            prior.get("schema") == SCHEMA
            and int(prior.get("n_splits") or 0) >= n_splits
            and int(prior.get("n") or 0) == n
            and int(prior.get("cv_seed") or 0) == seed
        ):
            return prior

    prior_splits: Dict[Tuple[int, ...], Dict[str, Any]] = {}
    if summary_path.exists():
        prior = json.loads(summary_path.read_text(encoding="utf-8"))
        if prior.get("schema") == SCHEMA and int(prior.get("cv_seed") or 0) == seed:
            for row in prior.get("splits") or []:
                prior_splits[tuple(int(i) for i in row["train_indices"])] = row

    problem = _load_plus_problem(source_dir, task_id)
    contract_dict = humaneval_repair_contract(
        task_id=task_id,
        model=model,
        temperature=temperature,
        prompt=problem["prompt"],
        entry_point=problem["entry_point"],
    )
    oracle = InheritPlusOracle(problem, allow_docker=allow_docker)
    for record in records:
        oracle.seed_from_record(record.get("stitched_code") or "", record)

    splits = balanced_splits_ordered(n, train_size, n_splits, seed)
    universe = set(range(n))
    canon_system = CanonSystem(str(out_dir / "canon" / stem))
    transformer = EnhancedCodeTransformer(canon_system, enable_agents=False)
    transformer.enable_agents = False
    memo = RepairMemo(out_dir / "memo" / f"{stem}.json")

    split_rows: List[Dict[str, Any]] = []
    for split_id, train_tuple in enumerate(splits):
        cached = prior_splits.get(train_tuple)
        if cached is not None and (
            split_id >= PERSIST_PROGRAM_SPLITS or cached.get("test_codes")
        ):
            split_rows.append(cached)
            continue
        train = list(train_tuple)
        test = sorted(universe - set(train))
        selected = select_train_canon(records, contract_dict, train)
        test_records = [records[index] for index in test]
        pre = fingerprint_repeatability(test_records)
        unresolved_before = oracle.n_unresolved
        repaired, transform_rows, n_transformed, n_rolled_back = apply_repair_with_memo(
            records=test_records,
            selected=selected,
            contract_dict=contract_dict,
            oracle=oracle,
            canon_store=out_dir / "canon" / stem,
            canon_system=canon_system,
            transformer=transformer,
            memo=memo,
        )
        post = fingerprint_repeatability(repaired)
        split_rows.append(
            _split_payload(
                split_id=split_id,
                train=train,
                test=test,
                selected=selected,
                n_transformed=n_transformed,
                n_rolled_back=n_rolled_back,
                transform_rows=transform_rows,
                pre=pre,
                post=post,
                persist_programs=split_id < PERSIST_PROGRAM_SPLITS,
                repaired=repaired,
                n_unresolved=oracle.n_unresolved - unresolved_before,
            )
        )

    memo.flush()
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
        "allow_docker": allow_docker,
        "repair_policy": "certified_consensus",
        "relation_version": RELATION_VERSION,
        "source_jsonl": str(source_jsonl),
        "n_splits_with_canon": sum(1 for row in split_rows if row["canon_created"]),
        "n_transformed_mean": _mean_field(split_rows, "n_transformed"),
        "n_rolled_back_mean": _mean_field(split_rows, "n_rolled_back"),
        "n_unresolved_oracle": oracle.n_unresolved,
        "oracle_inherit_hits": oracle.n_hits,
        "oracle_docker_misses": oracle.n_misses,
        "pre_same_at_2": _mean_field(split_rows, "pre_same_at_2"),
        "post_same_at_2": _mean_field(split_rows, "post_same_at_2"),
        "pre_plus_pass": _mean_field(split_rows, "pre_plus_pass"),
        "post_plus_pass": _mean_field(split_rows, "post_plus_pass"),
        "splits": split_rows,
    }
    atomic_write_json(summary_path, summary)
    return summary


def _config_row(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "task_id": summary["task_id"],
        "model": summary["model"],
        "temperature": summary["temperature"],
        "n_splits": summary["n_splits"],
        "n_splits_with_canon": summary.get("n_splits_with_canon"),
        "pre_same_at_2": summary.get("pre_same_at_2"),
        "post_same_at_2": summary.get("post_same_at_2"),
        "pre_plus_pass": summary.get("pre_plus_pass"),
        "post_plus_pass": summary.get("post_plus_pass"),
        "n_unresolved_oracle": summary.get("n_unresolved_oracle"),
        "oracle_docker_misses": summary.get("oracle_docker_misses"),
        "splits": summary.get("splits") or [],
    }


def b_robustness_table(
    rows: Sequence[Dict[str, Any]], targets: Sequence[int] = B_TABLE
) -> List[Dict[str, Any]]:
    table = []
    for b in targets:
        delta_rows = []
        pre_rows = []
        post_rows = []
        for row in rows:
            splits = row.get("splits") or []
            if len(splits) < b:
                continue
            prefix = splits[:b]
            pre_vals = [
                s["pre_same_at_2"] for s in prefix if s.get("pre_same_at_2") is not None
            ]
            post_vals = [
                s["post_same_at_2"] for s in prefix if s.get("post_same_at_2") is not None
            ]
            if not pre_vals or not post_vals:
                continue
            pre_m = sum(pre_vals) / len(pre_vals)
            post_m = sum(post_vals) / len(post_vals)
            task = {"task_id": row["task_id"]}
            pre_rows.append({**task, "pre": pre_m})
            post_rows.append({**task, "post": post_m})
            delta_rows.append({**task, "delta": post_m - pre_m})
        table.append(
            {
                "B": b,
                "n_configs": len(delta_rows),
                "nested_prefix": True,
                "note": (
                    "B=k is the first k unique 10/10 splits from seed "
                    f"{HELDOUT_SEED}; B=20 is the same set as the paper held-out run."
                ),
                "pre_same_at_2": _boot(pre_rows, "pre"),
                "post_same_at_2": _boot(post_rows, "post"),
                "delta_same_at_2": _boot(delta_rows, "delta"),
            }
        )
    return table


def post_fingerprint_from_persist(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    by_ruler: Dict[str, List[Dict[str, Any]]] = {name: [] for name in RULERS}
    n_with_programs = 0
    for row in rows:
        persist_splits = [
            split for split in row.get("splits") or [] if split.get("test_codes")
        ]
        if not persist_splits:
            continue
        n_with_programs += 1
        acc: Dict[str, List[float]] = {name: [] for name in RULERS}
        for split in persist_splits:
            codes = [code or "" for code in split["test_codes"]]
            plus = [bool(flag) for flag in split.get("test_plus") or [False] * len(codes)]
            if len(plus) != len(codes):
                plus = [False] * len(codes)
            for name, ruler in RULERS.items():
                acc[name].append(_repeat(codes, plus, ruler)["same_at_2"])
        for name in RULERS:
            values = acc[name]
            post = sum(values) / len(values) if values else None
            by_ruler[name].append(
                {
                    "task_id": row["task_id"],
                    "model": row["model"],
                    "temperature": row["temperature"],
                    "same_at_2": post,
                }
            )
    return {
        "n_configs_with_persisted_programs": n_with_programs,
        "slices": {
            name: {
                label: _boot(_cell_rows(ruler_rows, model, temp), "same_at_2")
                for label, model, temp in CELLS
            }
            for name, ruler_rows in by_ruler.items()
        },
    }


def paired_fingerprint_report(
    *,
    source_dir: Path = OVERLAY_SOURCE,
    out_dir: Path = ROBUST_OUT,
    persist_splits: int = PERSIST_PROGRAM_SPLITS,
) -> Dict[str, Any]:
    """PRE vs POST same@2 under each ruler from persisted repaired programs."""
    by_ruler: Dict[str, List[Dict[str, Any]]] = {
        name: [] for name in RULERS
    }
    n = 0
    n_skipped = 0
    for path in sorted(out_dir.glob("*_robust.json")):
        try:
            summary = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            n_skipped += 1
            continue
        if summary.get("schema") != SCHEMA:
            continue
        persist = [
            split
            for split in (summary.get("splits") or [])[:persist_splits]
            if split.get("test_codes")
        ]
        if len(persist) < persist_splits:
            n_skipped += 1
            continue
        stem = _safe_name(
            summary["task_id"], summary["model"], summary["temperature"]
        )
        records = sorted(
            _load_existing(source_dir / f"{stem}.jsonl"),
            key=lambda item: int(item["run_index"]),
        )[: FROZEN_PROTOCOL_N]
        codes = [record.get("stitched_code") or "" for record in records]
        plus = [
            _is_certified(
                record,
                fingerprint(code, flexible_naming=True) is not None,
            )
            for record, code in zip(records, codes)
        ]
        acc_pre: Dict[str, List[float]] = {name: [] for name in RULERS}
        acc_post: Dict[str, List[float]] = {name: [] for name in RULERS}
        for split in persist:
            test = [int(i) for i in split["test_indices"]]
            pre_codes = [codes[i] for i in test]
            pre_plus = [plus[i] for i in test]
            post_codes = [code or "" for code in split["test_codes"]]
            post_plus = [bool(flag) for flag in split.get("test_plus") or []]
            if len(post_plus) != len(post_codes):
                post_plus = [False] * len(post_codes)
            for name, ruler in RULERS.items():
                acc_pre[name].append(_repeat(pre_codes, pre_plus, ruler)["same_at_2"])
                acc_post[name].append(_repeat(post_codes, post_plus, ruler)["same_at_2"])
        n += 1
        if n % 50 == 0:
            print(f"  fingerprint persist {n}", flush=True)
        for name in RULERS:
            pre = sum(acc_pre[name]) / len(acc_pre[name])
            post = sum(acc_post[name]) / len(acc_post[name])
            by_ruler[name].append(
                {
                    "task_id": summary["task_id"],
                    "model": summary["model"],
                    "temperature": summary["temperature"],
                    "pre": pre,
                    "post": post,
                    "delta": post - pre,
                }
            )
    print(f"loaded {n} persist configs, skipped {n_skipped}; bootstrapping", flush=True)
    slices = {}
    for name, ruler_rows in by_ruler.items():
        slices[name] = {
            label: {
                "pre": _boot(_cell_rows(ruler_rows, model, temp), "pre"),
                "post": _boot(_cell_rows(ruler_rows, model, temp), "post"),
                "delta": _boot(_cell_rows(ruler_rows, model, temp), "delta"),
            }
            for label, model, temp in CELLS
        }
    report = {
        "schema": "skyt-heldout-fingerprint-post-v1",
        "n_configs": n,
        "n_skipped": n_skipped,
        "persist_splits": persist_splits,
        "slices": slices,
    }
    atomic_write_json(out_dir / "fingerprint_post_report.json", report)
    return report


def _flush_report(
    out_dir: Path,
    rows: List[Dict[str, Any]],
    n_splits: int,
    n_failed: int,
    *,
    heavy: bool = False,
) -> Dict[str, Any]:
    scored = [row for row in rows if "error" not in row]
    report = {
        "schema": "skyt-humaneval-plus-heldout-robust-grid-v1",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "n_splits": n_splits,
        "cv_seed": HELDOUT_SEED,
        "n_bootstrap": DEFAULT_N_BOOTSTRAP,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "n_configs": len(rows),
        "n_scored": len(scored),
        "n_failed_configs": n_failed,
        "b_robustness": b_robustness_table(scored) if heavy else None,
        "post_fingerprint": post_fingerprint_from_persist(scored) if heavy else None,
        "configs": [{k: v for k, v in row.items() if k != "splits"} for row in scored],
    }
    atomic_write_json(out_dir / "robust_report.json", report)
    return report


def robust_grid(
    *,
    source_dir: Path = OVERLAY_SOURCE,
    out_dir: Path = ROBUST_OUT,
    n_splits: int = DEFAULT_N_SPLITS,
    seed: int = HELDOUT_SEED,
    allow_docker: bool = False,
    force: bool = False,
    limit: int = 0,
    task_id: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> Dict[str, Any]:
    source_dir = source_dir.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    if source_dir == out_dir:
        raise ValueError("Refusing to overwrite the overlay source directory")
    assert_writable(out_dir)
    task_ids = all_evalplus_task_ids()
    configs = _iter_configs(
        task_ids=task_ids,
        models=list(MANIFEST["models"]),
        temperatures=[float(item) for item in MANIFEST["temperatures"]],
        only_task_id=task_id,
        only_model=model,
        only_temperature=temperature,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "robust_progress.log"
    rows: List[Dict[str, Any]] = []
    n_failed = 0
    done = 0
    for index, (cfg_task, cfg_model, cfg_temp) in enumerate(configs, start=1):
        line = f"[{index}/{len(configs)}] robust {cfg_task} {cfg_model} T={cfg_temp}"
        print(line, flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        try:
            summary = robust_config(
                source_dir=source_dir,
                out_dir=out_dir,
                task_id=cfg_task,
                model=cfg_model,
                temperature=cfg_temp,
                n_splits=n_splits,
                seed=seed,
                allow_docker=allow_docker,
                force=force,
            )
        except Exception as exc:
            err = type(exc).__name__
            detail = str(exc)[:400]
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
            _flush_report(out_dir, rows, n_splits, n_failed, heavy=False)
            if limit and done >= limit:
                break
            continue
        row = _config_row(summary)
        print(
            f"  pre={row.get('pre_same_at_2')} post={row.get('post_same_at_2')} "
            f"unresolved={row.get('n_unresolved_oracle')} "
            f"docker={row.get('oracle_docker_misses')}",
            flush=True,
        )
        rows.append(row)
        done += 1
        _flush_report(out_dir, rows, n_splits, n_failed, heavy=False)
        if limit and done >= limit:
            break
    return _flush_report(out_dir, rows, n_splits, n_failed, heavy=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Held-out SKYT robustness replay (no LLM).")
    parser.add_argument("--source-dir", default=str(OVERLAY_SOURCE))
    parser.add_argument("--out-dir", default=str(ROBUST_OUT))
    parser.add_argument("--n-splits", type=int, default=DEFAULT_N_SPLITS)
    parser.add_argument("--seed", type=int, default=HELDOUT_SEED)
    parser.add_argument("--allow-docker", action="store_true")
    parser.add_argument(
        "--allow-extra-b",
        action="store_true",
        help="Permit --n-splits above 100. Nested B=20/100/500 already finished (Δ 17.1 vs 17.3 vs 17.3); keep this flag so a 500-split replay is not started by accident.",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--task-id")
    parser.add_argument("--model")
    parser.add_argument("--temperature", type=float)
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Recompute fingerprint PRE/POST from persisted programs; no repair.",
    )
    args = parser.parse_args()
    if int(args.n_splits) > 100 and not args.allow_extra_b and not args.analyze_only:
        raise SystemExit(
            f"--n-splits {args.n_splits} is already on disk (nested B=20/100/500; "
            "Δ 17.1 vs 17.3 vs 17.3). Pass --allow-extra-b to re-run."
        )
    if args.analyze_only:
        payload = paired_fingerprint_report(
            source_dir=Path(args.source_dir),
            out_dir=Path(args.out_dir),
        )
        print(f"n={payload['n_configs']} skipped={payload['n_skipped']}", flush=True)
        for name, cells in (payload.get("slices") or {}).items():
            item = cells.get("all") or {}
            d = item.get("delta") or {}
            print(
                f"{name}: pre {item.get('pre', {}).get('pct')} "
                f"post {item.get('post', {}).get('pct')} "
                f"delta {d.get('pct')} CI {d.get('ci95_pct')}",
                flush=True,
            )
        raise SystemExit(0)
    payload = robust_grid(
        source_dir=Path(args.source_dir),
        out_dir=Path(args.out_dir),
        n_splits=args.n_splits,
        seed=args.seed,
        allow_docker=args.allow_docker,
        force=args.force,
        limit=args.limit,
        task_id=args.task_id,
        model=args.model,
        temperature=args.temperature,
    )
    print(f"scored {payload['n_scored']} failed {payload['n_failed_configs']}", flush=True)
    for row in payload.get("b_robustness") or []:
        delta = row["delta_same_at_2"]
        print(
            f"B={row['B']} n={row['n_configs']} delta {delta.get('pct')} CI {delta.get('ci95_pct')}",
            flush=True,
        )
    post = payload.get("post_fingerprint") or {}
    slices = post.get("slices") or {}
    for name, cells in slices.items():
        item = cells.get("all") or {}
        print(f"POST {name}: {item.get('pct')} CI {item.get('ci95_pct')}", flush=True)
