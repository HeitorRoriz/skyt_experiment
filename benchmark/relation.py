"""Canonical-form fingerprint. This is the benchmark's sameness relation.

Two programs are the same iff their fingerprints are identical. The other
SKYT properties are not part of identity. Unparseable code has no fingerprint
and can never certify.
"""

from __future__ import annotations

import ast
import copy
import hashlib
from typing import Optional, Set, Tuple


RELATION_VERSION = 2
RELATION_VERSION_NOTE = (
    "canonical-form fingerprint; docstrings stripped; "
    "scope-aware alpha-renaming of bound names only"
)


def strip_docstrings(tree: ast.AST) -> ast.AST:
    """Drop the leading string expression from every definition body."""
    for node in ast.walk(tree):
        if not isinstance(
            node,
            (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            node.body = body[1:] or [ast.Pass()]
    return tree


def collect_bound_names(tree: ast.AST) -> Set[str]:
    """Names bound locally, excluding function and class definition names."""
    bound: Set[str] = set()
    definitions: Set[str] = set()

    def bind_target(node: ast.AST) -> None:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name):
                bound.add(sub.id)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions.add(node.name)
            args = node.args
            for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
                bound.add(arg.arg)
            if args.vararg:
                bound.add(args.vararg.arg)
            if args.kwarg:
                bound.add(args.kwarg.arg)
        elif isinstance(node, ast.ClassDef):
            definitions.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                bind_target(target)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            bind_target(node.target)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            bind_target(node.target)
        elif isinstance(node, ast.comprehension):
            bind_target(node.target)
        elif isinstance(node, ast.withitem):
            if node.optional_vars is not None:
                bind_target(node.optional_vars)
        elif isinstance(node, ast.ExceptHandler):
            if node.name:
                bound.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound.add(alias.asname or alias.name.split(".")[0])

    return bound - definitions


def alpha_rename(tree: ast.AST) -> ast.AST:
    """Rename bound locals/params. Free names and definition names stay."""
    tree = copy.deepcopy(tree)
    bound_names = collect_bound_names(tree)

    class AlphaRenamer(ast.NodeTransformer):
        def __init__(self) -> None:
            self.var_map = {}
            self.counter = 0
            self.param_names: Set[str] = set()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
            for arg in node.args.args:
                if arg.arg not in self.var_map:
                    self.var_map[arg.arg] = f"p{len(self.param_names)}"
                    self.param_names.add(arg.arg)
            self.generic_visit(node)
            for arg in node.args.args:
                if arg.arg in self.var_map:
                    arg.arg = self.var_map[arg.arg]
            return node

        def visit_Name(self, node: ast.Name) -> ast.Name:
            if node.id in bound_names:
                if node.id not in self.var_map:
                    self.var_map[node.id] = f"v{self.counter}"
                    self.counter += 1
                node.id = self.var_map[node.id]
            return node

    return AlphaRenamer().visit(tree)


def canonicalize(
    tree: ast.AST,
    *,
    flexible_naming: bool = True,
) -> Tuple[ast.AST, str]:
    """Strip docstrings; optionally α-rename; unparse so tree and source agree."""
    tree = strip_docstrings(tree)
    if flexible_naming:
        tree = alpha_rename(tree)
    try:
        code = ast.unparse(ast.fix_missing_locations(tree))
        tree = ast.parse(code)
    except Exception:
        code = ""
    return tree, code


def fingerprint(code: str, *, flexible_naming: bool = True) -> Optional[str]:
    """Stable hash of the canonical tree, or None if the code does not parse."""
    if not (code or "").strip():
        return None
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    tree, _ = canonicalize(tree, flexible_naming=flexible_naming)
    dumped = ast.dump(tree, annotate_fields=False)
    return hashlib.md5(dumped.encode()).hexdigest()


def same(
    left: str,
    right: str,
    *,
    flexible_naming: bool = True,
) -> bool:
    """True iff both parse and their canonical fingerprints match."""
    a = fingerprint(left, flexible_naming=flexible_naming)
    b = fingerprint(right, flexible_naming=flexible_naming)
    return a is not None and a == b
