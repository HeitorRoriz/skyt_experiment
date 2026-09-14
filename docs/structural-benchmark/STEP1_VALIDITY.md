# Step 1 — validating the sameness relation

Date: 2026-09-14. Recomputed after the extractor canonicalize step landed.

Two corpora, pre-repair only (the population measure):

- **HumanEval+ 30-task pilot** (`outputs/humaneval_plus/pilot/`), 120 configs,
  N=10, flexible naming.
- **MSR/SBES contract corpus** (`outputs/`), 220 configs, N=20. Every contract
  declares `naming_policy: "strict"`.

Read-only analysis writes only to `outputs/validity/` (gitignored). Historical
trees are not overwritten. Reproduce:

```
python -m pytest tests/test_structural_validity.py
python -m benchmarks.structural_validity.metamorphic
python -m benchmarks.structural_validity.ablation
python -m benchmarks.structural_validity.audit
python -m benchmarks.structural_validity.contract_corpus
```

---

## Spec calls (settled this session)

| Edit | Call | Relation today |
| --- | --- | --- |
| Docstring reworded or removed | **same program** | distance 0 |
| Two independent statements swapped | **different program** | distance > 0 |
| Dead binding or bare `pass` inserted | **different program** | distance > 0 |

Whitespace, comments, line reflow, and bound-identifier renames under flexible
naming are also **same**. Algorithm / control-flow / builtin-call changes are
**different**.

Those cases are regression-tested in `tests/test_structural_validity.py`
(22 passed).

---

## Headline

**The 14-property distance is, empirically, a one-property relation: the AST
fingerprint of a canonical tree.** On both corpora, 13 of 14 properties are
inert and `ast_only` equals `all14` to full precision. Zero binding pairs
(AST agrees, full relation disagrees). Zero false merges on certified
distance-0 pairs. Zero transitivity violations.

The other 13 properties still *describe* how two programs differ when they
differ (see the metamorphic `DIFFERENT` rows). They never change a same/different
verdict on the stored data.

Three extractor defects found in the pre-fix pass were closed in
`src/foundational_properties.py` (`_canonicalize`): identifier leakage through
`data_dependency_graph` / `function_contracts`, docstring text in `ast.dump`,
and free-name collapse of non-allowlisted builtins. Details in
`PROPOSED_EXTRACTOR_FIX.md`. Contract-corpus headlines did not move; HumanEval+
did.

---

## Current numbers (post-fix)

| Corpus / measure | Published (pre-fix) | Recomputed now |
| --- | --- | --- |
| HumanEval+ pairwise, end-to-end | 56.9% | **62.19%** |
| HumanEval+ pairwise, certified | 67.4% | **73.69%** |
| HumanEval+ binding pairs | 209 | **0** |
| MSR raw pairwise, end-to-end | 61.0% | 60.99% |
| SBES raw pairwise, end-to-end | 67.5% | 67.53% |
| MSR / SBES binding, false merges, transitivity | — | **0 / 0 / 0** |

Dropping `normalized_ast_structure` is the only ablation that moves a headline
(HumanEval+ e2e 62.19% → 62.48%; SBES 67.53% → 69.80%; MSR 60.99% → 62.94%).
Dropping any of the other 13 properties changes nothing.

---

## 1A — Ablation

Distance zero under the full relation means every property agreed, so a pair
matches under a variant exactly when that variant's properties are all zero.

HumanEval+: 4,279 certified pairs. AST fingerprint agrees on 3,358 of them;
**0** of those are split by any other property.

Contract corpus: 13 inert properties in both scopes. `ast_only` equals `all14`
exactly.

---

## 1B — Metamorphic suite

22 settled cases, **0 failures**.

SAME (must be distance 0): blank lines, indentation width, comments, trailing
newlines, expression reflow, loop/parameter/assigned-local rename, docstring
reworded, docstring removed.

DIFFERENT (must be distance > 0): recursion rewrite, comprehension rewrite,
different loop bound, sieve, `all`→`any`, `sorted`→`reversed`, `max`→`min`,
inverted control flow, independent statements swapped, dead binding, bare
`pass`.

Pre-fix, seven of these failed (identifier leak, docstring leak, builtin
collapse). They are now regression guards.

---

## 1C — False merges on stored data

**Zero** on both corpora. HumanEval+: 0 of 3,358 certified distance-0 pairs
have differing free-name sequences. Contract corpus: 0 of 25,435 (MSR) / 0 of
23,096 (SBES).

The constructed `all`/`any` collapse from the pre-fix extractor does not fire
on certified data: both sides of a pair have to pass the same tests, and
strict naming on the contract corpus never consults the renamer.

---

## 1D — Transitivity

**Zero violations** across certified triples in all 340 configs. Distance 0 is
an equivalence relation on this data, so modal mass is well defined. The guard
inside `equivalence_classes` never fires.

---

## What this does *not* settle

- Human agreement (Phase 5). Distance 0 is canonical-form identity, not
  "same algorithm" as a person would say it.
- Multi-file / non-Python extractors.
- Held-out rewrite evaluation of SKYT (a tool question, not a ruler question).
- Metric names (`same@2` vs current wording) and a single *N* (SPEC.md OPEN 1
  and OPEN 3).

**Settled:** the public definition of sameness is the canonical-form
fingerprint. The 14-property list describes *how* two forms differ; it is not
the identity test. The current FSE draft still says "14-property distance of
0"; that sentence needs a rewrite before camera-ready, but it is not a new
experiment.
