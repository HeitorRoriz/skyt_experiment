# Plan — a structural repeatability benchmark

Goal: turn the structural repeatability protocol from "a measurement protocol
with a working reference implementation" into **a benchmark other people can
run, cite, and submit numbers to.**

Written 2026-09-14. Background and the code findings this plan rests on:
[`SESSION_2026-09-14.md`](SESSION_2026-09-14.md).

---

## Plain-language summary

### What the benchmark should do

Ask an LLM to write `is_prime` ten times. Maybe eight answers work. But one may
use a `for` loop and another a `while` loop, with different variable names. Both
pass every test.

Existing benchmarks ask only **"does it work?"** and report 8/10.

This benchmark adds a second question: **"are the answers the same program?"**
The output looks like *"this model at temperature 0.7 produces working code 79%
of the time, but two working answers are the same program only 50% of the
time."* Nobody reports that number today, and it matters because teams assume a
pinned model at temperature 0 gives stable output. It does not.

To be a real benchmark you need five things:

1. A fixed task set anyone can download
2. A fixed way to check "does it work" (unit tests)
3. A fixed way to check "is it the same program" ← **the new and hard part**
4. One agreed number everyone reports
5. Baseline results others can compare against

Items 1 and 2 come free by borrowing an existing task set. We have a version of
3 and 4. We have nothing for 5. And item 3 has never been checked for
correctness.

### How SKYT becomes that benchmark

SKYT today is a tool with three pieces:

- a **measuring tape** that decides how different two programs are
- a **chooser** that picks which version counts as official
- a **rewriter** that edits the others to match

The benchmark is **only the measuring tape**. The chooser and the rewriter are
product features. So the work is to pull the measuring tape out, make it
standalone, and prove it is accurate.

The measuring tape currently computes 14 numbers per program and calls two
programs identical when all 14 match. That rule has never been tested. It can
fail in two directions:

- **Too picky:** calls near-identical programs different. Example: the
  fingerprint covers the parsed code *including the docstring*, so the same
  logic with a reworded docstring counts as a different program. This makes
  models look less consistent than they are, which inflates our own headline
  claim.
- **Too loose:** calls different programs identical. Example: variables are
  renamed to `v0`, `v1`, ... to make naming irrelevant, but the built-in
  allowlist holds only seven names, so `sorted` and `enumerate` get renamed too.
  Two programs differing only in which of those they call can look identical.

There is also a strong possibility that one of the 14 numbers — an AST
fingerprint — is doing all the work, leaving the other 13 as decoration.

Steps, in order:

1. **Prove the measuring tape is accurate.** Cheap, days, no API spend. Phase 0.
2. **Write the rules down:** how many samples, what counts as working, and which
   differences we agree to ignore. Phase 1.
3. **Make it one command.** Phase 2.
4. **Run every task, not a sample.** Phase 3.
5. **Show we did not reinvent clone detection or AST diffing.** Phase 4.
6. **Ask humans whether they agree with the tape.** Phase 5.

Then SKYT becomes one row in the results table: numbers before, numbers after.
That is a stronger position than being the whole story.

Step 1 is not negotiable as the starting point. If the measuring tape is off,
every number measured with it is off too.

---

## 0. Design decision up front: overlay, not a new task set

The benchmark does **not** ship new prompts.

HumanEval bundles prompts, a test oracle, and a metric. EvalPlus kept the same
prompts and strengthened the oracle. This benchmark keeps the prompts *and* the
tests and adds a **structural report**: sample the prompt *N* times, keep the
passers, and measure how often two independent draws produce the same form.

Consequences of that choice:

- It composes with existing task sets (HumanEval+, MBPP, in-house contracts)
  rather than competing with them.
- The thing being validated is the **sameness relation**, not the tasks.
- The headline answers a question `pass@k` cannot: *would I get this program
  again?*

---

## Phase 0 — Validate the sameness relation (blocking prerequisite)

Nothing else is worth building until this is done. If the relation is not
defensible, every number computed on top of it inherits the problem.

Established already (see the session record): overall distance is the unweighted
mean of 14 per-property distances, and one property is an MD5 equality test on
the dumped AST. So distance zero is a **conjunction that includes AST-hash
identity**, and the relation can never be more permissive than that hash.

### 0.1 Property ablation

Recompute the headline measures using only `normalized_ast_structure`, then
recompute with each property dropped in turn.

- **Question:** does anything beyond the AST hash change the headline?
- **If no:** report it. The operative relation is AST hashing; the other 13
  properties are a descriptive layer. Simplify the story and say so plainly.
- **If yes:** identify exactly which properties add strictness, and justify each
  one. Unjustified strictness is brittleness.
- **Cost:** analysis over existing artifacts. No API spend.

### 0.2 Metamorphic suite — false splits (too strict)

Apply edits that should **not** change the form; assert distance stays zero.

| Edit | Expected |
|---|---|
| Reformat / whitespace | distance 0 |
| Comment changes | distance 0 |
| Docstring rewording | **decide and document** |
| Local variable rename (flexible-naming contract) | distance 0 |
| Reorder independent statements | **decide and document** |
| Insert dead / no-op code | **decide and document** |

The rows marked "decide" are the real work: they force a written specification
of what the relation is supposed to **ignore**. That specification is the
benchmark's normal form, and it currently does not exist.

Priority row is docstrings. The AST hash is computed over the unmodified parsed
tree and docstrings are `Expr(Constant(...))` nodes inside it, so identical
logic with reworded docstrings registers as a different structure. Muted on
stitched HumanEval+ prompts; live on tasks where the model writes its own
docstring. Impact on the headline is **unmeasured**.

- **Cost:** new test files, no API spend, no runtime modification.

### 0.3 Soundness probe — false merges (too coarse)

The α-renamer's built-in allowlist is seven names (`range`, `len`, `print`,
`max`, `min`, `sum`, `abs`). Every other callable — `sorted`, `enumerate`,
`any`, `str` — is renamed to `v{n}` as though it were a local variable, so two
programs differing only in which non-allowlisted function they call may collapse
to the same α-renamed dump. `control_flow_signature` records call names and may
catch it; confirm whether it always does.

Then sample distance-zero pairs, inspect them, and report precision.

### 0.4 Transitivity audit

`equivalence_classes` raises when the distance-zero relation is not transitive.
Report whether it has ever fired across the analyzed configs, and characterise
near-misses. A clean record is evidence for the construct; a firing is a finding.

### Phase 0 deliverable

A **validity report**: ablation table, metamorphic pass/fail matrix, false-merge
precision estimate, transitivity record, and a written normal-form spec.

Then decide whether the relation needs to change. **Changing the extractors is a
runtime change** requiring explicit approval, and it would invalidate existing
published numbers. Measure first, decide second, and keep any fix in a parallel
output tree.

---

## Phase 1 — Pin the benchmark definition

Everything here is a documented, versioned choice.

1. **Name the headline metric.** `pass@k` is citable because it has a name.
   End-to-end pairwise exact-match needs one too, with the secondary
   passers-only variant named distinctly so nobody silently swaps rulers.
2. **Fix *N*.** One value with a stated rationale, plus the cross-validation
   split size derived from it. Two different N values currently coexist.
3. **State the certification predicate per task set** (tests only, versus tests
   plus static checks) and forbid mixing base and extended test suites.
4. **Publish the normal form** from Phase 0.2: what the relation ignores and
   what it treats as a real difference.
5. **Versioning policy.** The relation will change over time; numbers must carry
   a relation version so results stay comparable.

---

## Phase 2 — Reference implementation and harness

Much of this exists in `benchmarks/humaneval_plus/` and needs packaging rather
than invention.

- Single-command runner over a task set, model, temperature, and *N*.
- Pins enforced, not documented: dataset hash checked with refuse-on-mismatch,
  sandbox image pinned by digest, network disabled, fixed seeds for sampling and
  bootstrap.
- Untrusted code executed only in the sandbox, never on the host.
- Stable output schema: per-config records plus an aggregate file, including
  every denominator (how many configs entered each column and how many were
  dropped as undefined).
- Cost estimate printed before any paid call, and a hard refusal without an
  explicit opt-in flag.

---

## Phase 3 — Full coverage and baselines

- Run the **complete** task set rather than a sampled subset. A benchmark cannot
  be a preregistered slice.
- Several models across at least two temperatures, so the table shows the
  accuracy-versus-repeatability trade rather than a single point.
- A second task set (MBPP is the obvious candidate) to show the overlay is not
  HumanEval-specific.
- Publish baselines in a shape others can extend with their own rows.

Guardrail: new runs go to new output trees. Do not overwrite
`outputs/gate0/` or `outputs/humaneval_plus/pilot/`, and never merge separate
datasets into one headline.

---

## Phase 4 — Discriminant validity against existing tools

Show the relation is not a rebranding of something standard. Compare, on the
same pairs:

- exact string equality (strict lower bound)
- normalized AST hash alone (the Phase 0.1 comparison, formalised)
- tree edit distance (GumTree-style AST differencing)
- a clone detector across Type-1/2/3 clones

Report where the verdicts disagree and argue why this relation's disagreements
are the desirable ones. Without this, the fair criticism is "AST hashing with
extra dials."

---

## Phase 5 — Human agreement study

Converts extractors into a validated instrument.

- Sample program pairs stratified by measured distance.
- Two or three labelers independently answer "same implementation?" under a
  written rubric.
- Report inter-rater agreement, then precision and recall of distance zero
  against the labeler consensus.

This is the expensive phase and the one that earns the word *benchmark*.

---

## Phase 6 — Release

- Artifact package: harness, pins, seeds, task id lists, raw generations, and
  per-config outputs.
- Documentation covering the normal form, the metric definitions, and the known
  failure directions.
- A submission format so third parties can report comparable numbers.

---

## Non-goals

- New programming prompts.
- Any claim of semantic or observational equivalence.
- Making models deterministic. Nothing here touches the sampler.
- Competing on `pass@k`, or scoring anything by match to a human reference
  solution.
- Any compliance claim against MISRA C or NASA Power-of-10. Those remain
  inspiration only, and the `*_strict` variants were never checked against a
  real rule set.

---

## Risks

| Risk | Mitigation |
|---|---|
| The relation turns out to be AST hashing | Report it honestly in Phase 0 and simplify the framing; a simpler validated ruler beats an elaborate unvalidated one |
| Brittleness inflates the measured gap | Phase 0.2 runs before any new headline claim |
| Coarseness inflates post-repair numbers | Phase 0.3 precision estimate |
| Single-function Python scope | State it; multi-file is future work and needs a different extractor |
| Weak test suites let a wrong-but-passing form become the canon | Document that the canon inherits oracle strength; report oracle quality per task set |
| Cost of full runs | Overlay design keeps *N* samples the only multiplier; publish the estimate before running |

---

## Immediate next actions

1. Phase 0.1 ablation over existing artifacts (no API spend).
2. Phase 0.2 metamorphic suite, docstring row first (no API spend).
3. Write the validity report and the normal-form spec.
4. Only then reopen definition and coverage questions.

Steps 1 and 2 are read-only analysis and require no runtime modification. They
also strengthen the current paper's threats section regardless of how the
benchmark question is eventually scoped.
