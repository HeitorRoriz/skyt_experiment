# Extractor fix — applied

Date: 2026-09-14. Status: **applied**, Option A, approved by Heitor in
conversation on 2026-09-14 under the architecture-freeze rule.

The change was first measured as a subclass, then landed in
`src/foundational_properties.py` as a new `_canonicalize` step plus
`_strip_docstrings` and `_collect_bound_names` helpers. The measurement subclass
has been removed now that the behavior is the default; the numbers it produced
are preserved below.

Verification after landing:

- All 22 settled metamorphic cases pass (`tests/test_structural_validity.py`),
  up from 15 passing and 7 xfailed.
- Contract corpus is **bit-identical** to before: SBES 67.53% / 68.86%, MSR
  60.99% / 66.48%.
- HumanEval+ moves to 62.19% e2e / 73.69% certified, and now has **zero**
  binding pairs: the relation is exactly the AST fingerprint on both corpora.
- Full suite: 132 passed, 3 pre-existing failures unrelated to this change
  (a relative-import bug in `src/transformations/property_driven_transformer.py`).

## Measured impact

Each part switched on independently, then all together. Task-mean for
HumanEval+, contract-mean for the contract corpus.

| Variant | HumanEval+ e2e | certified | Contract corpus e2e | certified |
| --- | --- | --- | --- | --- |
| Baseline (frozen) | 56.93% | 67.41% | 60.99% | 66.48% |
| + consistent naming | 60.80% (+3.87) | 72.00% | 60.99% (+0.00) | 66.48% |
| + strip docstrings | 58.31% (+1.39) | 69.10% | 60.99% (+0.00) | 66.48% |
| + scope-aware renamer | 56.93% (+0.00) | 67.41% | 60.99% (+0.00) | 66.48% |
| **All three** | **62.19% (+5.26)** | **73.69%** | **60.99% (+0.00)** | **66.48%** |

Two things to read off this table.

**The contract corpus does not move at all.** Every MSR/SBES contract declares
`naming_policy: "strict"`, so the policy branch never fires and raw identifiers
are the correct comparison. The published MSR and SBES numbers are unaffected by
all three parts. Only the HumanEval+ / FSE arm shifts.

**The scope-aware renamer changes no number.** It closes the false-merge hole
that never fired on certified data (see `STEP1_VALIDITY.md`, 1C). It is a
soundness fix, not a numbers fix.

Under the candidate fix all 22 settled metamorphic cases pass, versus 7 failures
today.

## Part 1 — apply the naming policy once, at extraction

Today `_should_use_alpha_renaming` is consulted in exactly one branch of
`_calculate_property_distance`, the one for `normalized_ast_structure`.
`data_dependency_graph` keys its dict on raw `target.id` / `node.id`, and
`function_contracts` stores raw `arg.arg`, so both treat identifier choice as
structure even when the contract says names are flexible.

Two ways to fix it.

### Option A — normalize the tree before extracting (what the table measures)

```python
def extract_all_properties(self, code: str) -> Dict[str, Any]:
    tree = ast.parse(code)
    if self._should_use_alpha_renaming(self.contract):
        tree = self._alpha_rename_ast(tree)
    # ... every property is then extracted from `tree`
```

One decision point, applied once, and every property inherits it. This is what
I measured.

The cost: extracted property dictionaries change meaning, so any *persisted*
property dict compared against a freshly extracted one would be comparing
different conventions. In practice the affected field is
`canon_data.foundational_properties` in historical `outputs/*.json`. Properties
are derived data and recomputable from the stored code, and Gate 0 already
recomputes them, so this is a re-derivation rather than a data loss. Raw
generations are never touched.

### Option B — store both conventions per property, choose at compare time

Mirrors the existing `ast_hash` / `alpha_renamed_hash` pattern, which is already
approved precedent:

```python
# in _extract_data_dependency_graph
return {
    "dependencies": {k: sorted(v) for k, v in dependencies.items()},
    "assignments": assignments,
    "alpha_dependencies": {...},   # extracted from the alpha-renamed tree
    "alpha_assignments": {...},
}

# in _calculate_property_distance
elif prop_name == "data_dependency_graph":
    if self._should_use_alpha_renaming(contract):
        prop1 = prop1.get("alpha_dependencies", prop1["dependencies"])
        prop2 = prop2.get("alpha_dependencies", prop2["dependencies"])
```

Legacy artifacts lack the new keys and fall back to current behavior, exactly as
`alpha_renamed_hash` already falls back to `ast_hash`. Nothing needs
re-deriving.

The cost: two conventions per property, and it does not extend cleanly to Part 2
(docstring stripping changes `ast_hash` *and* `statement_ordering`, so the
variant count grows).

**Recommendation: Option A**, on the grounds that properties are derived and
recomputable, and that one decision point is much easier to defend in a paper
than a per-property convention table. But this is the call that needs your
approval, since it is the one with a migration step.

## Part 2 — strip docstrings before extraction

`ast.dump` captures docstring text, so rewording prose changes the fingerprint
(d=0.0714) and deleting it changes two properties (d=0.1190, because
`statement_ordering` counts the docstring as a statement). That contradicts the
2026-09-14 decision that prose inside a function is not part of the form.

```python
def _strip_docstrings(tree: ast.AST) -> ast.AST:
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            node.body = body[1:] or [ast.Pass()]
    return tree
```

A body consisting only of a docstring becomes `pass`, which is what it already
means operationally. Worth noting this is a definitional change, so it must be
disclosed as such rather than presented as a bug fix: +1.39pp on HumanEval+.

## Part 3 — replace the seven-name allowlist with scope analysis

`_alpha_rename_ast` currently preserves exactly seven names:

```python
if node.id not in ['range', 'len', 'print', 'max', 'min', 'sum', 'abs']:
```

Every other global is renamed to `v0, v1, ...` like a local, so `all(...)` and
`any(...)`, and `sorted(...)` and `reversed(...)`, collapse onto identical
fingerprints at **distance exactly 0**. The `max`/`min` case separates only
because both happen to be on the list.

The fix is to rename only names that are *bound* somewhere in the module, and
leave free names alone. Free names are globals, builtins and imported callables,
and they carry meaning:

```python
collector = _BoundNames()          # collects params, assign/for/comprehension
collector.visit(tree)              # targets, with/except names, imports, defs
names_to_rename = set(collector.bound)
for node in ast.walk(tree):        # definition names stay: contract surface
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        names_to_rename.discard(node.name)
return _ScopeAwareRenamer(names_to_rename).visit(tree)
```

`_BoundNames` and `_ScopeAwareRenamer` are already written and exercised in
`benchmarks/structural_validity/`. This part changes no published number; it
removes an unsoundness that the oracle happened to screen on both corpora.

## What landed

```
src/foundational_properties.py
  extract_all_properties   + tree, code = self._canonicalize(tree, code)
  _canonicalize            new: strip docstrings, then apply naming policy
  _strip_docstrings        new
  _collect_bound_names     new
  _alpha_rename_ast        allowlist -> `if node.id in bound_names`
```

Two existing tests in `tests/test_repeatability_protocol.py` hardcoded raw
identifier names and were updated to preserve their intent rather than their
literals: the hash-seed stability test now uses a strict-naming contract so the
source identifiers survive, and the serialization-order test looks the
dependency key up instead of naming it.

## Migration hazard to remember

Property dictionaries extracted *before* this change are not comparable to
freshly extracted ones under a **flexible** policy: the old dicts carry raw
identifiers, and their `alpha_renamed_hash` was produced by the seven-name
allowlist. Two consequences:

- **Contract corpus: no impact.** All 15 contracts are strict, and the numbers
  were verified bit-identical after the change.
- **HumanEval+: recompute, do not compare across versions.** `table1.py` and
  `table2.py` re-extract from the stored generations, so they are fine. Any
  persisted canon property dict under `outputs/humaneval_plus/pilot_skyt/` is
  stale and must not be compared against fresh extraction.

Raw generations are never touched by any of this.
