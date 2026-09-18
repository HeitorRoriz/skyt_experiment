# FSE 2027 — SameEval (draft)

**Working title:** *SameEval: Measuring Whether Regenerated Code Is the Same Program*

**Venue:** ACM International Conference on the Foundations of Software Engineering (FSE 2027), Research track  
**Conference:** 12–16 July 2027, Shenzhen, China  
**Deadline:** 2 October 2026 (AoE)

**Authors (draft):** Heitor Roriz (Massimus), Nasser Jazdi-Motlagh (University of Stuttgart), Vicente Lucena (UFAM)

This folder is the **ACM Research draft** for Paper 1. It is not camera-ready.
**SameEval** is the overlay (prompts + tests + `same@2`).
**SKYT** is the repair tool scored on contracted tasks only.

HumanEval+ in this PDF is the 164-task N=20 overlay (plus-pass 83.3% / same@2 65.9% / same@2|cert 76.6%).
Remaining: anonymization, dry-run against SETTLED §10 / REVIEWER_FRY_AFTER_164.md.

**Venue:** ACM International Conference on the Foundations of Software Engineering (FSE 2027), Research track  
**Conference:** 12–16 July 2027, Shenzhen, China  
**Deadline:** 2 October 2026 (AoE)

**Authors (draft):** Heitor Roriz (Massimus), Nasser Jazdi-Motlagh (University of Stuttgart), Vicente Lucena (UFAM)

This folder is the **ACM Research draft** for Paper 1. It is not camera-ready.
W1/W3 (2026-09-02): Methods, Results A/B, Threats.
W2 (2026-09-03): measured-cost motivation, related work, Figure 1
(`fig1.pdf` / `make_figure1.py`), artifact pins.
Remaining: anonymization, dry-run against SETTLED §10 / REVIEWER_FRY_AFTER_164.md.
164-task overlay scored 2026-09-18.

---

## Paper identity (locked)

- **One** Research paper. Framing is **SameEval-first**: the primary contribution is the overlay (`same@2` / `same@2|cert`). SKYT is a tool scored on that overlay. Empirical scores (contract corpus, SKYT pre/post, HumanEval+) are the first numbers.
- **Not in this paper:** Code DNA / generation-by-construction (IVR track).
- **Scopes never merged:** SBES (12 contracts · 3,600 generations) and MSR (15 tasks · 4,500 generations) are reported separately wherever our corpus appears.
- The 3 `*_strict` variants were **not** validated against a real MISRA C / NASA P10 rule set. Keep that caveat; do not claim compliance.

### Contributions (C1–C4, order in abstract/intro)

1. **C1 — SameEval (the overlay).** N regenerations + canonical-form fingerprint + `same@2` / `same@2|cert`.
2. **C2 — Anchor-aware measurement.** First-compliant vs Certified Consensus; measure ≠ policy. SKYT is the tool, not the benchmark.
3. **C3 — Empirical finding.** Corrected behavioral–structural gap on our corpus; replication on HumanEval+ (Table 1 = 164 tasks N=20 overlay).
4. **C4 — Tool score.** SKYT under `same@2` (pre/post) on contracted tasks only. Not reported on HumanEval+.

---

## Methods freeze (do not reopen while drafting)

Copied into `main.tex` as LaTeX comments only. Do not print a drafting box.

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

**Normalization** = canonical-form fingerprint (docstrings stripped; bound
names α-renamed when the contract allows). The other 13 SKYT properties are
diagnostics, not identity conjuncts. Not a new unnamed normalizer.

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

- **W0:** scaffold + freeze box.
- **W1/W3 (2026-09-02):** Methods + Results A (Gate 0 both policies) + Results B + Threats.
- **W2 (2026-09-03):** related work (clones / GumTree / AlphaCode / APR); Figure 1;
  artifact pins in the PDF; intro outline.
- **W4 (2026-09-16):** fingerprint identity, `same@2` names.
- **W5 (2026-09-16):** SameEval name and title; PDF drafting box gone.
- **W6 (2026-09-18):** HumanEval+ table = 164-task N=20 overlay from
  `outputs/benchmark/humaneval_plus_164_n20/benchmark_report.json`
  (13,120 gens / 656 configs). SKYT is contracted-task only.
- **Leftover:** anonymization, internal dry-run against reviewer fries, submit by 1 Oct 2026.
  Pillar 3 citation sweep (SLSA / reproducible builds) is still a co-author task.

Do not commit this folder unless explicitly asked.
