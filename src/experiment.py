from .config import OPENAI_API_KEY, MODEL, TEMPERATURE
from typing import Optional
from openai import OpenAI
import re
_client = None
def _get_client():
    global _client
    if _client is None:
        if not OPENAI_API_KEY: raise RuntimeError("OPENAI_API_KEY not set")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client
def _extract_code(text: str) -> str:
    """Extract first code block if fenced, otherwise strip stray fences/phrases."""
    if "```" in text:
        # Prefer ```python blocks, fallback to any fenced block
        m = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, flags=re.S|re.I)
        if not m:
            m = re.findall(r"```\s*\n(.*?)```", text, flags=re.S)
        if m:
            return m[0].strip()
    # Remove any standalone fence lines
    lines = [ln for ln in text.splitlines() if not ln.strip().startswith("```")]
    # Drop common lead-in phrases
    while lines and lines[0].strip().lower().startswith(("here is", "here's", "the code", "python")):
        lines.pop(0)
    return "\n".join(lines).strip()
def call_model(prompt: str, model: Optional[str]=None, temperature: Optional[float]=None) -> str:
    client = _get_client()
    m = model or MODEL
    t = TEMPERATURE if temperature is None else temperature
    resp = client.chat.completions.create(
        model=m,
        temperature=t,
        messages=[
            {"role": "system", "content": (
                "You are a Python coding assistant. Return only valid Python code without any markdown fences, "
                "comments explaining, or prose. Output a single self-contained function or script as appropriate."
            )},
            {"role": "user", "content": prompt},
        ],
    )
    content = (resp.choices[0].message.content or "").strip()
    return _extract_code(content)
