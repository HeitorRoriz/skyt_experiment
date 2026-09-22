"""Post-hoc held-out SKYT analysis. No LLM. No runtime change.

Paired cluster-bootstrap deltas, common-support same@2|cert, first-cert and
consensus cache baselines, and task-level lifts. Reads the frozen overlay and
the held-out summary tree.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from benchmark.metrics import cluster_bootstrap_mean, config_repeatability
from benchmark.relation import fingerprint
from benchmark.schema import BOOTSTRAP_SEED, DEFAULT_N_BOOTSTRAP
from benchmark.score import _is_certified
from benchmarks.humaneval_plus.run import _load_existing, _safe_name
from skyt.humaneval_heldout import HELDOUT_OUT, OVERLAY_SOURCE


N_BOOT = DEFAULT_N_BOOTSTRAP
SEED = BOOTSTRAP_SEED
N = 20
TRAIN = 10
SPLITS = 20


def _pct(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(100.0 * float(value), 1)


def _ci_pct(interval: Optional[Sequence[float]]) -> Optional[List[float]]:
    if not interval or interval[0] is None or interval[1] is None:
        return None
    return [round(100.0 * float(interval[0]), 1), round(100.0 * float(interval[1]), 1)]


def _boot(rows: Sequence[Dict[str, Any]], field: str) -> Dict[str, Any]:
    usable = [row for row in rows if row.get(field) is not None]
    if not usable:
        return {
            "mean": None,
            "lower": None,
            "upper": None,
            "n_defined": 0,
            "n_dropped": len(rows),
            "pct": None,
            "ci95_pct": None,
        }
    result = cluster_bootstrap_mean(
        [float(row[field]) for row in usable],
        [str(row["task_id"]) for row in usable],
        n_bootstrap=N_BOOT,
        seed=SEED,
    )
    return {
        "mean": result["mean"],
        "lower": result["lower"],
        "upper": result["upper"],
        "n_defined": len(usable),
        "n_dropped": len(rows) - len(usable),
        "n_clusters": result["n_clusters"],
        "pct": _pct(result["mean"]),
        "ci95_pct": _ci_pct([result["lower"], result["upper"]]),
    }


def load_heldout_configs(heldout_dir: Path) -> List[Dict[str, Any]]:
    rows = []
    for path in sorted(heldout_dir.glob("*_heldout.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema") != "skyt-humaneval-plus-heldout-summary-v1":
            continue
        if int(payload.get("n_splits") or 0) != SPLITS:
            continue
        row: Dict[str, Any] = {
            "task_id": payload["task_id"],
            "model": payload["model"],
            "temperature": float(payload["temperature"]),
            "path": str(path),
            "n_splits_with_canon": payload.get("n_splits_with_canon"),
            "n_transformed_mean": payload.get("n_transformed_mean"),
            "n_rolled_back_mean": payload.get("n_rolled_back_mean"),
            "pre_plus_pass": payload.get("pre_plus_pass"),
            "post_plus_pass": payload.get("post_plus_pass"),
            "pre_same_at_2": payload.get("pre_same_at_2"),
            "post_same_at_2": payload.get("post_same_at_2"),
            "pre_same_at_2_given_cert": payload.get("pre_same_at_2_given_cert"),
            "post_same_at_2_given_cert": payload.get("post_same_at_2_given_cert"),
            "splits": payload.get("splits") or [],
        }
        if row["pre_same_at_2"] is not None and row["post_same_at_2"] is not None:
            row["delta_same_at_2"] = float(row["post_same_at_2"]) - float(
                row["pre_same_at_2"]
            )
        else:
            row["delta_same_at_2"] = None
        if row["pre_plus_pass"] is not None and row["post_plus_pass"] is not None:
            row["delta_plus_pass"] = float(row["post_plus_pass"]) - float(
                row["pre_plus_pass"]
            )
        else:
            row["delta_plus_pass"] = None
        if (
            row["pre_same_at_2_given_cert"] is not None
            and row["post_same_at_2_given_cert"] is not None
        ):
            row["delta_same_at_2_given_cert"] = float(
                row["post_same_at_2_given_cert"]
            ) - float(row["pre_same_at_2_given_cert"])
            row["common_support"] = True
        else:
            row["delta_same_at_2_given_cert"] = None
            row["common_support"] = False
        if row["pre_same_at_2_given_cert"] is not None:
            row["pre_disagreement"] = 1.0 - float(row["pre_same_at_2_given_cert"])
        else:
            row["pre_disagreement"] = None
        if row["post_same_at_2_given_cert"] is not None:
            row["post_disagreement"] = 1.0 - float(row["post_same_at_2_given_cert"])
        else:
            row["post_disagreement"] = None
        if row["pre_disagreement"] is not None and row["post_disagreement"] is not None:
            row["delta_disagreement"] = float(row["post_disagreement"]) - float(
                row["pre_disagreement"]
            )
        else:
            row["delta_disagreement"] = None
        rows.append(row)
    return rows


def _cell_rows(
    rows: Sequence[Dict[str, Any]], model: Optional[str], temperature: Optional[float]
) -> List[Dict[str, Any]]:
    out = []
    for row in rows:
        if model is not None and row["model"] != model:
            continue
        if temperature is not None and float(row["temperature"]) != float(temperature):
            continue
        out.append(row)
    return out


def _slice_report(rows: Sequence[Dict[str, Any]], label: str) -> Dict[str, Any]:
    common = [row for row in rows if row["common_support"]]
    pre_cert = [row for row in rows if row.get("pre_same_at_2_given_cert") is not None]
    post_cert = [row for row in rows if row.get("post_same_at_2_given_cert") is not None]
    payload = {
        "label": label,
        "n_configs": len(rows),
        "n_tasks": len({row["task_id"] for row in rows}),
        "plus_pass_pre": _boot(rows, "pre_plus_pass"),
        "plus_pass_post": _boot(rows, "post_plus_pass"),
        "delta_plus_pass": _boot(rows, "delta_plus_pass"),
        "same_at_2_pre": _boot(rows, "pre_same_at_2"),
        "same_at_2_post": _boot(rows, "post_same_at_2"),
        "delta_same_at_2": _boot(rows, "delta_same_at_2"),
        "same_at_2_given_cert_pre_all": _boot(rows, "pre_same_at_2_given_cert"),
        "same_at_2_given_cert_post_all": _boot(rows, "post_same_at_2_given_cert"),
        "delta_same_at_2_given_cert_all": _boot(rows, "delta_same_at_2_given_cert"),
        "coverage_pre": (len(pre_cert) / len(rows)) if rows else None,
        "coverage_post": (len(post_cert) / len(rows)) if rows else None,
        "coverage_common": (len(common) / len(rows)) if rows else None,
        "n_common_support": len(common),
        "same_at_2_given_cert_pre_common": _boot(common, "pre_same_at_2_given_cert"),
        "same_at_2_given_cert_post_common": _boot(common, "post_same_at_2_given_cert"),
        "delta_same_at_2_given_cert_common": _boot(common, "delta_same_at_2_given_cert"),
        "disagreement_pre_common": _boot(common, "pre_disagreement"),
        "disagreement_post_common": _boot(common, "post_disagreement"),
        "delta_disagreement_common": _boot(common, "delta_disagreement"),
        "n_no_canon_all_splits": sum(
            1 for row in rows if int(row.get("n_splits_with_canon") or 0) == 0
        ),
        "n_negative_same_at_2": sum(
            1
            for row in rows
            if row.get("delta_same_at_2") is not None and row["delta_same_at_2"] < 0
        ),
        "n_negative_plus_pass": sum(
            1
            for row in rows
            if row.get("delta_plus_pass") is not None and row["delta_plus_pass"] < -1e-12
        ),
    }
    pre_d = payload["disagreement_pre_common"]["mean"]
    post_d = payload["disagreement_post_common"]["mean"]
    if pre_d and pre_d > 0 and post_d is not None:
        payload["disagreement_relative_reduction_common"] = (pre_d - post_d) / pre_d
        payload["disagreement_relative_reduction_common_pct"] = round(
            100.0 * (pre_d - post_d) / pre_d, 1
        )
    else:
        payload["disagreement_relative_reduction_common"] = None
        payload["disagreement_relative_reduction_common_pct"] = None
    return payload


def temperature_interaction(
    rows: Sequence[Dict[str, Any]],
    field: str = "delta_same_at_2",
) -> Dict[str, Any]:
    by_task: Dict[str, Dict[float, List[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row.get(field) is None:
            continue
        by_task[str(row["task_id"])][float(row["temperature"])].append(
            float(row[field])
        )
    interaction_rows = []
    for task_id, temps in by_task.items():
        if 0.0 not in temps or 0.7 not in temps:
            continue
        d0 = sum(temps[0.0]) / len(temps[0.0])
        d7 = sum(temps[0.7]) / len(temps[0.7])
        interaction_rows.append(
            {"task_id": task_id, "interaction": d7 - d0, "delta_t0": d0, "delta_t7": d7}
        )
    per_model = {}
    for model in sorted({row["model"] for row in rows}):
        by_task_m: Dict[str, Dict[float, float]] = defaultdict(dict)
        for row in rows:
            if row["model"] != model or row.get(field) is None:
                continue
            by_task_m[str(row["task_id"])][float(row["temperature"])] = float(
                row[field]
            )
        inter = [
            {"task_id": task_id, "interaction": temps[0.7] - temps[0.0]}
            for task_id, temps in by_task_m.items()
            if 0.0 in temps and 0.7 in temps
        ]
        per_model[model] = _boot(inter, "interaction")
        per_model[model]["n_tasks"] = len(inter)
    return {
        "pooled_models": _boot(interaction_rows, "interaction"),
        "n_tasks": len(interaction_rows),
        "mean_delta_t0": _boot(interaction_rows, "delta_t0"),
        "mean_delta_t7": _boot(interaction_rows, "delta_t7"),
        "per_model": per_model,
        "field": field,
    }


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0.0 or dy == 0.0:
        return None
    return num / (dx * dy)


def _record_prints(
    records: Sequence[Dict[str, Any]],
) -> Tuple[List[Optional[str]], List[bool]]:
    prints = [
        fingerprint(record.get("stitched_code") or "", flexible_naming=True)
        for record in records
    ]
    certified = [
        _is_certified(record, fp is not None) for record, fp in zip(records, prints)
    ]
    return prints, certified


def _identical_copies(parseable: bool, certified: bool) -> Dict[str, Any]:
    if certified and parseable:
        return {
            "same_at_2": 1.0,
            "same_at_2_given_cert": 1.0,
            "plus_pass": 1.0,
        }
    return {
        "same_at_2": 0.0,
        "same_at_2_given_cert": None,
        "plus_pass": 0.0 if not certified else 1.0,
    }


def cache_baselines_for_config(
    source_dir: Path,
    row: Dict[str, Any],
) -> Dict[str, Any]:
    stem = _safe_name(row["task_id"], row["model"], row["temperature"])
    records = sorted(
        _load_existing(source_dir / f"{stem}.jsonl"),
        key=lambda item: int(item["run_index"]),
    )[:N]
    if len(records) < N:
        raise ValueError(f"{stem}: overlay incomplete")
    prints, certified = _record_prints(records)
    first_metrics: List[Dict[str, Any]] = []
    consensus_metrics: List[Dict[str, Any]] = []
    n_first = n_consensus = 0
    universe = set(range(N))
    for split_row in row["splits"]:
        train = [int(index) for index in split_row["train_indices"]]
        test = [int(index) for index in split_row.get("test_indices") or []]
        if not test:
            test = sorted(universe - set(train))
        test_prints = [prints[i] for i in test]
        test_certs = [certified[i] for i in test]
        raw_test = config_repeatability(test_prints, test_certs)
        first_idx = next((i for i in sorted(train) if certified[i]), None)
        if first_idx is not None:
            n_first += 1
            first_metrics.append(
                _identical_copies(prints[first_idx] is not None, certified[first_idx])
            )
        else:
            first_metrics.append(raw_test)
        cons = split_row.get("consensus_index")
        if split_row.get("canon_created") and cons is not None:
            cons_i = int(cons)
            n_consensus += 1
            consensus_metrics.append(
                _identical_copies(prints[cons_i] is not None, certified[cons_i])
            )
        else:
            consensus_metrics.append(raw_test)

    def _mean(items: Sequence[Dict[str, Any]], key: str) -> Optional[float]:
        values = [item[key] for item in items if item.get(key) is not None]
        if not values:
            return None
        return sum(float(v) for v in values) / len(values)

    return {
        "first_cache_same_at_2": _mean(first_metrics, "same_at_2"),
        "first_cache_same_at_2_given_cert": _mean(first_metrics, "same_at_2_given_cert"),
        "first_cache_plus_pass": _mean(first_metrics, "plus_pass"),
        "consensus_cache_same_at_2": _mean(consensus_metrics, "same_at_2"),
        "consensus_cache_same_at_2_given_cert": _mean(
            consensus_metrics, "same_at_2_given_cert"
        ),
        "consensus_cache_plus_pass": _mean(consensus_metrics, "plus_pass"),
        "n_splits_with_first_cache": n_first,
        "n_splits_with_consensus_cache": n_consensus,
    }


def attach_cache_baselines(rows: List[Dict[str, Any]], source_dir: Path) -> None:
    for index, row in enumerate(rows, start=1):
        row.update(cache_baselines_for_config(source_dir, row))
        post = row.get("post_same_at_2")
        first = row.get("first_cache_same_at_2")
        cons = row.get("consensus_cache_same_at_2")
        if post is not None and first is not None:
            row["skyt_minus_first_cache_same_at_2"] = float(post) - float(first)
        else:
            row["skyt_minus_first_cache_same_at_2"] = None
        if post is not None and cons is not None:
            row["skyt_minus_consensus_cache_same_at_2"] = float(post) - float(cons)
        else:
            row["skyt_minus_consensus_cache_same_at_2"] = None
        if index % 50 == 0:
            print(f"  cache baselines {index}/{len(rows)}", flush=True)


def failure_analysis(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    ranked = sorted(
        [row for row in rows if row.get("delta_same_at_2") is not None],
        key=lambda item: item["delta_same_at_2"],
        reverse=True,
    )

    def _brief(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "task_id": row["task_id"],
            "model": row["model"],
            "temperature": row["temperature"],
            "pre_same_at_2": row["pre_same_at_2"],
            "post_same_at_2": row["post_same_at_2"],
            "delta_same_at_2": row["delta_same_at_2"],
            "delta_plus_pass": row["delta_plus_pass"],
            "n_splits_with_canon": row["n_splits_with_canon"],
        }

    with_lift = [
        row
        for row in rows
        if row.get("delta_same_at_2") is not None and row.get("pre_same_at_2") is not None
    ]
    with_canon = [
        row
        for row in with_lift
        if row.get("n_splits_with_canon") is not None
    ]
    return {
        "n_negative_same_at_2": sum(1 for row in ranked if row["delta_same_at_2"] < 0),
        "n_negative_plus_pass": sum(
            1
            for row in rows
            if row.get("delta_plus_pass") is not None and row["delta_plus_pass"] < -1e-12
        ),
        "n_no_canon_all_splits": sum(
            1 for row in rows if int(row.get("n_splits_with_canon") or 0) == 0
        ),
        "pearson_pre_same_at_2_vs_lift": _pearson(
            [float(row["pre_same_at_2"]) for row in with_lift],
            [float(row["delta_same_at_2"]) for row in with_lift],
        ),
        "pearson_n_splits_with_canon_vs_lift": _pearson(
            [float(row["n_splits_with_canon"]) for row in with_canon],
            [float(row["delta_same_at_2"]) for row in with_canon],
        ),
        "top_wins": [_brief(row) for row in ranked[:10]],
        "top_losses": [
            _brief(row) for row in ranked if row["delta_same_at_2"] < 0
        ][:10],
    }


CELLS = [
    ("all", None, None),
    ("gpt-4o-mini T=0.0", "gpt-4o-mini", 0.0),
    ("gpt-4o-mini T=0.7", "gpt-4o-mini", 0.7),
    ("claude-sonnet-4-5-20250929 T=0.0", "claude-sonnet-4-5-20250929", 0.0),
    ("claude-sonnet-4-5-20250929 T=0.7", "claude-sonnet-4-5-20250929", 0.7),
]


def run(
    *,
    source_dir: Path = OVERLAY_SOURCE,
    heldout_dir: Path = HELDOUT_OUT,
    with_cache: bool = True,
) -> Dict[str, Any]:
    print("loading held-out summaries", flush=True)
    rows = load_heldout_configs(heldout_dir)
    if len(rows) != 656:
        raise ValueError(f"expected 656 held-out summaries, got {len(rows)}")
    slices = [
        _slice_report(_cell_rows(rows, model, temp), label)
        for label, model, temp in CELLS
    ]
    interaction = temperature_interaction(rows)
    failures = failure_analysis(rows)
    cache_slices = None
    if with_cache:
        print("computing cache baselines (no Docker)", flush=True)
        attach_cache_baselines(rows, source_dir)
        cache_slices = []
        for label, model, temp in CELLS:
            subset = _cell_rows(rows, model, temp)
            cache_slices.append(
                {
                    "label": label,
                    "first_cache_same_at_2": _boot(subset, "first_cache_same_at_2"),
                    "first_cache_plus_pass": _boot(subset, "first_cache_plus_pass"),
                    "consensus_cache_same_at_2": _boot(
                        subset, "consensus_cache_same_at_2"
                    ),
                    "consensus_cache_plus_pass": _boot(
                        subset, "consensus_cache_plus_pass"
                    ),
                    "first_cache_same_at_2_given_cert": _boot(
                        subset, "first_cache_same_at_2_given_cert"
                    ),
                    "consensus_cache_same_at_2_given_cert": _boot(
                        subset, "consensus_cache_same_at_2_given_cert"
                    ),
                    "skyt_same_at_2": _boot(subset, "post_same_at_2"),
                    "raw_same_at_2": _boot(subset, "pre_same_at_2"),
                    "skyt_minus_first_cache_same_at_2": _boot(
                        subset, "skyt_minus_first_cache_same_at_2"
                    ),
                    "skyt_minus_consensus_cache_same_at_2": _boot(
                        subset, "skyt_minus_consensus_cache_same_at_2"
                    ),
                }
            )
    report = {
        "schema": "skyt-heldout-posthoc-v1",
        "n_configs": len(rows),
        "n_bootstrap": N_BOOT,
        "seed": SEED,
        "slices": slices,
        "temperature_interaction_same_at_2": interaction,
        "failures": failures,
        "cache_baselines": cache_slices,
    }
    slim_rows = [{k: v for k, v in row.items() if k != "splits"} for row in rows]
    (heldout_dir / "posthoc_config_rows.json").write_text(
        json.dumps(slim_rows, indent=2, default=str), encoding="utf-8"
    )
    out_path = heldout_dir / "posthoc_report.json"
    out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"wrote {out_path}", flush=True)
    return report


def _print_slice(slice_row: Dict[str, Any]) -> None:
    print(f"\n== {slice_row['label']} n={slice_row['n_configs']}")
    d = slice_row["delta_same_at_2"]
    print(
        f"  delta same@2 {d['pct']} pp CI {d['ci95_pct']} "
        f"(pre {slice_row['same_at_2_pre']['pct']} -> post {slice_row['same_at_2_post']['pct']})"
    )
    p = slice_row["delta_plus_pass"]
    print(
        f"  delta plus-pass {p['pct']} pp CI {p['ci95_pct']} "
        f"({slice_row['plus_pass_pre']['pct']} -> {slice_row['plus_pass_post']['pct']})"
    )
    c = slice_row["delta_same_at_2_given_cert_common"]
    print(
        f"  common-support same@2|cert n={slice_row['n_common_support']} "
        f"cov={slice_row['coverage_common']:.3f} "
        f"pre {slice_row['same_at_2_given_cert_pre_common']['pct']} -> "
        f"post {slice_row['same_at_2_given_cert_post_common']['pct']} "
        f"delta {c['pct']} pp CI {c['ci95_pct']}"
    )
    print(
        f"  certified disagreement (common) "
        f"{slice_row['disagreement_pre_common']['pct']}% -> "
        f"{slice_row['disagreement_post_common']['pct']}% "
        f"(relative reduction {slice_row.get('disagreement_relative_reduction_common_pct')}%)"
    )


if __name__ == "__main__":
    payload = run()
    for slice_row in payload["slices"]:
        _print_slice(slice_row)
    inter = payload["temperature_interaction_same_at_2"]["pooled_models"]
    print(
        "\nT=0.7 minus T=0.0 same@2 lift (task mean over models): "
        f"{inter['pct']} pp CI {inter['ci95_pct']}"
    )
    if payload.get("cache_baselines"):
        all_cache = payload["cache_baselines"][0]
        print(
            "\nCache vs SKYT same@2 (all): "
            f"raw {all_cache['raw_same_at_2']['pct']} "
            f"first-cache {all_cache['first_cache_same_at_2']['pct']} "
            f"consensus-cache {all_cache['consensus_cache_same_at_2']['pct']} "
            f"SKYT {all_cache['skyt_same_at_2']['pct']}"
        )
