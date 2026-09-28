# SameEval

Replication package for the FSE 2027 research paper *SameEval: A Structural Repeatability Benchmark for LLM Code Generation*.

SameEval is an overlay on an existing benchmark. It does not add prompts or tests. It reports whether two independent generations from the same prompt both pass the benchmark tests and share a canonical-form fingerprint (`same@2`). A second column, `same@2|cert`, asks that question among passing generations only.

The paper is `paper/fse2027/main.tex`.

## This study

HumanEval+, all 164 tasks, 20 generations per configuration.

| Pool | Configurations | Generations |
|---|---:|---:|
| Four models at temperatures 0.0 and 0.7 | 1,312 | 26,240 |
| One model at provider-default sampling | 164 | 3,280 |
| Total | 1,476 | 29,520 |

On the four-model pool, Plus pass is 86.4% and `same@2` is 67.7%. The fifth model passes 92.9% of the time and has `same@2` 66.3%. The mitigation comparison uses only the original two models (GPT-4o-mini and Claude Sonnet 4.5). On static prompts, replaying a stored program is the repeatability ceiling.

Certified means the fingerprinter parses the program and the HumanEval+ suite passes. Fingerprints use `relation_version` 2.

## Other papers in this repository

`paper/cbsoft2026/` and `paper/msr2026/` are earlier papers. They use different tasks and different generation totals. Do not read their figures as results of this study.

## Recompute

Every number in the paper is printed by one of the commands below. They read the stored generations. No language-model calls are required. The Level-2 replay needs Docker.

```bash
pip install -r requirements.txt
```

Intervals are a cluster bootstrap by task: 10,000 resamples, seed `20260723`. The human-study interval resamples pairs inside each design stratum with the same seed.

**Main table, per-cell rows.** One tree per command. Write each report to a new directory.

```bash
python -m benchmark score --source-dir outputs/benchmark/humaneval_plus_164_n20 --out-dir outputs/benchmark/score_original
python -m benchmark score --source-dir outputs/benchmark/humaneval_plus_164_n20_expansion/haiku45 --out-dir outputs/benchmark/score_haiku45
python -m benchmark score --source-dir outputs/benchmark/humaneval_plus_164_n20_expansion/luna --out-dir outputs/benchmark/score_luna
python -m benchmark score --source-dir outputs/benchmark/humaneval_plus_164_n20_expansion/sonnet5 --out-dir outputs/benchmark/score_sonnet5
```

**Main table, pooled rows and model-pair deltas.**

```bash
python -m benchmarks.humaneval_plus.expansion_analyze
```

**Temperature intervals, human study, and diff cost.**

```bash
python -m skyt.fse_final_posthoc tgrid
python -m skyt.fse_final_posthoc human
python -m skyt.fse_final_posthoc diffcost
```

`tgrid` prints the paired temperature table. `human` prints the human-study table, the kappa interval, the reweighted rates, and the implementation-level disagreement. `diffcost` prints changed lines for fingerprint-same and fingerprint-different pairs. JSON is written under `outputs/benchmark/fse_final_posthoc/`.

**Three-ruler overlay, held-out columns, mitigation, and cache.**

```bash
python -m skyt.zero_api_analysis
python -m skyt.heldout_robust --analyze-only
python -m skyt.oracle_split_posthoc
python -m skyt.oracle_fair
```

`zero_api_analysis` prints the overlay column of the fingerprint table. `heldout_robust --analyze-only` reprints the held-out ruler columns and the nested splits from the stored programs (no repair, no Docker). `oracle_split_posthoc` prints the held-out mitigation table and the certified-disagreement table. `oracle_fair` prints the cache baselines.

**Diversity signal.** The `--out` path must not contain `heldout`, `oracle_split`, `expansion`, or `gate0`.

```bash
python -m benchmark.diversity_signal --trees outputs/benchmark/humaneval_plus_164_n20 --out outputs/benchmark/diversity_signal
python -m benchmark.diversity_signal --trees outputs/benchmark/humaneval_plus_164_n20 outputs/benchmark/humaneval_plus_164_n20_expansion/haiku45 outputs/benchmark/humaneval_plus_164_n20_expansion/luna outputs/benchmark/humaneval_plus_164_n20_expansion/sonnet5 --out outputs/benchmark/diversity_signal_model_replication
```

The first command prints the pre-specified rows. The second prints the five-model replication. The dated RQ3 analysis plan is `paper/fse2027/rq3_analysis_plan_2026-09-24.md`.

**Level ablation.** The second command is the Level-2 replay and requires Docker.

```bash
python -m skyt.level_ablation --max-level 3
python -m skyt.humaneval_oracle_split --max-transformation-level 2 --out-dir outputs/benchmark/humaneval_plus_164_n20_skyt_heldout_oracle_split_l2
```

## Pins

- Dataset: `evalplus==0.3.1`, HumanEvalPlus `v0.1.10`, MD5 `916d9bfe7b490c2447245ec91595fa4f`
- Scoring sandbox: `python:3.13-slim`, network disabled. The image digest is recorded with the generations.
- Generations: `outputs/benchmark/humaneval_plus_164_n20` and `outputs/benchmark/humaneval_plus_164_n20_expansion`
- Human labels: `outputs/benchmark/fingerprint_annotation_dual`

## Layout

```
paper/fse2027/          paper source and figures
benchmark/              overlay scorer
benchmarks/humaneval_plus/   HumanEval+ adapter and expansion analysis
skyt/                   held-out, cache, ablation, and post hoc scripts
outputs/benchmark/      stored generations and annotation sheets
```

## License

Code is under the MIT license in `LICENSE.txt`.
