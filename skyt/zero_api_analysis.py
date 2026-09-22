"""Zero-API analyses on stored overlay + held-out summaries. No LLM."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from benchmark.metrics import config_repeatability
from benchmark.relation import fingerprint, strip_docstrings
from benchmark.schema import BOOTSTRAP_SEED, DEFAULT_N_BOOTSTRAP
from benchmark.score import _is_certified
from benchmarks.humaneval_plus.run import _load_existing, _safe_name
from skyt.heldout_posthoc import (
    HELDOUT_OUT,
    OVERLAY_SOURCE,
    _boot,
    _cell_rows,
    load_heldout_configs,
)


N = 20
N_BOOT = DEFAULT_N_BOOTSTRAP
SEED = BOOTSTRAP_SEED
CELLS = [
    ("all", None, None),
    ("gpt-4o-mini T=0.0", "gpt-4o-mini", 0.0),
    ("gpt-4o-mini T=0.7", "gpt-4o-mini", 0.7),
    ("claude-sonnet-4-5-20250929 T=0.0", "claude-sonnet-4-5-20250929", 0.0),
    ("claude-sonnet-4-5-20250929 T=0.7", "claude-sonnet-4-5-20250929", 0.7),
]


def source_normalized_id(code: str) -> Optional[str]:
    if not (code or "").strip():
        return None
    try:
        text = ast.unparse(ast.parse(code))
    except (SyntaxError, Exception):
        return None
    return hashlib.md5(text.encode()).hexdigest()


def ast_normalized_id(code: str) -> Optional[str]:
    if not (code or "").strip():
        return None
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    tree = strip_docstrings(tree)
    return hashlib.md5(ast.dump(tree, annotate_fields=False).encode()).hexdigest()


def sameeval_id(code: str) -> Optional[str]:
    return fingerprint(code, flexible_naming=True)


RULERS: Dict[str, Callable[[str], Optional[str]]] = {
    "normalized_source": source_normalized_id,
    "ast_normalized": ast_normalized_id,
    "sameeval_v2": sameeval_id,
}


def _ranks(values: Sequence[float]) -> List[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(values):
        end = index
        while end + 1 < len(values) and values[order[end + 1]] == values[order[index]]:
            end += 1
        avg = (index + end) / 2.0 + 1.0
        for pos in range(index, end + 1):
            ranks[order[pos]] = avg
        index = end + 1
    return ranks


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


def spearman(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    return _pearson(_ranks([float(x) for x in xs]), _ranks([float(y) for y in ys]))


def spearman_bootstrap(
    xs: Sequence[float],
    ys: Sequence[float],
    task_ids: Sequence[str],
) -> Dict[str, Any]:
    grouped: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
    for x, y, task in zip(xs, ys, task_ids):
        grouped[str(task)].append((float(x), float(y)))
    tasks = sorted(grouped)
    point_xs = []
    point_ys = []
    for task in tasks:
        pairs = grouped[task]
        point_xs.append(sum(p[0] for p in pairs) / len(pairs))
        point_ys.append(sum(p[1] for p in pairs) / len(pairs))
    point = spearman(point_xs, point_ys)
    rng = random.Random(SEED)
    boot = []
    n = len(tasks)
    for _ in range(N_BOOT):
        sample = rng.choices(range(n), k=n)
        value = spearman([point_xs[i] for i in sample], [point_ys[i] for i in sample])
        if value is not None:
            boot.append(value)
    boot.sort()
    if not boot or point is None:
        return {"mean": point, "lower": None, "upper": None, "n_clusters": n}
    lo = boot[int((len(boot) - 1) * 0.025)]
    hi = boot[int((len(boot) - 1) * 0.975)]
    return {
        "mean": point,
        "lower": lo,
        "upper": hi,
        "n_clusters": n,
        "pct": round(point, 3),
        "ci95": [round(lo, 3), round(hi, 3)],
    }


def _repeat(codes: Sequence[str], certified: Sequence[bool], ruler) -> Dict[str, Any]:
    prints = [ruler(code or "") for code in codes]
    cert = [bool(ok and fp is not None) for ok, fp in zip(certified, prints)]
    return config_repeatability(prints, cert)


def overlay_fingerprint_rows(source_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    by_ruler: Dict[str, List[Dict[str, Any]]] = {name: [] for name in RULERS}
    for path in sorted(source_dir.glob("*.jsonl")):
        records = sorted(
            _load_existing(path), key=lambda item: int(item.get("run_index", 0))
        )[:N]
        if len(records) < N:
            continue
        codes = [record.get("stitched_code") or "" for record in records]
        plus = [
            _is_certified(
                record,
                fingerprint(record.get("stitched_code") or "", flexible_naming=True)
                is not None,
            )
            for record in records
        ]
        meta = {
            "task_id": records[0]["task_id"],
            "model": records[0]["model"],
            "temperature": float(records[0]["temperature"]),
        }
        for name, ruler in RULERS.items():
            analysis = _repeat(codes, plus, ruler)
            by_ruler[name].append({**meta, "same_at_2": analysis["same_at_2"]})
    return by_ruler


def heldout_pre_fingerprint_rows(
    rows: List[Dict[str, Any]], source_dir: Path
) -> Dict[str, List[Dict[str, Any]]]:
    by_ruler: Dict[str, List[Dict[str, Any]]] = {name: [] for name in RULERS}
    for index, row in enumerate(rows, start=1):
        stem = _safe_name(row["task_id"], row["model"], row["temperature"])
        records = sorted(
            _load_existing(source_dir / f"{stem}.jsonl"),
            key=lambda item: int(item["run_index"]),
        )[:N]
        codes = [record.get("stitched_code") or "" for record in records]
        plus = [
            _is_certified(record, fingerprint(code, flexible_naming=True) is not None)
            for record, code in zip(records, codes)
        ]
        acc: Dict[str, List[float]] = {name: [] for name in RULERS}
        for split_row in row["splits"]:
            test = [int(i) for i in split_row["test_indices"]]
            test_codes = [codes[i] for i in test]
            test_plus = [plus[i] for i in test]
            for name, ruler in RULERS.items():
                acc[name].append(_repeat(test_codes, test_plus, ruler)["same_at_2"])
        for name in RULERS:
            values = acc[name]
            pre = sum(values) / len(values) if values else None
            post = row.get("post_same_at_2")
            by_ruler[name].append(
                {
                    "task_id": row["task_id"],
                    "model": row["model"],
                    "temperature": row["temperature"],
                    "same_at_2": pre,
                    "post_same_at_2": post,
                    "delta_same_at_2": (
                        None if pre is None or post is None else float(post) - pre
                    ),
                }
            )
        if index % 100 == 0:
            print(f"  pre fingerprint {index}/{len(rows)}", flush=True)
    return by_ruler


def operational_cache(
    rows: List[Dict[str, Any]], source_dir: Path
) -> List[Dict[str, Any]]:
    out = []
    for row in rows:
        stem = _safe_name(row["task_id"], row["model"], row["temperature"])
        records = sorted(
            _load_existing(source_dir / f"{stem}.jsonl"),
            key=lambda item: int(item["run_index"]),
        )[:N]
        prints = [
            fingerprint(record.get("stitched_code") or "", flexible_naming=True)
            for record in records
        ]
        base_ok = [
            bool((record.get("oracle") or {}).get("base_passed")) and fp is not None
            for record, fp in zip(records, prints)
        ]
        plus_ok = [_is_certified(record, fp is not None) for record, fp in zip(records, prints)]
        same_vals = []
        plus_vals = []
        n_avail = 0
        universe = set(range(N))
        for split_row in row["splits"]:
            train = [int(i) for i in split_row["train_indices"]]
            test = [int(i) for i in split_row.get("test_indices") or []]
            if not test:
                test = sorted(universe - set(train))
            first = next((i for i in sorted(train) if base_ok[i]), None)
            if first is None:
                analysis = config_repeatability(
                    [prints[i] for i in test], [plus_ok[i] for i in test]
                )
            else:
                n_avail += 1
                analysis = config_repeatability(
                    [prints[first]] * len(test), [plus_ok[first]] * len(test)
                )
            same_vals.append(analysis["same_at_2"])
            plus_vals.append(analysis["plus_pass"])
        item = dict(row)
        item["op_cache_same_at_2"] = sum(same_vals) / len(same_vals)
        item["op_cache_plus_pass"] = sum(plus_vals) / len(plus_vals)
        item["op_cache_n_splits_available"] = n_avail
        out.append(item)
    return out


def split_prefix_robustness(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    table = []
    for b in (5, 10, 15, 20):
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
                "pre_same_at_2": _boot(pre_rows, "pre"),
                "post_same_at_2": _boot(post_rows, "post"),
                "delta_same_at_2": _boot(delta_rows, "delta"),
            }
        )
    return table


def failure_correlates(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    usable = [row for row in rows if row.get("delta_same_at_2") is not None]
    rollback = [row for row in usable if row.get("n_rolled_back_mean") is not None]
    transformed = [row for row in usable if row.get("n_transformed_mean") is not None]
    heavy = sorted(
        rollback, key=lambda item: float(item["n_rolled_back_mean"]), reverse=True
    )[:10]
    canon_poor = sorted(
        usable, key=lambda item: int(item.get("n_splits_with_canon") or 0)
    )[:10]
    return {
        "n_negative_same_at_2": sum(1 for row in usable if row["delta_same_at_2"] < 0),
        "n_negative_plus_pass": sum(
            1
            for row in rows
            if row.get("delta_plus_pass") is not None and row["delta_plus_pass"] < -1e-12
        ),
        "spearman_lift_vs_rollback": spearman(
            [float(row["n_rolled_back_mean"]) for row in rollback],
            [float(row["delta_same_at_2"]) for row in rollback],
        ),
        "spearman_lift_vs_n_canon_splits": spearman(
            [float(row.get("n_splits_with_canon") or 0) for row in usable],
            [float(row["delta_same_at_2"]) for row in usable],
        ),
        "spearman_lift_vs_n_transformed": spearman(
            [float(row["n_transformed_mean"]) for row in transformed],
            [float(row["delta_same_at_2"]) for row in transformed],
        ),
        "top_rollback": [
            {
                "task_id": row["task_id"],
                "model": row["model"],
                "temperature": row["temperature"],
                "n_rolled_back_mean": row["n_rolled_back_mean"],
                "n_transformed_mean": row["n_transformed_mean"],
                "n_splits_with_canon": row["n_splits_with_canon"],
                "delta_same_at_2": row["delta_same_at_2"],
            }
            for row in heavy
        ],
        "canon_poor": [
            {
                "task_id": row["task_id"],
                "model": row["model"],
                "temperature": row["temperature"],
                "n_splits_with_canon": row["n_splits_with_canon"],
                "delta_same_at_2": row["delta_same_at_2"],
            }
            for row in canon_poor
        ],
    }


def run(
    *,
    source_dir: Path = OVERLAY_SOURCE,
    heldout_dir: Path = HELDOUT_OUT,
) -> Dict[str, Any]:
    print("loading held-out summaries", flush=True)
    rows = load_heldout_configs(heldout_dir)
    print("overlay fingerprint rulers", flush=True)
    overlay = overlay_fingerprint_rows(source_dir)
    overlay_slices = {
        name: {
            label: _boot(_cell_rows(ruler_rows, model, temp), "same_at_2")
            for label, model, temp in CELLS
        }
        for name, ruler_rows in overlay.items()
    }
    print("held-out PRE fingerprint rulers", flush=True)
    pre = heldout_pre_fingerprint_rows(rows, source_dir)
    pre_slices = {
        name: {
            "raw_pre": _boot(ruler_rows, "same_at_2"),
            "note": (
                "POST repaired programs were not persisted; cannot score "
                "alternate rulers on SKYT post without a Docker rewrite."
            ),
        }
        for name, ruler_rows in pre.items()
    }
    print("operational (base) first-passer cache", flush=True)
    cached = operational_cache(rows, source_dir)
    cache_slices = [
        {
            "label": label,
            "op_cache_same_at_2": _boot(subset, "op_cache_same_at_2"),
            "op_cache_plus_pass": _boot(subset, "op_cache_plus_pass"),
            "raw_same_at_2": _boot(subset, "pre_same_at_2"),
            "skyt_same_at_2": _boot(subset, "post_same_at_2"),
        }
        for label, model, temp in CELLS
        for subset in [_cell_rows(cached, model, temp)]
    ]
    usable = [row for row in rows if row.get("delta_same_at_2") is not None]
    hetero = {
        "spearman_pre_same_at_2_vs_lift": spearman_bootstrap(
            [float(row["pre_same_at_2"]) for row in usable],
            [float(row["delta_same_at_2"]) for row in usable],
            [str(row["task_id"]) for row in usable],
        ),
        "pearson_pre_same_at_2_vs_lift": _pearson(
            [float(row["pre_same_at_2"]) for row in usable],
            [float(row["delta_same_at_2"]) for row in usable],
        ),
        "n": len(usable),
    }
    report = {
        "schema": "skyt-zero-api-analysis-v1",
        "n_configs": len(rows),
        "overlay_fingerprint_same_at_2": overlay_slices,
        "heldout_pre_fingerprint_same_at_2": pre_slices,
        "operational_first_cache": cache_slices,
        "heterogeneity": hetero,
        "split_prefix_robustness": split_prefix_robustness(rows),
        "failures": failure_correlates(rows),
    }
    out = heldout_dir / "zero_api_report.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"wrote {out}", flush=True)
    return report


if __name__ == "__main__":
    payload = run()
    print("\nOverlay same@2 by ruler (all):")
    for name, slices in payload["overlay_fingerprint_same_at_2"].items():
        item = slices["all"]
        print(f"  {name}: {item['pct']} CI {item['ci95_pct']}")
    print("\nHeld-out PRE same@2 by ruler (all):")
    for name, slices in payload["heldout_pre_fingerprint_same_at_2"].items():
        print(f"  {name}: {slices['raw_pre']['pct']} CI {slices['raw_pre']['ci95_pct']}")
    print("\nSpearman:", payload["heterogeneity"]["spearman_pre_same_at_2_vs_lift"])
    for row in payload["split_prefix_robustness"]:
        d = row["delta_same_at_2"]
        print(f"B={row['B']} delta {d['pct']} CI {d['ci95_pct']}")
    cache = payload["operational_first_cache"][0]
    print(
        "Op-cache vs SKYT same@2:",
        cache["op_cache_same_at_2"]["pct"],
        "vs",
        cache["skyt_same_at_2"]["pct"],
    )
