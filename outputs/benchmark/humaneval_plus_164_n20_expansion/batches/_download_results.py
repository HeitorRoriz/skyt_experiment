"""Download finished expansion batches. Does not score or stitch."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from benchmarks.humaneval_plus.generate import _load_dotenv, _use_windows_certificate_store
from benchmarks.humaneval_plus.provenance import atomic_write_json

ROOT = Path("outputs/benchmark/humaneval_plus_164_n20_expansion/batches")
FROZEN = Path("outputs/benchmark/humaneval_plus_164_n20")


def _ids(path: Path) -> set[str]:
    found: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                found.add(json.loads(line)["custom_id"])
    return found


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _anthropic(name: str, batch_id: str, dest: Path) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=3600.0)
    batch = client.messages.batches.retrieve(batch_id)
    if batch.processing_status != "ended":
        raise RuntimeError(f"{name} status {batch.processing_status}")
    counts = {"succeeded": 0, "errored": 0, "canceled": 0, "expired": 0, "other": 0}
    usage = {"input_tokens": 0, "output_tokens": 0}
    seen: set[str] = set()
    tmp = dest.with_suffix(".jsonl.partial")
    with tmp.open("w", encoding="utf-8") as handle:
        for item in client.messages.batches.results(batch_id):
            payload = item.model_dump(mode="json")
            custom_id = payload["custom_id"]
            if custom_id in seen:
                raise RuntimeError(f"duplicate custom_id {custom_id}")
            seen.add(custom_id)
            result = payload.get("result") or {}
            kind = result.get("type") or "other"
            counts[kind] = counts.get(kind, 0) + 1
            message = result.get("message") or {}
            used = message.get("usage") or {}
            usage["input_tokens"] += int(used.get("input_tokens") or 0)
            usage["output_tokens"] += int(used.get("output_tokens") or 0)
            handle.write(json.dumps(payload, default=str) + "\n")
            if len(seen) % 500 == 0:
                print(f"  {name} {len(seen)}", flush=True)
    tmp.replace(dest)
    return {"provider_status": batch.processing_status, "counts": counts, "usage": usage, "ids": seen}


def _openai(name: str, batch_id: str, dest: Path) -> dict:
    import openai

    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=3600.0)
    batch = client.batches.retrieve(batch_id)
    if batch.status != "completed":
        raise RuntimeError(f"{name} status {batch.status}")
    if not batch.output_file_id:
        raise RuntimeError(f"{name} has no output_file_id")
    content = client.files.content(batch.output_file_id)
    tmp = dest.with_suffix(".jsonl.partial")
    tmp.write_bytes(content.read())
    counts = {"succeeded": 0, "failed": 0}
    usage = {"prompt_tokens": 0, "completion_tokens": 0}
    seen: set[str] = set()
    with tmp.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            custom_id = payload["custom_id"]
            if custom_id in seen:
                raise RuntimeError(f"duplicate custom_id {custom_id}")
            seen.add(custom_id)
            response = payload.get("response") or {}
            if response.get("status_code") == 200 and not payload.get("error"):
                counts["succeeded"] += 1
            else:
                counts["failed"] += 1
            used = ((response.get("body") or {}).get("usage") or {})
            usage["prompt_tokens"] += int(used.get("prompt_tokens") or 0)
            usage["completion_tokens"] += int(used.get("completion_tokens") or 0)
    tmp.replace(dest)
    return {"provider_status": batch.status, "counts": counts, "usage": usage, "ids": seen, "output_file_id": batch.output_file_id}


def main() -> None:
    if ROOT.resolve().is_relative_to(FROZEN.resolve()):
        raise RuntimeError("refusing to write inside the frozen overlay")
    _use_windows_certificate_store()
    _load_dotenv()
    registry_path = ROOT / "batch_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for name, record in registry["batches"].items():
        dest = ROOT / f"{name}_results.jsonl"
        expected = _ids(ROOT / record["input_jsonl"])
        print(f"download {name} -> {dest.name}", flush=True)
        if record["provider"] == "anthropic":
            summary = _anthropic(name, record["batch_id"], dest)
        else:
            summary = _openai(name, record["batch_id"], dest)
        got = summary.pop("ids")
        if got != expected:
            missing = len(expected - got)
            extra = len(got - expected)
            raise RuntimeError(f"{name} custom_id mismatch missing={missing} extra={extra}")
        record["status"] = summary["provider_status"]
        record["results_jsonl"] = dest.name
        record["downloaded_at"] = datetime.now(timezone.utc).isoformat()
        record["download_lines"] = len(got)
        record["download_counts"] = summary["counts"]
        record["download_usage"] = summary["usage"]
        record["download_sha256"] = _sha256(dest)
        if "output_file_id" in summary:
            record["output_file_id"] = summary["output_file_id"]
        registry["updated_at"] = record["downloaded_at"]
        atomic_write_json(registry_path, registry)
        print(
            f"saved {name} lines={len(got)} counts={summary['counts']} sha256={record['download_sha256']}",
            flush=True,
        )
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
