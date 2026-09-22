"""Oracle-fair Base-cache baselines on the oracle-split tree. No LLM.

Every policy sees only HumanEval Base tests at selection time. Plus / Extra
are evaluation-only, matching RQ2.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from benchmark.relation import fingerprint
from benchmarks.humaneval_plus.provenance import atomic_write_json
from benchmarks.humaneval_plus.run import _load_existing, _safe_name
from skyt.heldout_posthoc import CELLS, N, _boot, _cell_rows
from skyt.humaneval_heldout import OVERLAY_SOURCE
from skyt.humaneval_oracle_split import ORACLE_SPLIT_OUT
from skyt.oracle_split_posthoc import load_oracle_split_configs


def _mean(items: Sequence[Dict[str, Any]], key: str) -> Optional[float]:
    values = [item[key] for item in items if item.get(key) is not None]
    if not values:
        return None
    return sum(float(v) for v in values) / len(values)


def replay_cached_record(record: Dict[str, Any]) -> Dict[str, Any]:
    code = record.get("stitched_code") or ""
    parseable = fingerprint(code, flexible_naming=True) is not None
    oracle = record.get("oracle") or {}
    base_ok = bool(oracle.get("base_passed")) and parseable
    plus_ok = bool(oracle.get("plus_passed")) and parseable
    extra = (1.0 if plus_ok else 0.0) if base_ok else None
    return {
        "base_pass": 1.0 if base_ok else 0.0,
        "plus_pass": 1.0 if plus_ok else 0.0,
        "extra_survival": extra,
        "plus_same_at_2": 1.0 if plus_ok else 0.0,
        "plus_same_at_2_given_cert": 1.0 if plus_ok else None,
        "base_same_at_2": 1.0 if base_ok else 0.0,
        "hit": True,
        "base_pass_extra_fail": 1.0 if (base_ok and not plus_ok) else 0.0,
    }


def raw_split_metrics(split: Dict[str, Any]) -> Dict[str, Any]:
    n_base = split.get("pre_n_base_certified")
    n_plus = split.get("pre_n_plus_certified")
    extra = (float(n_plus) / float(n_base)) if n_base else None
    return {
        "base_pass": split.get("pre_base_pass"),
        "plus_pass": split.get("pre_plus_pass"),
        "extra_survival": extra,
        "plus_same_at_2": split.get("pre_plus_same_at_2"),
        "plus_same_at_2_given_cert": split.get("pre_plus_same_at_2_given_cert"),
        "base_same_at_2": split.get("pre_same_at_2"),
        "hit": False,
        "base_pass_extra_fail": None,
    }


def skyt_split_metrics(split: Dict[str, Any]) -> Dict[str, Any]:
    n_base = split.get("post_n_base_certified")
    n_plus = split.get("post_n_plus_certified")
    extra = (float(n_plus) / float(n_base)) if n_base else None
    return {
        "base_pass": split.get("post_base_pass"),
        "plus_pass": split.get("post_plus_pass"),
        "extra_survival": extra,
        "plus_same_at_2": split.get("post_plus_same_at_2"),
        "plus_same_at_2_given_cert": split.get("post_plus_same_at_2_given_cert"),
        "base_same_at_2": split.get("post_same_at_2"),
        "hit": bool(split.get("canon_created")),
        "base_pass_extra_fail": None,
    }


def _base_ok(record: Dict[str, Any]) -> bool:
    fp = fingerprint(record.get("stitched_code") or "", flexible_naming=True)
    return bool((record.get("oracle") or {}).get("base_passed")) and fp is not None


def cache_for_config(
    records: Sequence[Dict[str, Any]],
    splits: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    first_rows: List[Dict[str, Any]] = []
    cons_rows: List[Dict[str, Any]] = []
    raw_rows: List[Dict[str, Any]] = []
    skyt_rows: List[Dict[str, Any]] = []
    for split in splits:
        train = [int(i) for i in split["train_indices"]]
        raw = raw_split_metrics(split)
        raw_rows.append(raw)
        skyt_rows.append(skyt_split_metrics(split))
        first_idx = next((i for i in sorted(train) if _base_ok(records[i])), None)
        if first_idx is not None:
            first_rows.append(replay_cached_record(records[first_idx]))
        else:
            first_rows.append(raw)
        cons = split.get("consensus_index")
        if split.get("canon_created") and cons is not None:
            cons_rows.append(replay_cached_record(records[int(cons)]))
        else:
            cons_rows.append(raw)

    def pack(prefix: str, items: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            f"{prefix}_base_pass": _mean(items, "base_pass"),
            f"{prefix}_plus_pass": _mean(items, "plus_pass"),
            f"{prefix}_extra_survival": _mean(items, "extra_survival"),
            f"{prefix}_plus_same_at_2": _mean(items, "plus_same_at_2"),
            f"{prefix}_plus_same_at_2_given_cert": _mean(
                items, "plus_same_at_2_given_cert"
            ),
            f"{prefix}_base_same_at_2": _mean(items, "base_same_at_2"),
            f"{prefix}_coverage": _mean(items, "hit"),
            f"{prefix}_base_pass_extra_fail": _mean(items, "base_pass_extra_fail"),
        }

    out = {}
    out.update(pack("raw", raw_rows))
    out.update(pack("first_cache", first_rows))
    out.update(pack("consensus_cache", cons_rows))
    out.update(pack("skyt", skyt_rows))
    if out.get("skyt_plus_same_at_2") is not None and out.get("first_cache_plus_same_at_2") is not None:
        out["skyt_minus_first_cache_plus_same_at_2"] = float(
            out["skyt_plus_same_at_2"]
        ) - float(out["first_cache_plus_same_at_2"])
    else:
        out["skyt_minus_first_cache_plus_same_at_2"] = None
    if (
        out.get("skyt_plus_same_at_2") is not None
        and out.get("consensus_cache_plus_same_at_2") is not None
    ):
        out["skyt_minus_consensus_cache_plus_same_at_2"] = float(
            out["skyt_plus_same_at_2"]
        ) - float(out["consensus_cache_plus_same_at_2"])
    else:
        out["skyt_minus_consensus_cache_plus_same_at_2"] = None
    return out


def attach_base_cache(
    rows: List[Dict[str, Any]],
    source_dir: Path,
) -> None:
    for index, row in enumerate(rows, start=1):
        stem = _safe_name(row["task_id"], row["model"], row["temperature"])
        records = sorted(
            _load_existing(source_dir / f"{stem}.jsonl"),
            key=lambda item: int(item["run_index"]),
        )[:N]
        if len(records) < N:
            raise ValueError(f"{stem}: overlay incomplete")
        row.update(cache_for_config(records, row.get("splits") or []))
        if index % 50 == 0:
            print(f"  base-cache {index}/{len(rows)}", flush=True)


def _policy_slice(subset: Sequence[Dict[str, Any]], prefix: str) -> Dict[str, Any]:
    return {
        "base_pass": _boot(subset, f"{prefix}_base_pass"),
        "plus_pass": _boot(subset, f"{prefix}_plus_pass"),
        "extra_survival": _boot(subset, f"{prefix}_extra_survival"),
        "plus_same_at_2": _boot(subset, f"{prefix}_plus_same_at_2"),
        "coverage": _boot(subset, f"{prefix}_coverage"),
        "base_pass_extra_fail": _boot(subset, f"{prefix}_base_pass_extra_fail"),
        "regenerates": prefix in {"raw", "skyt"},
    }


def run(
    *,
    source_dir: Path = OVERLAY_SOURCE,
    out_dir: Path = ORACLE_SPLIT_OUT,
) -> Dict[str, Any]:
    print("loading oracle-split summaries", flush=True)
    rows = load_oracle_split_configs(out_dir)
    if len(rows) != 656:
        raise ValueError(f"expected 656 oracle-split summaries, got {len(rows)}")
    print("computing Base-only cache baselines (no Docker)", flush=True)
    attach_base_cache(rows, source_dir)
    slices = []
    for label, model, temp in CELLS:
        subset = _cell_rows(rows, model, temp)
        slices.append(
            {
                "label": label,
                "n_configs": len(subset),
                "raw": _policy_slice(subset, "raw"),
                "first_base_cache": _policy_slice(subset, "first_cache"),
                "consensus_base_cache": _policy_slice(subset, "consensus_cache"),
                "skyt": _policy_slice(subset, "skyt"),
                "skyt_minus_first_cache_plus_same_at_2": _boot(
                    subset, "skyt_minus_first_cache_plus_same_at_2"
                ),
                "skyt_minus_consensus_cache_plus_same_at_2": _boot(
                    subset, "skyt_minus_consensus_cache_plus_same_at_2"
                ),
            }
        )
    report = {
        "schema": "skyt-oracle-fair-base-cache-v1",
        "n_configs": len(rows),
        "operational_oracle": "humaneval_base",
        "evaluation_oracle": "evalplus_plus",
        "note": (
            "Cache replays one Base-certified train program on the test slice. "
            "Plus / Extra are evaluation-only. Coverage is the split-mean hit rate."
        ),
        "slices": slices,
    }
    path = out_dir / "oracle_fair_cache.json"
    atomic_write_json(path, report)
    print(f"wrote {path}", flush=True)
    return report


def _print_policy(name: str, cell: Dict[str, Any]) -> None:
    print(
        f"  {name:22} plus-same@2 {cell['plus_same_at_2']['pct']} "
        f"plus-pass {cell['plus_pass']['pct']} "
        f"base-pass {cell['base_pass']['pct']} "
        f"extra-surv {cell['extra_survival']['pct']} "
        f"cov {cell['coverage']['pct']} "
        f"regen={cell['regenerates']}"
    )


if __name__ == "__main__":
    payload = run()
    all_row = payload["slices"][0]
    print("\n== oracle-fair Base-cache (all)")
    for name in ("raw", "first_base_cache", "consensus_base_cache", "skyt"):
        _print_policy(name, all_row[name])
    print(
        "SKYT minus first-cache plus same@2 "
        f"{all_row['skyt_minus_first_cache_plus_same_at_2']['pct']} "
        f"CI {all_row['skyt_minus_first_cache_plus_same_at_2']['ci95_pct']}"
    )
    print(
        "first-cache Base-pass Extra-fail rate "
        f"{all_row['first_base_cache']['base_pass_extra_fail']['pct']}"
    )
