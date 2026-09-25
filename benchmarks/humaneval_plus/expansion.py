"""Batch request builders for the 2026-09-24 model expansion.

Three models only: Claude Haiku 4.5, GPT-6 Luna, Claude Sonnet 5.
This module writes JSONL. It does not call an API.

Prefill check (2026-09-24): the frozen overlay client sends a system
prompt plus one user message. It never sends an assistant turn and never
opens a code fence. Sonnet 5 can use that same prompt.

The frozen GPT-4o-mini and Claude Sonnet 4.5 overlay was synchronous
(one chat completion or messages.create per draw), not the Batch API.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .manifest import MANIFEST
from .prompts import SYSTEM_PROMPT, render_user_prompt


_CUSTOM_ID = re.compile(r"^[A-Za-z0-9_-]+$")

HAIKU_MODEL = "claude-haiku-4-5-20251001"
LUNA_MODEL = "gpt-6-luna"
SONNET5_MODEL = "claude-sonnet-5"

# Model page lists only the alias gpt-6-luna. No dated snapshot as of 2026-09-24.
LUNA_SNAPSHOT_NOTE = "no dated snapshot on the model page; request gpt-6-luna and record the returned model string"

FROZEN_MAX_TOKENS = int(MANIFEST["generation"]["max_tokens"])
SONNET5_MAX_TOKENS = 16000
N_FULL = 20
TEMPERATURES = (0.0, 0.7)

SLUGS = {
    HAIKU_MODEL: "haiku45",
    LUNA_MODEL: "luna",
    SONNET5_MODEL: "sonnet5",
}


def frozen_harness_prefills() -> bool:
    """True only if the frozen client would send an assistant turn."""
    user = render_user_prompt("def add(a, b):\n")
    openai_roles = [item["role"] for item in _openai_messages(user)]
    anthropic_roles = [item["role"] for item in _anthropic_messages(user)]
    return "assistant" in openai_roles or "assistant" in anthropic_roles


def custom_id(slug: str, task_id: str, temperature: Optional[float], run_index: int) -> str:
    task = task_id.replace("/", "_")
    if temperature is None:
        temp = "Tdef"
    elif temperature == 0.0:
        temp = "T00"
    elif temperature == 0.7:
        temp = "T07"
    else:
        raise ValueError(f"temperature {temperature} is not in the expansion grid")
    if not 0 <= run_index <= 99:
        raise ValueError(f"run_index {run_index} does not fit r{{run:02d}}")
    value = f"{slug}__{task}__{temp}__r{run_index:02d}"
    if not _CUSTOM_ID.fullmatch(value):
        raise ValueError(f"custom_id {value!r} has characters the Batch API rejects")
    return value


def _openai_messages(user_prompt: str) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _anthropic_messages(user_prompt: str) -> List[Dict[str, str]]:
    return [{"role": "user", "content": user_prompt}]


def _reject_sampling_keys(payload: Dict[str, Any], forbidden: Sequence[str]) -> None:
    found = [key for key in forbidden if key in payload]
    if found:
        raise ValueError(f"sampling keys not allowed on this model: {found}")
    if "seed" in payload:
        raise ValueError("expansion requests must not set seed")


def haiku_request(task_id: str, prompt: str, temperature: float, run_index: int) -> Dict[str, Any]:
    if temperature not in TEMPERATURES:
        raise ValueError("Haiku 4.5 uses only T=0.0 and T=0.7")
    params = {
        "model": HAIKU_MODEL,
        "max_tokens": FROZEN_MAX_TOKENS,
        "temperature": temperature,
        "system": SYSTEM_PROMPT,
        "messages": _anthropic_messages(render_user_prompt(prompt)),
    }
    _reject_sampling_keys(params, ("top_p", "top_k", "thinking"))
    return {
        "custom_id": custom_id(SLUGS[HAIKU_MODEL], task_id, temperature, run_index),
        "params": params,
    }


def luna_request(task_id: str, prompt: str, temperature: float, run_index: int) -> Dict[str, Any]:
    if temperature not in TEMPERATURES:
        raise ValueError("GPT-6 Luna uses only T=0.0 and T=0.7")
    body = {
        "model": LUNA_MODEL,
        "temperature": temperature,
        "max_completion_tokens": FROZEN_MAX_TOKENS,
        "reasoning_effort": "none",
        "messages": _openai_messages(render_user_prompt(prompt)),
    }
    _reject_sampling_keys(body, ())
    return {
        "custom_id": custom_id(SLUGS[LUNA_MODEL], task_id, temperature, run_index),
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": body,
    }


def sonnet5_request(task_id: str, prompt: str, run_index: int) -> Dict[str, Any]:
    params = {
        "model": SONNET5_MODEL,
        "max_tokens": SONNET5_MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "messages": _anthropic_messages(render_user_prompt(prompt)),
    }
    _reject_sampling_keys(params, ("temperature", "top_p", "top_k"))
    return {
        "custom_id": custom_id(SLUGS[SONNET5_MODEL], task_id, None, run_index),
        "params": params,
    }


def iter_batch_requests(
    problems: Iterable[Dict[str, Any]],
    *,
    n: int = N_FULL,
) -> Dict[str, List[Dict[str, Any]]]:
    """One list per batch. Five batches: haiku×2, luna×2, sonnet5×1."""
    if n < 1:
        raise ValueError("n must be >= 1")
    rows = list(problems)
    batches: Dict[str, List[Dict[str, Any]]] = {
        "haiku45_T00": [],
        "haiku45_T07": [],
        "luna_T00": [],
        "luna_T07": [],
        "sonnet5_default": [],
    }
    for problem in rows:
        task_id = str(problem["task_id"])
        prompt = str(problem["prompt"])
        for run_index in range(n):
            batches["haiku45_T00"].append(haiku_request(task_id, prompt, 0.0, run_index))
            batches["haiku45_T07"].append(haiku_request(task_id, prompt, 0.7, run_index))
            batches["luna_T00"].append(luna_request(task_id, prompt, 0.0, run_index))
            batches["luna_T07"].append(luna_request(task_id, prompt, 0.7, run_index))
            batches["sonnet5_default"].append(sonnet5_request(task_id, prompt, run_index))
    return batches


def write_batch_requests(problems: Sequence[Dict[str, Any]], out_dir: Path, *, n: int = N_FULL) -> Path:
    """Write the five batch JSONL files. No network."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    batches = iter_batch_requests(problems, n=n)
    for name, requests in batches.items():
        path = out_dir / f"{name}.jsonl"
        lines = [json.dumps(item, ensure_ascii=False) for item in requests]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    note = {
        "frozen_overlay_api_mode": "synchronous",
        "frozen_models": list(MANIFEST["models"]),
        "expansion_api_mode": "batch",
        "luna_model_string": LUNA_MODEL,
        "luna_snapshot": LUNA_SNAPSHOT_NOTE,
        "assistant_prefill": frozen_harness_prefills(),
        "n_tasks": len(problems),
        "n": n,
        "n_requests": {name: len(rows) for name, rows in batches.items()},
        "batches": 5,
    }
    (out_dir / "batch_build_note.json").write_text(
        json.dumps(note, indent=2) + "\n", encoding="utf-8"
    )
    return out_dir
