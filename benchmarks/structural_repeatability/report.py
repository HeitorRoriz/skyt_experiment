"""Map protocol analysis rows onto the overlay schema."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence

from src.repeatability_protocol import cluster_bootstrap_mean

from .schema import (
    METRIC_FIELDS,
    METRIC_HELP,
    RELATION_VERSION,
    RELATION_VERSION_NOTE,
    SCHEMA,
)


BOOTSTRAP_SEED = 20260723


def _clustered(
    rows: Sequence[Dict[str, Any]],
    field: str,
    *,
    n_bootstrap: int,
) -> Optional[Dict[str, Any]]:
    usable = [row for row in rows if row.get(field) is not None]
    if not usable:
        return {
            "mean": None,
            "lower": None,
            "upper": None,
            "n_defined": 0,
            "n_missing": len(rows),
        }
    result = cluster_bootstrap_mean(
        [float(row[field]) for row in usable],
        [str(row["task_id"]) for row in usable],
        n_bootstrap=n_bootstrap,
        seed=BOOTSTRAP_SEED,
    )
    result["n_defined"] = len(usable)
    result["n_missing"] = len(rows) - len(usable)
    return result


def overlay_row_from_analysis(
    *,
    task_id: str,
    model: str,
    temperature: float,
    n: int,
    analysis: Dict[str, Any],
) -> Dict[str, Any]:
    certified = analysis.get("n_certified")
    if certified is None:
        certified = analysis.get("n_plus_certified")
    dropped = analysis.get("pairwise_exact_match_certified") is None
    return {
        "task_id": task_id,
        "model": model,
        "temperature": float(temperature),
        "n": n,
        "n_certified": certified,
        "same_at_2": analysis.get("pairwise_exact_match_end_to_end"),
        "same_at_2_given_cert": analysis.get("pairwise_exact_match_certified"),
        "plus_pass": analysis.get("certification_rate"),
        "same_at_2_given_cert_undefined": dropped,
        "pairwise_exact_match_end_to_end": analysis.get(
            "pairwise_exact_match_end_to_end"
        ),
        "pairwise_exact_match_certified": analysis.get(
            "pairwise_exact_match_certified"
        ),
        "certification_rate": analysis.get("certification_rate"),
        "no_skyt_repair": True,
        "no_style_contracts": True,
        "relation_version": RELATION_VERSION,
    }


def build_overlay_report(
    rows: Sequence[Dict[str, Any]],
    *,
    n_bootstrap: int = 10000,
    source_dir: Optional[str] = None,
) -> Dict[str, Any]:
    if not rows:
        raise ValueError("No scored configs")
    ns = {int(row["n"]) for row in rows}
    headline: Dict[str, Any] = {
        "n_configs": len(rows),
        "n_tasks": len({row["task_id"] for row in rows}),
        "n": sorted(ns) if len(ns) > 1 else next(iter(ns)),
        "n_dropped_same_at_2_given_cert": sum(
            1 for row in rows if row.get("same_at_2_given_cert") is None
        ),
    }
    for public_name, protocol_name in METRIC_FIELDS.items():
        clustered = _clustered(rows, protocol_name, n_bootstrap=n_bootstrap)
        assert clustered is not None
        headline[public_name] = clustered["mean"]
        headline[f"{public_name}_ci95"] = (
            None
            if clustered["mean"] is None
            else [clustered["lower"], clustered["upper"]]
        )
        headline[f"{public_name}_n_defined"] = clustered["n_defined"]
        headline[f"{public_name}_n_missing"] = clustered["n_missing"]
        headline[f"{public_name}_pct"] = (
            None if clustered["mean"] is None else round(100.0 * clustered["mean"], 2)
        )

    return {
        "schema": SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "relation_version": RELATION_VERSION,
        "relation_version_note": RELATION_VERSION_NOTE,
        "no_skyt_repair": True,
        "no_style_contracts": True,
        "source_dir": source_dir,
        "metrics": METRIC_HELP,
        "aggregation": (
            "task-mean, cluster bootstrap by task_id "
            f"({n_bootstrap}, seed {BOOTSTRAP_SEED})"
        ),
        "headline": headline,
        "configs": list(rows),
        "note": (
            "Measuring tape only. No Certified Consensus pick and no SKYT "
            "repair. Do not mix with SBES/MSR headlines. Public names "
            "same_at_2 / same_at_2_given_cert are SPEC OPEN 1 recommendations."
        ),
    }
