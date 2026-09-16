"""Independent sameness bits. None of these is written into ``same()``."""

from __future__ import annotations

import ast
import hashlib
from typing import Any, Dict, Optional

from benchmark.relation import alpha_rename, fingerprint, same
from benchmark.discriminant.ted import ted_and_size


# Near-miss clone (Type-3) cutoff. Roy/Cordy-style "a bit of edit".
# Not fitted to same@2 headlines. Change it only with a version bump.
TYPE3_TED_RATIO = 0.30
JUDGE_VERSION = 1


def _md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def parse_ok(code: str) -> bool:
    try:
        ast.parse(code or "")
        return True
    except SyntaxError:
        return False


def string_eq(a: str, b: str) -> bool:
    return a == b


def parse_unparse_eq(a: str, b: str) -> Optional[bool]:
    """Type-1-ish: parser drops comments and formatting."""
    try:
        left = ast.unparse(ast.parse(a))
        right = ast.unparse(ast.parse(b))
    except (SyntaxError, Exception):
        return None
    return left == right


def raw_ast_hash(code: str) -> Optional[str]:
    """ast.dump of the raw tree: names and docstrings still count."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    return _md5(ast.dump(tree, annotate_fields=False))


def raw_ast_eq(a: str, b: str) -> Optional[bool]:
    left, right = raw_ast_hash(a), raw_ast_hash(b)
    if left is None or right is None:
        return None
    return left == right


def type2_hash(code: str) -> Optional[str]:
    """Type-2-ish: α-rename bound names, keep docstrings."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    tree = alpha_rename(tree)
    try:
        tree = ast.parse(ast.unparse(ast.fix_missing_locations(tree)))
    except Exception:
        pass
    return _md5(ast.dump(tree, annotate_fields=False))


def type2_eq(a: str, b: str) -> Optional[bool]:
    left, right = type2_hash(a), type2_hash(b)
    if left is None or right is None:
        return None
    return left == right


def fingerprint_eq(a: str, b: str, *, flexible_naming: bool = True) -> Optional[bool]:
    if not parse_ok(a) or not parse_ok(b):
        return None
    return same(a, b, flexible_naming=flexible_naming)


def ted_zero(a: str, b: str) -> Optional[bool]:
    packed = ted_and_size(a, b)
    if packed is None:
        return None
    distance, _, _ = packed
    return distance == 0


def type3_near(a: str, b: str, *, ratio: float = TYPE3_TED_RATIO) -> Optional[bool]:
    packed = ted_and_size(a, b)
    if packed is None:
        return None
    distance, size_a, size_b = packed
    denom = max(size_a, size_b)
    if denom <= 0:
        return None
    return (distance / denom) < ratio


JUDGE_ORDER = (
    "string_eq",
    "parse_unparse_eq",
    "raw_ast_eq",
    "type2_eq",
    "ted_zero",
    "type3_near",
    "fingerprint_eq",
)


def judge_pair(a: str, b: str, *, flexible_naming: bool = True) -> Dict[str, Any]:
    packed = ted_and_size(a, b)
    ted = None if packed is None else packed[0]
    size_a = None if packed is None else packed[1]
    size_b = None if packed is None else packed[2]
    denom = max(size_a or 0, size_b or 0)
    ted_ratio = None if ted is None or denom <= 0 else ted / denom
    return {
        "string_eq": string_eq(a, b),
        "parse_unparse_eq": parse_unparse_eq(a, b),
        "raw_ast_eq": raw_ast_eq(a, b),
        "type2_eq": type2_eq(a, b),
        "ted_zero": None if ted is None else ted == 0,
        "type3_near": None if ted_ratio is None else ted_ratio < TYPE3_TED_RATIO,
        "fingerprint_eq": fingerprint_eq(a, b, flexible_naming=flexible_naming),
        "ted": ted,
        "ted_ratio": ted_ratio,
        "size_a": size_a,
        "size_b": size_b,
        "fp_a": fingerprint(a, flexible_naming=flexible_naming),
        "fp_b": fingerprint(b, flexible_naming=flexible_naming),
    }


def classify_cell(verdict: Dict[str, Any]) -> str:
    """Cheap tag for appendix rows. Not a human label."""
    tape = verdict.get("fingerprint_eq")
    if tape is None:
        return "unparseable"
    if tape and verdict.get("string_eq"):
        return "identical_text"
    if tape and verdict.get("parse_unparse_eq") and not verdict.get("string_eq"):
        return "formatting"
    if tape and verdict.get("type2_eq") and not verdict.get("raw_ast_eq"):
        return "bound_rename"
    if tape and not verdict.get("type2_eq"):
        return "docstring_or_prose"
    if (not tape) and verdict.get("type3_near"):
        return "type3_near_miss"
    if (not tape) and verdict.get("raw_ast_eq"):
        return "raw_ast_agrees_tape_differs"
    if not tape:
        return "structurally_different"
    return "other_tape_same"
