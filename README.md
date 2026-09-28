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

No language-model calls are required. The commands below read the stored generations.

```bash
pip install -r requirements.txt
```

| Result | Command |
|---|---|
| Per-cell rows of the main table | `python -m benchmark score` |
| Pooled rows and model-pair deltas | `python -m benchmarks.humaneval_plus.expansion_analyze` |
| Temperature intervals | `python -m skyt.fse_final_posthoc tgrid` |
| Diff-cost summary | `python -m skyt.fse_final_posthoc diffcost` |
| Human-study table, kappa interval, reweighted rates | `python -m skyt.fse_final_posthoc human` |
| Three-ruler overlay column | `python -m skyt.zero_api_analysis` |
| Held-out ruler columns and nested splits | `python -m skyt.heldout_robust --analyze-only` |
| Diversity signal, pre-registered overlay | `python -m benchmark.diversity_signal --trees outputs/benchmark/humaneval_plus_164_n20` |
| Diversity signal, five-model replication | `python -m benchmark.diversity_signal --trees outputs/benchmark/humaneval_plus_164_n20 outputs/benchmark/humaneval_plus_164_n20_expansion/haiku45 outputs/benchmark/humaneval_plus_164_n20_expansion/luna outputs/benchmark/humaneval_plus_164_n20_expansion/sonnet5` |
| Held-out mitigation table and certified disagreement | `python -m skyt.oracle_split_posthoc` |
| Cache baselines | `python -m skyt.oracle_fair` |
| Level ablation | `python -m skyt.level_ablation --max-level 3` and `python -m skyt.humaneval_oracle_split --max-transformation-level 2` |

Intervals are a cluster bootstrap by task: 10,000 resamples, seed `20260723`.

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
