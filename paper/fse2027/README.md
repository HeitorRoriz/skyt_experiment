# FSE 2027 — SameEval (draft)

**Working title:** *SameEval: Measuring Whether Regenerated Code Is the Same Program*

**Venue:** ACM International Conference on the Foundations of Software Engineering (FSE 2027), Research track  
**Conference:** 12–16 July 2027, Shenzhen, China  
**Deadline:** 2 October 2026 (AoE)

**Authors (draft):** Heitor Roriz (Massimus), Nasser Jazdi-Motlagh (University of Stuttgart), Vicente Lucena (UFAM)

This folder is the **ACM Research draft** for Paper 1. It is not camera-ready.
**SameEval** is the overlay (prompts + tests + `same@2` / `same@2|cert`).
The study in this PDF is HumanEval+ only: 164 tasks, N=20, 13,120 generations
(plus-pass 83.3% / same@2 65.9% / same@2|cert 76.6%).

Do **not** import SBES (12/3600) or MSR (15/4500) numbers into this paper.
Primary evaluation is \skyt{} on held-out test generations, using only
HumanEval base tests during repair and reserving HumanEval+ extra tests for
final evaluation.
(HumanEval Base operational; Extra tests unseen until evaluation).

Remaining: anonymization, dry-run against SETTLED §10 / REVIEWER_FRY_AFTER_164.md.

---

## Paper identity

- **One** Research paper. Framing is **SameEval-first**.
- **Empirical scores:** HumanEval+ 164 × N=20 overlay only.
- **Not in this paper:** Code DNA / generation-by-construction; SKYT repair scores;
  contracted-task Gate 0; SBES; MSR.

### Contributions

1. **C1 — SameEval (the overlay).** N regenerations + canonical-form fingerprint + `same@2` / `same@2|cert`.
2. **C2 — Measurement, not policy.** The overlay does not pick a canon.
3. **C3 — Empirical finding.** On HumanEval+, passing plus tests does not imply the same form.

**Normalization** = canonical-form fingerprint (docstrings stripped; bound
names α-renamed when the task allows). Inference: one score per task, cluster
bootstrap 10,000 seed 20260723. Never Wilson/binomial on C(N,2) pairs.

---

## Files

| File | Purpose |
|---|---|
| `main.tex` | ACM `sigconf` skeleton (anonymous/review flags on) |
| `main.bib` | Working bibliography |
| `acmart.cls`, `ACM-Reference-Format.bst` | Offline ACM class (copied from `paper/cbsoft2026/`) |
| `fig1.pdf` / `make_figure1.py` | HumanEval+ overlay figure |

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

Do not commit this folder unless explicitly asked.
