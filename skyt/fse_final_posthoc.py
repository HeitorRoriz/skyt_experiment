"""Final post hoc numbers for the FSE 2027 draft (plan items 3.1-3.5).

No API. Reads frozen scored trees and the dual-annotation kit. Writes JSON only.
Bootstrap: benchmark.metrics.cluster_bootstrap_mean (percentile, 10,000, seed 20260723)
for task-cluster CIs; a design-stratified pair bootstrap for the 128-pair human study.

    python -m skyt.fse_final_posthoc tgrid      # 3.1  paired T=0.7 - T=0.0 per model
    python -m skyt.fse_final_posthoc human      # 3.2-3.4  kappa CI, reweighted sens/spec, impl. disagreement
    python -m skyt.fse_final_posthoc diffcost   # 3.5  changed lines, fp-same vs fp-diff
"""

from __future__ import annotations

import argparse
import difflib
import itertools
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from benchmark.metrics import _percentile, cluster_bootstrap_mean
from benchmark.schema import BOOTSTRAP_SEED, DEFAULT_N_BOOTSTRAP

T_GRID_MODELS = (
    "gpt-4o-mini",
    "claude-sonnet-4-5-20250929",
    "claude-haiku-4-5-20251001",
    "gpt-6-luna",
)
T_LOW, T_HIGH = 0.0, 0.7
OUT = Path("outputs") / "benchmark" / "fse_final_posthoc"
DUAL = Path("outputs") / "benchmark" / "fingerprint_annotation_dual"


# ---------------------------------------------------------------- 3.1


def paired_temperature_deltas(
    rows: Sequence[Dict[str, Any]],
    fields: Sequence[str] = ("plus_pass", "same_at_2"),
    models: Sequence[str] = T_GRID_MODELS,
) -> Dict[str, Any]:
    """Per model and field: task-level d = cell(T_HIGH) - cell(T_LOW), then task bootstrap."""
    out: Dict[str, Any] = {}
    for model in models:
        cells: Dict[str, Dict[float, Dict[str, Any]]] = defaultdict(dict)
        for row in rows:
            if str(row["model"]) != model or row.get("temperature") is None:
                continue
            temp = float(row["temperature"])
            if temp in cells[str(row["task_id"])]:
                raise ValueError(f"duplicate cell {model} {row['task_id']} T={temp}")
            cells[str(row["task_id"])][temp] = row
        out[model] = {}
        for field in fields:
            vals, ids = [], []
            for task, by_t in sorted(cells.items()):
                lo, hi = by_t.get(T_LOW), by_t.get(T_HIGH)
                if lo is None or hi is None or lo.get(field) is None or hi.get(field) is None:
                    continue
                vals.append(float(hi[field]) - float(lo[field]))
                ids.append(task)
            if not vals:
                out[model][field] = None
                continue
            r = cluster_bootstrap_mean(vals, ids, n_bootstrap=DEFAULT_N_BOOTSTRAP, seed=BOOTSTRAP_SEED)
            out[model][field] = {
                "delta_pts": round(100 * r["mean"], 2),
                "ci95_pts": [round(100 * r["lower"], 2), round(100 * r["upper"], 2)],
                "ci_includes_zero": r["lower"] <= 0 <= r["upper"],
                "n_tasks": r["n_clusters"],
            }
    plus = [v["plus_pass"] for v in out.values() if v.get("plus_pass")]
    same = [v["same_at_2"] for v in out.values() if v.get("same_at_2")]
    out["_claim_check"] = {
        "all_plus_ci_include_zero": all(p["ci_includes_zero"] for p in plus),
        "max_abs_plus_ci_bound_pts": max(max(abs(b) for b in p["ci95_pts"]) for p in plus) if plus else None,
        "all_same2_ci_exclude_zero": all(not s["ci_includes_zero"] for s in same),
    }
    return out


# ---------------------------------------------------------------- 3.2-3.4


def cohen_kappa(a: Sequence[int], b: Sequence[int]) -> Optional[float]:
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    if pe >= 1.0:
        return None
    return (po - pe) / (1 - pe)


def _design_key(row: Dict[str, Any]) -> Tuple[str, float, str]:
    return (str(row["model"]), float(row["temperature"]), str(row["stratum"]))


def _is_fp_same(key: Tuple[str, float, str]) -> bool:
    return key[2].startswith("fp_same")


def _is_both_cert(key: Tuple[str, float, str]) -> bool:
    return key[2].endswith("|both_cert")


def reweighted(
    labeled: Dict[Tuple[str, float, str], List[int]],
    population: Dict[Tuple[str, float, str], int],
) -> Dict[str, Optional[float]]:
    """Fingerprint = predictor, human_same = reference. Strata sampled on the predictor,
    so p_h = P(human same | stratum h) is unbiased; population rates use N_h weights."""
    same_mass = {h: population[h] * statistics.mean(y) for h, y in labeled.items() if y}
    diff_mass = {h: population[h] * (1 - statistics.mean(y)) for h, y in labeled.items() if y}

    def ratio(num: float, den: float) -> Optional[float]:
        return num / den if den > 0 else None

    def s(mass: Dict, pred: Callable[[Tuple], bool]) -> float:
        return sum(v for h, v in mass.items() if pred(h))

    every = lambda h: True  # noqa: E731
    cert = _is_both_cert
    n_cert = sum(population[h] for h in labeled if cert(h))
    return {
        "sensitivity": ratio(s(same_mass, _is_fp_same), s(same_mass, every)),
        "specificity": ratio(s(diff_mass, lambda h: not _is_fp_same(h)), s(diff_mass, every)),
        "ppv": ratio(s(same_mass, _is_fp_same), sum(population[h] for h in labeled if _is_fp_same(h))),
        "npv": ratio(s(diff_mass, lambda h: not _is_fp_same(h)),
                     sum(population[h] for h in labeled if not _is_fp_same(h))),
        # 3.4: among both-certified pairs in the annotated frame
        "fp_disagreement_cert": ratio(
            sum(population[h] for h in labeled if cert(h) and not _is_fp_same(h)), n_cert),
        "human_disagreement_cert": ratio(s(diff_mass, cert), n_cert),
        "human_diff_among_fp_diff_cert": ratio(
            s(diff_mass, lambda h: cert(h) and not _is_fp_same(h)),
            sum(population[h] for h in labeled if cert(h) and not _is_fp_same(h))),
        "human_diff_among_fp_same_cert": ratio(
            s(diff_mass, lambda h: cert(h) and _is_fp_same(h)),
            sum(population[h] for h in labeled if cert(h) and _is_fp_same(h))),
    }


def stratified_bootstrap(
    strata: Dict[Tuple, List[Any]],
    stat: Callable[[Dict[Tuple, List[Any]]], Dict[str, Optional[float]]],
    *,
    n_boot: int = DEFAULT_N_BOOTSTRAP,
    seed: int = BOOTSTRAP_SEED,
) -> Dict[str, Any]:
    """Resample items with replacement within each design stratum (n_h fixed)."""
    point = stat(strata)
    rng = random.Random(seed)
    keys = sorted(strata)
    draws: Dict[str, List[float]] = defaultdict(list)
    for _ in range(n_boot):
        sample = {k: rng.choices(strata[k], k=len(strata[k])) for k in keys if strata[k]}
        for name, value in stat(sample).items():
            if value is not None:
                draws[name].append(value)
    out = {}
    for name, value in point.items():
        d = sorted(draws.get(name, []))
        out[name] = {
            "estimate": value,
            "ci95": [_percentile(d, 0.025), _percentile(d, 0.975)] if d else [None, None],
            "n_undefined_draws": n_boot - len(d),
        }
    return out


def human_study(gold_path: Path, sheet_a: Path, sheet_b: Path, population: Dict) -> Dict[str, Any]:
    from skyt.annotation_score import load_gold, load_sheet

    gold = load_gold(gold_path)
    sheets = {"A": load_sheet(sheet_a), "B": load_sheet(sheet_b)}

    both: Dict[Tuple, List[Tuple[int, int]]] = defaultdict(list)
    for pid, row in gold.items():
        a, b = sheets["A"].get(pid), sheets["B"].get(pid)
        if a is not None and b is not None:
            both[_design_key(row)].append((a, b))

    def kappa_stat(st: Dict[Tuple, List[Tuple[int, int]]]) -> Dict[str, Optional[float]]:
        pairs = [p for v in st.values() for p in v]
        return {
            "kappa": cohen_kappa([p[0] for p in pairs], [p[1] for p in pairs]),
            "raw_agreement": sum(x == y for x, y in pairs) / len(pairs) if pairs else None,
        }

    result: Dict[str, Any] = {
        "n_both_labeled": sum(len(v) for v in both.values()),
        "kappa_sample": stratified_bootstrap(both, kappa_stat),
        "note_kappa": "Sample kappa on the design-balanced 128 pairs; stratified pair bootstrap.",
        "per_annotator_reweighted": {},
    }
    missing = [k for k in {_design_key(r) for r in gold.values()} if k not in population]
    if missing:
        raise ValueError(f"population count missing for strata {missing}")
    for name, labels in sheets.items():
        strata: Dict[Tuple, List[int]] = defaultdict(list)
        for pid, row in gold.items():
            if labels.get(pid) is not None:
                strata[_design_key(row)].append(int(labels[pid]))
        result["per_annotator_reweighted"][name] = stratified_bootstrap(
            strata, lambda st: reweighted(st, population))
    result["population_frame"] = {
        "cells": sorted({f"{k[0]} T={k[1]}" for k in population}),
        "n_pairs_by_stratum": {"|".join(map(str, k)): v for k, v in sorted(population.items())},
        "note": "Pair-weighted over parseable within-config pairs of the four annotated cells only.",
    }
    return result


def population_counts() -> Dict[Tuple[str, float, str], int]:
    from skyt.annotation_sample import collect_candidates
    from skyt.humaneval_heldout import OVERLAY_SOURCE

    return {k: len(v) for k, v in collect_candidates(Path(OVERLAY_SOURCE)).items()}


# ---------------------------------------------------------------- 3.5


def changed_lines(a: str, b: str) -> Tuple[int, float]:
    la, lb = a.splitlines(), b.splitlines()
    n = sum(
        1
        for line in difflib.unified_diff(la, lb, lineterm="", n=0)
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    )
    total = len(la) + len(lb)
    return n, (n / total if total else 0.0)


def diff_cost_cell(configs: Sequence[Sequence[Dict[str, Any]]]) -> Dict[str, Any]:
    """configs: records of one model x temperature cell, one list per task. Plus-passing pairs only."""
    from benchmark.relation import fingerprint

    buckets: Dict[str, List[Tuple[int, float]]] = {"fp_same": [], "fp_diff": []}
    for records in configs:
        ok = []
        for rec in sorted(records, key=lambda r: int(r.get("run_index", 0)))[:20]:
            code = rec.get("stitched_code") or ""
            fp = fingerprint(code, flexible_naming=True)
            if fp is not None and (rec.get("oracle") or {}).get("plus_passed"):
                ok.append((code, fp))
        for (ca, fa), (cb, fb) in itertools.combinations(ok, 2):
            buckets["fp_same" if fa == fb else "fp_diff"].append(changed_lines(ca, cb))

    def summary(v: List[Tuple[int, float]]) -> Dict[str, Any]:
        if not v:
            return {"n_pairs": 0}
        return {
            "n_pairs": len(v),
            "median_changed_lines": statistics.median(x[0] for x in v),
            "median_changed_share": round(statistics.median(x[1] for x in v), 3),
            "share_byte_identical": round(sum(1 for x in v if x[0] == 0) / len(v), 3),
        }

    return {k: summary(v) for k, v in buckets.items()}


def load_tree_records(tree: Path) -> Dict[Tuple[str, float], List[List[Dict[str, Any]]]]:
    from benchmark.score import _iter_jsonl

    cells: Dict[Tuple[str, float], List[List[Dict[str, Any]]]] = defaultdict(list)
    for path in sorted(tree.glob("*.jsonl")):
        recs = list(_iter_jsonl(path))
        if len(recs) < 2 or recs[0].get("temperature") is None:
            continue
        cells[(str(recs[0]["model"]), float(recs[0]["temperature"]))].append(recs)
    return cells


# ---------------------------------------------------------------- main


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("what", choices=["tgrid", "human", "diffcost"])
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    from benchmarks.humaneval_plus.expansion_analyze import EXPANSION, FROZEN, _load_rows

    trees = [FROZEN] + [EXPANSION / s for s in ("haiku45", "luna", "sonnet5") if (EXPANSION / s).exists()]

    if args.what == "tgrid":
        rows = [r for t in trees for r in _load_rows(t) if str(r["model"]) in T_GRID_MODELS]
        payload = paired_temperature_deltas(rows)
    elif args.what == "human":
        payload = human_study(
            DUAL / "gold.json",
            DUAL / "annotator_a" / "annotation_sheet.csv",
            DUAL / "annotator_b" / "annotation_sheet.csv",
            population_counts(),
        )
    else:
        payload = {}
        for tree in trees:
            for (model, temp), configs in sorted(load_tree_records(tree).items()):
                if model in T_GRID_MODELS and temp in (T_LOW, T_HIGH):
                    payload[f"{model} T={temp}"] = diff_cost_cell(configs)

    path = OUT / f"{args.what}.json"
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
