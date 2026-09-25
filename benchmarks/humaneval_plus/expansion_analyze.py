"""Pooled Table 1, T3 pairs, and T6 reliability for expansion + frozen trees.

No API. Reads scored overlay trees. Writes analysis JSON only.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from benchmark.metrics import cluster_bootstrap_mean, _percentile
from benchmark.relation import fingerprint
from benchmark.score import score_directory
from benchmark.schema import BOOTSTRAP_SEED

SEED = BOOTSTRAP_SEED
N_BOOT = 10000
FROZEN = Path("outputs/benchmark/humaneval_plus_164_n20")
EXPANSION = Path("outputs/benchmark/humaneval_plus_164_n20_expansion")
OUT = EXPANSION / "analysis"


def _score_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    from benchmark.metrics import config_repeatability
    from benchmark.relation import RELATION_VERSION, fingerprint
    from benchmark.score import _is_certified

    by_index = {int(record.get("run_index", -1)): record for record in records}
    ordered = [by_index[key] for key in sorted(by_index)]
    prints = [
        fingerprint(record.get("stitched_code") or "", flexible_naming=True)
        for record in ordered
    ]
    certified = [
        _is_certified(record, fp is not None) for record, fp in zip(ordered, prints)
    ]
    analysis = config_repeatability(prints, certified)
    return {
        "task_id": ordered[0]["task_id"],
        "model": ordered[0]["model"],
        "temperature": None
        if ordered[0].get("temperature") is None
        else float(ordered[0]["temperature"]),
        "n": analysis["n"],
        "n_certified": analysis["n_certified"],
        "same_at_2": analysis["same_at_2"],
        "same_at_2_given_cert": analysis["same_at_2_given_cert"],
        "plus_pass": analysis["plus_pass"],
        "relation_version": RELATION_VERSION,
    }


def _load_rows(source_dir: Path) -> List[Dict[str, Any]]:
    from benchmark.score import _iter_jsonl

    files = sorted(source_dir.glob("*.jsonl"))
    rows = []
    for path in files:
        records = list(_iter_jsonl(path))
        if len(records) < 2:
            continue
        if any((record.get("oracle") or {}).get("plus_passed") is None and record.get("oracle") is None for record in records):
            # incomplete docker score
            if any(record.get("oracle") is None for record in records):
                continue
        rows.append(_score_records(records))
    return rows


def _task_means(rows: Sequence[Dict[str, Any]], field: str) -> Dict[str, float]:
    buckets: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        value = row.get(field)
        if value is None:
            continue
        buckets[str(row["task_id"])].append(float(value))
    return {task: sum(vals) / len(vals) for task, vals in buckets.items() if vals}


def pooled_estimate(rows: Sequence[Dict[str, Any]], field: str) -> Dict[str, Any]:
    values: List[float] = []
    cluster_ids: List[str] = []
    for row in rows:
        value = row.get(field)
        if value is None:
            continue
        values.append(float(value))
        cluster_ids.append(str(row["task_id"]))
    if not values:
        return {"estimate": None, "ci95": [None, None], "n_tasks": 0, "n_configs": 0}
    result = cluster_bootstrap_mean(
        values, cluster_ids, n_bootstrap=N_BOOT, seed=SEED
    )
    return {
        "estimate": result["mean"],
        "ci95": [result["lower"], result["upper"]],
        "n_tasks": result["n_clusters"],
        "n_configs": len(values),
    }


def table1_block(rows: Sequence[Dict[str, Any]], label: str) -> Dict[str, Any]:
    same_cert_rows = [row for row in rows if row.get("same_at_2_given_cert") is not None]
    dropped = len(rows) - len(same_cert_rows)
    return {
        "label": label,
        "n_configs": len(rows),
        "n_dropped_same_at_2_given_cert": dropped,
        "plus_pass": pooled_estimate(rows, "plus_pass"),
        "same_at_2": pooled_estimate(rows, "same_at_2"),
        "same_at_2_given_cert": pooled_estimate(same_cert_rows, "same_at_2_given_cert"),
    }


def t3_pairs(rows: Sequence[Dict[str, Any]], temperature: float) -> List[Dict[str, Any]]:
    by_model: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("temperature") != temperature:
            continue
        by_model[str(row["model"])].append(row)
    models = sorted(by_model)
    out = []
    for i, left in enumerate(models):
        for right in models[i + 1 :]:
            left_map = {row["task_id"]: row for row in by_model[left]}
            right_map = {row["task_id"]: row for row in by_model[right]}
            tasks = sorted(set(left_map) & set(right_map))
            plus = {}
            cert = {}
            for task in tasks:
                a, b = left_map[task], right_map[task]
                if a.get("plus_pass") is not None and b.get("plus_pass") is not None:
                    plus[task] = float(a["plus_pass"]) - float(b["plus_pass"])
                if (
                    a.get("same_at_2_given_cert") is not None
                    and b.get("same_at_2_given_cert") is not None
                ):
                    cert[task] = float(a["same_at_2_given_cert"]) - float(
                        b["same_at_2_given_cert"]
                    )
            plus_vals = list(plus.values())
            plus_ids = list(plus.keys())
            cert_vals = list(cert.values())
            cert_ids = list(cert.keys())
            plus_result = (
                cluster_bootstrap_mean(plus_vals, plus_ids, n_bootstrap=N_BOOT, seed=SEED)
                if plus_vals
                else None
            )
            cert_result = (
                cluster_bootstrap_mean(cert_vals, cert_ids, n_bootstrap=N_BOOT, seed=SEED)
                if cert_vals
                else None
            )
            plus_point = None if plus_result is None else plus_result["mean"]
            cert_point = None if cert_result is None else cert_result["mean"]
            plus_ci = (
                [None, None]
                if plus_result is None
                else [plus_result["lower"], plus_result["upper"]]
            )
            cert_ci = (
                [None, None]
                if cert_result is None
                else [cert_result["lower"], cert_result["upper"]]
            )
            reversal = False
            if (
                plus_point is not None
                and cert_point is not None
                and plus_ci[0] is not None
                and cert_ci[0] is not None
            ):
                # claim reversal only if cert CI excludes 0 with opposite sign to plus
                cert_excludes = cert_ci[0] > 0 or cert_ci[1] < 0
                opposite = (plus_point > 0 and cert_point < 0) or (
                    plus_point < 0 and cert_point > 0
                )
                reversal = bool(cert_excludes and opposite)
            out.append(
                {
                    "temperature": temperature,
                    "model_a": left,
                    "model_b": right,
                    "plus_pass_diff": {"estimate": plus_point, "ci95": plus_ci, "n_tasks": len(plus)},
                    "same_at_2_given_cert_diff": {
                        "estimate": cert_point,
                        "ci95": cert_ci,
                        "n_tasks": len(cert),
                    },
                    "rank_reversal": reversal,
                }
            )
    return out


def t6_reliability(rows: Sequence[Dict[str, Any]], ns: Sequence[int] = (4, 6, 10, 14)) -> Dict[str, Any]:
    """Subsample first k generations from each config's stored order by run_index."""
    from benchmark.score import score_config, _iter_jsonl

    # regroup by loading trees again is expensive; instead expect caller to pass
    # enriched rows with fingerprints already. For T6 we need re-score from gens.
    raise NotImplementedError("call t6_from_trees instead")


def t6_from_trees(trees: Sequence[Path], ns: Sequence[int] = (4, 6, 10, 14)) -> Dict[str, Any]:
    from benchmark.score import _iter_jsonl

    by_cell: Dict[Tuple[str, Optional[float]], List[Dict[str, Any]]] = defaultdict(list)
    for tree in trees:
        for path in sorted(tree.glob("*.jsonl")):
            records = sorted(_iter_jsonl(path), key=lambda item: int(item["run_index"]))
            if len(records) < 20:
                continue
            if any(record.get("oracle") is None for record in records):
                continue
            model = records[0]["model"]
            raw_temp = records[0].get("temperature")
            temperature = None if raw_temp is None else float(raw_temp)
            full = _score_records(records)
            for n in ns:
                scored = _score_records(records[:n])
                by_cell[(model, temperature)].append(
                    {
                        "n": n,
                        "task_id": records[0]["task_id"],
                        "same_at_2": scored["same_at_2"],
                        "full_same_at_2": full["same_at_2"],
                    }
                )
    report: Dict[str, Any] = {"ns": list(ns), "cells": {}}
    for (model, temperature), items in by_cell.items():
        cell = f"{model}|{temperature}"
        cell_out: Dict[str, Any] = {}
        for n in ns:
            rows = [item for item in items if item["n"] == n]
            means = {}
            widths = {}
            # CI width per task then mean width; correlation with N=20
            for task, group in _groupby(rows, "task_id").items():
                # one row per task here
                row = group[0]
                means[task] = float(row["same_at_2"])
            means_vals = list(means.values())
            means_ids = list(means.keys())
            result = cluster_bootstrap_mean(
                means_vals, means_ids, n_bootstrap=N_BOOT, seed=SEED
            )
            point, lower, upper = result["mean"], result["lower"], result["upper"]
            width = None if lower is None or upper is None else upper - lower
            pairs = [
                (float(row["same_at_2"]), float(row["full_same_at_2"])) for row in rows
            ]
            corr = _pearson([a for a, _ in pairs], [b for _, b in pairs]) if len(pairs) >= 3 else None
            cell_out[str(n)] = {
                "estimate": point,
                "ci95": [lower, upper],
                "mean_ci_width": width,
                "corr_with_n20": corr,
                "n_tasks": len(means),
            }
        report["cells"][cell] = cell_out
    return report


def _groupby(rows: Sequence[Dict[str, Any]], key: str) -> Dict[Any, List[Dict[str, Any]]]:
    out: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        out[row[key]].append(row)
    return out


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = sum((x - mx) ** 2 for x in xs) ** 0.5
    deny = sum((y - my) ** 2 for y in ys) ** 0.5
    if denx == 0 or deny == 0:
        return None
    return num / (denx * deny)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frozen_rows = _load_rows(FROZEN)
    expansion_rows: List[Dict[str, Any]] = []
    for slug in ("haiku45", "luna", "sonnet5"):
        tree = EXPANSION / slug
        if not tree.exists():
            continue
        expansion_rows.extend(_load_rows(tree))

    # Require oracles present
    def ready(rows: Sequence[Dict[str, Any]]) -> bool:
        return all(row.get("plus_pass") is not None for row in rows) and bool(rows)

    if not ready(frozen_rows):
        raise SystemExit("frozen tree not scorable")
    if expansion_rows and not ready(expansion_rows):
        raise SystemExit("expansion trees incomplete; finish Docker score first")

    t_grid = [
        row
        for row in frozen_rows + expansion_rows
        if row.get("temperature") is not None
        and str(row["model"])
        in {
            "gpt-4o-mini",
            "claude-sonnet-4-5-20250929",
            "claude-haiku-4-5-20251001",
            "gpt-6-luna",
        }
    ]
    rq4 = [
        row
        for row in frozen_rows
        if str(row["model"]) in {"gpt-4o-mini", "claude-sonnet-4-5-20250929"}
    ]
    payload = {
        "schema": "sameeval-expansion-analysis-v1",
        "seed": SEED,
        "n_bootstrap": N_BOOT,
        "rq4_subset": table1_block(rq4, "RQ4 subset (GPT-4o-mini + Sonnet 4.5)"),
        "all_t_grid": table1_block(t_grid, "All T-grid models"),
        "per_cell": [],
        "t3": t3_pairs(t_grid, 0.0) + t3_pairs(t_grid, 0.7),
    }
    cells: Dict[Tuple[str, Optional[float]], List[Dict[str, Any]]] = defaultdict(list)
    for row in frozen_rows + expansion_rows:
        cells[(str(row["model"]), None if row.get("temperature") is None else float(row["temperature"]))].append(row)
    for (model, temperature), rows in sorted(cells.items(), key=lambda item: (item[0][0], item[0][1] is None, item[0][1] or -1)):
        payload["per_cell"].append(table1_block(rows, f"{model} T={temperature}"))

    path = OUT / "table1_pools.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "rq4_plus": payload["rq4_subset"]["plus_pass"]["estimate"],
        "rq4_same2": payload["rq4_subset"]["same_at_2"]["estimate"],
        "rq4_same2c": payload["rq4_subset"]["same_at_2_given_cert"]["estimate"],
        "path": str(path),
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
