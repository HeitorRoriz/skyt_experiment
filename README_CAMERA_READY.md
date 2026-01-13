# SKYT: Prompt Contracts for Software Repeatability in LLM-Assisted Development

**MSR 2026 - Data and Tool Showcase Track (Accepted)**  
**Camera-Ready Branch:** `camera-ready-msr2026`

---

## Overview

**SKYT** is a middleware framework that measures and improves **software repeatability** in LLM-assisted code generation. It treats repeatability as a pinned-pipeline property through:

1. **Prompt Contracts** - Versioned specifications with constraints and oracles
2. **Canonical Anchoring** - Fixed reference implementation for normalization
3. **Property-Based Transformation** - AST-level repair to canonical form

### Key Metrics

- **R_raw** - Raw repeatability (byte-identical outputs)
- **R_structural** - Structural repeatability (post-canonicalization)
- **Δ_rescue** - Improvement from canonicalization (R_structural - R_raw)

---

## What's New in Camera-Ready Version

### ✅ Expanded Evaluation

- **Models:** 3 models (was 1)
  - GPT-4o-mini
  - GPT-5.2
  - Claude Sonnet 4.5
- **Contracts:** 12 contracts (was 5)
  - Added: quick_sort, factorial, is_palindrome, is_prime, gcd, brackets_balanced, longest_common_subsequence
- **Runs:** 20 runs per contract (was 10)
- **Total:** 3,600 generations (was 250)

### ✅ Statistical Rigor

Implemented per Professor Nasser's recommendations:

1. **Confidence Intervals**
   - Wilson score (small samples)
   - Bootstrap (any statistic)

2. **Statistical Tests**
   - Fisher's exact test (n=20)
   - Wilcoxon signed-rank test

3. **Effect Sizes**
   - Cohen's h
   - Odds ratios
   - Absolute/relative improvement

4. **Multiple Comparison Correction**
   - Holm-Bonferroni method

### ✅ Comprehensive Documentation

- **DISTANCE_METRICS.md** - Metric justification and anchor selection
- **STATISTICAL_METHODS.md** - Complete statistical methods with references
- **LIMITATIONS.md** - Threats to validity (internal, external, construct)
- **DISCUSSION_CAMERA_READY.md** - N-Version Programming comparison
- **MULTI_FILE_ROADMAP.md** - 12-week plan for multi-file support
- **REVIEWER_RESPONSES.md** - All reviewer concerns mapped to solutions

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/HeitorRoriz/skyt_experiment.git
cd skyt_experiment

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Set Up API Keys

```bash
# Create .env file
cp .env.example .env

# Add your API keys
echo "OPENAI_API_KEY=your_key_here" >> .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env
```

### Run Single Experiment

```bash
# Run fibonacci contract with GPT-4o-mini
python main.py --contract fibonacci --runs 20 --temperature 0.7 --model gpt-4o-mini
```

### Run Full Evaluation

```bash
# Run all 12 contracts × 3 models × 5 temperatures × 20 runs
python scripts/run_full_experiments.py
```

---

## Repository Structure

```
skyt_experiment/
├── README.md                           # This file
├── DISTANCE_METRICS.md                 # Metric justification (addresses reviewer concerns)
├── STATISTICAL_METHODS.md              # Statistical rigor documentation
├── LIMITATIONS.md                      # Threats to validity
├── DISCUSSION_CAMERA_READY.md          # N-Version Programming comparison
├── CROSS_MODEL_SUPPORT.md              # Multi-model evaluation details
├── MULTI_FILE_ROADMAP.md               # Future work: multi-file support
├── REVIEWER_RESPONSES.md               # Reviewer concern mapping (16/19 addressed)
├── DOCUMENTATION_INDEX.md              # Complete documentation organization
│
├── main.py                             # CLI entry point
├── requirements.txt                    # Python dependencies
│
├── src/                                # Core implementation
│   ├── llm_client.py                   # Multi-provider LLM client
│   ├── contract.py                     # Contract system
│   ├── oracle_system.py                # Behavioral testing
│   ├── canon_system.py                 # Canonical anchoring
│   ├── code_transformer.py             # AST-level transformations
│   ├── metrics.py                      # Three-tier metrics
│   ├── simple_stats.py                 # Basic statistics (Wilcoxon)
│   ├── enhanced_stats.py               # Rigorous statistics (Fisher, Cohen's h, Holm-Bonferroni)
│   └── comprehensive_experiment.py     # Experiment pipeline
│
├── tests/                              # Test suite (27 tests, all passing)
│   ├── test_simple_stats.py
│   ├── test_enhanced_stats.py
│   └── ...
│
├── contracts/                          # Contract templates
│   └── templates.json                  # 12 algorithmic contracts
│
├── docs/                               # Reference documentation
│   ├── IMPLEMENTATION_COMPLETE.md
│   ├── METRICS_IMPLEMENTATION.md
│   └── archive/                        # Historical documentation
│
├── api/                                # Production API (FastAPI)
├── workers/                            # Background workers (Celery)
└── web/                                # Frontend (React)
```

---

## Core Concepts

### 1. Prompt Contracts

Versioned specifications with:
- **Constraints:** Type hints, naming conventions, complexity bounds
- **Oracle:** Behavioral test cases
- **Normalization rules:** AST-level transformations

Example:
```json
{
  "contract_id": "fibonacci",
  "function_name": "fibonacci",
  "constraints": {
    "max_lines": 20,
    "allowed_imports": ["typing"],
    "naming_pattern": "^[a-z_][a-z0-9_]*$"
  },
  "oracle": {
    "test_cases": [
      {"input": [0], "expected": 0},
      {"input": [1], "expected": 1},
      {"input": [10], "expected": 55}
    ]
  }
}
```

### 2. Canonical Anchoring

- **Anchor:** First contract-adherent, oracle-passing output
- **Purpose:** Fixed reference for measuring structural distance
- **Properties:** Deterministic, objective, reproducible

**Note:** "First" is pragmatic, not optimal. See LIMITATIONS.md §4.2 for quality-based selection as future work.

### 3. Property-Based Transformation

13 foundational properties for semantic equivalence:
- Statement ordering
- Logical equivalence
- Normalized AST structure
- Control flow signature
- Variable naming
- ... and 8 more

Transformations bring outputs closer to canonical form while preserving behavior.

---

## Metrics Explained

### R_raw (Raw Repeatability)

**Definition:** Proportion of output pairs that are byte-identical.

**Formula:**
```
R_raw = (# identical pairs) / (# total pairs)
```

**Interpretation:**
- R_raw = 1.0: Perfect repeatability (all outputs identical)
- R_raw = 0.0: No repeatability (all outputs different)

### R_structural (Structural Repeatability)

**Definition:** Proportion of output pairs with identical AST structure after canonicalization.

**Formula:**
```
R_structural = (# structurally identical pairs) / (# total pairs)
```

**Interpretation:**
- R_structural ≥ R_raw (always)
- Measures repeatability after removing surface-level variance

### Δ_rescue (Canonicalization Improvement)

**Definition:** Improvement in repeatability from canonicalization.

**Formula:**
```
Δ_rescue = R_structural - R_raw
```

**Interpretation:**
- Δ_rescue > 0: Canonicalization improves repeatability
- Δ_rescue = 0: No improvement (outputs already identical or too diverse)

---

## Statistical Analysis

All experiments report:

1. **Descriptive Statistics**
   ```
   R_raw: 0.45 ± 0.03 [0.38, 0.52] (95% CI)
   R_structural: 0.78 ± 0.02 [0.75, 0.81] (95% CI)
   ```

2. **Significance Testing**
   ```
   Fisher's exact test: p=0.0023 *
   Odds ratio: 9.0 (9× higher odds of success)
   ```

3. **Effect Sizes**
   ```
   Cohen's h: 0.72 (medium effect)
   Absolute improvement: +0.33
   Relative improvement: +73%
   ```

4. **Multiple Comparison Correction**
   ```
   Significant contracts: 8/12 (Holm-Bonferroni, α=0.05)
   ```

See **STATISTICAL_METHODS.md** for complete methodology.

---

## Reproducibility

### Pinned Environment

All experiments use:
- **Python:** 3.10+
- **Models:** Exact version identifiers (e.g., `gpt-4-0613`)
- **Temperature:** Fixed per experiment
- **Seeds:** Deterministic where possible

### Replication Package

Available on Zenodo (link TBD):
- All 12 contracts
- Experiment runner scripts
- Raw experimental data (3,600 generations)
- Analysis scripts
- Complete documentation

---

## Limitations

### Current Scope

- **Single-file programs only** (multi-file roadmap in MULTI_FILE_ROADMAP.md)
- **Algorithmic tasks** (12 contracts: sorting, searching, math, string processing)
- **Python only** (multi-language support planned)
- **20 runs per contract** (sufficient for exploratory work, not definitive validation)

### Acknowledged Threats

- **Internal validity:** Anchor selection pragmatic, not optimal
- **External validity:** Results may not generalize beyond algorithmic tasks
- **Construct validity:** Distance metric limitations, oracle adequacy
- **Reproducibility:** API model drift, stochastic behavior

See **LIMITATIONS.md** for comprehensive discussion.

---

## Future Work

### Near-Term (Q1 2026)

1. **Multi-file support** (12-week roadmap in MULTI_FILE_ROADMAP.md)
   - Import graph analysis
   - Cross-file canonicalization
   - Multi-file metrics

2. **Quality-based anchor selection**
   - Multi-dimensional scoring (structural simplicity, code quality, canonicalization potential)
   - Improved Δ_rescue through better anchors

### Long-Term

3. **Multi-language support** (Java, JavaScript, Go)
4. **Real-world evaluation** (web apps, data pipelines, ML code)
5. **Integration with CI/CD** (GitHub Actions, GitLab CI)

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

## Documentation

### For Paper Writing

- **DISTANCE_METRICS.md** - Methods section (metric justification)
- **STATISTICAL_METHODS.md** - Statistical analysis section
- **LIMITATIONS.md** - Threats to validity section
- **DISCUSSION_CAMERA_READY.md** - Discussion section (N-Version comparison)

### For Code Understanding

- **DOCUMENTATION_INDEX.md** - Complete documentation map
- **docs/IMPLEMENTATION_COMPLETE.md** - System architecture
- **docs/METRICS_IMPLEMENTATION.md** - Metrics calculation details

### For Development

- **MULTI_FILE_ROADMAP.md** - Multi-file support plan
- **CLEANUP_GUIDE.md** - Repository organization
- **tests/** - Test suite with 27 passing tests

---

## Contact

**Author:** Heitor Roriz Filho  
**Institution:** [Your Institution]  
**Email:** [Your Email]  
**Repository:** https://github.com/HeitorRoriz/skyt_experiment

---

## License

- **Code:** MIT License
- **Data:** CC-BY-4.0
- **Documentation:** CC-BY-4.0

---

## Acknowledgments

We thank the MSR 2026 reviewers for their constructive feedback, which significantly improved this work. Special thanks to Professor Nasser for statistical methodology guidance.

---

**Status:** Camera-Ready Preparation (16/19 reviewer concerns addressed)  
**Last Updated:** January 13, 2026
