# Structural repeatability benchmark — specification

Draft, 2026-09-14. This is Step 2 (Phase 1) of
[`BENCHMARK_PLAN.md`](BENCHMARK_PLAN.md): write down the rules so a number
someone else reports is comparable to ours.

Every choice here is versioned. Items marked **OPEN** need a call before the
spec can be called v1.

---

## 1. What the benchmark measures

Given a task with a prompt and a test oracle, draw *N* independent generations.
The benchmark reports how often **two independent draws are the same program**,
not whether any single draw works.

This is an overlay. It ships no prompts and no tests; it borrows a task set and
adds a structural report. See `BENCHMARK_PLAN.md` §0.

## 2. Metric names and definitions

The recurring confusion in our own drafts was two metrics with different
denominators and no distinguishing names ("MEASURE 1" meant nothing to anyone).
Names must make the denominator visible.

Let the *N* draws for one task be \(g_1 \dots g_N\), let `cert(g)` be the
certification predicate (§4), and let `same(a, b)` be the sameness relation
(§3).

### Primary — `same@2`

> The probability that two independent draws both certify **and** are the same
> program.

\[
\texttt{same@2} = \Pr[\,\text{cert}(g_i) \wedge \text{cert}(g_j) \wedge \text{same}(g_i, g_j)\,]
\]

Estimated over all \(\binom{N}{2}\) pairs. **Non-certifying draws stay in the
denominator.** This is the headline: it prices both "does it work" and "is it
the same" in one number, so a model cannot win by being repeatably wrong.

Previously called "end-to-end pairwise exact-match", internally "MEASURE 1".

### Secondary — `same@2|cert`

> Given that both draws certify, the probability that they are the same program.

Denominator is certified pairs only. This isolates structural dispersion from
pass rate, and it is **undefined** for a task with fewer than two certified
draws — those tasks must be dropped from this column and the drop count
reported. Previously "certified pairwise exact-match".

### Reporting rules

- Both numbers are always reported together. Reporting `same@2|cert` alone is
  forbidden: it rises when the pass rate falls.
- Pairs share generations, so they are not independent binomial trials. These
  are U-statistics; intervals come from an **equal-cluster bootstrap over
  tasks**, never a binomial interval over pairs. Locked in code:
  [`STEP5_INFERENCE.md`](STEP5_INFERENCE.md) (schema v2, jackknife sensitivity,
  `pilot_grid` warning).
- Aggregate as task-mean (each task weighted equally), not pair-weighted.
- Report every denominator: tasks entering each column, and tasks dropped as
  undefined.

### Descriptive, not headline

`certified modal mass` (largest same-form class over *N*) and `canon stability`
are diagnostics. They depend on a canon choice, so they are policy evaluation
rather than a population measure. Match-to-human-reference is **not** a
benchmark metric; see non-goals.

**OPEN 1.** Are `same@2` / `same@2|cert` the names? They parallel `pass@k` and
put the denominator in the name. Alternatives considered: `rep@N` (reads as
"repeatability at N" but hides that it is pairwise), `SRR` (structural
repeatability rate — no parallel to existing usage).

## 3. The sameness relation

### 3.1 Definition

Two programs are the same iff their **canonical forms** are identical.

The canonical form is produced by `benchmark.relation.canonicalize`
(shared with `src/foundational_properties.py` so SKYT still sees the same
tree). Identity for the **benchmark** is fingerprint equality. SKYT still
averages 14 properties for the tool.

1. Parse to an AST. Unparseable code is *structurally invalid* and can never
   certify, but it stays in the `same@2` denominator.
2. Strip docstrings from every module, function and class body. A body that is
   only a docstring becomes `pass`.
3. If the task's naming policy is **flexible**, α-rename every *bound* name:
   parameters to `p0, p1, ...` and other bound locals to `v0, v1, ...` in
   traversal order. Under a **strict** policy, identifiers are preserved.
4. Regenerate source from the canonical tree so text-based and tree-based
   extractors agree.

Sameness is then equality of the fingerprint over that canonical tree.

**Settled 2026-09-14.** The public definition is the **canonical-form
fingerprint**. The other 13 properties remain published diagnostics that
describe *how* two forms differ when they differ. They are not conjuncts of
sameness: on stored data they never change a same/different verdict.

The benchmark scorer implements fingerprint equality (`benchmark.relation.same`).
SKYT still extracts all 14 properties for the tool's distance; those 13 extras
are not identity conjuncts for the benchmark.

Clone-like and TED judges live in `benchmark.discriminant` and are a
**comparison**, not part of this definition. See
[`STEP4_DISCRIMINANT.md`](STEP4_DISCRIMINANT.md).

### 3.2 Normal form — what is ignored

Settled and regression-tested in `tests/test_structural_validity.py`:

| Difference | Verdict | Rationale |
| --- | --- | --- |
| Whitespace, blank lines, indentation width | ignored | not program structure |
| Comments | ignored | discarded by the parser |
| Line reflow inside one expression | ignored | same tree |
| Docstring reworded or removed | ignored | prose, not form (settled 2026-09-14) |
| Bound local / parameter rename | ignored *under flexible naming* | that is what the policy means |
| Bound local / parameter rename | **significant** under strict naming | contract fixes the names |

### 3.3 Normal form — what is significant

| Difference | Verdict | Rationale |
| --- | --- | --- |
| Free names (globals, builtins, imports) | significant | `all` vs `any` are different programs |
| Function and class names | significant | contract surface |
| Statement order, even when independent | significant | visible to a reviewer (settled 2026-09-14) |
| Dead bindings, bare `pass` | significant | part of the delivered form (settled 2026-09-14) |
| Control flow shape, loop vs recursion | significant | the difference the benchmark exists to catch |
| Iteration bound, operator choice | significant | different program, same answers |

### 3.4 Known limits

- Distance zero is **not** semantic equivalence and must never be described as
  such. It is canonical-form identity.
- Single-function Python only. Multi-file and cross-language need a different
  extractor.
- The relation is an upper bound on sameness: it cannot be more permissive than
  fingerprint identity.
- Not validated against human judgement yet. That is Phase 5 and it is the only
  thing that earns the word *benchmark* for the relation itself.

## 4. Certification predicate

Certification is **per task set**, declared, and never mixed.

| Task set | Predicate |
| --- | --- |
| HumanEval+ | HumanEval+ (`plus`) tests pass. Base-only passes are recorded but never counted as certified. No style contract. |
| SKYT contract corpus | Behavioral oracle passes **and** static contract compliance passes. |

Rules:

- Mixing base and extended suites within one reported number is forbidden.
- A task set must state whether certification includes static checks. The two
  are different instruments and produce different numbers.
- Certification must be a subset of structural validity: unparseable code cannot
  certify. `analyze_repeatability` enforces this.

## 5. Sample size *N*

**Settled 2026-09-16: *N* = 20.** Cross-validation split is 10/10
(`train_size = N/2`).

- Gives \(\binom{20}{2} = 190\) pairs per config rather than 45 at *N*=10.
- The canon, when one is picked for SKYT, is chosen from ten draws, not five.
- Modal mass is less downward-biased than at *N*=10.

The HumanEval+ **30-task pilot** remains *N*=10. That grid is a labeled
historical run (`pilot_grid`), not the protocol. New overlay runs use *N*=20.
Do not pool *N*=10 and *N*=20 numbers.

What *N* does **not** buy: interval width on the headline is driven by the
**number of tasks**, because the bootstrap clusters on tasks. Going from
*N*=10 to *N*=20 doubles generation cost and tightens within-task estimates,
but it does not substantially narrow the published CIs. More tasks do that.
That is why the next overlay run is 164 tasks at *N*=20, not another 30-task
slice at *N*=20.

## 6. Versioning

Numbers are only comparable within a relation version. The Step 1 fix changed
the relation, so the version must be stamped, not implied.

Proposed scheme, recorded in every output file:

```
relation_version   2   canonical-form fingerprint, docstrings stripped,
                       scope-aware alpha-renaming        (2026-09-14)
relation_version   1   14-property conjunction, docstrings significant,
                       seven-name allowlist              (published MSR/SBES)
```

Rules:

- Any change to `_canonicalize`, the property set, or the naming policy
  increments the version.
- Results carrying different relation versions are never pooled or compared.
- Under relation 1, MSR and SBES numbers are unchanged by the v2 fix (verified
  bit-identical), so those published figures are valid under **both** versions.
  The HumanEval+ figures are version-sensitive: 56.93% under v1, 62.19% under
  v2.

**OPEN 4.** Stamping the version into *generation* artifacts means writing a
constant into `src/` and threading it through that schema. That still needs
approval. Overlay reports from
`benchmarks.structural_repeatability` already carry `relation_version: 2`
without changing the frozen jsonl schema.

## 7. Out of scope for the benchmark

The benchmark is the **measuring tape only**. These are product features and are
explicitly not part of the specification:

- Canon selection (Certified Consensus) — a policy, not a measurement.
- Repair toward a canon — a tool, not a measurement.
- Match to a human reference solution — scoring against one author's style is
  not repeatability.

SKYT appears in the results table as one row, before and after. That is a
stronger position than being the whole table.

## 8. Open items, collected

| # | Item | Status |
| --- | --- | --- |
| 1 | Metric names | **OPEN.** Recommendation: `same@2` and `same@2\|cert` |
| 2 | Relation definition | **Settled.** Canonical-form fingerprint; 13 properties are diagnostics |
| 3 | Fix *N* | **Settled.** *N*=20, CV 10/10. HumanEval+ 30-task pilot stays *N*=10 as a labeled historical grid. |
| 4 | Stamp `relation_version` into artifacts | **OPEN** for generation jsonl / `src/`. Overlay reports already stamp `2`. |
