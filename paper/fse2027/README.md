# FSE 2027 — Structural Repeatability Protocol (draft)

**Working title:** *A Structural Repeatability Protocol for LLM-Generated Code*

**Venue:** ACM International Conference on the Foundations of Software Engineering (FSE 2027), Research track  
**Conference:** 12–16 July 2027, Shenzhen, China  
**Deadline:** 2 October 2026 (AoE)

**Authors (draft):** Heitor Roriz (Massimus), Nasser Jazdi-Motlagh (University of Stuttgart), Vicente Lucena (UFAM)

This folder is the **ACM Research skeleton** for Paper 1. It is not a camera-ready draft. Methods and Results sections are stubs until W1.

---

## Paper identity (locked)

- **One** Research paper. Framing is **ruler-first**: the primary contribution is a structural repeatability *protocol*. Empirical scores (our corpus, SKYT pre/post, later HumanEval) are the first numbers on that ruler.
- **Not in this paper:** Code DNA / generation-by-construction (IVR track).
- **Scopes never merged:** SBES (12 contracts · 3,600 generations) and MSR (15 tasks · 4,500 generations) are reported separately wherever our corpus appears.
- The 3 `*_strict` variants were **not** validated against a real MISRA C / NASA P10 rule set. Keep that caveat; do not claim compliance.

### Contributions (C1–C4, order in abstract/intro)

1. **C1 — Protocol (the ruler).** N regenerations + structural distance + reports (pairwise U-statistics, certified modal mass, optional churn).
2. **C2 — Anchor-aware measurement.** First-compliant vs Certified Consensus Canon; measure ≠ policy.
3. **C3 — Empirical finding.** Corrected behavioral–structural gap on our corpus; replication on HumanEval (pilot → full).
4. **C4 — Tool score.** SKYT under pairwise / honest metrics (pre/post).

---

## Methods freeze (do not reopen while drafting)

Copied into `main.tex` as a drafting box. Remove that box before submission.

```
SELECT   Certified Consensus Canon
         (certified mode → medoid on ties → deterministic tie-break)
         "Certified" = oracle-pass + contract compliance

MEASURE  1. End-to-end pairwise exact-match U-statistic
            (+ conditional-among-valid secondary)
         2. Certified modal mass (largest certified class / n)
         3. Pairwise distance U-statistic (secondary)
         Inference: one score per contract → cluster bootstrap
         Within-config pairwise: generation bootstrap if shown
         NEVER: Wilson/binomial on C(n,2) pairs
         NEVER: plain Wilson on in-sample modal share

POLICY   Repeated balanced CV at operational s=10
         (U-statistic CV; large fixed-seed B, not single split-half)
         Report held-out match, distance, canon stability
         Baselines: first-compliant vs Certified Consensus
         LOO / temporal = sensitivity only
         Fresh holdout = strongest confirmation when budget allows

WILSON   Only: frozen canon + independent evaluation batch
```

**Headline numbers are not** the Gate 0 “74.3% split-half medoid.” That figure is policy/sensitivity language only.

**Normalization** = existing 14-property distance-0 equivalence (including α-renaming where the contract allows). Not a new unnamed normalizer.

Do **not** quote the MSR-era “66pp gap” without the **anchor-relative** qualifier. The Gate 0 corrected gap on the same 220 configs is **~22–24pp** (behavioral ~98.4% vs modal ~76.5% / split-half medoid ~74.3%). Recompute under this freeze before any camera-ready table.

---

## Files

| File | Purpose |
|---|---|
| `main.tex` | ACM `sigconf` skeleton (anonymous/review flags on) |
| `main.bib` | Working bibliography |
| `acmart.cls`, `ACM-Reference-Format.bst` | Offline ACM class (copied from `paper/cbsoft2026/`) |

Internal briefing (gitignored): `docs/internal/GATE0_MEMO.md`.

---

## Compile

```bash
# from this folder, with a TeX Live / MiKTeX install
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

---

## Writing sequence

- **W0 (this folder):** scaffold + freeze box + restored Gate 0 memo.
- **W1:** Methods + Results A from `outputs/gate0/` and `outputs/problem_evidence/` (recompute under freeze before final tables).
- **W2:** Intro, Motivation, Related Work stubs, Threats.
- **W3:** HumanEval harness + Results B.
- **W4:** figures, artifact, anonymization, submit by 1 Oct 2026.

Do not commit this folder unless explicitly asked.
