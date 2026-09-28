# SameEval

Replication package for the FSE 2027 research paper
**SameEval: A Structural Repeatability Benchmark for LLM Code Generation**.

SameEval is an overlay on an existing benchmark. It adds no prompts and no tests. It reports whether two independent generations from the same prompt both pass the benchmark tests and share a canonical-form fingerprint (**same@2**). A second column, **same@2|cert**, asks the same question among passing generations only.

- *Certified* means the fingerprinter parses the program and the full HumanEval+ suite passes.
- Fingerprints use `relation_version` 2.

## What this package reproduces

HumanEval+, all 164 tasks, 20 generations per configuration.

| Pool | Configurations | Generations |
|---|---:|---:|
| Four models at temperatures 0.0 and 0.7 | 1,312 | 26,240 |
| One model at provider-default sampling | 164 | 3,280 |
| **Total** | **1,476** | **29,520** |

Headline results:

- On the four-model pool, Plus pass is 86.4% and same@2 is 67.7%.
- The fifth model passes 92.9% of the time and has same@2 66.3%.
- The mitigation comparison uses the original two models only. On static prompts, replaying a stored program is the repeatability ceiling.

**No language-model calls and no API keys are needed.** Every number is recomputed from the stored generations.

## Requirements

- Python 3.13
- `pip install -r requirements.txt`
- Docker, only for the Level-2 replay (Table 9, row L1+L2). No other command needs Docker.
- Disk: about 640 MB for `outputs/benchmark`.
- Runtime: each command takes minutes, except the Level-2 replay. The stored Level-2 run took about 31 hours.

## Quick check (under 5 minutes)

```bash
pip install -r requirements.txt

# 1. Unit tests cited in the paper (Section 5.5)
python -m pytest -q tests/test_benchmark_inference.py tests/test_annotation_score.py \
  tests/test_annotation_sample.py tests/test_heldout_posthoc.py \
  tests/test_diversity_signal.py tests/test_fse_final_posthoc.py

# 2. Record count: expect 29520
# Count only the four generation directories. A recursive search also
# picks up batch and raw JSONL files and will not equal 29520.
python -c "import pathlib; roots=['outputs/benchmark/humaneval_plus_164_n20','outputs/benchmark/humaneval_plus_164_n20_expansion/haiku45','outputs/benchmark/humaneval_plus_164_n20_expansion/luna','outputs/benchmark/humaneval_plus_164_n20_expansion/sonnet5']; print(sum(1 for d in roots for p in pathlib.Path(d).glob('*.jsonl') for line in open(p, encoding='utf-8') if line.strip()))"

# 3. One headline number: the temperature table (Table 2)
python -m skyt.fse_final_posthoc tgrid     # GPT-4o-mini: Δ same@2 = -25.4 [-29.8, -21.1]
```

## Paper element → command

Intervals are a cluster bootstrap by task (10,000 resamples, seed 20260723). The human-study interval resamples pairs within each design stratum, using the same seed.

The "Expected" column gives one value per element, for a quick check.

| Paper element | Command | Expected |
|---|---|---|
| Table 1, per-cell rows | `benchmark score` (one per tree, below) | GPT-4o-mini T=0.0: Plus pass 79.3 |
| Table 1, pooled rows; model-pair deltas (Sec. 6.2) | `python -m benchmarks.humaneval_plus.expansion_analyze` | All T-grid: same@2 67.7 |
| Table 2 (temperature) | `python -m skyt.fse_final_posthoc tgrid` | Haiku 4.5: Δ same@2 −28.0 |
| Diff cost (Sec. 6.1) | `python -m skyt.fse_final_posthoc diffcost` | median changed lines 7–14 |
| Table 3, κ CI, reweighted rates, implementation-level disagreement (Sec. 8) | `python -m skyt.fse_final_posthoc human` | κ 0.41 [0.26, 0.55] |
| Sample-size reliability (Sec. 6.2) | `python -m benchmarks.humaneval_plus.expansion_split_half` | split-half r₁₀ 0.89–0.98 |
| Table 4, overlay column | `python -m skyt.zero_api_analysis` | SameEval ruler 65.9 |
| Table 4, held-out columns; nested splits (Sec. 6.4.5) | `python -m skyt.heldout_robust --analyze-only` | SameEval ruler Δ +17.1 |
| Table 5, original rows | `diversity_signal`, first command below | A1 Δ 0.06 |
| Table 5, replication rows | `diversity_signal`, second command below | within-task ρ 0.04 |
| Uniformity check (Sec. 6.3) | `diversity_signal --posthoc-uniformity`, below | 65.0% [50.0, 80.3]. The paper's 53.3% [34.7, 72.0] keeps only configs with at least two distinct Base-passing forms; this flag does not apply that filter. |
| Tables 6 and 8; temperature interaction (Sec. 6.4.3) | `python -m skyt.oracle_split_posthoc` | same@2 66.1 → 83.1 |
| Table 7 (cache baselines) | `python -m skyt.oracle_fair` | First-cache same@2 84.9 |
| Table 9, L3-only row | `python -m skyt.level_ablation --max-level 3` | same@2 84.2 |
| Table 9, L1+L2 row (Docker) | Level-2 replay, below | same@2 66.4 |
| Figure 1 | `python paper/fse2027/make_figure1.py` | |
| Figure 2 | `python paper/fse2027/make_figure_diversity.py` | |
| Figures 3, 4, 5 | `python paper/fse2027/make_figure_skyt.py` | |

Table 10 (the protocol) is derived from the results above and has no command of its own.

### Full commands

Main table, per-cell rows. Run one command per tree, and write each report to a new directory:

```bash
python -m benchmark score --source-dir outputs/benchmark/humaneval_plus_164_n20 --out-dir outputs/benchmark/score_original
python -m benchmark score --source-dir outputs/benchmark/humaneval_plus_164_n20_expansion/haiku45 --out-dir outputs/benchmark/score_haiku45
python -m benchmark score --source-dir outputs/benchmark/humaneval_plus_164_n20_expansion/luna --out-dir outputs/benchmark/score_luna
python -m benchmark score --source-dir outputs/benchmark/humaneval_plus_164_n20_expansion/sonnet5 --out-dir outputs/benchmark/score_sonnet5
```

Diversity signal, original rows then the five-model replication. The `--out` path must not contain `heldout`, `oracle_split`, `expansion`, or `gate0`.

```bash
python -m benchmark.diversity_signal --trees outputs/benchmark/humaneval_plus_164_n20 --out outputs/benchmark/diversity_signal
python -m benchmark.diversity_signal --trees outputs/benchmark/humaneval_plus_164_n20 \
  outputs/benchmark/humaneval_plus_164_n20_expansion/haiku45 \
  outputs/benchmark/humaneval_plus_164_n20_expansion/luna \
  outputs/benchmark/humaneval_plus_164_n20_expansion/sonnet5 \
  --out outputs/benchmark/diversity_signal_model_replication
```

Uniformity check. This writes `posthoc_uniformity.json` next to the diversity-signal report and does not rewrite that report. The printed rate is 65.0% [50.0, 80.3].

```bash
python -m benchmark.diversity_signal --trees outputs/benchmark/humaneval_plus_164_n20 \
  --out outputs/benchmark/diversity_signal --posthoc-uniformity
```

Split-half reliability. Writes `outputs/benchmark/humaneval_plus_164_n20_expansion/analysis/t6_split_half.json`.

```bash
python -m benchmarks.humaneval_plus.expansion_split_half
```

Level-2 replay (requires Docker):

```bash
python -m skyt.humaneval_oracle_split --max-transformation-level 2 \
  --out-dir outputs/benchmark/humaneval_plus_164_n20_skyt_heldout_oracle_split_l2
```

The post hoc commands write their JSON under `outputs/benchmark/fse_final_posthoc/`.

## RQ3 analysis plan

The exploratory RQ3 analysis (Sec. 5.3) was pre-specified in a dated plan, written before computation:
`paper/fse2027/rq3_analysis_plan_2026-09-24.md` (dated 2026-09-24).

## Pins

- **Dataset:** `evalplus==0.3.1`, HumanEvalPlus v0.1.10, MD5 `916d9bfe7b490c2447245ec91595fa4f`.
- **Scoring sandbox:** `python:3.13-slim`, network disabled. The image SHA-256 digest is recorded with the generations.
- **Models:**

  | Model | Identifier | Generated |
  |---|---|---|
  | GPT-4o-mini | alias | 17–18 Sep 2026 |
  | Claude Sonnet 4.5 | `claude-sonnet-4-5-20250929` | 16–18 Sep 2026 |
  | Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | 24–25 Sep 2026 |
  | GPT-6 Luna | `gpt-6-luna` (alias) | 24–25 Sep 2026 |
  | Claude Sonnet 5 | `claude-sonnet-5` (alias) | 24–25 Sep 2026 |

- **Bootstrap:** seed 20260723, 10,000 resamples.

## Layout

```
benchmark/                   overlay scorer (same@2, same@2|cert, fingerprint)
benchmarks/humaneval_plus/   HumanEval+ adapter and pooled analysis
skyt/                        held-out, cache, ablation, and post hoc scripts
tests/                       unit tests
paper/fse2027/               figure scripts
outputs/benchmark/
  humaneval_plus_164_n20/              original two models (13,120 generations)
  humaneval_plus_164_n20_expansion/    Haiku 4.5, Luna, Sonnet 5 (16,400 generations)
  fingerprint_annotation_dual/         human-study kit: blind sheets, both filled sheets, gold
```

Each generation is one JSON line with the task, model, temperature, run index, extracted program (`stitched_code`), and oracle outcome.

## License

- **Code:** MIT (`LICENSE.txt`).
- **Generations and annotation labels:** CC-BY-4.0.
