# Diversity as a defect signal — pre-registration

**Created:** 2026-09-24
**Status:** written before any diversity-signal result was computed.
**Exploratory.** No API calls. Read-only on existing generation trees.

> Hypotheses: (H1) Base-passing programs in the configuration's modal form survive Extra tests more often than Base-passing programs in other forms. (H2) Configurations with higher form diversity among Base-passers have higher Extra-failure rates among Base-passers, including after controlling for Base pass rate. Both are exploratory. All results will be reported regardless of direction or significance.

Schema confirmed before this note (frozen overlay `outputs/benchmark/humaneval_plus_164_n20/`, 13,120 records):

- Configuration fields: `task_id`, `model`, `temperature`.
- Per generation: `oracle.base_passed`, `oracle.plus_passed`. Code for `same()` is `stitched_code`.
- `fingerprint()` (`benchmark/relation.py`) returns a hashable MD5 of the canonical tree. `same()` is equality of those hashes. Forms are groups of that key, not a pairwise union-find.
- `plus_passed` implies `base_passed` on every record (0 violations). Extra survival given Base pass is `plus_passed` among Base-passers.

## 3. Definitions

Configuration **c** = (task, model, temperature). N = 20 generations per configuration.

- **B_c** = Base-passing generations in c. **n_c** = |B_c|.
- **Forms** = equivalence classes of B_c under `same()` (relation_version=2).
- **Extra survival** of a program = `plus_passed` (given it is in B_c).
- **F_c** = Extra-failure rate among Base-passers = 1 − (Extra-surviving programs in B_c) / n_c.
- **D_c** (primary diversity) = 1 − same@2 among Base-passers
  = 1 − Σ_k m_k(m_k − 1) / (n_c(n_c − 1)), where m_k are form class sizes in B_c.
  This is **1 − Base-certified same@2**, which ties the analysis directly to the SameEval metric.
- Secondary diversity measures (report, do not headline): number of distinct forms; Shannon entropy of form shares.

**Leave-one-out (LOO) modal form** for program i ∈ B_c:
- Compute form class sizes on B_c \ {i}.
- The LOO mode is the largest class. If two or more classes tie for largest, program i is **unclassified** (excluded from A1).
- Program i is **modal** if its form equals the LOO mode; otherwise **non-modal**.
- LOO prevents a program from voting for its own form.

**Exclusions** (report counts for each):
- A1 and A2: configurations with n_c < 2.
- A1: configurations without at least one modal **and** one non-modal classified program (no within-configuration contrast).
- A1: unclassified programs (LOO ties).

**Never use Extra results to define forms, modes, or diversity.** Extra is outcome only.

## 4. Analyses

All CIs: task-cluster bootstrap, 10,000 resamples, seed **20260723**, resampling tasks **jointly** across all model × temperature cells. Point estimates: aggregate configurations within task, then average across tasks (same convention as the paper).

### A1 — Modal vs. non-modal Extra survival (H1)

Per eligible configuration c:
- s_mod(c) = Extra survival rate among modal programs
- s_non(c) = Extra survival rate among non-modal programs
- Δ_c = s_mod(c) − s_non(c)

Report:
- Pooled mean s_mod, s_non, and Δ with 95% CI.
- Same for each model × temperature cell.
- Number of eligible configurations and tasks.
- Descriptive only: generation-pooled survival rates for modal vs. non-modal (no CI needed).

### A2 — Diversity vs. Extra failure (H2)

Per configuration with n_c ≥ 2:
- **Primary:** Spearman ρ(D_c, F_c) with 95% CI.
- **Control for Base pass rate:** partial Spearman ρ(D_c, F_c | n_c/20) with 95% CI. This is the "information beyond pass@k" test.
- **Within-task:** Spearman ρ on task-demeaned D_c and F_c (removes task difficulty), with 95% CI.
- **Binned descriptive:** D_c = 0 vs. D_c in tertiles of positive values; mean F_c per bin (for the figure).
- Repeat primary ρ per model × temperature cell.
- Sensitivity: restrict to n_c ≥ 10; report primary and partial ρ.

**Do not** use "any Extra failure in the configuration" as an outcome. With more distinct forms, the chance that at least one form fails rises mechanically. Use the rate F_c only.

### A3 — Cross-check (sanity, not reported as a result)

For 5 random configurations, confirm D_c computed here equals 1 − same@2|cert computed by the existing scorer **when certification is Base**. If the existing scorer only certifies on Plus, compute both here and confirm the Plus version matches the scorer exactly. Fail loudly on mismatch.
