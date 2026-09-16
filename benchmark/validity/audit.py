"""Real-data audit of the sameness relation (Steps 1C and 1D).

Read-only. Three checks over the stored HumanEval+ generations:

**False merges (1C).** For each distance-0 certified pair we compare the
sequence of **free** names (names used but never bound locally — globals,
builtins, imported modules). If those sequences differ, the relation merged
two programs that call different functions: a mechanically certain false
merge, no manual labeling required. After the 2026-09-14 extractor fix the
α-renamer only rewrites *bound* names, so free names are preserved. This
check still runs as a regression probe.

**Naming leaks (1B bridge).** ``data_dependency_graph`` keys on raw assigned
variable names and ``function_contracts`` stores raw parameter names, and
neither consults the naming policy. For every *binding* pair (α-renamed ASTs
agree, full relation still says different) we re-extract those two properties
from the α-renamed trees. If they then agree, the split was pure identifier
noise that the declared policy says to ignore.

**Transitivity (1D).** "Distance 0" must be an equivalence relation for modal
mass and equivalence classes to be well defined. We check every certified
triple directly rather than trusting the guard in the protocol.

Usage:
    python -m benchmarks.structural_validity.audit
"""

from __future__ import annotations

import argparse
import ast
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from src.foundational_properties import FoundationalProperties

from .ablation import (
    AST_PROP,
    DEFAULT_OUT,
    DEFAULT_SOURCE,
    HE_CONTRACT,
    certified_flag,
    config_identity,
    load_records,
)

LEAK_PROPS = ("data_dependency_graph", "function_contracts")


class _BoundNames(ast.NodeVisitor):
    """Collect every name bound somewhere in the module."""

    def __init__(self) -> None:
        self.bound: Set[str] = set()

    def _bind_target(self, node: ast.AST) -> None:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name):
                self.bound.add(sub.id)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.bound.add(node.name)
        args = node.args
        for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
            self.bound.add(arg.arg)
        if args.vararg:
            self.bound.add(args.vararg.arg)
        if args.kwarg:
            self.bound.add(args.kwarg.arg)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.bound.add(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._bind_target(target)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._bind_target(node.target)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._bind_target(node.target)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self._bind_target(node.target)
        self.generic_visit(node)

    visit_AsyncFor = visit_For  # type: ignore[assignment]

    def visit_comprehension(self, node: ast.comprehension) -> None:
        self._bind_target(node.target)
        self.generic_visit(node)

    def visit_withitem(self, node: ast.withitem) -> None:
        if node.optional_vars is not None:
            self._bind_target(node.optional_vars)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self.bound.add(node.name)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.bound.add(alias.asname or alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.bound.add(alias.asname or alias.name)
        self.generic_visit(node)


def free_name_sequence(code: str) -> Optional[List[str]]:
    """Names used but never bound locally, in AST traversal order.

    These are the globals, builtins and imported callables. Local identifiers
    are excluded on purpose: the naming policy says those may differ freely.
    Every free name is kept, including builtins: after the extractor fix they
    are part of the form.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    collector = _BoundNames()
    collector.visit(tree)

    sequence: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in collector.bound:
                continue
            sequence.append(node.id)
        elif isinstance(node, ast.Attribute):
            sequence.append(f".{node.attr}")
    return sorted(sequence)


def alpha_reextract(
    extractor: FoundationalProperties, code: str
) -> Optional[Dict[str, Any]]:
    """Re-extract the leaky properties from the α-renamed tree."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    renamed = extractor._alpha_rename_ast(tree)
    return {
        "data_dependency_graph": extractor._extract_data_dependency_graph(renamed, code),
        "function_contracts": extractor._extract_function_contracts(renamed, code),
    }


def audit_config(path: Path, extractor: FoundationalProperties) -> Optional[Dict[str, Any]]:
    records = load_records(path)
    if len(records) < 2:
        return None

    properties = list(extractor.properties)
    codes = [record.get("stitched_code") or "" for record in records]

    props: List[Optional[Dict[str, Any]]] = []
    for code in codes:
        extracted = extractor.extract_all_properties(code)
        props.append(
            FoundationalProperties.normalize_properties(extracted)
            if any(value is not None for value in extracted.values())
            else None
        )

    certified = [
        certified_flag(record) and props[index] is not None
        for index, record in enumerate(records)
    ]
    indices = [i for i, ok in enumerate(certified) if ok]

    zero_pairs: List[Tuple[int, int]] = []
    binding_pairs: List[Tuple[int, int, frozenset]] = []
    for i, j in itertools.combinations(indices, 2):
        nonzero = set()
        for name in properties:
            distance = extractor._calculate_property_distance(
                props[i].get(name), props[j].get(name), name, HE_CONTRACT
            )
            if distance > 1e-12:
                nonzero.add(name)
        if not nonzero:
            zero_pairs.append((i, j))
        elif AST_PROP not in nonzero:
            binding_pairs.append((i, j, frozenset(nonzero)))

    # 1C: distance-0 pairs whose free-name sequences disagree.
    free_names = {i: free_name_sequence(codes[i]) for i in indices}
    merges = []
    for i, j in zero_pairs:
        left, right = free_names[i], free_names[j]
        if left is None or right is None or left == right:
            continue
        merges.append(
            {
                "pair": [i, j],
                "free_names_a": left,
                "free_names_b": right,
                "only_in_a": sorted(set(left) - set(right)),
                "only_in_b": sorted(set(right) - set(left)),
                "code_a": codes[i],
                "code_b": codes[j],
            }
        )

    # 1B bridge: do binding splits survive consistent α-renaming?
    alpha_cache: Dict[int, Optional[Dict[str, Any]]] = {}
    leaks = {"naming_only": 0, "survives": 0, "by_property": Counter()}
    for i, j, nonzero in binding_pairs:
        for index in (i, j):
            if index not in alpha_cache:
                alpha_cache[index] = alpha_reextract(extractor, codes[index])
        left, right = alpha_cache[i], alpha_cache[j]
        if left is None or right is None:
            continue
        still_differs = set()
        for name in nonzero:
            if name not in LEAK_PROPS:
                still_differs.add(name)
                continue
            distance = extractor._calculate_property_distance(
                left[name], right[name], name, HE_CONTRACT
            )
            if distance > 1e-12:
                still_differs.add(name)
        if still_differs:
            leaks["survives"] += 1
            leaks["by_property"].update(still_differs)
        else:
            leaks["naming_only"] += 1

    # 1D: transitivity of the distance-0 relation among certified generations.
    zero_set = {frozenset(pair) for pair in zero_pairs}

    def is_zero(a: int, b: int) -> bool:
        return a == b or frozenset((a, b)) in zero_set

    violations = []
    for a, b, c in itertools.combinations(indices, 3):
        for x, y, z in ((a, b, c), (b, a, c), (a, c, b)):
            if is_zero(x, y) and is_zero(y, z) and not is_zero(x, z):
                violations.append([x, y, z])
                break

    return {
        **config_identity(path),
        "file": path.name,
        "n_certified": len(indices),
        "n_zero_pairs": len(zero_pairs),
        "n_binding_pairs": len(binding_pairs),
        "false_merges": merges,
        "leaks": {
            "naming_only": leaks["naming_only"],
            "survives": leaks["survives"],
            "by_property": dict(leaks["by_property"]),
        },
        "transitivity_violations": violations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--examples", type=int, default=6)
    args = parser.parse_args()

    extractor = FoundationalProperties(HE_CONTRACT)
    files = sorted(args.source_dir.glob("*.jsonl"))
    if not files:
        raise SystemExit(f"No .jsonl configs under {args.source_dir}")

    configs = [c for c in (audit_config(p, extractor) for p in files) if c]

    total_zero = sum(c["n_zero_pairs"] for c in configs)
    total_binding = sum(c["n_binding_pairs"] for c in configs)
    total_merges = sum(len(c["false_merges"]) for c in configs)
    naming_only = sum(c["leaks"]["naming_only"] for c in configs)
    survives = sum(c["leaks"]["survives"] for c in configs)
    survive_props: Counter = Counter()
    for config in configs:
        survive_props.update(config["leaks"]["by_property"])
    violations = sum(len(c["transitivity_violations"]) for c in configs)

    print(f"configs {len(configs)}")
    print()
    print("1C  false merges among certified distance-0 pairs")
    print(f"      distance-0 certified pairs      {total_zero}")
    print(f"      pairs with differing free names {total_merges}"
          f"  ({total_merges / total_zero:.2%})" if total_zero else "")
    merge_props: Counter = Counter()
    for config in configs:
        for merge in config["false_merges"]:
            merge_props.update(merge["only_in_a"] + merge["only_in_b"])
    if merge_props:
        print("      names involved:", ", ".join(
            f"{name}({count})" for name, count in merge_props.most_common(15)
        ))
    print()
    print("1B  binding splits re-checked under consistent alpha-renaming")
    print(f"      binding pairs                   {total_binding}")
    print(f"      pure identifier noise           {naming_only}")
    print(f"      real structural difference      {survives}")
    if survive_props:
        print("      surviving properties:", dict(survive_props.most_common()))
    print()
    print("1D  transitivity of the distance-0 relation")
    print(f"      violating certified triples     {violations}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / "audit.json"
    out_path.write_text(
        json.dumps(
            {
                "source_dir": str(args.source_dir),
                "totals": {
                    "zero_pairs": total_zero,
                    "binding_pairs": total_binding,
                    "false_merge_pairs": total_merges,
                    "binding_naming_only": naming_only,
                    "binding_survives": survives,
                    "binding_surviving_properties": dict(survive_props),
                    "transitivity_violations": violations,
                },
                "configs": configs,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print()
    print(f"wrote {out_path}")

    shown = 0
    for config in configs:
        for merge in config["false_merges"]:
            if shown >= args.examples:
                return
            shown += 1
            print()
            print(f"--- false merge {shown}: {config['file']} pair {merge['pair']} ---")
            print(f"    only in A: {merge['only_in_a']}    only in B: {merge['only_in_b']}")


if __name__ == "__main__":
    main()
