"""Memoize SKYT repair by (candidate, canon). Inherit oracles without Docker.

Does not change Certified Consensus pick. Used by held-out robustness replay
so extra splits and fingerprint POST can run with 0 LLM calls and, when the
repaired entry point matches a stored program, 0 new Docker evaluations.
"""

from __future__ import annotations

import ast
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

from benchmark.relation import fingerprint
from benchmarks.humaneval_plus.provenance import sha256_text
from skyt.humaneval_repair import CachedPlusOracle, _oracle_payload
from skyt.zero_api_analysis import ast_normalized_id


class UnresolvedOracle(RuntimeError):
    """Repaired code did not match a stored program and Docker is disabled."""


def entry_function_dump(code: str, entry_point: str) -> Optional[str]:
    if not entry_point or not (code or "").strip():
        return None
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == entry_point:
            return ast.dump(node, annotate_fields=False)
    return None


def _source_variants(code: str) -> list[str]:
    variants = [code or ""]
    try:
        tree = ast.parse(code or "")
    except (SyntaxError, ValueError):
        return variants
    try:
        import astor

        variants.append(astor.to_source(tree))
    except Exception:
        pass
    try:
        variants.append(ast.unparse(tree))
    except Exception:
        pass
    seen = set()
    out = []
    for item in variants:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def inherit_keys(code: str, entry_point: str) -> list[str]:
    keys: list[str] = []
    seen = set()
    for variant in _source_variants(code):
        candidates = [
            f"sha:{sha256_text(variant)}",
            f"fp:{fingerprint(variant, flexible_naming=True)}",
            f"ast:{ast_normalized_id(variant)}",
            f"entry:{entry_function_dump(variant, entry_point)}",
        ]
        for key in candidates:
            if not key or key.endswith(":None") or key.endswith(":"):
                continue
            if key in seen:
                continue
            seen.add(key)
            keys.append(key)
    return keys


class InheritPlusOracle:
    """Hash / AST / fingerprint / entry-point inherit, then optional Docker."""

    def __init__(
        self,
        problem: Dict[str, Any],
        *,
        allow_docker: bool = False,
        inner: Optional[CachedPlusOracle] = None,
    ):
        self.problem = problem
        self.entry_point = str(problem.get("entry_point") or "")
        self.allow_docker = bool(allow_docker)
        self.inner = inner if inner is not None else CachedPlusOracle(problem)
        self.table: Dict[str, Dict[str, Any]] = {}
        self.canon_code: Optional[str] = None
        self.canon_payload: Optional[Dict[str, Any]] = None
        self.n_hits = 0
        self.n_misses = 0
        self.n_unresolved = 0

    def index_payload(self, code: str, payload: Dict[str, Any]) -> None:
        stored = dict(payload)
        for key in inherit_keys(code, self.entry_point):
            self.table.setdefault(key, stored)

    def seed_from_record(self, code: str, record: Dict[str, Any]) -> None:
        payload = _oracle_payload(record)
        self.index_payload(code, payload)
        self.inner.seed_from_record(code, record)

    def bind_canon(self, code: str, payload: Dict[str, Any]) -> None:
        self.canon_code = code
        self.canon_payload = dict(payload)
        self.index_payload(code, payload)

    def _lookup(self, code: str) -> Optional[Dict[str, Any]]:
        for key in inherit_keys(code, self.entry_point):
            hit = self.table.get(key)
            if hit is not None:
                return dict(hit)
        if self.canon_code and self.canon_payload and self.entry_point:
            cand = entry_function_dump(code, self.entry_point)
            canon = entry_function_dump(self.canon_code, self.entry_point)
            if cand and canon and cand == canon:
                return dict(self.canon_payload)
        return None

    def run_oracle_tests(
        self, code: str, contract: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        sha_key = f"sha:{sha256_text(code or '')}"
        hit = self.table.get(sha_key)
        if hit is not None:
            self.n_hits += 1
            return dict(hit)
        dump = entry_function_dump(code, self.entry_point)
        if dump:
            hit = self.table.get(f"entry:{dump}")
            if hit is not None:
                self.table[sha_key] = hit
                self.n_hits += 1
                return dict(hit)
        if (
            dump
            and self.canon_code
            and self.canon_payload
            and dump == entry_function_dump(self.canon_code, self.entry_point)
        ):
            self.table[sha_key] = dict(self.canon_payload)
            self.n_hits += 1
            return dict(self.canon_payload)
        if self.allow_docker:
            self.n_misses += 1
            payload = self.inner.run_oracle_tests(code, contract)
            self.index_payload(code, payload)
            return dict(payload)
        self.n_unresolved += 1
        return {
            "passed": False,
            "pass_rate": 0.0,
            "base_passed": False,
            "plus_passed": False,
            "certified": False,
        }


def preindex_level3(
    oracle: InheritPlusOracle,
    records: list,
    canon_code: str,
    contract: Dict[str, Any],
    payload: Dict[str, Any],
) -> int:
    """Index Level-3 substitution outputs so later transformer oracle calls hit."""
    from src.transformations.convert_to_simple_algorithm import (
        convert_to_simple_algorithm,
    )

    n_indexed = 0
    for record in records:
        result = convert_to_simple_algorithm(
            record.get("stitched_code") or "", canon_code, contract
        )
        code = result.get("transformed_code")
        if result.get("success") and code:
            oracle.index_payload(code, payload)
            n_indexed += 1
    return n_indexed


class RepairMemo:
    """Disk-backed (candidate_sha, canon_sha) -> repair result."""

    def __init__(self, path: Path):
        self.path = path
        self.rows: Dict[str, Dict[str, Any]] = {}
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.rows = dict(raw.get("rows") or {})

    @staticmethod
    def key(candidate: str, canon: str) -> str:
        return f"{sha256_text(candidate)}|{sha256_text(canon)}"

    def get(self, candidate: str, canon: str) -> Optional[Dict[str, Any]]:
        return deepcopy(self.rows.get(self.key(candidate, canon)))

    def put(self, candidate: str, canon: str, payload: Dict[str, Any]) -> None:
        self.rows[self.key(candidate, canon)] = deepcopy(payload)

    def flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"schema": "skyt-repair-memo-v1", "rows": self.rows}, indent=2),
            encoding="utf-8",
        )
