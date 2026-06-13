# Code DNA — Discussion Summary

> ## RECONCILIATION NOTE — 2026-06-13
>
> This is **forward-looking framing** for the FSE / Code-DNA vision, not a published result. Two figures here differ from the papers and are kept as-is for the vision narrative:
> - The **"246 experiments / 4,920 LLM calls"** figure is a *looser* count that includes pilot and chunk re-runs in `outputs/`. The **paper-clean** datasets are **3,600 generations** (SBES/CBSoft 2026, 12 contracts) and **4,500 generations** (MSR 2026 camera-ready, 15 tasks). Treat 4,920 as "calls on hand," not a published n.
> - **"13 foundational properties"** → the code now has **14** (`src/foundational_properties.py`).
>
> **Strict-contract note (neutral):** the 3 `*_strict` variants were run, but at the time of this note no contract had been validated against an actual MISRA C / NASA Power-of-10 rule set — flagged as a concern (2026-06-13). No data was deleted.

## 1. The Motivation: The 66pp Gap

SKYT experiments (246 experiments, 4,920 LLM calls) revealed:

| Metric | Value |
|--------|-------|
| R_behavioral (code works) | 99% |
| R_anchor_pre (structurally canonical) | 32% |
| **Gap** | **66 percentage points** |

LLMs produce code that *works* almost always, but is structurally identical to the canonical form only 32% of the time. SKYT's 13 foundational properties close ~6pp of that gap. Code DNA aims to close the remaining 60pp.

---

## 2. What Code DNA Is

Code DNA is **the complete generative blueprint from which a program can be deterministically constructed**.

It is NOT:
- The "mathematical essence" of the code
- A fingerprint or hash
- A set of properties or traits

It IS:
- The full set of instructions needed to grow a program
- A representation from which a single canonical form follows by construction
- A level of abstraction above surface properties

**Key property**: If two programs share the same Code DNA, their canonical form is identical — by construction, not by comparison.

---

## 3. The Biological Analogy (Corrected)

Human DNA is not "the mathematical essence of humans." It's the **blueprint that encodes how to build and operate the organism**.

| | Biology | Code |
|--|---------|------|
| **DNA** | Blueprint for building the organism | Blueprint for building the program |
| **NOT** | "The essence of being human" | "The essence of the computation" |
| **Contains** | Instructions for constructing proteins, organs, systems | Instructions for constructing variables, logic, behavior |
| **Key property** | Same DNA → same organism | Same Code DNA → same program |

### The Double Helix

- **Syntactic strand** (AST, lexical patterns) ↔ structural proteins
- **Semantic strand** (mathematical essence, I/O behavior) ↔ functional genes
- **Contract constraints** ↔ regulatory regions that control gene expression
- **Canonicalization** ↔ DNA repair mechanisms that correct mutations

### What's Inside Code DNA

The math (e.g., `f(n) = f(n-1) + f(n-2)`) is just *one gene*. The full DNA also includes:

- **How** to implement it (iterative vs recursive — a structural gene)
- **What** to name things (variable naming — an expression gene)
- **How** to handle edges (input validation — a regulatory gene)
- **How** to optimize (memoization — an optimization gene)

---

## 4. Why "Just Improve the Algorithms" Isn't Enough

The natural pushback: *"Can't you just add more properties or better canonicalization algorithms?"*

### The Fundamental Limitation

Properties are **lossy projections**. They reduce a program to a handful of numbers. Two programs can match on all 13 properties and still be structurally different, because properties don't capture how elements interact.

Adding property #14, #15, #50 helps incrementally, but you're playing whack-a-mole: every new property closes some cases and misses others. There's a ceiling.

### The Analogy

> "Improving the property algorithms is like adding more diagnostic tests. Code DNA is like sequencing the genome — it's a different level of representation, not a better version of the same one."

### The Distinction

- **Properties**: Describe *traits* of the program (blood type, eye color)
- **Code DNA**: Encodes the *complete construction plan* (the genome)

You can keep adding measurements, but you'll never reconstruct the person from them. Code DNA is a shift from measuring traits to capturing the generative blueprint.

---

## 5. Research Roadmap

### Phase 1 — Organ-Level DNA
Extract and validate DNA signatures for single, self-contained functions (the 15 contracts in the SKYT study).

### Phase 2 — DNA Synthesis
Given a DNA signature, generate behaviorally equivalent code — proving the representation is complete.

### Phase 3 — Genetic Engineering
Mutate DNA to evolve code (add features, optimize performance) with formal behavioral guarantees.

---

## 6. Poster-Ready Language

### Future Work Section

> "Current SKYT compares 13 individual code properties — analogous to comparing isolated traits like eye color or blood type. This closes ~6pp of the 66pp gap. Code DNA aims to extract the complete generative blueprint — the full set of instructions from which a program is constructed. Just as biological DNA deterministically produces an organism, Code DNA would deterministically produce a canonical program. When two outputs share the same Code DNA, their canonical form is identical by construction — closing the gap entirely."

### Rebuttal to "Why is the improvement small?"

> "The 6pp improvement is modest because we're currently comparing surface-level code features — how the code looks, not what it computes. The 66pp gap tells us the real problem: two programs can solve the same problem using the same core algorithm but look completely different in their syntax and structure. For example, Fibonacci can be written as a loop or as recursion — same blueprint, different code. Code DNA aims to extract that core blueprint directly. Once you have it, the surface differences become irrelevant, and a single canonical form follows naturally. The gap becomes the roadmap."

### Rebuttal to "Just improve the algorithms!"

> "Yes, and we should — that's incremental improvement. But there's a ceiling. Properties are projections: they reduce a program to a checklist of traits. Two programs can match on every trait we measure and still differ structurally, because the traits don't capture how they interact. It's the difference between describing someone by their height, weight, and eye color versus having their genome. You can keep adding measurements, but you'll never reconstruct the person from them. Code DNA is a shift in representation — from measuring traits to capturing the generative blueprint. That's not an optimization of the current approach; it's a different level of abstraction."

---

## 7. Connection to SKYT Results

| What SKYT Proved | What It Means for Code DNA |
|-----------------|---------------------------|
| 66pp gap exists | There's room for a fundamentally better representation |
| 13 properties close 6pp | Properties help but hit a ceiling |
| 0% negative Δ | Canonicalization never hurts — safe foundation to build on |
| Claude: 84% R_raw, 9% R_anchor_pre | High surface similarity can mask deep structural divergence |
| T=0 only 91% repeatable | Even "deterministic" settings need a canonicalization layer |

Code DNA builds on SKYT's empirical foundation: we now know *how big* the problem is, *where* properties help, and *where* they don't. That data directly informs what Code DNA must capture that properties cannot.
