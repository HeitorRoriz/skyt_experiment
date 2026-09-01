"""Pinned prompt templates. Changing these after the pilot freeze requires a rerun."""

from __future__ import annotations

import hashlib

SYSTEM_PROMPT_ID = "humaneval-plus-complete-v1"
USER_PROMPT_ID = "humaneval-plus-user-v1"

SYSTEM_PROMPT = (
    "You are a Python code generator. Complete the given function. "
    "Output only Python code, with no explanation."
)

USER_PROMPT_TEMPLATE = "{prompt}"


def render_user_prompt(problem_prompt: str) -> str:
    return USER_PROMPT_TEMPLATE.format(prompt=problem_prompt)


def prompt_bundle_hash() -> str:
    payload = "\n".join(
        [
            SYSTEM_PROMPT_ID,
            SYSTEM_PROMPT,
            USER_PROMPT_ID,
            USER_PROMPT_TEMPLATE,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
