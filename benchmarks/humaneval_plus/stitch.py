"""Extract a completion and stitch it onto the HumanEval function prompt."""

from __future__ import annotations

import ast
import re
from typing import Any, Dict, Optional


_FENCE_PYTHON = re.compile(r"```(?:python)?\n(.*?)```", re.DOTALL)


def extract_completion(raw_text: str) -> str:
    """Take the first markdown fence if present, otherwise the raw text."""
    if not raw_text:
        return ""
    match = _FENCE_PYTHON.search(raw_text)
    if match:
        return match.group(1).strip("\n")
    return raw_text.strip("\n")


def _defines_entry_point(code: str, entry_point: str) -> bool:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == entry_point:
                return True
    return False


def stitch_solution(
    prompt: str,
    completion: str,
    entry_point: str,
) -> Dict[str, Any]:
    """Build an executable module from a prompt plus a model completion.

    HumanEval prompts already contain the function signature. Models may
    return only the body, a full function, or a fenced code block.
    """
    extracted = extract_completion(completion)
    prompt = prompt if prompt.endswith("\n") else prompt + "\n"
    candidates = []
    if extracted.strip():
        candidates.append(("standalone", extracted if extracted.endswith("\n") else extracted + "\n"))
        candidates.append(("prompt_plus_body", prompt + extracted + ("\n" if not extracted.endswith("\n") else "")))
    else:
        candidates.append(("empty_completion", prompt))

    chosen: Optional[Dict[str, Any]] = None
    for mode, code in candidates:
        parse_ok = True
        try:
            ast.parse(code)
        except SyntaxError:
            parse_ok = False
        has_entry = _defines_entry_point(code, entry_point) if parse_ok else False
        record = {
            "stitch_mode": mode,
            "stitched_code": code,
            "parse_ok": parse_ok,
            "has_entry_point": has_entry,
        }
        if parse_ok and has_entry:
            chosen = record
            break
        if chosen is None:
            chosen = record

    assert chosen is not None
    chosen["extracted_completion"] = extracted
    return chosen
