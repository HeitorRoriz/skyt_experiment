"""Provenance records for one HumanEval+ generation."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .prompts import (
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_ID,
    USER_PROMPT_ID,
    prompt_bundle_hash,
    render_user_prompt,
)


SCHEMA = "skyt-humaneval-plus-generation-v1"


def sha256_text(value: str) -> str:
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def new_generation_record(
    *,
    task_id: str,
    model: str,
    temperature: float,
    run_index: int,
    problem_prompt: str,
    raw_response: Optional[str],
    stitch: Dict[str, Any],
    usage: Optional[Dict[str, Any]] = None,
    retry_history: Optional[list] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    user_prompt = render_user_prompt(problem_prompt)
    stitched = stitch.get("stitched_code") or ""
    return {
        "schema": SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "model": model,
        "temperature": temperature,
        "run_index": run_index,
        "prompt": {
            "system_prompt_id": SYSTEM_PROMPT_ID,
            "user_prompt_id": USER_PROMPT_ID,
            "system": SYSTEM_PROMPT,
            "user": user_prompt,
            "prompt_bundle_sha256": prompt_bundle_hash(),
        },
        "raw_response": raw_response,
        "raw_response_sha256": sha256_text(raw_response or ""),
        "extracted_completion": stitch.get("extracted_completion"),
        "stitched_code": stitched,
        "stitched_sha256": sha256_text(stitched),
        "stitch_mode": stitch.get("stitch_mode"),
        "parse_ok": bool(stitch.get("parse_ok")),
        "has_entry_point": bool(stitch.get("has_entry_point")),
        "usage": usage or {},
        "retry_history": retry_history or [],
        "error": error,
        "oracle": None,
        "repair_applied": False,
        "style_contract": None,
    }


def attach_oracle(record: Dict[str, Any], oracle: Dict[str, Any]) -> Dict[str, Any]:
    updated = dict(record)
    updated["oracle"] = {
        "base_status": oracle.get("base_status"),
        "base_passed": oracle.get("base_passed"),
        "plus_status": oracle.get("plus_status"),
        "plus_passed": oracle.get("plus_passed"),
        "certified": oracle.get("certified"),
    }
    return updated


def dump_jsonl(path, records) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, default=str) + "\n")
