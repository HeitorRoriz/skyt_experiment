# SKYT Experiment Output Structure

**Purpose:** Documents the complete output structure for the full SKYT experiment (3,600 generations).

**For Paper:** Reference this structure in the replication package section.

---

## Directory Structure

```
outputs/full_experiment_YYYY-MM-DD_HH-MM-SS/
│
├── raw_outputs/                          # Raw LLM-generated code (before transformation)
│   ├── fibonacci/
│   │   ├── gpt-4o-mini/
│   │   │   ├── temp_0.0/
│   │   │   │   ├── run_01.py
│   │   │   │   ├── run_02.py
│   │   │   │   └── ... (run_20.py)
│   │   │   ├── temp_0.3/
│   │   │   ├── temp_0.5/
│   │   │   ├── temp_0.7/
│   │   │   └── temp_1.0/
│   │   ├── gpt-4o/
│   │   │   └── (same structure)
│   │   └── claude-3-5-sonnet-20241022/
│   │       └── (same structure)
│   ├── binary_search/
│   ├── merge_sort/
│   ├── quick_sort/
│   ├── factorial/
│   ├── is_palindrome/
│   ├── is_prime/
│   ├── gcd/
│   ├── brackets_balanced/
│   ├── longest_common_subsequence/
│   ├── slugify/
│   └── matrix_multiply/
│
├── repaired_outputs/                     # Canonicalized code (after transformation)
│   └── (same structure as raw_outputs)
│
├── metrics/                              # Computed metrics
│   ├── per_contract/
│   │   ├── fibonacci.json
│   │   ├── binary_search.json
│   │   └── ... (12 files)
│   ├── per_model/
│   │   ├── gpt-4o-mini.json
│   │   ├── gpt-4o.json
│   │   └── claude-3-5-sonnet-20241022.json
│   ├── aggregate/
│   │   └── summary.json
│   └── summary.json                      # Overall metrics summary
│
├── statistical_analysis/                 # Statistical test results
│   ├── fisher_exact_tests.json
│   ├── effect_sizes.json
│   ├── confidence_intervals.json
│   ├── holm_bonferroni.json
│   └── analysis.json
│
├── logs/                                 # Execution logs
│   ├── experiment.log                    # Main execution log
│   └── errors.log                        # Error-only log
│
├── results.json                          # Complete raw results
├── checkpoint.json                       # Resume checkpoint
└── README.md                             # Experiment metadata
```

---

## File Formats

### 1. Raw/Repaired Outputs (`.py` files)

**Location:** `raw_outputs/` and `repaired_outputs/`

**Format:** Plain Python source code

**Example:**
```python
def fibonacci(n: int) -> int:
    if n <= 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
```

**Naming:** `run_XX.py` where XX is zero-padded run number (01-20)

---

### 2. Results File (`results.json`)

**Location:** Root of experiment directory

**Format:** JSON array of generation results

**Schema:**
```json
[
  {
    "config_id": "fibonacci_gpt-4o-mini_0.0_1",
    "contract_id": "fibonacci",
    "model": "gpt-4o-mini",
    "temperature": 0.0,
    "run_number": 1,
    "oracle_passed": true,
    "contract_adherent": true,
    "transformation_success": true,
    "transformations_applied": [
      "StatementReordering",
      "VariableNormalization"
    ],
    "raw_file": "raw_outputs/fibonacci/gpt-4o-mini/temp_0.0/run_01.py",
    "repaired_file": "repaired_outputs/fibonacci/gpt-4o-mini/temp_0.0/run_01.py",
    "timestamp": "2026-01-19T11:30:45.123456"
  }
]
```

**Fields:**
- `config_id`: Unique identifier for this generation
- `contract_id`: Contract name
- `model`: Model identifier
- `temperature`: Sampling temperature
- `run_number`: Run number (1-20)
- `oracle_passed`: Boolean - passed behavioral tests
- `contract_adherent`: Boolean - satisfied contract constraints
- `transformation_success`: Boolean - transformation succeeded
- `transformations_applied`: List of applied transformations
- `raw_file`: Path to raw output
- `repaired_file`: Path to repaired output (null if transformation failed)
- `timestamp`: ISO 8601 timestamp

---

### 3. Per-Contract Metrics (`metrics/per_contract/*.json`)

**Format:** JSON object with contract-level statistics

**Schema:**
```json
{
  "total_runs": 300,
  "oracle_pass_rate": 0.95,
  "contract_adherence_rate": 0.98,
  "transformation_success_rate": 0.87
}
```

**Fields:**
- `total_runs`: Total generations for this contract (3 models × 5 temps × 20 runs = 300)
- `oracle_pass_rate`: Proportion passing oracle tests
- `contract_adherence_rate`: Proportion satisfying contract constraints
- `transformation_success_rate`: Proportion with successful transformations

---

### 4. Per-Model Metrics (`metrics/per_model/*.json`)

**Format:** JSON object with model-level statistics

**Schema:**
```json
{
  "total_runs": 1200,
  "oracle_pass_rate": 0.94
}
```

**Fields:**
- `total_runs`: Total generations for this model (12 contracts × 5 temps × 20 runs = 1,200)
- `oracle_pass_rate`: Proportion passing oracle tests

---

### 5. Aggregate Metrics (`metrics/aggregate/summary.json`)

**Format:** JSON object with overall statistics

**Schema:**
```json
{
  "total_calls": 3600,
  "successful_calls": 3580,
  "failed_calls": 20,
  "overall_oracle_pass_rate": 0.95
}
```

**Fields:**
- `total_calls`: Total attempted generations
- `successful_calls`: Successfully completed generations
- `failed_calls`: Failed generations (API errors, timeouts, etc.)
- `overall_oracle_pass_rate`: Overall proportion passing oracle tests

---

### 6. Statistical Analysis (`statistical_analysis/*.json`)

**Format:** JSON objects with statistical test results

**Files:**
- `fisher_exact_tests.json`: Fisher's exact test results per contract
- `effect_sizes.json`: Cohen's h, odds ratios per contract
- `confidence_intervals.json`: Wilson score CIs per contract
- `holm_bonferroni.json`: Multiple comparison correction results
- `analysis.json`: Combined analysis summary

**Example (`fisher_exact_tests.json`):**
```json
{
  "fibonacci": {
    "p_value": 0.0023,
    "odds_ratio": 9.0,
    "significant": true,
    "alpha": 0.05
  }
}
```

---

### 7. Checkpoint File (`checkpoint.json`)

**Purpose:** Enable experiment resumption after interruption

**Format:** JSON object tracking progress

**Schema:**
```json
{
  "completed_calls": 1500,
  "completed_configs": [
    "fibonacci_gpt-4o-mini_0.0_1",
    "fibonacci_gpt-4o-mini_0.0_2"
  ],
  "timestamp": "2026-01-19T14:30:00.000000"
}
```

**Fields:**
- `completed_calls`: Number of completed generations
- `completed_configs`: List of completed config IDs
- `timestamp`: Last checkpoint time

---

### 8. Logs (`logs/*.log`)

**Format:** Plain text log files

**experiment.log:**
```
2026-01-19 11:30:00 - INFO - Starting SKYT Experiment - Phase: pilot
2026-01-19 11:30:00 - INFO - Total calls: 30
2026-01-19 11:30:01 - INFO - Generating: fibonacci_gpt-4o-mini_0.0_1
2026-01-19 11:30:05 - INFO - Completed fibonacci_gpt-4o-mini_0.0_1
```

**errors.log:**
```
2026-01-19 11:35:00 - ERROR - Failed: fibonacci_gpt-4o_0.7_15
2026-01-19 11:35:00 - ERROR - Traceback (most recent call last):
  ...
```

---

## Data Volume Estimates

### Phase 1 (Pilot)
- **Generations:** 30
- **Raw outputs:** ~30 KB (30 files × ~1 KB each)
- **Repaired outputs:** ~30 KB
- **Logs:** ~50 KB
- **Metrics/Results:** ~100 KB
- **Total:** ~210 KB

### Phase 2 (Full)
- **Generations:** 3,600
- **Raw outputs:** ~3.6 MB (3,600 files × ~1 KB each)
- **Repaired outputs:** ~3.6 MB
- **Logs:** ~5 MB
- **Metrics/Results:** ~10 MB
- **Total:** ~22 MB

---

## Usage in Paper

### Methods Section

> "All experimental data is organized in a structured directory hierarchy with raw LLM outputs, canonicalized outputs, per-contract metrics, per-model metrics, and comprehensive statistical analysis. The complete output structure is documented in EXPERIMENT_OUTPUT_STRUCTURE.md."

### Replication Package Section

> "The replication package includes:
> 1. All 3,600 raw LLM-generated outputs
> 2. All 3,600 canonicalized outputs
> 3. Per-contract, per-model, and aggregate metrics
> 4. Statistical analysis results (Fisher's exact tests, effect sizes, confidence intervals, Holm-Bonferroni correction)
> 5. Complete execution logs
> 6. Experiment runner script with checkpoint/resume capability
> 
> See EXPERIMENT_OUTPUT_STRUCTURE.md for complete directory structure and file format specifications."

### Data Availability Statement

> "All experimental data is available in the replication package at [Zenodo DOI]. The package includes 3,600 code generations across 12 contracts, 3 models, and 5 temperatures, with complete metrics and statistical analysis. Total size: ~22 MB."

---

## Accessing the Data

### Load Results Programmatically

```python
import json
from pathlib import Path

# Load all results
with open("outputs/full_experiment_2026-01-19/results.json") as f:
    results = json.load(f)

# Filter by contract
fibonacci_results = [r for r in results if r["contract_id"] == "fibonacci"]

# Filter by model
gpt4o_results = [r for r in results if r["model"] == "gpt-4o"]

# Filter by temperature
temp_0_results = [r for r in results if r["temperature"] == 0.0]

# Load specific output
raw_code = Path("outputs/full_experiment_2026-01-19/raw_outputs/fibonacci/gpt-4o-mini/temp_0.0/run_01.py").read_text()
```

### Load Metrics

```python
# Load aggregate metrics
with open("outputs/full_experiment_2026-01-19/metrics/aggregate/summary.json") as f:
    aggregate = json.load(f)

print(f"Overall oracle pass rate: {aggregate['overall_oracle_pass_rate']:.2%}")

# Load per-contract metrics
with open("outputs/full_experiment_2026-01-19/metrics/per_contract/fibonacci.json") as f:
    fibonacci_metrics = json.load(f)

print(f"Fibonacci oracle pass rate: {fibonacci_metrics['oracle_pass_rate']:.2%}")
```

---

## Version Control

**Important:** Do NOT commit experiment outputs to git.

**`.gitignore` entry:**
```
outputs/
```

**Reason:** Experiment outputs are large (~22 MB) and should be distributed via Zenodo, not git.

---

**Document Version:** 1.0  
**Last Updated:** January 19, 2026  
**Status:** Ready for Phase 1 Pilot
