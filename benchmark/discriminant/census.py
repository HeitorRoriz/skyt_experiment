"""Disagreement census vs the fingerprint tape.

Certified pairs only, same task × model × temperature. No canon, no repair.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from benchmark.protect import assert_writable
from benchmark.relation import RELATION_VERSION, fingerprint
from benchmark.score import _is_certified, load_configs
from benchmark.discriminant.judges import (
    JUDGE_ORDER,
    JUDGE_VERSION,
    TYPE3_TED_RATIO,
    classify_cell,
    judge_pair,
)


SCHEMA = "structural-repeatability-discriminant-v1"
SAMPLE_SEED = 20260723
SAMPLE_PER_CELL = 20
TAPE = "fingerprint_eq"


def _cell_key(tape: Optional[bool], other: Optional[bool]) -> Optional[str]:
    if tape is None or other is None:
        return None
    if tape and other:
        return "both_same"
    if (not tape) and (not other):
        return "both_different"
    if tape and not other:
        return "tape_same_judge_different"
    return "tape_different_judge_same"


def _empty_counts() -> Dict[str, int]:
    return {
        "both_same": 0,
        "both_different": 0,
        "tape_same_judge_different": 0,
        "tape_different_judge_same": 0,
        "n_compared": 0,
        "n_skipped": 0,
    }


def _sha(code: str) -> str:
    return hashlib.sha256((code or "").encode()).hexdigest()[:16]


def iter_certified_pairs(source_dir: Path) -> Iterable[Dict[str, Any]]:
    grouped = load_configs(source_dir)
    for (task_id, model, temperature), records in sorted(grouped.items()):
        ordered = sorted(records, key=lambda item: int(item.get("run_index", 0)))
        certified = []
        for record in ordered:
            code = record.get("stitched_code") or ""
            fp = fingerprint(code)
            if _is_certified(record, fp is not None):
                certified.append(record)
        for left, right in itertools.combinations(certified, 2):
            yield {
                "task_id": task_id,
                "model": model,
                "temperature": float(temperature),
                "i": int(left.get("run_index", 0)),
                "j": int(right.get("run_index", 0)),
                "code_a": left.get("stitched_code") or "",
                "code_b": right.get("stitched_code") or "",
            }


def run_census(
    source_dir: Path,
    out_dir: Path,
    *,
    sample_per_cell: int = SAMPLE_PER_CELL,
    seed: int = SAMPLE_SEED,
    limit_pairs: int = 0,
    flexible_naming: bool = True,
) -> Dict[str, Any]:
    assert_writable(out_dir)
    source_dir = source_dir.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    counts = {name: _empty_counts() for name in JUDGE_ORDER if name != TAPE}
    samples: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
        name: {
            "tape_same_judge_different": [],
            "tape_different_judge_same": [],
        }
        for name in counts
    }
    n_pairs = 0
    for pair in iter_certified_pairs(source_dir):
        if limit_pairs and n_pairs >= limit_pairs:
            break
        n_pairs += 1
        verdict = judge_pair(
            pair["code_a"],
            pair["code_b"],
            flexible_naming=flexible_naming,
        )
        tape = verdict[TAPE]
        tag = classify_cell(verdict)
        for judge in counts:
            other = verdict.get(judge)
            bucket = _cell_key(tape, other)
            if bucket is None:
                counts[judge]["n_skipped"] += 1
                continue
            counts[judge][bucket] += 1
            counts[judge]["n_compared"] += 1
            if bucket in samples[judge]:
                samples[judge][bucket].append(
                    {
                        "task_id": pair["task_id"],
                        "model": pair["model"],
                        "temperature": pair["temperature"],
                        "i": pair["i"],
                        "j": pair["j"],
                        "tag": tag,
                        "ted": verdict.get("ted"),
                        "ted_ratio": verdict.get("ted_ratio"),
                        "sha_a": _sha(pair["code_a"]),
                        "sha_b": _sha(pair["code_b"]),
                        "code_a": pair["code_a"],
                        "code_b": pair["code_b"],
                    }
                )

    rng = random.Random(seed)
    sampled = {}
    for judge, cells in samples.items():
        sampled[judge] = {}
        for cell, rows in cells.items():
            rows = list(rows)
            rng.shuffle(rows)
            sampled[judge][cell] = rows[:sample_per_cell]
            sampled[judge][f"{cell}_n_available"] = len(rows)

    report = {
        "schema": SCHEMA,
        "relation_version": RELATION_VERSION,
        "judge_version": JUDGE_VERSION,
        "type3_ted_ratio": TYPE3_TED_RATIO,
        "sample_seed": seed,
        "sample_per_cell": sample_per_cell,
        "n_pairs": n_pairs,
        "source_dir": str(source_dir),
        "tape": TAPE,
        "judges": {
            "string_eq": "Exact source string.",
            "parse_unparse_eq": "ast.unparse(ast.parse) — Type-1-ish, comments/format dropped.",
            "raw_ast_eq": "MD5 of ast.dump, no canonicalize (docstrings and names count).",
            "type2_eq": "α-rename bound names, keep docstrings — Type-2-ish.",
            "ted_zero": "Zhang–Shasha distance 0 on labeled Python ASTs (GumTree-style labels).",
            "type3_near": f"TED / max(size) < {TYPE3_TED_RATIO} — Type-3-ish, not fitted.",
            "fingerprint_eq": "Benchmark same(): canonical-form fingerprint.",
        },
        "note": (
            "Off-diagonal cells are the result. Do not retune TYPE3_TED_RATIO "
            "or the tape to shrink them. Codes in the sample are for the appendix."
        ),
        "vs_fingerprint": counts,
        "sample": sampled,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "discriminant_report.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    report["report_path"] = str(path)
    return report
