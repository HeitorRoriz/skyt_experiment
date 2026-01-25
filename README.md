# SKYT: Prompt Contracts for Software Repeatability

**MSR 2026 - Data and Tool Showcase Track**  
**Artifact for Paper Reproduction**

---

## Overview

**SKYT** measures and improves **software repeatability** in LLM-generated code through:

1. **Prompt Contracts** - Structured specifications with behavioral oracles
2. **Canonical Anchoring** - Fixed reference for structural comparison
3. **Property-Based Repair** - AST-level transformations to canonical form

### Research Question

*Can prompt contracts and canonicalization improve repeatability of LLM-generated code under pinned settings?*

---

## Experiment Summary

### Scope

- **12 algorithmic contracts** (sorting, searching, math, string processing)
- **3 model families** (GPT-4o-mini, GPT-4o, Claude Sonnet 4.5)
- **5 temperature settings** (0.0, 0.3, 0.5, 0.7, 1.0)
- **20 runs per configuration**
- **Total: 3,600 LLM generations**

### Key Results

| Task | Model | R_raw | R_anchor_pre | R_anchor_post | Δ_rescue |
|------|-------|-------|--------------|---------------|----------|
| Binary-Search | GPT-4o-mini | 0.49 | 0.25 | 0.50 | **+0.25** |
| Balanced-Brackets | GPT-4o-mini | 0.30 | 0.36 | 0.82 | **+0.46** |
| Slugify | GPT-4o-mini | 0.56 | 0.54 | 0.76 | **+0.22** |

*Aggregated across all temperatures (N=100 per task/model)*

**Key Finding:** Canonicalization improves repeatability by 22-46% for GPT-4o-mini, with the largest improvement on Balanced-Brackets (Δ_rescue = +0.46).

---

## Reproducing Paper Results

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up API keys
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and ANTHROPIC_API_KEY

# 3. Verify existing results match paper
python reproduce_paper_results.py --verify-only
```

### Full Reproduction

```bash
# Run all 3,600 experiments (requires API keys, ~2-4 hours)
python reproduce_paper_results.py
```

### Granular Experiments

```bash
# Single experiment
python main.py --contract binary_search \
  --model gpt-4o-mini --temperature 0.5 --runs 20

# Full evaluation (all 12 contracts)
python run_phase2_full.py
```

---

## Experimental Data

All experimental data is in `outputs/`:

### `metrics_summary.csv`
Aggregated metrics for all 180 configurations (12 contracts × 3 models × 5 temps):
- `R_raw` - Raw repeatability (byte-identical)
- `R_anchor_pre` - Canon match before repair
- `R_anchor_post` - Canon match after repair
- `Delta_rescue` - Improvement (R_anchor_post - R_anchor_pre)
- `R_behavioral` - Oracle pass rate
- `R_structural` - Structural constraint pass rate

### Per-Run JSON Files
Detailed logs for each experiment configuration:
- Raw LLM outputs
- Canonical anchor
- Oracle test results
- Property distances
- Transformation steps

**Example:** `outputs/binary_search_temp0.5_20260123_115030.json`

---

## Repository Structure

```
skyt_experiment/
├── README.md                    # This file
├── reproduce_paper_results.py   # Single-command reproduction
├── main.py                      # CLI for experiments
├── requirements.txt             # Python dependencies
│
├── src/                         # Core implementation
│   ├── llm_client.py            # Multi-provider LLM client
│   ├── contract.py              # Contract system
│   ├── oracle_system.py         # Behavioral testing
│   ├── canon_system.py          # Canonical anchoring
│   ├── code_transformer.py      # Property-based repair
│   ├── foundational_properties.py  # 13 semantic properties
│   ├── metrics.py               # Repeatability metrics
│   └── enhanced_stats.py        # Statistical analysis
│
├── contracts/
│   └── templates.json           # 12 algorithmic contracts
│
└── outputs/
    ├── metrics_summary.csv      # Aggregated results
    └── *.json                   # Per-run detailed logs
```

---

## Metrics Explained

### R_raw (Raw Repeatability)
Proportion of byte-identical outputs under pinned settings.

### R_anchor_pre (Pre-Repair Canon Match)
Proportion of outputs matching canonical anchor before repair.

### R_anchor_post (Post-Repair Canon Match)
Proportion of outputs matching canonical anchor after property-based repair.

### Δ_rescue (Rescue Delta)
Improvement from repair: `R_anchor_post - R_anchor_pre`

**Interpretation:**
- Δ_rescue > 0: Repair successfully increases canon alignment
- Δ_rescue = 0: No improvement (outputs already canonical or too diverse)

---

## Statistical Rigor

All results include:

1. **Wilson 95% Confidence Intervals** (for proportions with n=20)
2. **Fisher's Exact Test** (for comparing pre/post repair)
3. **Effect Sizes** (Cohen's h, odds ratios)
4. **Holm-Bonferroni Correction** (for multiple comparisons)

See `src/enhanced_stats.py` for implementation details.

---

## Contracts Evaluated

### Numeric (5 tasks)
- Fibonacci (iterative)
- Fibonacci (recursive)
- Factorial
- GCD (Euclidean algorithm)
- Primality test

### String (2 tasks)
- Slugify (URL normalization)
- Palindrome check

### Data Structures (2 tasks)
- Balanced brackets (stack-based)
- LRU Cache (OrderedDict)

### Sorting/Searching (3 tasks)
- Binary search
- Merge sort
- Quick sort

---

## Key Findings

1. **Temperature Effect:** R_raw decreases with temperature (more diversity), but canonicalization maintains structural repeatability.

2. **Model Differences:** 
   - GPT-4o-mini: Best rescue performance (Δ_rescue up to +0.46)
   - Claude Sonnet: High raw repeatability but poor canon alignment (different structural patterns)

3. **Task Complexity:** 
   - Simple tasks (GCD, Fibonacci): High baseline repeatability
   - Complex tasks (Binary-Search, Balanced-Brackets): Larger improvement from canonicalization

---

## Citation

```bibtex
@inproceedings{skyt2026,
  title     = {SKYT: Prompt Contracts for Software Repeatability in LLM-Assisted Development},
  author    = {[Authors]},
  booktitle = {Proceedings of the 23rd International Conference on Mining Software Repositories (MSR)},
  series    = {MSR '26},
  year      = {2026},
  publisher = {ACM},
  note      = {Data and Tool Showcase Track}
}
```

---

## License

- **Code:** MIT License
- **Data:** CC-BY-4.0
- **Documentation:** CC-BY-4.0

---

## Contact

**Repository:** https://github.com/HeitorRoriz/skyt_experiment  
**Branch:** `camera-ready-msr2026`

For questions about reproduction or artifact usage, please open an issue on GitHub.

---

## Acknowledgments

We thank the MSR 2026 reviewers for their constructive feedback and Professor Nasser for statistical methodology guidance.
