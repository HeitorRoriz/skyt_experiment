"""Score stored generation jsonl with the current extractor.

No API calls. No SKYT repair. Writes only to --out-dir.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from benchmarks.humaneval_plus.analyze import analyze_records

from .protect import assert_writable
from .report import build_overlay_report, overlay_row_from_analysis
from .schema import RELATION_VERSION, SCHEMA


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


def load_configs(source_dir: Path) -> Dict[ConfigKey, List[Dict[str, Any]]]:
    grouped: Dict[ConfigKey, List[Dict[str, Any]]] = defaultdict(list)
    jsonl_files = sorted(source_dir.glob("*.jsonl"))
    if not jsonl_files:
        raise ValueError(f"No *.jsonl files in {source_dir}")
    for path in jsonl_files:
        for record in _iter_jsonl(path):
            if record.get("repair_applied"):
                raise ValueError(
                    f"{path.name}: overlay scoring refuses SKYT-repaired records"
                )
            if record.get("style_contract"):
                raise ValueError(
                    f"{path.name}: overlay scoring refuses records with a style contract"
                )
            task_id = record.get("task_id")
            model = record.get("model")
            if task_id is None or model is None:
                continue
            temperature = float(record.get("temperature", 0.0))
            grouped[(str(task_id), str(model), temperature)].append(record)
    if not grouped:
        raise ValueError(f"No generation records in {source_dir}")
    return grouped


def score_directory(
    source_dir: Path,
    out_dir: Path,
    *,
    cv_splits: int = 2000,
    cv_seed: int = 20260723,
    n_bootstrap: int = 10000,
) -> Dict[str, Any]:
    assert_writable(out_dir)
    source_dir = source_dir.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    grouped = load_configs(source_dir)
    rows = []
    for (task_id, model, temperature), records in sorted(grouped.items()):
        ordered = sorted(records, key=lambda item: int(item.get("run_index", 0)))
        if len(ordered) < 2:
            raise ValueError(
                f"{task_id} {model} T={temperature}: need at least two generations"
            )
        analysis = analyze_records(
            ordered,
            cv_splits=cv_splits,
            cv_seed=cv_seed,
        )
        if not analysis.get("no_skyt_repair", True):
            raise ValueError("analysis claimed SKYT repair; overlay refuses it")
        rows.append(
            overlay_row_from_analysis(
                task_id=task_id,
                model=model,
                temperature=temperature,
                n=len(ordered),
                analysis=analysis,
            )
        )
    report = build_overlay_report(
        rows,
        n_bootstrap=n_bootstrap,
        source_dir=str(source_dir),
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "overlay_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    report["report_path"] = str(report_path)
    report["schema"] = SCHEMA
    report["relation_version"] = RELATION_VERSION
    return report
