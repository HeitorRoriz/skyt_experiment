# Step 5 — inference lock (do not binomial-on-pairs)

Date: 2026-09-16. Hardens the `same@2` reporting strategy so a reviewer cannot
read the JSON as a Wilson interval on \(\binom{N}{2}\) pairs.

This does **not** change the kernel. Two independent draws, U-statistic of
order 2, failures in the `same@2` denominator. It changes how intervals and
denominators are **stamped**, tested, and warned.

Runtime, `outputs/gate0/`, and `outputs/humaneval_plus/pilot/` are untouched.
FSE Table 1/2 numbers are not recomputed here.

```
python -m pytest tests/test_benchmark_inference.py tests/test_structural_repeatability.py
python -m benchmark score \
    --source-dir outputs/humaneval_plus/pilot \
    --out-dir outputs/benchmark/pilot_v2
```

`score` prints `WARNING: pilot_grid=true` when any slice has `n_tasks < 30`
or `N < 20`. That is the frozen-protocol size, not a desk-reject.

## The five parts

1. **Reviewer-proof report** (`benchmark/schema.py`, `benchmark/report.py`).
   Schema `structural-repeatability-benchmark-v2`. Every slice carries `n`,
   `n_tasks`, per-metric `*_n_clusters`, drop count, all three rates, CIs, and
   `inference_version`. Top-level `inference` is a fixed block:

   - unit: task
   - estimator: U-statistic order 2, then equal-cluster mean
   - interval: percentile cluster bootstrap over `task_id`
   - seed `20260723`, default 10 000 resamples
   - **not** binomial or Wilson on pairs

   Mixed `N` in one model × temperature slice is refused. Pair counts on
   per-config rows are `u_statistic_pair_count` / `u_statistic_certified_pair_count`
   so they cannot be pasted in as CI `n`.

2. **Jackknife over tasks** (`cluster_jackknife_mean`). Leave-one-task-out SE
   and a 95% normal interval next to the bootstrap (`same_at_2_jackknife_ci95`).
   Skipped when `n_tasks < 3`. Still not a pair-level interval.

3. **Tests** (`tests/test_benchmark_inference.py`). Cluster CI is wider than a
   Wilson-on-pairs straw man; busy tasks do not dominate; drops are counted;
   mixed `N` and missing metrics raise; `benchmark/` does not import
   `wilson_confidence_interval`.

4. **CLI flag.** `pilot_grid` on the report and a stderr warning. Do not quote
   a 30×10 grid as N=20 / 164.

5. **Leave SKYT / Gate 0 / Table 1–2 headlines alone.** Same cluster bootstrap
   already lives in `src/repeatability_protocol.py`. This pass does not retune
   published 56.9% / 67.4% or overwrite frozen trees.

## What this does not fix

- 30 tasks is still a convenience sample. The code can label `pilot_grid`; it
  cannot invent a superpopulation. Full HumanEval+ (164 × *N*=20) is
  `python -m benchmark full`: paid API, new `--out-dir`, default refuse.
- Binary same/not-same stays. Discriminant is [`STEP4_DISCRIMINANT.md`](STEP4_DISCRIMINANT.md).
- Humans are still Phase 5.

## Paper one-liner

Intervals are a **task-clustered bootstrap**, not a binomial on pairs. Report
`same@2`, `same@2|cert` (with drop count), and pass rate together, with *N*
and the task count in the same sentence as the headline.
