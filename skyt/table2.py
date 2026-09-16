"""Table 2: SKYT Certified Consensus repair on the same HumanEval+ generations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from benchmarks.humaneval_plus.table1 import (
    FIELDS,
    MODEL_LABEL,
    _human_match_rate,
    _row_payload,
    build_table1,
)


def load_repair_rows(out_dir: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in sorted(out_dir.glob("*_summary.json")):
        summary = json.loads(path.read_text(encoding="utf-8"))
        analysis = summary.get("analysis") or {}
        if summary.get("n") != 10:
            raise ValueError(f"{path.name}: expected n=10")
        if summary.get("no_skyt_repair", True):
            raise ValueError(f"{path.name}: Table 2 needs repaired summaries")
        rows.append(
            {
                "task_id": summary["task_id"],
                "model": summary["model"],
                "temperature": float(summary["temperature"]),
                "n": summary["n"],
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
                "cv_train_size": analysis.get("cv_train_size"),
                "n_regressions": int(summary.get("n_regressions") or 0),
                "n_rescues": int(summary.get("n_rescues") or 0),
                "n_transformed": int(summary.get("n_transformed") or 0),
                "n_rolled_back": int(summary.get("n_rolled_back") or 0),
                "canon_created": bool(summary.get("canon_created")),
            }
        )
    return rows


def _counts(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    return {
        "n_regressions": sum(row["n_regressions"] for row in rows),
        "n_rescues": sum(row["n_rescues"] for row in rows),
        "n_transformed": sum(row["n_transformed"] for row in rows),
        "n_rolled_back": sum(row["n_rolled_back"] for row in rows),
        "n_no_canon": sum(1 for row in rows if not row["canon_created"]),
    }


def build_table2(*, pre_dir: Path, post_dir: Path) -> Dict[str, Any]:
    pre_table = build_table1(pre_dir)
    post_rows = load_repair_rows(post_dir)
    if len(post_rows) != 120:
        raise ValueError(f"Expected 120 repaired summaries, found {len(post_rows)}")
    table_rows = []
    for model in ("gpt-4o-mini", "claude-sonnet-4-5-20250929"):
        for temp in (0.0, 0.7):
            subset = [
                row
                for row in post_rows
                if row["model"] == model and row["temperature"] == temp
            ]
            if len(subset) != 30:
                raise ValueError(f"{model} T={temp}: expected 30 tasks, got {len(subset)}")
            payload = _row_payload(
                {
                    "scope": "Pilot 30 SKYT",
                    "model": MODEL_LABEL[model],
                    "model_id": model,
                    "temperature": temp,
                    "pass": "post",
                },
                subset,
            )
            payload.update(_counts(subset))
            table_rows.append(payload)
    overall = _row_payload(
        {
            "scope": "Pilot 30 SKYT",
            "model": "both",
            "model_id": "both",
            "temperature": "both",
            "pass": "post",
        },
        post_rows,
    )
    overall.update(_counts(post_rows))
    table_rows.append(overall)

    pre_by_key = {
        (row["model_id"], row["temperature"]): row for row in pre_table["rows"]
    }
    for row in table_rows:
        pre = pre_by_key[(row["model_id"], row["temperature"])]
        row["delta_pct"] = {
            name: None
            if row.get(f"{name}_pct") is None or pre.get(f"{name}_pct") is None
            else round(row[f"{name}_pct"] - pre[f"{name}_pct"], 1)
            for name in FIELDS
        }

    return {
        "schema": "skyt-humaneval-plus-table2-v1",
        "n_configs": 120,
        "n_tasks": 30,
        "n": 10,
        "repair_policy": "certified_consensus",
        "no_style_contracts": True,
        "aggregation": "task-mean, cluster bootstrap by task_id (10k, seed 20260723)",
        "note": (
            "Same 1,200 generations as Table 1. SKYT treatment = Certified "
            "Consensus pick + repair toward that form + rollback if plus tests "
            "fail. No MISRA/naming style contracts. Human is still a baseline. "
            "Do not mix with SBES/MSR."
        ),
        "pre_headline": pre_table["headline"],
        "rows": table_rows,
        "headline": overall,
    }


def main() -> None:
    pre_dir = Path("outputs") / "humaneval_plus" / "pilot"
    post_dir = Path("outputs") / "humaneval_plus" / "pilot_skyt"
    table = build_table2(pre_dir=pre_dir, post_dir=post_dir)
    path = post_dir / "table2.json"
    path.write_text(json.dumps(table, indent=2), encoding="utf-8")
    print(json.dumps(table, indent=2))
    print(f"wrote {path}", flush=True)


if __name__ == "__main__":
    main()
