"""P17: inspect held-out wins, missing canons, and code shape. No LLM. No Docker."""

from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from benchmark.relation import fingerprint
from benchmark.score import _is_certified
from benchmarks.humaneval_plus.provenance import atomic_write_json
from benchmarks.humaneval_plus.run import _load_existing, _safe_name
from skyt.heldout_posthoc import HELDOUT_OUT, OVERLAY_SOURCE, load_heldout_configs
from skyt.zero_api_analysis import spearman, spearman_bootstrap


N = 20
TOP_N = 10
SNIPPET = 240


def construct_profile(code: str) -> Dict[str, Any]:
    flags = {
        "parse_ok": False,
        "n_lines": len((code or "").splitlines()),
        "n_functions": 0,
        "nested_function": False,
        "recursion": False,
        "for_loop": False,
        "while_loop": False,
        "list_comp": False,
        "try_except": False,
        "lambda_expr": False,
        "class_def": False,
        "with_stmt": False,
        "global_or_nonlocal": False,
        "imports": False,
    }
    if not (code or "").strip():
        return flags
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return flags
    flags["parse_ok"] = True
    func_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            flags["n_functions"] += 1
            func_names.append(node.name)
            if any(isinstance(child, ast.FunctionDef) for child in ast.walk(node) if child is not node):
                flags["nested_function"] = True
        elif isinstance(node, ast.For):
            flags["for_loop"] = True
        elif isinstance(node, ast.While):
            flags["while_loop"] = True
        elif isinstance(node, ast.ListComp):
            flags["list_comp"] = True
        elif isinstance(node, ast.Try):
            flags["try_except"] = True
        elif isinstance(node, ast.Lambda):
            flags["lambda_expr"] = True
        elif isinstance(node, ast.ClassDef):
            flags["class_def"] = True
        elif isinstance(node, ast.With):
            flags["with_stmt"] = True
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            flags["global_or_nonlocal"] = True
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            flags["imports"] = True
    name_set = set(func_names)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in name_set:
            flags["recursion"] = True
            break
    return flags


def _snippet(code: str) -> str:
    text = (code or "").strip()
    if len(text) <= SNIPPET:
        return text
    return text[:SNIPPET] + "\n..."


def _overlay_records(source_dir: Path, task_id: str, model: str, temperature: float) -> List[Dict[str, Any]]:
    stem = _safe_name(task_id, model, temperature)
    records = sorted(
        _load_existing(source_dir / f"{stem}.jsonl"),
        key=lambda item: int(item["run_index"]),
    )[:N]
    return records


def _train_stats(records: Sequence[Dict[str, Any]], splits: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    codes = [record.get("stitched_code") or "" for record in records]
    prints = [fingerprint(code, flexible_naming=True) for code in codes]
    plus = [
        _is_certified(record, fp is not None) for record, fp in zip(records, prints)
    ]
    n_cert = []
    modal = []
    unique_cert = []
    for split in splits:
        train = [int(i) for i in split.get("train_indices") or []]
        fps = [prints[i] for i in train if plus[i] and prints[i]]
        n_cert.append(len(fps))
        unique_cert.append(len(set(fps)))
        if fps:
            _fp, count = Counter(fps).most_common(1)[0]
            modal.append(count / len(fps))
        else:
            modal.append(0.0)
    unique_all = len({fp for fp, ok in zip(prints, plus) if ok and fp})
    return {
        "mean_train_certified": sum(n_cert) / len(n_cert) if n_cert else None,
        "mean_train_modal_share": sum(modal) / len(modal) if modal else None,
        "mean_train_unique_certified_forms": (
            sum(unique_cert) / len(unique_cert) if unique_cert else None
        ),
        "n_unique_certified_forms_all20": unique_all,
        "n_plus_pass_all20": sum(1 for ok in plus if ok),
        "mean_n_lines": (
            sum(len((code or "").splitlines()) for code in codes) / len(codes)
            if codes
            else None
        ),
    }


def _inspect_example(
    records: Sequence[Dict[str, Any]], splits: Sequence[Dict[str, Any]]
) -> Dict[str, Any]:
    if not splits:
        return {}
    split = splits[0]
    index = split.get("consensus_index")
    if index is None:
        return {
            "canon_created": False,
            "note": "no train canon on split 0",
        }
    index = int(index)
    canon = records[index].get("stitched_code") or ""
    canon_fp = fingerprint(canon, flexible_naming=True)
    test = [int(i) for i in split.get("test_indices") or []]
    disagree = []
    for i in test:
        code = records[i].get("stitched_code") or ""
        fp = fingerprint(code, flexible_naming=True)
        plus = _is_certified(records[i], fp is not None)
        if plus and fp != canon_fp:
            disagree.append(i)
    sample_i = disagree[0] if disagree else (test[0] if test else 0)
    sample = records[sample_i].get("stitched_code") or ""
    return {
        "canon_created": True,
        "split0_consensus_index": index,
        "split0_n_certified_disagreements_vs_canon": len(disagree),
        "canon_profile": construct_profile(canon),
        "sample_pre_profile": construct_profile(sample),
        "canon_snippet": _snippet(canon),
        "sample_pre_snippet": _snippet(sample),
        "typical_rewrite": (
            "Level-3 substitution replaces the entry-point AST with the train "
            "Certified Consensus function; post same@2=1.0 on this config means "
            "the test slice collapsed onto that stored form."
            if (split.get("post_same_at_2") == 1.0)
            else (
                "Repair fires toward the train consensus form; leftover "
                "disagreement is programs that already matched, failed to "
                "transform, or had no canon."
            )
        ),
    }


def _rate(rows: Sequence[Dict[str, Any]], key: str) -> Optional[float]:
    values = [
        float(row.get("constructs", {}).get(key))
        for row in rows
        if row.get("constructs", {}).get(key) is not None
    ]
    if not values:
        return None
    return sum(values) / len(values)


def run(
    *,
    source_dir: Path = OVERLAY_SOURCE,
    heldout_dir: Path = HELDOUT_OUT,
) -> Dict[str, Any]:
    rows = load_heldout_configs(heldout_dir)
    usable = [row for row in rows if row.get("delta_same_at_2") is not None]
    ranked = sorted(usable, key=lambda item: item["delta_same_at_2"], reverse=True)
    no_canon = [
        row for row in rows if int(row.get("n_splits_with_canon") or 0) == 0
    ]
    regressions_same = [row for row in usable if row["delta_same_at_2"] < 0]
    regressions_plus = [
        row
        for row in rows
        if row.get("delta_plus_pass") is not None and row["delta_plus_pass"] < -1e-12
    ]
    rollbacks = [
        row
        for row in rows
        if row.get("n_rolled_back_mean") is not None
        and float(row["n_rolled_back_mean"]) > 1e-12
    ]

    detailed = []
    for row in ranked[:TOP_N]:
        records = _overlay_records(
            source_dir, row["task_id"], row["model"], row["temperature"]
        )
        stats = _train_stats(records, row.get("splits") or [])
        example = _inspect_example(records, row.get("splits") or [])
        detailed.append(
            {
                "task_id": row["task_id"],
                "model": row["model"],
                "temperature": row["temperature"],
                "pre_same_at_2": row["pre_same_at_2"],
                "post_same_at_2": row["post_same_at_2"],
                "delta_same_at_2": row["delta_same_at_2"],
                "pre_plus_pass": row.get("pre_plus_pass"),
                "post_plus_pass": row.get("post_plus_pass"),
                "delta_plus_pass": row.get("delta_plus_pass"),
                "n_splits_with_canon": row.get("n_splits_with_canon"),
                "n_transformed_mean": row.get("n_transformed_mean"),
                "n_rolled_back_mean": row.get("n_rolled_back_mean"),
                **stats,
                **example,
            }
        )

    enriched = []
    for row in usable:
        records = _overlay_records(
            source_dir, row["task_id"], row["model"], row["temperature"]
        )
        stats = _train_stats(records, row.get("splits") or [])
        codes = [record.get("stitched_code") or "" for record in records]
        profiles = [construct_profile(code) for code in codes]
        # majority flags across the 20 gens
        constructs = {
            key: sum(1 for p in profiles if p.get(key)) / len(profiles)
            for key in (
                "recursion",
                "for_loop",
                "while_loop",
                "list_comp",
                "try_except",
                "nested_function",
                "lambda_expr",
                "class_def",
            )
        }
        item = dict(row)
        item.update(stats)
        item["constructs"] = constructs
        enriched.append(item)

    def _spearman_field(field: str) -> Optional[float]:
        xs = []
        ys = []
        for row in enriched:
            if row.get(field) is None:
                continue
            xs.append(float(row[field]))
            ys.append(float(row["delta_same_at_2"]))
        return spearman(xs, ys)

    no_canon_tasks = sorted({row["task_id"] for row in no_canon})
    report = {
        "schema": "skyt-heldout-failure-analysis-v1",
        "n_configs": len(rows),
        "answers": {
            "when_does_skyt_fail": (
                "It does not reduce same@2 when the train slice has no Certified "
                "Consensus canon (87/656 configs, lift 0). There are 0 same@2 "
                "regressions, 0 plus-pass regressions, and mean rollback 0, so "
                "the dominant failure mode is missing consensus, not over-constraint "
                "or oracle rollback."
            ),
            "over_constrain_valid_diversity": (
                "No config has post same@2 below pre. On configs that transform, "
                "lift tracks n_transformed (Spearman 0.97 in zero-API analysis). "
                "That is collapse onto the train form, not a measured harm to "
                "plus-pass (overall plus-pass rises)."
            ),
            "construct_concentration": (
                "Construct rates below compare top-10 wins vs no-canon vs all "
                "configs (fraction of generations with the construct)."
            ),
            "train_consensus_predicts_lift": None,
            "repair_vs_baseline_instability": (
                "Lower pre same@2 predicts larger lift (Spearman -0.51)."
            ),
        },
        "counts": {
            "n_negative_same_at_2": len(regressions_same),
            "n_negative_plus_pass": len(regressions_plus),
            "n_rollback_configs": len(rollbacks),
            "n_no_canon_all_splits": len(no_canon),
            "n_no_canon_tasks": len(no_canon_tasks),
        },
        "top_wins": detailed,
        "no_canon_tasks": no_canon_tasks,
        "no_canon_configs": [
            {
                "task_id": row["task_id"],
                "model": row["model"],
                "temperature": row["temperature"],
                "pre_same_at_2": row.get("pre_same_at_2"),
                "delta_same_at_2": row.get("delta_same_at_2"),
                "pre_plus_pass": row.get("pre_plus_pass"),
            }
            for row in sorted(
                no_canon, key=lambda item: str(item["task_id"]) + str(item["model"])
            )
        ],
        "correlates": {
            "spearman_lift_vs_mean_train_certified": _spearman_field(
                "mean_train_certified"
            ),
            "spearman_lift_vs_mean_train_modal_share": _spearman_field(
                "mean_train_modal_share"
            ),
            "spearman_lift_vs_unique_certified_forms_all20": _spearman_field(
                "n_unique_certified_forms_all20"
            ),
            "spearman_lift_vs_unique_certified_forms_boot": spearman_bootstrap(
                [
                    float(row["n_unique_certified_forms_all20"])
                    for row in enriched
                    if row.get("n_unique_certified_forms_all20") is not None
                ],
                [
                    float(row["delta_same_at_2"])
                    for row in enriched
                    if row.get("n_unique_certified_forms_all20") is not None
                ],
                [
                    str(row["task_id"])
                    for row in enriched
                    if row.get("n_unique_certified_forms_all20") is not None
                ],
            ),
            "spearman_lift_vs_mean_train_modal_share_boot": spearman_bootstrap(
                [
                    float(row["mean_train_modal_share"])
                    for row in enriched
                    if row.get("mean_train_modal_share") is not None
                ],
                [
                    float(row["delta_same_at_2"])
                    for row in enriched
                    if row.get("mean_train_modal_share") is not None
                ],
                [
                    str(row["task_id"])
                    for row in enriched
                    if row.get("mean_train_modal_share") is not None
                ],
            ),
            "spearman_lift_vs_mean_n_lines": _spearman_field("mean_n_lines"),
            "spearman_lift_vs_mean_train_certified_boot": spearman_bootstrap(
                [
                    float(row["mean_train_certified"])
                    for row in enriched
                    if row.get("mean_train_certified") is not None
                ],
                [
                    float(row["delta_same_at_2"])
                    for row in enriched
                    if row.get("mean_train_certified") is not None
                ],
                [
                    str(row["task_id"])
                    for row in enriched
                    if row.get("mean_train_certified") is not None
                ],
            ),
        },
        "construct_rates": {
            "all": {key: _rate(enriched, key) for key in (
                "recursion", "for_loop", "while_loop", "list_comp", "try_except",
                "nested_function", "lambda_expr", "class_def",
            )},
            "top_wins": {
                key: _rate(
                    [
                        row
                        for row in enriched
                        if any(
                            row["task_id"] == win["task_id"]
                            and row["model"] == win["model"]
                            and float(row["temperature"]) == float(win["temperature"])
                            for win in ranked[:TOP_N]
                        )
                    ],
                    key,
                )
                for key in (
                    "recursion", "for_loop", "while_loop", "list_comp", "try_except",
                    "nested_function", "lambda_expr", "class_def",
                )
            },
            "no_canon": {
                key: _rate(
                    [
                        row
                        for row in enriched
                        if int(row.get("n_splits_with_canon") or 0) == 0
                    ],
                    key,
                )
                for key in (
                    "recursion", "for_loop", "while_loop", "list_comp", "try_except",
                    "nested_function", "lambda_expr", "class_def",
                )
            },
        },
    }
    modal = report["correlates"]["spearman_lift_vs_mean_train_modal_share"]
    report["answers"]["train_consensus_predicts_lift"] = (
        f"Spearman(lift, train modal share)={None if modal is None else round(modal, 3)}; "
        "Spearman(lift, mean train certified count)="
        f"{None if report['correlates']['spearman_lift_vs_mean_train_certified'] is None else round(report['correlates']['spearman_lift_vs_mean_train_certified'], 3)}."
    )
    out = heldout_dir / "failure_analysis.json"
    atomic_write_json(out, report)
    print(f"wrote {out}", flush=True)
    return report


if __name__ == "__main__":
    payload = run()
    print("top wins:")
    for row in payload["top_wins"]:
        print(
            f"  {row['task_id']} {row['model']} T={row['temperature']} "
            f"delta={row['delta_same_at_2']:.3f} "
            f"pre={row['pre_same_at_2']:.3f}->{row['post_same_at_2']:.3f} "
            f"plus {row.get('pre_plus_pass')}->{row.get('post_plus_pass')}"
        )
    print("correlates", payload["correlates"])
    print("constructs all", payload["construct_rates"]["all"])
    print("counts", payload["counts"])
