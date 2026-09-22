"""Post-hoc on the base-operational / Plus-evaluation held-out rewrite. No LLM."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from benchmarks.humaneval_plus.provenance import atomic_write_json
from skyt.heldout_posthoc import CELLS, _boot, _cell_rows, _slice_report, temperature_interaction
from skyt.humaneval_oracle_split import ORACLE_SPLIT_OUT, SCHEMA


def _mean(values: Sequence[Optional[float]]) -> Optional[float]:
    usable = [float(v) for v in values if v is not None]
    if not usable:
        return None
    return sum(usable) / len(usable)


def extra_survival_rate(splits: Sequence[Dict[str, Any]], prefix: str) -> Optional[float]:
    """P(Plus pass | Base pass) on a test slice, then mean over splits.

    EvalPlus plus_passed requires base_passed, so this is Extra-survival
    among Base-certified generations. Undefined when a split has no Base passer.
    """
    rates: List[float] = []
    for split in splits:
        n_base = split.get(f"{prefix}_n_base_certified")
        n_plus = split.get(f"{prefix}_n_plus_certified")
        if not n_base:
            continue
        rates.append(float(n_plus or 0) / float(n_base))
    if not rates:
        return None
    return sum(rates) / len(rates)


def load_oracle_split_configs(out_dir: Path) -> List[Dict[str, Any]]:
    rows = []
    for path in sorted(out_dir.glob("*_oracle_split.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema") != SCHEMA:
            continue
        splits = payload.get("splits") or []
        row: Dict[str, Any] = {
            "task_id": payload["task_id"],
            "model": payload["model"],
            "temperature": float(payload["temperature"]),
            "n_splits_with_canon": payload.get("n_splits_with_canon"),
            "n_transformed_mean": payload.get("n_transformed_mean"),
            "n_rolled_back_mean": payload.get("n_rolled_back_mean"),
            "pre_same_at_2": payload.get("pre_same_at_2"),
            "post_same_at_2": payload.get("post_same_at_2"),
            "pre_same_at_2_given_cert": payload.get("pre_same_at_2_given_cert"),
            "post_same_at_2_given_cert": payload.get("post_same_at_2_given_cert"),
            "pre_base_pass": payload.get("pre_base_pass"),
            "post_base_pass": payload.get("post_base_pass"),
            "pre_plus_pass": payload.get("pre_plus_pass"),
            "post_plus_pass": payload.get("post_plus_pass"),
            "pre_plus_same_at_2": _mean(
                [s.get("pre_plus_same_at_2") for s in splits]
            ),
            "post_plus_same_at_2": _mean(
                [s.get("post_plus_same_at_2") for s in splits]
            ),
            "pre_plus_same_at_2_given_cert": _mean(
                [s.get("pre_plus_same_at_2_given_cert") for s in splits]
            ),
            "post_plus_same_at_2_given_cert": _mean(
                [s.get("post_plus_same_at_2_given_cert") for s in splits]
            ),
            "pre_extra_survival": extra_survival_rate(splits, "pre"),
            "post_extra_survival": extra_survival_rate(splits, "post"),
            "splits": splits,
        }
        for pre_key, post_key, delta_key in (
            ("pre_same_at_2", "post_same_at_2", "delta_same_at_2"),
            ("pre_plus_pass", "post_plus_pass", "delta_plus_pass"),
            ("pre_base_pass", "post_base_pass", "delta_base_pass"),
            ("pre_plus_same_at_2", "post_plus_same_at_2", "delta_plus_same_at_2"),
            (
                "pre_same_at_2_given_cert",
                "post_same_at_2_given_cert",
                "delta_same_at_2_given_cert",
            ),
            (
                "pre_plus_same_at_2_given_cert",
                "post_plus_same_at_2_given_cert",
                "delta_plus_same_at_2_given_cert",
            ),
            ("pre_extra_survival", "post_extra_survival", "delta_extra_survival"),
        ):
            if row.get(pre_key) is not None and row.get(post_key) is not None:
                row[delta_key] = float(row[post_key]) - float(row[pre_key])
            else:
                row[delta_key] = None
        row["common_support"] = (
            row.get("pre_same_at_2_given_cert") is not None
            and row.get("post_same_at_2_given_cert") is not None
        )
        row["plus_common_support"] = (
            row.get("pre_plus_same_at_2_given_cert") is not None
            and row.get("post_plus_same_at_2_given_cert") is not None
        )
        if row.get("pre_same_at_2_given_cert") is not None:
            row["pre_disagreement"] = 1.0 - float(row["pre_same_at_2_given_cert"])
        else:
            row["pre_disagreement"] = None
        if row.get("post_same_at_2_given_cert") is not None:
            row["post_disagreement"] = 1.0 - float(row["post_same_at_2_given_cert"])
        else:
            row["post_disagreement"] = None
        if row["pre_disagreement"] is not None and row["post_disagreement"] is not None:
            row["delta_disagreement"] = float(row["post_disagreement"]) - float(
                row["pre_disagreement"]
            )
        else:
            row["delta_disagreement"] = None
        if row.get("pre_plus_same_at_2_given_cert") is not None:
            row["pre_plus_disagreement"] = 1.0 - float(
                row["pre_plus_same_at_2_given_cert"]
            )
        else:
            row["pre_plus_disagreement"] = None
        if row.get("post_plus_same_at_2_given_cert") is not None:
            row["post_plus_disagreement"] = 1.0 - float(
                row["post_plus_same_at_2_given_cert"]
            )
        else:
            row["post_plus_disagreement"] = None
        if (
            row["pre_plus_disagreement"] is not None
            and row["post_plus_disagreement"] is not None
        ):
            row["delta_plus_disagreement"] = float(row["post_plus_disagreement"]) - float(
                row["pre_plus_disagreement"]
            )
        else:
            row["delta_plus_disagreement"] = None
        rows.append(row)
    return rows


def _oracle_slice(rows: Sequence[Dict[str, Any]], label: str) -> Dict[str, Any]:
    payload = _slice_report(rows, label)
    plus_common = [row for row in rows if row.get("plus_common_support")]
    payload["plus_same_at_2_pre"] = _boot(rows, "pre_plus_same_at_2")
    payload["plus_same_at_2_post"] = _boot(rows, "post_plus_same_at_2")
    payload["delta_plus_same_at_2"] = _boot(rows, "delta_plus_same_at_2")
    payload["base_pass_pre"] = _boot(rows, "pre_base_pass")
    payload["base_pass_post"] = _boot(rows, "post_base_pass")
    payload["delta_base_pass"] = _boot(rows, "delta_base_pass")
    payload["n_plus_common_support"] = len(plus_common)
    payload["plus_same_at_2_given_cert_pre_common"] = _boot(
        plus_common, "pre_plus_same_at_2_given_cert"
    )
    payload["plus_same_at_2_given_cert_post_common"] = _boot(
        plus_common, "post_plus_same_at_2_given_cert"
    )
    payload["delta_plus_same_at_2_given_cert_common"] = _boot(
        plus_common, "delta_plus_same_at_2_given_cert"
    )
    payload["plus_disagreement_pre_common"] = _boot(plus_common, "pre_plus_disagreement")
    payload["plus_disagreement_post_common"] = _boot(
        plus_common, "post_plus_disagreement"
    )
    payload["delta_plus_disagreement_common"] = _boot(
        plus_common, "delta_plus_disagreement"
    )
    pre_d = payload["plus_disagreement_pre_common"]["mean"]
    post_d = payload["plus_disagreement_post_common"]["mean"]
    if pre_d and pre_d > 0 and post_d is not None:
        payload["plus_disagreement_relative_reduction_common"] = (pre_d - post_d) / pre_d
        payload["plus_disagreement_relative_reduction_common_pct"] = round(
            100.0 * (pre_d - post_d) / pre_d, 1
        )
    else:
        payload["plus_disagreement_relative_reduction_common"] = None
        payload["plus_disagreement_relative_reduction_common_pct"] = None
    payload["extra_survival_pre"] = _boot(rows, "pre_extra_survival")
    payload["extra_survival_post"] = _boot(rows, "post_extra_survival")
    payload["delta_extra_survival"] = _boot(rows, "delta_extra_survival")
    payload["n_negative_plus_pass"] = sum(
        1
        for row in rows
        if row.get("delta_plus_pass") is not None and row["delta_plus_pass"] < -1e-12
    )
    payload["n_negative_same_at_2"] = sum(
        1
        for row in rows
        if row.get("delta_same_at_2") is not None and row["delta_same_at_2"] < 0
    )
    return payload


def run(*, out_dir: Path = ORACLE_SPLIT_OUT) -> Dict[str, Any]:
    rows = load_oracle_split_configs(out_dir)
    if len(rows) != 656:
        raise ValueError(f"expected 656 oracle-split summaries, got {len(rows)}")
    slices = [
        _oracle_slice(_cell_rows(rows, model, temp), label)
        for label, model, temp in CELLS
    ]
    report = {
        "schema": "skyt-oracle-split-posthoc-v2",
        "n_configs": len(rows),
        "operational_oracle": "humaneval_base",
        "evaluation_oracle": "evalplus_plus",
        "slices": slices,
        "temperature_interaction_plus_same_at_2": temperature_interaction(
            rows, field="delta_plus_same_at_2"
        ),
        "temperature_interaction_operational_same_at_2": temperature_interaction(
            rows, field="delta_same_at_2"
        ),
    }
    slim_rows = [{k: v for k, v in row.items() if k != "splits"} for row in rows]
    atomic_write_json(out_dir / "oracle_split_config_rows.json", slim_rows)
    path = out_dir / "oracle_split_posthoc.json"
    atomic_write_json(path, report)
    print(f"wrote {path}", flush=True)
    return report


def _print_slice(row: Dict[str, Any]) -> None:
    print(f"\n== {row['label']} n={row['n_configs']}")
    d = row["delta_same_at_2"]
    print(
        f"  operational same@2 {row['same_at_2_pre']['pct']} -> "
        f"{row['same_at_2_post']['pct']} delta {d['pct']} CI {d['ci95_pct']}"
    )
    p = row["delta_plus_pass"]
    print(
        f"  plus-pass {row['plus_pass_pre']['pct']} -> {row['plus_pass_post']['pct']} "
        f"delta {p['pct']} CI {p['ci95_pct']}"
    )
    b = row["delta_base_pass"]
    print(
        f"  base-pass {row['base_pass_pre']['pct']} -> {row['base_pass_post']['pct']} "
        f"delta {b['pct']} CI {b['ci95_pct']}"
    )
    s = row["delta_plus_same_at_2"]
    print(
        f"  plus same@2 {row['plus_same_at_2_pre']['pct']} -> "
        f"{row['plus_same_at_2_post']['pct']} delta {s['pct']} CI {s['ci95_pct']}"
    )
    print(
        f"  plus common-support n={row['n_plus_common_support']} "
        f"disagreement {row['plus_disagreement_pre_common']['pct']}% -> "
        f"{row['plus_disagreement_post_common']['pct']}% "
        f"(rel {row.get('plus_disagreement_relative_reduction_common_pct')}%)"
    )
    e = row["delta_extra_survival"]
    print(
        f"  extra-survival {row['extra_survival_pre']['pct']} -> "
        f"{row['extra_survival_post']['pct']} delta {e['pct']} CI {e['ci95_pct']}"
    )
    print(
        f"  negative plus-pass {row['n_negative_plus_pass']} "
        f"negative op-same@2 {row['n_negative_same_at_2']}"
    )


if __name__ == "__main__":
    payload = run()
    for slice_row in payload["slices"]:
        _print_slice(slice_row)
    inter = payload["temperature_interaction_plus_same_at_2"]["pooled_models"]
    print(
        "\nT=0.7 minus T=0.0 plus same@2 lift: "
        f"{inter['pct']} pp CI {inter['ci95_pct']}"
    )
    for name, cell in payload["temperature_interaction_plus_same_at_2"]["per_model"].items():
        print(f"  {name}: {cell['pct']} pp CI {cell['ci95_pct']}")
