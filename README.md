# Skyt: Prompt Contracts for Software Repeatability in LLM-Assisted Development

> **Artifact for MSR 2026 (Data & Tool Showcase Track)**  
> Companion repository for the paper: *"Skyt: Prompt Contracts for Software Repeatability in LLM-Assisted Development"*

**Same prompt, different code** is the default for LLMs; **Skyt** makes **same prompt, same code** a measurable, enforceable pipeline property.

---

## Overview

**Skyt** is a lightweight, schema-bound middleware that transforms stochastic LLM code generation into an auditable, quality-controlled process suitable for CI/CD pipelines, compliance contexts, and production deployment.

### Core Capabilities

Skyt measures and enforces **repeatability** as a pinned-pipeline property through:

- **📋 Versioned Contracts**: Schema-bound prompts with acceptance oracles and behavioral constraints
- **⚓ Canonical Anchoring**: Immutable reference fixed at first contract-compliant output
- **🔧 Monotonic Repair**: Bounded AST-level transformations (variable renaming, clause normalization) that preserve correctness
- **📊 Comprehensive Metrics**: R_raw, R_anchor (pre/post), Δ_rescue, R_behavioral, R_structural, distributional measures (Δμ, ΔP_τ)

### Key Results

Across 250 generations (5 contracts × 5 temperatures × 10 runs):
- **Anchored repeatability gains**: 0.00 to 0.48 (Δ_rescue)
- **Behavioral correctness maintained**: R_behavioral = 1.00 throughout
- **Monotonicity validated**: All repairs satisfy d_post ≤ d_pre

---

## Repository Structure

```
skyt_experiment/
├── README.md                      # This file
├── DISTRIBUTIONAL_METRICS.md     # Δμ and ΔP_τ documentation
├── LICENSE.txt                    # MIT License
├── requirements.txt               # Python dependencies
│
├── contracts/
│   └── templates.json             # 5 contract definitions (see below)
│
├── src/                           # Core Skyt modules
│   ├── contract.py                # Contract schema and validation
│   ├── llm_client.py              # LLM interface (GPT-4)
│   ├── canon_system.py            # Canonical anchor system
│   ├── oracle_system.py           # Behavioral testing
│   ├── code_transformer.py        # Monotonic repair pipeline
│   ├── metrics.py                 # Comprehensive metrics (R_raw, R_anchor, Δμ, ΔP_τ)
│   ├── foundational_properties.py # 14 property distance computation
│   ├── bell_curve_analysis.py     # Distributional visualization
│   └── comprehensive_experiment.py # Main experiment runner
│
├── main.py                        # CLI entry point
├── verify_metrics.py              # Quick verification script
│
├── outputs/                       # Experiment results (generated)
│   ├── final_YYYY-MM-DD/          # Date-stamped experiment runs
│   │   ├── {contract}_temp{X}_{timestamp}.json  # Complete run data
│   │   ├── canon/{contract}_canon.json          # Canonical anchors
│   │   ├── metrics_summary.csv                  # Aggregate metrics
│   │   └── analysis/*.png                       # Visualizations
│
└── tests/                         # Test suite
    ├── test_integration.py
    ├── test_transformation_validation.py
    └── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.9+
- OpenAI API key (GPT-4 access)

### 1. Environment Setup

```bash
# Clone repository (adjust URL for your setup)
git clone <repository-url>
cd skyt_experiment

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export OPENAI_API_KEY=your_api_key_here  # On Windows: set OPENAI_API_KEY=your_api_key_here
```

### 2. Run a Single Experiment

```bash
# Basic experiment: Fibonacci, 10 runs, temperature 0.3
python main.py --contract fibonacci_basic --runs 10 --temperature 0.3

# View results
cat outputs/metrics_summary.csv
```

### 3. Reproduce Paper Results (Temperature Sweep)

```bash
# Run full temperature sweep for one contract
python main.py --contract balanced_brackets --sweep --temperatures 0.0 0.2 0.3 0.5 0.7 --runs 10

# Verify distributional metrics are computed
python verify_metrics.py
```

---

## Available Contracts

Skyt includes 5 contracts evaluated in the paper:

| Contract ID | Task | Key Properties | Oracle Tests |
|-------------|------|----------------|--------------|
| `fibonacci_basic` | Iterative Fibonacci | Numerical sequences, base cases | 4 test cases |
| `slugify` | URL slug generation | String normalization, unicode | 6 test cases |
| `balanced_brackets` | Bracket validation | Stack discipline, parsing | 7 test cases |
| `euclid_gcd` | GCD computation | Algebraic invariants, modulo | 6 test cases |
| `binary_search` | Binary search | Boundary conditions, termination | 9 test cases |

Each contract specifies:
- **Task intent**: Natural language description
- **Constraints**: Function name, implementation style, variable naming policy
- **Oracle requirements**: Behavioral test cases with pass/fail thresholds
- **Domain specification**: Input constraints and out-of-domain handling
- **Rescue bounds**: Maximum transformations allowed

Full contract schemas: [`contracts/templates.json`](contracts/templates.json)

---

## Metrics and Analysis

### Core Repeatability Metrics

- **R_raw**: Modal probability mass of byte-identical outputs
- **R_anchor_pre**: Fraction matching canonical anchor before repair
- **R_anchor_post**: Fraction matching canonical anchor after repair
- **Δ_rescue**: R_anchor_post − R_anchor_pre (improvement from repair)

### Distributional Metrics

- **Δμ**: Mean distance reduction (E[d_pre] − E[d_post])
- **ΔP_τ**: Probability mass shift within tolerance τ

See [`DISTRIBUTIONAL_METRICS.md`](DISTRIBUTIONAL_METRICS.md) for details.

### Complementary Metrics

- **R_behavioral**: Oracle pass rate (behavioral correctness)
- **R_structural**: Structural compliance rate
- **Rescue rate**: Fraction of non-canonical outputs successfully repaired
- **Canon coverage**: Fraction passing oracle tests

### Output Files

All metrics are saved in two formats:

1. **JSON** (complete data): `outputs/{experiment_id}.json`
   ```json
   {
     "metrics": {
       "R_raw": 0.38,
       "R_anchor_pre": 0.44,
       "R_anchor_post": 0.92,
       "Delta_rescue": 0.48,
       "R_behavioral": 1.00,
       "R_structural": 0.92,
       "Delta_mu": 0.22,
       "Delta_P_tau": {"tau=0.05": 0.15, "tau=0.1": 0.35, ...}
     }
   }
   ```

2. **CSV** (aggregate): `outputs/metrics_summary.csv`
   - Columns: experiment_id, contract_id, temperature, R_raw, R_anchor_pre/post, Δ_rescue, Δμ, ΔP_τ (4 thresholds), R_behavioral, R_structural, rescue_rate, canon_coverage
   - One row per experiment
   - Easily imported into pandas/R for analysis

---

## CLI Usage

### Basic Commands

```bash
# Single experiment
python main.py --contract <contract_id> --runs <N> --temperature <T>

# Temperature sweep
python main.py --contract <contract_id> --sweep --temperatures <T1> <T2> ... --runs <N>

# Custom output directory
python main.py --contract <contract_id> --runs 10 --temperature 0.5 --output-dir custom_outputs
```

### Examples

```bash
# Reproduce Balanced-Brackets result (Δ_rescue = 0.48)
python main.py --contract balanced_brackets --sweep --temperatures 0.0 0.2 0.3 0.5 0.7 --runs 10

# Reproduce Slugify result (Δ_rescue = 0.16)
python main.py --contract slugify --sweep --temperatures 0.0 0.2 0.3 0.5 0.7 --runs 10

# Reproduce Binary-Search result (Δ_rescue = 0.00, zero-gain task)
python main.py --contract binary_search --sweep --temperatures 0.0 0.2 0.3 0.5 0.7 --runs 10

# Quick test (5 runs, single temperature)
python main.py --contract fibonacci_basic --runs 5 --temperature 0.3
```

---

## Reproducing Paper Results

### Full Reproduction (All Contracts, All Temperatures)

```bash
# Runs 250 LLM generations (5 contracts × 5 temperatures × 10 runs)
# Estimated time: 30-60 minutes depending on API rate limits
# Estimated cost: ~$5-10 in API calls

for contract in fibonacci_basic slugify balanced_brackets euclid_gcd binary_search; do
  python main.py --contract $contract --sweep --temperatures 0.0 0.2 0.3 0.5 0.7 --runs 10
done

# Aggregate results
python verify_metrics.py
cat outputs/metrics_summary.csv
```

### Expected Results (Table 1 from paper)

| Contract | R_raw | R_anchor_pre | R_anchor_post | Δ_rescue | R_behav | R_struct |
|----------|-------|--------------|---------------|----------|---------|----------|
| Balanced Brackets | 0.38 | 0.44 | 0.92 | **0.48** | 1.00 | 0.92 |
| Binary Search | 0.44 | 0.70 | 0.70 | 0.00 | 1.00 | 0.70 |
| Fibonacci | 0.62 | 0.98 | 1.00 | 0.02 | 1.00 | 1.00 |
| Euclid-GCD | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 |
| Slugify | 0.72 | 0.68 | 0.84 | **0.16** | 1.00 | 0.84 |

**Note:** Results may vary slightly due to LLM stochasticity even at low temperatures. Aggregate trends (large/moderate/zero gains) should replicate consistently.

---

## Understanding the Results

### Three Repeatability Patterns

**1. Large Gains (Balanced-Brackets: Δ_rescue = 0.48)**
- High byte-level diversity (R_raw = 0.38)
- But 44% structurally match canon already
- AST-level repair converts 48% of non-canonical outputs
- **Interpretation**: Structural diversity ≠ semantic diversity

**2. Moderate Gains (Slugify: Δ_rescue = 0.16)**
- Naturally higher LLM consistency (R_raw = 0.72)
- Still shows measurable improvement from canonicalization
- **Interpretation**: Even consistent tasks benefit from structural normalization

**3. Zero Gains (Binary-Search, Euclid-GCD: Δ_rescue = 0.00)**
- Binary-Search: Algorithmic equivalences beyond AST scope (different loop conditions)
- Euclid-GCD: Pre-saturated (LLM already produces identical outputs)
- **Interpretation**: Current AST-level transformations have natural limits

### Behavioral Correctness Guarantee

**R_behavioral = 1.00 across all experiments**
- Monotonic repair never sacrifices correctness
- All outputs (raw and repaired) pass oracle tests
- Quality and repeatability are complementary, not trade-offs

---

## Advanced Usage

### Analyzing Distributional Metrics

```python
import pandas as pd

# Load metrics
df = pd.read_csv('outputs/metrics_summary.csv')

# Show distributional improvements
print(df[['contract_id', 'temperature', 'Delta_mu', 'Delta_P_tau_0.1']])

# Filter large improvements
large_gains = df[df['Delta_rescue'] > 0.3]
print(large_gains[['contract_id', 'Delta_rescue', 'rescue_rate']])
```

### Custom Contract Creation

See [`contracts/templates.json`](contracts/templates.json) for schema. Key fields:

```json
{
  "your_contract_id": {
    "id": "your_contract_id",
    "task_intent": "Description",
    "prompt": "Your prompt text",
    "constraints": {
      "function_name": "required_name",
      "variable_naming": {"naming_policy": "strict"}
    },
    "oracle_requirements": {
      "test_cases": [
        {"input": ..., "expected": ..., "description": "..."}
      ]
    }
  }
}
```

---

## Troubleshooting

### Common Issues

**1. "No canon found" error**
- **Cause**: No LLM output passed oracle tests
- **Solution**: Check oracle requirements aren't too strict, adjust temperature, or use curated golden implementation

**2. Distributional metrics missing**
- **Cause**: Old outputs from previous version
- **Solution**: Re-run experiments; metrics computation is automatic in current version

**3. API rate limit errors**
- **Cause**: OpenAI API rate limiting
- **Solution**: Reduce `--runs` or add delays between experiments

**4. Transformation success but distance not zero**
- **Cause**: Current AST-level transformations don't capture all equivalences (e.g., Binary-Search)
- **Expected**: This is documented behavior for zero-gain tasks

### Verification

```bash
# Check that all metrics are computed
python verify_metrics.py

# View recent experiment results
ls -lh outputs/final_*/metrics_summary.csv

# Inspect specific run
cat outputs/final_*/fibonacci_basic_temp0.3_*.json | jq '.metrics'
```

---

## Reproducibility Statement

This artifact provides:

- ✅ **Complete source code** for all Skyt components
- ✅ **Exact contract definitions** used in paper evaluation
- ✅ **Pinned dependencies** (`requirements.txt`)
- ✅ **Runnable experiments** with single commands
- ✅ **Output format documentation** for independent verification

**Replication checklist:**
1. Install dependencies: `pip install -r requirements.txt`
2. Set API key: `export OPENAI_API_KEY=...`
3. Run experiments: `python main.py --contract <id> --sweep --temperatures 0.0 0.2 0.3 0.5 0.7 --runs 10`
4. Verify metrics: `python verify_metrics.py`
5. Compare results to paper Table 1

**Expected variance:** R_anchor values may vary ±0.05 due to LLM stochasticity; aggregate patterns should replicate.

---

## Citation

```bibtex
@inproceedings{skyt2026,
  title     = {Skyt: Prompt Contracts for Software Repeatability in LLM-Assisted Development},
  author    = {[Authors]},
  booktitle = {Proceedings of the 23rd International Conference on Mining Software Repositories (MSR)},
  series    = {Data \& Tool Showcase Track},
  year      = {2026},
  location  = {Rio de Janeiro, Brazil}
}
```

---

## License

- **Code**: MIT License (see [`LICENSE.txt`](LICENSE.txt))
- **Data**: Generated outputs are CC-BY-4.0 (synthetic LLM-generated code)

---

## Contact

For questions about the artifact or paper:
- Open an issue in this repository
- Contact: [to be revealed after review]

---

## Acknowledgments

This work evaluates repeatability in LLM code generation using contracts, canonical anchoring, and monotonic repair. The framework is designed for production CI/CD integration, compliance auditability, and engineering-grade software practice.
