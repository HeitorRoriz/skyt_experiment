"""Live-print each stored generation. Does not call an LLM. Ctrl+C stops this viewer only."""

from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _status(record: dict) -> str:
    if record.get("error"):
        return "FAIL " + str(record["error"])
    oracle = record.get("oracle") or {}
    if oracle.get("plus_passed"):
        return "plus-pass"
    return "plus-fail"


def _line_count(path: Path) -> list[str]:
    try:
        return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError:
        return []


def main() -> None:
    print("Watching SameEval calls. Ctrl+C stops this viewer, not the overlay.", flush=True)
    seen: dict[str, int] = {}
    for path in sorted(ROOT.glob("*.jsonl")):
        seen[path.name] = len(_line_count(path))
    print(
        f"Already on disk: {sum(seen.values())} generations in {len(seen)} jsonl files.",
        flush=True,
    )
    while True:
        for path in sorted(ROOT.glob("*.jsonl")):
            lines = _line_count(path)
            old = seen.get(path.name, 0)
            if len(lines) <= old:
                continue
            for raw in lines[old:]:
                try:
                    record = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                usage = record.get("usage") or {}
                inp = usage.get("input_tokens") or usage.get("prompt_tokens")
                out = usage.get("output_tokens") or usage.get("completion_tokens")
                print(
                    "CALL "
                    f"{record.get('task_id')}  {record.get('model')}  "
                    f"T={record.get('temperature')}  "
                    f"gen {int(record.get('run_index', -1)) + 1}/20  "
                    f"{_status(record)}  in={inp}  out={out}",
                    flush=True,
                )
            seen[path.name] = len(lines)
        time.sleep(0.5)


if __name__ == "__main__":
    main()
