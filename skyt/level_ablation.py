"""Zero-API SKYT level ablation on the oracle-split design. No LLM.

The live transformer (agents off) has no separate Level-1 style pass:
distance < 0.1 returns unchanged, then Level 2, then Level 3. So L1-only
is identical to Raw.

Level 2 needs oracle tests on mutated programs (Docker). This module does
not overwrite the headline oracle-split tree. Level-3-only is a no-Docker
inherit replay: substitute the entry-point AST with the train Base-certified
consensus and inherit that program's stored Base/Plus oracle.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from benchmark.protect import assert_writable
from benchmark.schema import FROZEN_PROTOCOL_N
from benchmarks.humaneval_plus.provenance import atomic_write_json, attach_oracle
from benchmarks.humaneval_plus.run import _load_existing, _safe_name
from src.transformations.convert_to_simple_algorithm import convert_to_simple_algorithm

from skyt.humaneval_heldout import OVERLAY_SOURCE, select_train_canon
from skyt.humaneval_oracle_split import (
    ORACLE_SPLIT_OUT,
    SCHEMA,
    _base_operational_payload,
    _prefix,
    dual_repeatability,
)
from skyt.humaneval_repair import _load_plus_problem, _oracle_payload, humaneval_repair_contract
from skyt.oracle_split_posthoc import run as run_posthoc


L3_OUT = (
    Path("outputs") / "benchmark" / "humaneval_plus_164_n20_skyt_heldout_oracle_split_l3only"
)
N = FROZEN_PROTOCOL_N


def ablation_dir(max_level: int) -> Path:
    if int(max_level) == 3:
        return L3_OUT
    return Path("outputs") / "benchmark" / (
        f"humaneval_plus_164_n20_skyt_heldout_oracle_split_l{int(max_level)}"
    )


def _mean_field(rows: List[Dict[str, Any]], key: str) -> Optional[float]:
    values = [row[key] for row in rows if row.get(key) is not None]
    if not values:
        return None
    return sum(float(v) for v in values) / len(values)


def l3_only_config(
    *,
    source_dir: Path,
    headline_dir: Path,
    out_dir: Path,
    task_id: str,
    model: str,
    temperature: float,
    force: bool = False,
) -> Dict[str, Any]:
    source_dir = source_dir.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    if out_dir == ORACLE_SPLIT_OUT.expanduser().resolve():
        raise ValueError("Refusing to overwrite the oracle-split headline tree")
    assert_writable(out_dir)
    stem = _safe_name(task_id, model, temperature)
    summary_path = out_dir / f"{stem}_oracle_split.json"
    headline_path = headline_dir / f"{stem}_oracle_split.json"
    if not force and summary_path.exists():
        prior = json.loads(summary_path.read_text(encoding="utf-8"))
        if prior.get("schema") == SCHEMA and prior.get("ablation") == "l3_only":
            return prior
    headline = json.loads(headline_path.read_text(encoding="utf-8"))
    records = sorted(
        _load_existing(source_dir / f"{stem}.jsonl"),
        key=lambda item: int(item["run_index"]),
    )[:N]
    if len(records) < N:
        raise ValueError(f"{stem}: overlay incomplete")
    problem = _load_plus_problem(source_dir, task_id)
    contract_dict = humaneval_repair_contract(
        task_id=task_id,
        model=model,
        temperature=temperature,
        prompt=problem["prompt"],
        entry_point=problem["entry_point"],
    )

    split_rows: List[Dict[str, Any]] = []
    for split in headline.get("splits") or []:
        train = [int(i) for i in split["train_indices"]]
        test = [int(i) for i in split["test_indices"]]
        test_records = [records[i] for i in test]
        selected = select_train_canon(
            records, contract_dict, train, payload_fn=_base_operational_payload
        )
        n_transformed = 0
        if selected is None:
            repaired = [deepcopy(item) for item in test_records]
        else:
            canon_code = selected["code"]
            canon_oracle = _oracle_payload(records[int(selected["index"])])
            repaired = []
            for record in test_records:
                updated = deepcopy(record)
                result = convert_to_simple_algorithm(
                    record.get("stitched_code") or "",
                    canon_code,
                    contract_dict,
                )
                if result.get("success") and result.get("transformations"):
                    updated["stitched_code"] = result["transformed_code"]
                    updated = attach_oracle(updated, canon_oracle)
                    updated["repair_applied"] = True
                    updated["transformation_level"] = 3
                    n_transformed += 1
                else:
                    updated["repair_applied"] = False
                repaired.append(updated)
        post = dual_repeatability(repaired)
        split_rows.append(
            {
                "split_id": split["split_id"],
                "train_indices": train,
                "test_indices": test,
                "canon_created": selected is not None,
                "consensus_index": None if selected is None else selected["index"],
                "n_transformed": n_transformed,
                "n_rolled_back": 0,
                **{k: split[k] for k in split if str(k).startswith("pre_")},
                **_prefix("post", post),
            }
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema": SCHEMA,
        "ablation": "l3_only",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "model": model,
        "temperature": temperature,
        "n": N,
        "n_splits": len(split_rows),
        "operational_oracle": "humaneval_base",
        "evaluation_oracle": "evalplus_plus",
        "max_transformation_level": 3,
        "min_transformation_level": 3,
        "n_splits_with_canon": sum(1 for row in split_rows if row["canon_created"]),
        "n_transformed_mean": _mean_field(split_rows, "n_transformed"),
        "n_rolled_back_mean": 0.0,
        "pre_same_at_2": _mean_field(split_rows, "pre_same_at_2"),
        "post_same_at_2": _mean_field(split_rows, "post_same_at_2"),
        "pre_same_at_2_given_cert": _mean_field(split_rows, "pre_same_at_2_given_cert"),
        "post_same_at_2_given_cert": _mean_field(split_rows, "post_same_at_2_given_cert"),
        "pre_base_pass": _mean_field(split_rows, "pre_base_pass"),
        "post_base_pass": _mean_field(split_rows, "post_base_pass"),
        "pre_plus_pass": _mean_field(split_rows, "pre_plus_pass"),
        "post_plus_pass": _mean_field(split_rows, "post_plus_pass"),
        "splits": split_rows,
    }
    atomic_write_json(summary_path, summary)
    return summary


def run_l3_only(
    *,
    source_dir: Path = OVERLAY_SOURCE,
    headline_dir: Path = ORACLE_SPLIT_OUT,
    out_dir: Path = L3_OUT,
    limit: int = 0,
    force: bool = False,
) -> Path:
    paths = sorted(headline_dir.glob("*_oracle_split.json"))
    if limit:
        paths = paths[: int(limit)]
    out_dir = out_dir.expanduser().resolve()
    assert_writable(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n_failed = 0
    for index, path in enumerate(paths, start=1):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema") != SCHEMA:
            continue
        print(
            f"[{index}/{len(paths)}] L3-only {payload['task_id']} "
            f"{payload['model']} T={payload['temperature']}",
            flush=True,
        )
        try:
            l3_only_config(
                source_dir=source_dir,
                headline_dir=headline_dir,
                out_dir=out_dir,
                task_id=payload["task_id"],
                model=payload["model"],
                temperature=float(payload["temperature"]),
                force=force,
            )
        except Exception as exc:  # noqa: BLE001
            n_failed += 1
            print(f"  FAILED {exc}", flush=True)
    print(f"L3-only scored {len(paths) - n_failed} failed {n_failed}", flush=True)
    n_written = len(list(out_dir.glob("*_oracle_split.json")))
    if n_written == 656:
        run_posthoc(out_dir=out_dir)
    else:
        print(f"skip posthoc (have {n_written}/656)", flush=True)
    return out_dir


def run_level(
    max_level: int,
    *,
    source_dir: Path = OVERLAY_SOURCE,
    limit: int = 0,
    force: bool = False,
) -> Path:
    if int(max_level) == 1:
        raise SystemExit(
            "L1-only is identical to Raw on this transformer path "
            "(no separate style pass). Use the oracle-split pre columns."
        )
    if int(max_level) == 2:
        raise SystemExit(
            "L1+L2 requires Docker for oracle-gated statement removal. "
            "Docker is not used from this helper; pass "
            "`python -m skyt.humaneval_oracle_split --max-transformation-level 2 "
            "--out-dir outputs/benchmark/humaneval_plus_164_n20_skyt_heldout_oracle_split_l2` "
            "when Docker is available."
        )
    if int(max_level) == 3:
        return run_l3_only(source_dir=source_dir, limit=limit, force=force)
    raise SystemExit(f"unsupported max-level {max_level}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-level", type=int, required=True, choices=(1, 2, 3))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    path = run_level(int(args.max_level), limit=int(args.limit), force=bool(args.force))
    print(json.dumps({"out_dir": str(path)}, indent=2))
