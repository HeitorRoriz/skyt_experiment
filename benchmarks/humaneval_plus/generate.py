"""Paid generation is opt-in. Default CLI refuses to spend API budget."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Tuple

from .prompts import SYSTEM_PROMPT, render_user_prompt


class ApiSpendBlocked(RuntimeError):
    """Raised unless the caller passes --allow-api."""


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _use_windows_certificate_store() -> None:
    """Use the OS trust store so corporate roots work (same class of fix as git schannel)."""
    try:
        import truststore
    except ImportError:
        return
    truststore.inject_into_ssl()


_INFRA_RETRY = {
    "RateLimitError",
    "APIConnectionError",
    "APITimeoutError",
    "InternalServerError",
    "ServiceUnavailableError",
}


def generate_completion(
    *,
    model: str,
    problem_prompt: str,
    temperature: float,
    max_tokens: int,
    allow_api: bool,
) -> Tuple[str, Dict[str, Any]]:
    if not allow_api:
        raise ApiSpendBlocked(
            "Refusing to call an LLM. Re-run with --allow-api after smoke tests pass."
        )
    _load_dotenv()
    _use_windows_certificate_store()
    user_prompt = render_user_prompt(problem_prompt)
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            if model.startswith("claude-"):
                text, usage = _anthropic(model, user_prompt, temperature, max_tokens)
            else:
                text, usage = _openai(model, user_prompt, temperature, max_tokens)
            usage = dict(usage)
            usage["attempts"] = attempt + 1
            return text, usage
        except Exception as exc:
            last_error = exc
            if type(exc).__name__ not in _INFRA_RETRY or attempt == 3:
                raise
            time.sleep(20 * (attempt + 1))
    assert last_error is not None
    raise last_error


def _openai(
    model: str, user_prompt: str, temperature: float, max_tokens: int
) -> Tuple[str, Dict[str, Any]]:
    import openai

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
    }
    if model.startswith("gpt-5") or model.startswith("o1"):
        kwargs["max_completion_tokens"] = max_tokens
    else:
        kwargs["max_tokens"] = max_tokens
    response = client.chat.completions.create(**kwargs)
    text = response.choices[0].message.content or ""
    usage = response.usage
    return text, {
        "provider": "openai",
        "id": getattr(response, "id", None),
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
    }


def _anthropic(
    model: str, user_prompt: str, temperature: float, max_tokens: int
) -> Tuple[str, Dict[str, Any]]:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = response.content[0].text if response.content else ""
    usage = getattr(response, "usage", None)
    return text, {
        "provider": "anthropic",
        "id": getattr(response, "id", None),
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
    }
