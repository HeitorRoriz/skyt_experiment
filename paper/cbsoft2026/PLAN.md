# SKYT — CBSoft 2026 Industry Track Plan (Adapted)

## Context

Industry Track submission for **SBES / CBSoft 2026**, reframed from the MSR 2026 Data & Tool Showcase paper.

**This is NOT a repackaged MSR paper.** It is an industry-oriented extended abstract centered on the practical problem, engineering relevance, early lessons, and collaboration agenda.

---

## Venue Constraints

- **Track:** SBES / CBSoft 2026 Industry Track
- **Format:** 2-4 page extended abstract
- **Abstract registration:** May 22, 2026
- **Submission deadline:** May 29, 2026
- **Format:** ACM `sigconf` class (adapted for CBSoft, no ACM reference block, no CCS, no copyright)
- **Template:** Confirmed — `\documentclass[sigconf]{acmart}` with CBSoft overrides
- **Note (checklist item 20):** SBES Industry Track papers must NOT include author biographies

---

## Core Thesis

> **Repeatability must be treated as an engineering property in LLM-assisted software development, and SKYT is an initial practical step in that direction.**

---

## Working Title Options

**CONFIRMED:** "When the Same Prompt Yields Different Code: Engineering Repeatability with SKYT"

Short title (page headers): "Engineering Repeatability with SKYT"

---

## Strategic Positioning

### What this paper IS
- Industry-facing argument that non-repeatability is a real engineering problem
- Introduction of SKYT as an initial practical response
- Early evidence and lessons suggesting broader collaboration is warranted

### What this paper IS NOT
- Not a replication of the MSR paper
- Not a dense empirical research paper
- Not the venue for Code DNA or new theoretical contributions (save for FSE 2027)

### Venue split
- **CBSoft 2026 (Industry Track):** practical framing, concise, agenda-building
- **FSE 2027:** substantially extended with new contributions (Code DNA, broader evaluation)

---

## Paper Structure (4 sections, 2-4 pages)

### Section 1: The Problem — Non-Repeatability in LLM-Assisted Development (~400 words)

**Goal:** Show non-repeatability is a real engineering problem, not just an academic curiosity.

**Content:**
- Identical prompts yield different programs (even at temperature=0)
- This harms verification, maintenance, auditability, and process reliability
- The problem intensifies in safety-critical/deterministic contexts (firmware, medical, automotive)
- Current workflows (ad hoc prompting, no traceability, no repeatability discipline) are operationally weak
- Frame: "If you can't reproduce your build, you can't audit it"

**Motivating example:** Balanced Brackets contract
- At T=0.7, raw repeatability drops to 15%
- Same prompt, same model, same settings — 85% of outputs are structurally different
- This is the hook that makes practitioners pay attention

### Section 2: The SKYT Approach (~500 words)

**Goal:** Introduce the solution in practitioner-accessible terms.

**Content:**
- Prompt contracts: structured specifications with behavioral oracles
- Canonical anchoring: fixed reference point for structural comparison
- Property-based repair: deterministic AST-level transformation toward canonical form
- Pipeline: Contract -> LLM -> Canon -> Transform -> Metrics
- Repeatability as a first-class software property (measured, not assumed)
- Key metrics explained simply: R_raw (before), R_anchor_post (after), Delta_rescue (improvement)

**One compact architecture diagram** (if space allows).

### Section 3: Early Evidence & Lessons Learned (~500 words)

**Goal:** Present only the strongest evidence + practical insights.

**Evidence (keep tight):**
- Balanced Brackets: R_raw=15% at T=0.7, rescued to 70% (Delta=+0.45)
- Aggregate: canonicalization improves repeatability by 22-46% for GPT-4o-mini
- ~~MISRA+NASA contracts improve structural conformance by +55% relative over standard contracts~~ **[NOT VALIDATED — actual data shows ~+9% aggregate with high heterogeneity; finding dropped from paper 2026-05-15]**
- Behavioral correctness maintained at ~100% throughout (transformations don't break code)

**Lessons learned (the differentiator):**
- Temperature has dramatic impact on repeatability (practitioners rarely consider this)
- Simple algorithms (GCD, Fibonacci) are naturally repeatable; complex ones (bracket matching, string processing) are not — problem structure matters
- Contracts don't make LLMs deterministic, but they make post-processing deterministic
- Model choice matters: GPT-4o-mini responds best to canonicalization; Claude produces structurally different patterns
- Even "pinned" settings (same model, same temperature) don't guarantee repeatability

### Section 4: Collaboration Agenda & Next Steps (~300 words)

**Goal:** End with an agenda, not just a summary.

**Content:**
- Need for broader evaluation (multi-file projects, industrial codebases, non-algorithmic tasks)
- Industry-academia collaboration opportunities (ongoing contacts from ICSE 2026 with researchers from Sweden and Zurich)
- Open-source tool availability for practitioners
- Integration with CI/CD pipelines as quality gate
- Benchmark and dataset expansion (beyond 12 algorithmic tasks)
- Connection to agile practices: contracts as executable specifications

**NO mention of Code DNA** — save for FSE 2027.

---

## Evidence Selection Rules

### Keep
- Balanced Brackets motivating example (strongest dramatic effect)
- One aggregate headline number (22-46% improvement)
- MISRA+NASA comparison (safety-critical hook)
- 3-4 concise lessons learned

### Cut / defer to FSE
- Per-temperature detailed tables
- Statistical methods detail (Wilson CI, Fisher's exact, Holm-Bonferroni)
- Full 12-contract breakdown
- Claude deep-dive analysis
- Threats to validity section
- Code DNA

### Litmus test
> If a paragraph does not directly help a reviewer answer "Why should industry care?", cut it.

---

## Working Calendar

### Phase 1 — Direction Lock (Apr 20-24)
- [x] Final submission angle: Option A (Industry Experience + Practical Agenda)
- [x] Lock working title: "When the Same Prompt Yields Different Code: Engineering Repeatability with SKYT"
- [x] Confirm format/template: ACM sigconf with CBSoft overrides
- [x] Create LaTeX skeleton: `paper/cbsoft2026/main.tex`
- [x] Write the motivating example (balanced brackets scenario) — in Section 1
- [ ] Fill in author affiliations and emails (TODO placeholders in main.tex)
- [ ] Align with Profs. Nasser and Vicente

### Phase 2 — Draft v1 (Apr 25 - May 2)
- [ ] Write all 4 sections using MSR material as source
- [ ] Initial industry-oriented reframing
- [ ] Create architecture diagram (if space allows)
- [ ] Select and format the 1-2 key result figures/tables

### Phase 3 — Industry Rewrite & Compression (May 3-8)
- [ ] Sharpen opening (problem hook)
- [ ] Strengthen industry voice throughout
- [ ] Reduce technical clutter
- [ ] Tighten evidence and conclusion
- [ ] Ensure 2-4 page limit compliance

### Phase 4 — Advisor Review (May 9-15)
- [ ] Send to Profs. Nasser and Vicente
- [ ] Consolidate comments
- [ ] Decision on final framing adjustments

### Phase 5 — Finalization (May 16-21)
- [ ] Final text edits
- [ ] Title/abstract polishing
- [ ] Author metadata
- [ ] Formatting compliance
- [ ] Internal proofread

### Deadlines
- **May 22, 2026:** Abstract registration
- **May 29, 2026:** Final submission

---

## Framing Decision

**CHOSEN: Option A — Industry Experience + Practical Agenda**

This emphasizes:
- engineering pain (the problem is real)
- practical need for repeatability
- SKYT as a practical response
- lessons learned from early evaluation
- collaboration agenda for broader validation

---

## Strategic Reminders

1. **Build momentum** in the Brazilian SE community
2. **Strengthen practical positioning** of the work
3. **Preserve room** for a substantially extended FSE 2027 paper
4. **Discipline:** reframe, compress, and sharpen — not copy, overload, or over-claim
