# SKYT — SBES 2026 Industry Track Artifact

**Paper:** *When the Same Prompt Yields Different Code: Engineering Repeatability with SKYT*
**Venue:** 40th Brazilian Symposium on Software Engineering (SBES 2026), Industry Track
**Authors:** Heitor Roriz (Massimus), Humberto Plinio Ribeiro (Wisi Group), Nasser Jazdi-Motlagh (University of Stuttgart), Vicente Lucena (UFAM)

This folder contains the LaTeX source, bibliography, and analysis scripts for the SBES 2026 submission. It points to the experimental data and reproduction scripts in the rest of the repository.

**Permanent artifact URL:** <https://github.com/HeitorRoriz/skyt_experiment/tree/sbes2026-submission/paper/cbsoft2026>

> **Post-submission correction (2026-08-26):** the original pipeline measured
> behavioral correctness on raw outputs but did not persist independent
> post-repair oracle results. Sandboxed revalidation of all 3,600 SBES-scope
> repaired outputs found 14 behavioral regressions (post pass rate 97.7% vs
> 98.1% pre). None occurred in GPT-4o-mini; 13 occurred in GPT-4o and one in
> Claude. The broad claim that no canonicalization step regressed any model is
> withdrawn. The runtime now validates and rolls back every final repair.

---

## Reproducibility snapshot

The exact state of the codebase that produced the paper numbers is preserved as the immutable Git tag:

```
git checkout sbes2026-submission
```

---

## Experimental scope

| | |
|---|---|
| Total generations | **3,600** |
| Algorithmic contracts | 12 |
| Commercial LLMs | 3 (GPT-4o-mini, GPT-4o, Claude Sonnet 4.5) |
| Decoding temperatures | 5 (0.0, 0.3, 0.5, 0.7, 1.0) |
| Runs per (contract × model × temperature) | 20 |

Raw aggregated metrics are in [`outputs/metrics_summary.csv`](../../outputs/metrics_summary.csv) at the repo root.

---

## Headline results (Table 1 of the paper)

SKYT repeatability across three tasks and three commercial LLMs, pooled across five temperatures (0.0–1.0). Each cell aggregates 66–100 generations.

| Task | Model | R<sub>raw</sub> | R<sub>pre</sub> | R<sub>post</sub> | Δ |
|---|---|---:|---:|---:|---:|
| Balanced Brackets | GPT-4o-mini       | 0.31 | 0.36 | 0.80 | **+0.43** |
| Balanced Brackets | GPT-4o            | 0.27 | 0.00 | 0.00 | +0.00 |
| Balanced Brackets | Claude Sonnet 4.5 | 0.80 | 0.00 | 0.00 | +0.00 |
| Binary Search     | GPT-4o-mini       | 0.47 | 0.02 | 0.30 | **+0.29** |
| Binary Search     | GPT-4o            | 0.61 | 0.34 | 0.51 | +0.17 |
| Binary Search     | Claude Sonnet 4.5 | 0.83 | 0.00 | 0.00 | +0.00 |
| Slugify           | GPT-4o-mini       | 0.60 | 0.58 | 0.75 | **+0.17** |
| Slugify           | GPT-4o            | 0.32 | 0.02 | 0.09 | +0.07 |
| Slugify           | Claude Sonnet 4.5 | 0.66 | 0.00 | 0.00 | +0.00 |

**Key claims (with anchors in the data):**

- **17–43 percentage-point improvement** for GPT-4o-mini across the three most diverse contracts (Δ column above).
- **Peak rescue Δ = +0.95** — binary search, GPT-4o-mini, T = 0.0, n = 20.
- **100% raw behavioral correctness** across all 1,200 GPT-4o-mini generations; post-repair revalidation also found no GPT-4o-mini regression. Across all models, however, 14/3,600 repaired outputs regressed (see correction above).
- **Strongest temperature effect:** balanced brackets at T = 0.7 — R<sub>raw</sub> = 0.15 rescued to R<sub>post</sub> = 0.70 (Δ = +0.45, n = 20).

---

## Reproducing the paper numbers

The two scripts in this folder regenerate every headline number directly from `outputs/metrics_summary.csv`:

```bash
# From the repo root
python paper/cbsoft2026/extract_paper_numbers.py
python paper/cbsoft2026/rescue_deep_dive.py
```

To re-run the full 3,600-generation experiment from scratch (requires OpenAI and Anthropic API keys, ~2–4 hours of LLM calls):

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in OPENAI_API_KEY and ANTHROPIC_API_KEY
python reproduce_paper_results.py
```

---

## Files in this folder

| File | Purpose |
|---|---|
| `main.tex` | Paper source (sigconf acmart class, CBSoft template) |
| `references.bib` | Bibliography (12 entries, all cited in `main.tex`) |
| `acmart.cls`, `ACM-Reference-Format.bst` | ACM class files for offline compilation |
| `extract_paper_numbers.py` | Pulls per-cell headline numbers from `metrics_summary.csv` |
| `rescue_deep_dive.py` | Multi-angle Δ analysis (per-cell, per-(contract, model), per-contract, by temperature, distribution buckets) |
| `PLAN.md` | Internal planning notes for the submission |

---

## License

- **Code:** MIT (see [`LICENSE.txt`](../../LICENSE.txt))
- **Data and documentation:** CC-BY-4.0

---

## Citation

```bibtex
@inproceedings{roriz2026skyt,
  title     = {When the Same Prompt Yields Different Code:
               Engineering Repeatability with {SKYT}},
  author    = {Roriz, Heitor and Ribeiro, Humberto Plinio and
               Jazdi-Motlagh, Nasser and Lucena, Vicente},
  booktitle = {Proceedings of the 40th Brazilian Symposium on
               Software Engineering (SBES 2026), Industry Track},
  year      = {2026},
  publisher = {SBC}
}
```

---

## Contact

Open an issue at <https://github.com/HeitorRoriz/skyt_experiment/issues> for reproducibility questions.
