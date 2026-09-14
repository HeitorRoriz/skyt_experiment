"""Table 1 from stored HumanEval+ summaries. No API spend. No SKYT."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.repeatability_protocol import cluster_bootstrap_mean


MODEL_LABEL = {
    "gpt-4o-mini": "gpt-4o-mini",
    "claude-sonnet-4-5-20250929": "Claude Sonnet 4.5",
}

# Same columns as the preregistered Table 1 sketch. Pairwise = certified
# pairwise (passing regenerations look the same). CV = end-to-end held-out
# match, matching Gate 0. Human match is among plus-certified only.
FIELDS = {
    "plus_pass": "certification_rate",
    "pairwise": "pairwise_exact_match_certified",
    "pairwise_end_to_end": "pairwise_exact_match_end_to_end",
    "modal": "certified_modal_mass",
    "cv": "cv_heldout_match_end_to_end",
    "human": "human_match_rate",
}


def _human_match_rate(analysis: Dict[str, Any]) -> Optional[float]:
    ref = analysis.get("human_reference") or {}
    n_certified = ref.get("n_certified")
    if not n_certified:
        return None
    return ref["n_structurally_equal_to_human"] / n_certified


def load_config_rows(out_dir: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in sorted(out_dir.glob("*_summary.json")):
        summary = json.loads(path.read_text(encoding="utf-8"))
        analysis = summary.get("analysis") or {}
        if summary.get("n") != 10:
            raise ValueError(f"{path.name}: expected n=10")
        rows.append(
            {
                "task_id": summary["task_id"],
                "model": summary["model"],
                "temperature": float(summary["temperature"]),
                "n": summary["n"],
                "n_plus_certified": analysis.get("n_plus_certified"),
                "n_base_passed": analysis.get("n_base_passed"),
                "cv_train_size": analysis.get("cv_train_size"),
                "certification_rate": analysis.get("certification_rate"),
                "pairwise_exact_match_certified": analysis.get(
                    "pairwise_exact_match_certified"
                ),
                "pairwise_exact_match_end_to_end": analysis.get(
                    "pairwise_exact_match_end_to_end"
                ),
                "certified_modal_mass": analysis.get("certified_modal_mass"),
                "cv_heldout_match_end_to_end": analysis.get(
                    "cv_heldout_match_end_to_end"
                ),
                "human_match_rate": _human_match_rate(analysis),
                "no_skyt_repair": bool(summary.get("no_skyt_repair")),
            }
        )
    return rows


def _clustered(rows: Sequence[Dict[str, Any]], field: str) -> Optional[Dict[str, Any]]:
    usable = [row for row in rows if row.get(field) is not None]
    if not usable:
        return None
    result = cluster_bootstrap_mean(
        [float(row[field]) for row in usable],
        [str(row["task_id"]) for row in usable],
        n_bootstrap=10000,
        seed=20260723,
    )
    result["n_defined"] = len(usable)
    result["n_missing"] = len(rows) - len(usable)
    return result


def _pct(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(100.0 * value, 1)


def _row_payload(label: Dict[str, Any], rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    payload = dict(label)
    payload["n_configs"] = len(rows)
    payload["n_tasks"] = len({row["task_id"] for row in rows})
    for name, field in FIELDS.items():
        clustered = _clustered(rows, field)
        payload[name] = None if clustered is None else round(clustered["mean"], 6)
        payload[f"{name}_pct"] = None if clustered is None else _pct(clustered["mean"])
        payload[f"{name}_ci95"] = (
            None
            if clustered is None
            else [
                round(clustered["lower"], 6),
                round(clustered["upper"], 6),
            ]
        )
        payload[f"{name}_ci95_pct"] = (
            None
            if clustered is None
            else [_pct(clustered["lower"]), _pct(clustered["upper"])]
        )
        payload[f"{name}_n_defined"] = None if clustered is None else clustered["n_defined"]
        payload[f"{name}_n_missing"] = None if clustered is None else clustered["n_missing"]
    return payload


def build_table1(out_dir: Path) -> Dict[str, Any]:
    rows = load_config_rows(out_dir)
    if len(rows) != 120:
        raise ValueError(f"Expected 120 summaries, found {len(rows)}")
    if not all(row["no_skyt_repair"] for row in rows):
        raise ValueError("Table 1 refuses summaries that applied SKYT repair")
    cv_sizes = {row["cv_train_size"] for row in rows}
    table_rows = []
    for model in ("gpt-4o-mini", "claude-sonnet-4-5-20250929"):
        for temp in (0.0, 0.7):
            subset = [
                row
                for row in rows
                if row["model"] == model and row["temperature"] == temp
            ]
            if len(subset) != 30:
                raise ValueError(f"{model} T={temp}: expected 30 tasks, got {len(subset)}")
            table_rows.append(
                _row_payload(
                    {
                        "scope": "Pilot 30",
                        "model": MODEL_LABEL[model],
                        "model_id": model,
                        "temperature": temp,
                    },
                    subset,
                )
            )
    overall = _row_payload(
        {
            "scope": "Pilot 30",
            "model": "both",
            "model_id": "both",
            "temperature": "both",
        },
        rows,
    )
    table_rows.append(overall)
    return {
        "schema": "skyt-humaneval-plus-table1-v1",
        "n_configs": 120,
        "n_tasks": 30,
        "n": 10,
        "no_skyt_repair": True,
        "no_style_contracts": True,
        "aggregation": "task-mean, cluster bootstrap by task_id (10k, seed 20260723)",
        "cv_train_size": sorted(cv_sizes),
        "columns": {
            "plus_pass": "certification_rate (HumanEval+ pass)",
            "pairwise": "pairwise_exact_match_certified",
            "pairwise_end_to_end": "pairwise_exact_match_end_to_end (MEASURE 1)",
            "modal": "certified_modal_mass (modal size / N)",
            "cv": "cv_heldout_match_end_to_end",
            "human": "share of plus-certified gens structurally equal to the shipped human solution",
        },
        "note": (
            "Human solution is an external baseline, not the canon. "
            "Do not mix with SBES/MSR. No SKYT repair on these generations."
        ),
        "rows": table_rows,
        "headline": overall,
    }


def main() -> None:
    out_dir = Path("outputs") / "humaneval_plus" / "pilot"
    table = build_table1(out_dir)
    path = out_dir / "table1.json"
    path.write_text(json.dumps(table, indent=2), encoding="utf-8")
    print(json.dumps(table, indent=2))
    print(f"wrote {path}", flush=True)


if __name__ == "__main__":
    main()
