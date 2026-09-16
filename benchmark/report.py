"""Aggregate per model × temperature. No mixed SKYT-style headline."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .metrics import cluster_bootstrap_mean, cluster_jackknife_mean
from .schema import (
    FROZEN_PROTOCOL_N,
    INFERENCE,
    INFERENCE_VERSION,
    METRIC_HELP,
    PILOT_TASK_WARN_BELOW,
    RELATION_VERSION,
    RELATION_VERSION_NOTE,
    REQUIRED_SLICE_KEYS,
    SCHEMA,
    SLICE_METRICS,
)


def is_pilot_grid(*, n_tasks: int, n: int) -> bool:
    """True when the slice is smaller than the frozen protocol (N=20, 30+ tasks)."""
    return n_tasks < PILOT_TASK_WARN_BELOW or n < FROZEN_PROTOCOL_N


def _clustered(
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
            "n_missing": len(rows),
            "n_clusters": 0,
            "jackknife": {
                "mean": None,
                "se": None,
                "lower": None,
                "upper": None,
                "n_clusters": 0,
                "skipped": "no_defined_values",
            },
        }
    values = [float(row[field]) for row in usable]
    ids = [str(row["task_id"]) for row in usable]
    result = cluster_bootstrap_mean(values, ids, n_bootstrap=n_bootstrap)
    result["n_defined"] = len(usable)
    result["n_missing"] = len(rows) - len(usable)
    result["jackknife"] = cluster_jackknife_mean(values, ids)
    return result


def _require_row_metrics(rows: Sequence[Dict[str, Any]]) -> None:
    for row in rows:
        for name in SLICE_METRICS:
            if name not in row:
                raise ValueError(f"Config row missing required metric {name!r}")


def _operational_n(rows: Sequence[Dict[str, Any]]) -> int:
    ns = {int(row["n"]) for row in rows}
    if len(ns) != 1:
        raise ValueError(
            "A model × temperature slice cannot mix sample sizes N="
            f"{sorted(ns)}. Score those grids separately."
        )
    return next(iter(ns))


def _slice_payload(
    rows: Sequence[Dict[str, Any]],
    *,
    model: str,
    temperature: float,
    n_bootstrap: int,
) -> Dict[str, Any]:
    _require_row_metrics(rows)
    operational_n = _operational_n(rows)
    n_tasks = len({row["task_id"] for row in rows})
    payload: Dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "n_configs": len(rows),
        "n_tasks": n_tasks,
        "n": operational_n,
        "n_dropped_same_at_2_given_cert": sum(
            1 for row in rows if row.get("same_at_2_given_cert") is None
        ),
        "inference_version": INFERENCE_VERSION,
        "pilot_grid": is_pilot_grid(n_tasks=n_tasks, n=operational_n),
    }
    for name in SLICE_METRICS:
        clustered = _clustered(rows, name, n_bootstrap=n_bootstrap)
        jack = clustered["jackknife"]
        payload[name] = clustered["mean"]
        payload[f"{name}_ci95"] = (
            None
            if clustered["mean"] is None
            else [clustered["lower"], clustered["upper"]]
        )
        payload[f"{name}_n_defined"] = clustered["n_defined"]
        payload[f"{name}_n_missing"] = clustered["n_missing"]
        payload[f"{name}_n_clusters"] = clustered["n_clusters"]
        payload[f"{name}_pct"] = (
            None if clustered["mean"] is None else round(100.0 * clustered["mean"], 2)
        )
        payload[f"{name}_jackknife_se"] = jack.get("se")
        payload[f"{name}_jackknife_ci95"] = (
            None
            if jack.get("lower") is None or jack.get("upper") is None
            else [jack["lower"], jack["upper"]]
        )
        payload[f"{name}_jackknife_skipped"] = jack.get("skipped")
    missing = [key for key in REQUIRED_SLICE_KEYS if key not in payload]
    if missing:
        raise ValueError(f"Slice missing required keys: {missing}")
    return payload


def build_report(
    rows: Sequence[Dict[str, Any]],
    *,
    n_bootstrap: int = 10000,
    source_dir: Optional[str] = None,
) -> Dict[str, Any]:
    if not rows:
        raise ValueError("No scored configs")
    groups: Dict[Tuple[str, float], List[Dict[str, Any]]] = {}
    for row in rows:
        key = (str(row["model"]), float(row["temperature"]))
        groups.setdefault(key, []).append(row)
    slices = [
        _slice_payload(
            groups[key],
            model=key[0],
            temperature=key[1],
            n_bootstrap=n_bootstrap,
        )
        for key in sorted(groups)
    ]
    inference = dict(INFERENCE)
    inference["n_bootstrap"] = n_bootstrap
    return {
        "schema": SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "relation_version": RELATION_VERSION,
        "relation_version_note": RELATION_VERSION_NOTE,
        "inference_version": INFERENCE_VERSION,
        "inference": inference,
        "metrics": METRIC_HELP,
        "aggregation": (
            "one slice per model × temperature; task-mean with cluster "
            f"bootstrap by task_id ({n_bootstrap}, seed {inference['seed']}); "
            "not binomial on C(N,2) pairs"
        ),
        "slices": slices,
        "pilot_grid": any(slice_row.get("pilot_grid") for slice_row in slices),
        "configs": list(rows),
        "source_dir": source_dir,
        "note": (
            "Benchmark tape only: canonical-form fingerprint. "
            "No Certified Consensus, no SKYT repair, no match-to-human. "
            "Do not mix slices into one headline. "
            "Do not treat u_statistic_pair_count as the n of a confidence interval."
        ),
    }
