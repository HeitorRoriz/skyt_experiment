"""Score stored jsonl with fingerprint same(). No SKYT protocol."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .metrics import config_repeatability
from .protect import assert_writable
from .relation import RELATION_VERSION, fingerprint
from .report import build_report
from .schema import SCHEMA
from benchmarks.humaneval_plus.provenance import atomic_write_json


ConfigKey = Tuple[str, str, float]


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _is_certified(record: Dict[str, Any], parseable: bool) -> bool:
    """HumanEval+ plus tests. Missing plus_passed is not a base fallback."""
    if not parseable:
        return False
    oracle = record.get("oracle") or {}
    plus = oracle.get("plus_passed")
    if plus is None:
        return False
    return bool(plus)


def load_configs(source_dir: Path) -> Dict[ConfigKey, List[Dict[str, Any]]]:
    grouped: Dict[ConfigKey, List[Dict[str, Any]]] = defaultdict(list)
    jsonl_files = sorted(source_dir.glob("*.jsonl"))
    if not jsonl_files:
        raise ValueError(f"No *.jsonl files in {source_dir}")
    for path in jsonl_files:
        for record in _iter_jsonl(path):
            if record.get("repair_applied"):
                raise ValueError(
                    f"{path.name}: benchmark scoring refuses SKYT-repaired records"
                )
            if record.get("style_contract"):
                raise ValueError(
                    f"{path.name}: benchmark scoring refuses records with a style contract"
                )
            task_id = record.get("task_id")
            model = record.get("model")
            if task_id is None or model is None:
                continue
            raw_temp = record.get("temperature", 0.0)
            temperature = None if raw_temp is None else float(raw_temp)
            grouped[(str(task_id), str(model), temperature)].append(record)
    if not grouped:
        raise ValueError(f"No generation records in {source_dir}")
    return grouped


def score_directory(
    source_dir: Path,
    out_dir: Path,
    *,
    n_bootstrap: int = 10000,
    flexible_naming: bool = True,
    skip_incomplete: bool = False,
    require_n: int | None = None,
    report_filename: str = "benchmark_report.json",
) -> Dict[str, Any]:
    assert_writable(out_dir)
    source_dir = source_dir.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    grouped = load_configs(source_dir)
    rows = []
    n_skipped_incomplete = 0
    for (task_id, model, temperature), records in sorted(
        grouped.items(),
        key=lambda item: (
            item[0][0],
            item[0][1],
            item[0][2] is None,
            -1.0 if item[0][2] is None else float(item[0][2]),
        ),
    ):
        by_index = {
            int(record.get("run_index", -1)): record for record in records
        }
        ordered = [by_index[key] for key in sorted(by_index)]
        if require_n is not None and set(range(require_n)).issubset(by_index):
            ordered = [by_index[index] for index in range(require_n)]
        elif require_n is not None or len(ordered) < 2:
            if skip_incomplete:
                n_skipped_incomplete += 1
                continue
            raise ValueError(
                f"{task_id} {model} T={temperature}: need at least two generations"
                + (f" and N={require_n}" if require_n is not None else "")
            )
        prints = [
            fingerprint(
                record.get("stitched_code") or "",
                flexible_naming=flexible_naming,
            )
            for record in ordered
        ]
        certified = [
            _is_certified(record, fp is not None)
            for record, fp in zip(ordered, prints)
        ]
        analysis = config_repeatability(prints, certified)
        rows.append(
            {
                "task_id": task_id,
                "model": model,
                "temperature": None if temperature is None else float(temperature),
                "n": analysis["n"],
                "n_certified": analysis["n_certified"],
                "same_at_2": analysis["same_at_2"],
                "same_at_2_given_cert": analysis["same_at_2_given_cert"],
                "plus_pass": analysis["plus_pass"],
                "u_statistic_pair_count": analysis["u_statistic_pair_count"],
                "u_statistic_certified_pair_count": analysis[
                    "u_statistic_certified_pair_count"
                ],
                "relation_version": RELATION_VERSION,
            }
        )
    if not rows:
        report = {
            "schema": SCHEMA,
            "relation_version": RELATION_VERSION,
            "n_complete_configs": 0,
            "n_skipped_incomplete": n_skipped_incomplete,
            "slices": [],
            "configs": [],
            "pilot_grid": True,
            "source_dir": str(source_dir),
            "note": "No complete configs to score yet.",
        }
    else:
        report = build_report(
            rows,
            n_bootstrap=n_bootstrap,
            source_dir=str(source_dir),
        )
        report["n_complete_configs"] = len(rows)
        report["n_skipped_incomplete"] = n_skipped_incomplete
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / report_filename
    atomic_write_json(report_path, report)
    report["report_path"] = str(report_path)
    report["schema"] = SCHEMA
    return report
