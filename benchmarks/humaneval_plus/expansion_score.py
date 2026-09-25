"""Fill oracle fields on expansion overlay trees with the frozen Docker scorer.

Resume-safe per config. No LLM calls. Does not touch the frozen overlay.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .dataset import load_evalplus_problems
from .provenance import attach_oracle, dump_jsonl
from .run import _failed_oracle, _load_existing
from .sandbox import evaluate_stitched, plus_cases_for_problem

ROOT = Path("outputs/benchmark/humaneval_plus_164_n20_expansion")
SLUGS = ("haiku45", "luna", "sonnet5")
# Same task + same stitched bytes ⇒ same oracle. Speeds T=0 cells where
# many draws are identical. Does not change the frozen evaluator.
_ORACLE_CACHE: Dict[tuple, Dict] = {}


def _needs_oracle(records: List[Dict]) -> bool:
    return any(record.get("oracle") is None for record in records)


def score_file(path: Path, problems: Dict) -> str:
    records = _load_existing(path)
    if not records or not _needs_oracle(records):
        return "skip"
    task_id = records[0]["task_id"]
    problem = problems[task_id]
    plus_cases_for_problem(problem)
    updated = []
    for record in records:
        if record.get("oracle") is not None:
            updated.append(record)
            continue
        if not record.get("parse_ok") or not record.get("has_entry_point"):
            updated.append(attach_oracle(record, _failed_oracle()))
            continue
        key = (task_id, record.get("stitched_sha256") or record.get("stitched_code") or "")
        oracle = _ORACLE_CACHE.get(key)
        if oracle is None:
            oracle = evaluate_stitched(record.get("stitched_code") or "", problem)
            _ORACLE_CACHE[key] = oracle
        updated.append(attach_oracle(record, oracle))
    dump_jsonl(path, updated)
    return "scored"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--of", type=int, default=1)
    args = parser.parse_args()
    problems, _digest = load_evalplus_problems()
    files = [path for slug in SLUGS for path in sorted((ROOT / slug).glob("*.jsonl"))]
    files = [path for index, path in enumerate(files) if index % args.of == args.shard]
    print(f"shard {args.shard}/{args.of} configs {len(files)}", flush=True)
    done = 0
    for index, path in enumerate(files, start=1):
        status = score_file(path, problems)
        if status == "scored":
            done += 1
        if index == 1 or index % 1 == 0:
            message = f"[{index}/{len(files)}] {status} {path.name}"
            print(message, flush=True)
            with (ROOT / f"score_shard_{args.shard}.log").open("a", encoding="utf-8") as handle:
                handle.write(message + "\n")


if __name__ == "__main__":
    main()
