"""Freeze expansion downloads, QA them, and write overlay jsonl trees.

No LLM calls. Oracle fields stay empty until expansion_score fills them
with the frozen Docker evaluator. Does not write into the frozen overlay.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .expansion import (
    FROZEN_MAX_TOKENS,
    HAIKU_MODEL,
    LUNA_MODEL,
    SONNET5_MAX_TOKENS,
    SONNET5_MODEL,
)
from .prompts import SYSTEM_PROMPT, render_user_prompt
from .provenance import atomic_write_json, dump_jsonl, new_generation_record
from .run import _safe_name
from .stitch import stitch_solution

ROOT = Path("outputs/benchmark/humaneval_plus_164_n20_expansion")
BATCHES = ROOT / "batches"
RAW = ROOT / "raw"
FROZEN = Path("outputs/benchmark/humaneval_plus_164_n20")
_CUSTOM = re.compile(
    r"^(haiku45|luna|sonnet5)__HumanEval_(\d+)__(T00|T07|Tdef)__r(\d{2})$"
)
_TEMP = {"T00": 0.0, "T07": 0.7, "Tdef": None}

BATCH_META = {
    "haiku45_T00": {"slug": "haiku45", "temp_key": "T00", "provider": "anthropic"},
    "haiku45_T07": {"slug": "haiku45", "temp_key": "T07", "provider": "anthropic"},
    "sonnet5_default": {"slug": "sonnet5", "temp_key": "Tdef", "provider": "anthropic"},
    "luna_T00": {"slug": "luna", "temp_key": "T00", "provider": "openai"},
    "luna_T07": {"slug": "luna", "temp_key": "T07", "provider": "openai"},
}
REQUESTED = {
    "haiku45": HAIKU_MODEL,
    "luna": LUNA_MODEL,
    "sonnet5": SONNET5_MODEL,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _readonly(path: Path) -> None:
    os.chmod(path, stat.S_IREAD)


def freeze_raw() -> Dict[str, Any]:
    if RAW.resolve().is_relative_to(FROZEN.resolve()):
        raise RuntimeError("refusing to write inside the frozen overlay")
    registry = json.loads((BATCHES / "batch_registry.json").read_text(encoding="utf-8"))
    RAW.mkdir(parents=True, exist_ok=True)
    checksums: List[str] = []
    manifest_batches: Dict[str, Any] = {}
    for name, meta in BATCH_META.items():
        record = registry["batches"][name]
        src = BATCHES / f"{name}_results.jsonl"
        if not src.exists():
            raise FileNotFoundError(src)
        dest_dir = RAW / meta["slug"]
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{record['batch_id']}.output.jsonl"
        if not dest.exists():
            dest.write_bytes(src.read_bytes())
        digest = _sha256(dest)
        if digest != _sha256(src):
            raise RuntimeError(f"{name} copy hash mismatch")
        _readonly(dest)
        input_path = BATCHES / record["input_jsonl"]
        checksums.append(f"{digest}  {dest.as_posix()}")
        manifest_batches[name] = {
            "provider": record["provider"],
            "batch_id": record["batch_id"],
            "status": record.get("status"),
            "submitted_at": record.get("submitted_at"),
            "downloaded_at": record.get("downloaded_at"),
            "n_requests": record.get("n_requests"),
            "download_counts": record.get("download_counts"),
            "download_usage": record.get("download_usage"),
            "input_jsonl": str(input_path.as_posix()),
            "input_sha256": _sha256(input_path),
            "output_jsonl": str(dest.as_posix()),
            "output_sha256": digest,
            "error_file": None,
            "note": (
                "Anthropic file is the SDK model_dump of the results stream, "
                "not the provider's raw bytes."
                if meta["provider"] == "anthropic"
                else "OpenAI file is the Files API output body. error_file_id was absent at download."
            ),
        }
    checksum_path = RAW / "checksums.sha256"
    checksum_path.write_text("\n".join(checksums) + "\n", encoding="utf-8")
    manifest = {
        "schema": "sameeval-expansion-manifest-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "copied from batches/*_results.jsonl; no second download",
        "batches": manifest_batches,
    }
    atomic_write_json(ROOT / "manifest.json", manifest)
    return manifest


def _anthropic_text(message: Dict[str, Any]) -> Tuple[str, int, bool]:
    thinking = 0
    leaked = False
    texts: List[str] = []
    for block in message.get("content") or []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "thinking":
            thinking += 1
            continue
        if block.get("type") == "text":
            texts.append(block.get("text") or "")
    text = "".join(texts)
    if "<thinking>" in text.lower() or "</thinking>" in text.lower():
        leaked = True
    return text, thinking, leaked


def _parse_id(custom_id: str) -> Tuple[str, str, Optional[float], int]:
    match = _CUSTOM.fullmatch(custom_id)
    if not match:
        raise ValueError(f"unparseable custom_id {custom_id!r}")
    slug, number, temp_key, run = match.groups()
    return slug, f"HumanEval/{int(number)}", _TEMP[temp_key], int(run)


def _load_requests(name: str) -> Dict[str, Dict[str, Any]]:
    path = BATCHES / f"{name}.jsonl"
    found: Dict[str, Dict[str, Any]] = {}
    for row in _read_jsonl(path):
        found[row["custom_id"]] = row
    return found


def _cell_key(slug: str, temperature: Optional[float]) -> str:
    if temperature is None:
        return f"{slug} default"
    return f"{slug} T={temperature:.1f}"


def validate_and_extract(problems: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Return the QA payload and per-cell generation records. No Docker."""
    cells: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    stops: Dict[str, Counter] = defaultdict(Counter)
    models_seen: Dict[str, Counter] = defaultdict(Counter)
    thinking_responses = Counter()
    leaked = Counter()
    reasoning_tokens = Counter()
    param_errors: List[str] = []
    extraction_fail = Counter()
    extraction_n = Counter()
    identical_configs = Counter()
    identical_n = Counter()
    short_configs: List[str] = []

    for name, meta in BATCH_META.items():
        requests = _load_requests(name)
        registry = json.loads((BATCHES / "batch_registry.json").read_text(encoding="utf-8"))
        batch_id = registry["batches"][name]["batch_id"]
        dest = RAW / meta["slug"] / f"{batch_id}.output.jsonl"
        seen: Dict[str, int] = Counter()
        by_config: Dict[Tuple[str, Optional[float]], List[str]] = defaultdict(list)
        for row in _read_jsonl(dest):
            custom_id = row["custom_id"]
            seen[custom_id] += 1
            slug, task_id, temperature, run_index = _parse_id(custom_id)
            if slug != meta["slug"] or _TEMP[meta["temp_key"]] != temperature:
                param_errors.append(f"{custom_id} does not match batch {name}")
            request = requests.get(custom_id)
            if request is None:
                param_errors.append(f"{custom_id} missing from submitted input")
            else:
                _check_params(name, request, param_errors)
            text, stop, usage, model_returned, truncated, refusal, think_n, did_leak, reason_n = (
                _response_fields(meta["provider"], row)
            )
            cell = _cell_key(slug, temperature)
            stops[cell][stop or "missing"] += 1
            models_seen[slug][model_returned or "missing"] += 1
            if think_n:
                thinking_responses[cell] += 1
            if did_leak:
                leaked[cell] += 1
            if reason_n:
                reasoning_tokens[cell] += reason_n
            problem = problems[task_id]
            stitch = stitch_solution(problem["prompt"], text, problem["entry_point"])
            extraction_n[cell] += 1
            ok = bool(stitch.get("parse_ok") and stitch.get("has_entry_point"))
            if not ok:
                extraction_fail[cell] += 1
            record = new_generation_record(
                task_id=task_id,
                model=model_returned or REQUESTED[slug],
                temperature=temperature,  # type: ignore[arg-type]
                run_index=run_index,
                problem_prompt=problem["prompt"],
                raw_response=text,
                stitch=stitch,
                usage=usage,
            )
            record["custom_id"] = custom_id
            record["batch_id"] = batch_id
            record["model_requested"] = REQUESTED[slug]
            record["model_returned"] = model_returned
            record["stop_reason"] = stop
            record["truncated"] = truncated
            record["refusal"] = refusal
            record["thinking_blocks"] = think_n
            record["oracle"] = None
            cells[cell].append(record)
            by_config[(task_id, temperature)].append(stitch.get("extracted_completion") or "")
        expected = set(requests)
        missing = sorted(expected - set(seen))
        extra = sorted(set(seen) - expected)
        dupes = sorted(cid for cid, count in seen.items() if count > 1)
        if missing or extra or dupes:
            param_errors.append(
                f"{name} missing={len(missing)} extra={len(extra)} dupes={len(dupes)}"
            )
        for (task_id, temperature), programs in by_config.items():
            cell = _cell_key(meta["slug"], temperature)
            identical_n[cell] += 1
            if len(programs) == 20 and len(set(programs)) == 1:
                identical_configs[cell] += 1
            if len(programs) < 20:
                short_configs.append(f"{cell} {task_id} n={len(programs)}")

    qa = {
        "schema": "sameeval-expansion-qa-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "stops": {key: dict(counter) for key, counter in stops.items()},
        "models_seen": {key: dict(counter) for key, counter in models_seen.items()},
        "thinking_responses": dict(thinking_responses),
        "thinking_leaked_into_text": dict(leaked),
        "luna_reasoning_tokens": dict(reasoning_tokens),
        "param_errors": param_errors,
        "extraction_fail": dict(extraction_fail),
        "extraction_n": dict(extraction_n),
        "identical_configs": dict(identical_configs),
        "configs": dict(identical_n),
        "short_configs": short_configs,
    }
    qa["gate"] = _gate(qa)
    return {"qa": qa, "cells": cells}


def _check_params(name: str, request: Dict[str, Any], errors: List[str]) -> None:
    if name.startswith("haiku"):
        params = request["params"]
        if "temperature" not in params or "top_p" in params or "top_k" in params:
            errors.append(f"{request['custom_id']} haiku sampling keys")
        if params.get("max_tokens") != FROZEN_MAX_TOKENS:
            errors.append(f"{request['custom_id']} haiku max_tokens")
        if params.get("system") != SYSTEM_PROMPT:
            errors.append(f"{request['custom_id']} haiku system prompt")
        roles = [item["role"] for item in params.get("messages") or []]
        if roles != ["user"]:
            errors.append(f"{request['custom_id']} haiku roles {roles}")
    elif name.startswith("luna"):
        body = request["body"]
        if body.get("reasoning_effort") != "none" or "temperature" not in body or "seed" in body:
            errors.append(f"{request['custom_id']} luna sampling keys")
        if body.get("max_completion_tokens") != FROZEN_MAX_TOKENS:
            errors.append(f"{request['custom_id']} luna max_completion_tokens")
        messages = body.get("messages") or []
        if not messages or messages[0].get("content") != SYSTEM_PROMPT:
            errors.append(f"{request['custom_id']} luna system prompt")
    elif name.startswith("sonnet"):
        params = request["params"]
        for key in ("temperature", "top_p", "top_k"):
            if key in params:
                errors.append(f"{request['custom_id']} sonnet has {key}")
        if params.get("max_tokens") != SONNET5_MAX_TOKENS:
            errors.append(f"{request['custom_id']} sonnet max_tokens")
        if params.get("system") != SYSTEM_PROMPT:
            errors.append(f"{request['custom_id']} sonnet system prompt")
        roles = [item["role"] for item in params.get("messages") or []]
        if "assistant" in roles:
            errors.append(f"{request['custom_id']} sonnet assistant prefill")


def _response_fields(provider: str, row: Dict[str, Any]) -> Tuple[Any, ...]:
    if provider == "anthropic":
        result = row.get("result") or {}
        message = result.get("message") or {}
        text, thinking, leaked = _anthropic_text(message)
        stop = message.get("stop_reason")
        usage = message.get("usage") or {}
        return (
            text,
            stop,
            {
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
            },
            message.get("model"),
            stop == "max_tokens",
            stop == "refusal",
            thinking,
            leaked,
            0,
        )
    body = ((row.get("response") or {}).get("body") or {})
    choice = (body.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content = message.get("content") or ""
    if isinstance(content, list):
        content = "".join(
            part.get("text") or "" for part in content if isinstance(part, dict)
        )
    stop = choice.get("finish_reason")
    usage = body.get("usage") or {}
    details = usage.get("completion_tokens_details") or {}
    return (
        content,
        stop,
        {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "reasoning_tokens": details.get("reasoning_tokens"),
        },
        body.get("model"),
        stop == "length",
        stop == "content_filter",
        0,
        False,
        int(details.get("reasoning_tokens") or 0),
    )


def _gate(qa: Dict[str, Any]) -> Dict[str, Any]:
    failures: List[str] = []
    if qa["param_errors"]:
        failures.append(f"parameter mismatches: {len(qa['param_errors'])}")
    for slug, counter in qa["models_seen"].items():
        if len(counter) != 1:
            failures.append(f"{slug} returned model strings: {counter}")
    if qa["luna_reasoning_tokens"]:
        failures.append(f"luna reasoning tokens: {qa['luna_reasoning_tokens']}")
    if qa["thinking_leaked_into_text"]:
        failures.append(f"thinking leaked into text: {qa['thinking_leaked_into_text']}")
    for cell, n in qa["extraction_n"].items():
        fail = qa["extraction_fail"].get(cell, 0)
        if n and fail / n > 0.02:
            failures.append(f"{cell} extraction failure {fail}/{n}")
        stops = qa["stops"].get(cell) or {}
        truncated = stops.get("max_tokens", 0) + stops.get("length", 0)
        if n and truncated / n > 0.02:
            failures.append(f"{cell} truncated {truncated}/{n}")
    for cell, n_cfg in qa["configs"].items():
        if "T=0.7" not in cell:
            continue
        share = qa["identical_configs"].get(cell, 0) / n_cfg if n_cfg else 0
        if share > 0.5:
            failures.append(f"{cell} byte-identical configs {share:.3f}")
    if qa["short_configs"]:
        failures.append(f"short configs: {len(qa['short_configs'])}")
    return {"pass": not failures, "failures": failures}


def write_trees(cells: Dict[str, List[Dict[str, Any]]]) -> None:
    grouped: Dict[Tuple[str, str, Optional[float]], List[Dict[str, Any]]] = defaultdict(list)
    for records in cells.values():
        for record in records:
            slug = record["custom_id"].split("__", 1)[0]
            grouped[(slug, record["task_id"], record["temperature"])].append(record)
    for (slug, task_id, temperature), records in grouped.items():
        records.sort(key=lambda item: int(item["run_index"]))
        model = records[0]["model"]
        leaf = ROOT / slug
        if leaf.resolve().is_relative_to(FROZEN.resolve()):
            raise RuntimeError("refusing to write inside the frozen overlay")
        stem = _safe_name(task_id, model, 0.0 if temperature is None else temperature)
        if temperature is None:
            stem = stem.replace("temp0.0", "tempdefault")
        dump_jsonl(leaf / f"{stem}.jsonl", records)


def write_qa_md(qa: Dict[str, Any]) -> None:
    lines = [
        "# Expansion QA",
        "",
        f"Gate: **{'PASS' if qa['gate']['pass'] else 'FAIL'}**",
        "",
    ]
    if qa["gate"]["failures"]:
        lines.append("## Failures")
        lines.extend(f"- {item}" for item in qa["gate"]["failures"])
        lines.append("")
    lines.append("## Returned model strings")
    for slug, counter in qa["models_seen"].items():
        lines.append(f"- {slug}: {counter}")
    lines.append("")
    lines.append("## Stop reasons")
    for cell, counter in qa["stops"].items():
        fail = qa["extraction_fail"].get(cell, 0)
        n = qa["extraction_n"].get(cell, 0)
        identical = qa["identical_configs"].get(cell, 0)
        configs = qa["configs"].get(cell, 0)
        lines.append(
            f"- {cell}: stops={counter}; extraction fail {fail}/{n}; "
            f"all-20-identical configs {identical}/{configs}"
        )
    lines.append("")
    lines.append(f"Thinking responses: {qa['thinking_responses'] or 'none'}")
    lines.append(f"Thinking leaked into extracted text: {qa['thinking_leaked_into_text'] or 'none'}")
    lines.append(f"Luna reasoning tokens: {qa['luna_reasoning_tokens'] or 'none'}")
    lines.append(f"Short configs: {len(qa['short_configs'])}")
    (ROOT / "qa_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    from .dataset import load_evalplus_problems

    freeze_raw()
    problems, _digest = load_evalplus_problems()
    payload = validate_and_extract(problems)
    atomic_write_json(ROOT / "qa_report.json", payload["qa"])
    write_qa_md(payload["qa"])
    print(json.dumps(payload["qa"]["gate"], indent=2), flush=True)
    if not payload["qa"]["gate"]["pass"]:
        raise SystemExit(2)
    write_trees(payload["cells"])
    print("TREES_WRITTEN", flush=True)


if __name__ == "__main__":
    main()
