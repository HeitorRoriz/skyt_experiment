# Distributional Metrics in SKYT

## Overview

SKYT computes two distributional metrics as claimed in the paper abstract:

- **Δμ (Delta Mu)**: Mean distance shift before vs. after repair
- **ΔP_τ (Delta P Tau)**: Probability mass shift within tolerance τ

## How They're Computed

### Δμ - Mean Distance Shift

```python
# From src/metrics.py line 80-83
mean_distance_pre = np.mean(distances_pre)    # Average distance before repair
mean_distance_post = np.mean(distances_post)  # Average distance after repair
delta_mu = mean_distance_pre - mean_distance_post
```

**Interpretation:**
- **Δμ > 0**: Repair moved outputs closer to canon on average (good)
- **Δμ = 0**: No average improvement
- **Δμ < 0**: Outputs moved farther (shouldn't happen due to monotonicity)

**Example:**
- Pre-repair distances: [0.3, 0.4, 0.5] → mean = 0.4
- Post-repair distances: [0.0, 0.1, 0.2] → mean = 0.1
- **Δμ = 0.3** (30% average improvement)

### ΔP_τ - Probability Mass Shift

```python
# From src/metrics.py line 446-469
for tau in [0.05, 0.1, 0.15, 0.2]:
    p_pre = fraction of distances_pre <= tau
    p_post = fraction of distances_post <= tau
    delta_p_tau[tau] = p_post - p_pre
```

**Interpretation:**
- **ΔP_τ > 0**: More outputs within "acceptable" distance after repair
- **τ** = tolerance threshold (e.g., 0.1 = within 10% of canon)

**Example:**
With τ=0.1:
- Pre: 4/10 outputs have d ≤ 0.1 → P_pre = 0.40
- Post: 7/10 outputs have d ≤ 0.1 → P_post = 0.70
- **ΔP_0.1 = 0.30** (30% more outputs now within tolerance)

## Where They're Saved

### 1. JSON Output (Complete Data)

```json
{
  "metrics": {
    "Delta_mu": 0.156,
    "Delta_P_tau": {
      "tau=0.05": 0.10,
      "tau=0.1": 0.25,
      "tau=0.15": 0.35,
      "tau=0.2": 0.45
    },
    "mean_distance_pre": 0.234,
    "mean_distance_post": 0.078,
    ...
  }
}
```

**Location:** `outputs/{experiment_id}.json`

### 2. CSV Output (Tabular Summary)

**Location:** `outputs/metrics_summary.csv`

**Columns:**
```
..., Delta_mu, Delta_P_tau_0.05, Delta_P_tau_0.1, Delta_P_tau_0.15, Delta_P_tau_0.2, ...
```

**Example row:**
```csv
fibonacci_basic_temp0.3_..., ..., 0.156, 0.10, 0.25, 0.35, 0.45, ...
```

## How to View Results

### Quick Check

Run the verification script:

```bash
python verify_metrics.py
```

This checks that all distributional metrics columns are present in your CSV.

### View in CSV

```bash
# Linux/Mac
cut -d',' -f25-29 outputs/metrics_summary.csv | column -t -s','

# Windows PowerShell
Import-Csv outputs/metrics_summary.csv | Select Delta_mu, Delta_P_tau_0.05, Delta_P_tau_0.1, Delta_P_tau_0.15, Delta_P_tau_0.2
```

### View in Python

```python
import pandas as pd

df = pd.read_csv('outputs/metrics_summary.csv')

# Show distributional metrics
dist_metrics = df[['contract_id', 'temperature', 'Delta_mu', 
                   'Delta_P_tau_0.05', 'Delta_P_tau_0.1', 
                   'Delta_P_tau_0.15', 'Delta_P_tau_0.2']]
print(dist_metrics)
```

## Relationship to Paper Claims

**Abstract states:**
> "We report repeatability metrics (R_raw, R_anchor, Δ_rescue) and distributional measures (Δμ, ΔP_τ) over LLM generations."

**Status:** ✅ **FULLY IMPLEMENTED**

All claimed metrics are computed in `src/metrics.py` (lines 29-148) and saved in both JSON and CSV formats by `src/comprehensive_experiment.py` (lines 451-533).

## Implementation Files

- **Computation**: `src/metrics.py`
  - Line 80-83: Δμ calculation
  - Line 446-469: ΔP_τ calculation

- **CSV Writing**: `src/comprehensive_experiment.py`
  - Line 472-474: CSV headers including distributional metrics
  - Line 516: Delta_mu value
  - Line 518-521: Delta_P_tau values (4 thresholds)

- **Verification**: `verify_metrics.py`
  - Quick check script to confirm metrics are present

## Typical Values

From our experiments:

| Contract | Temperature | Δμ | ΔP_0.1 | Interpretation |
|----------|-------------|-----|--------|----------------|
| Balanced-Brackets | 0.5 | 0.22 | 0.48 | Strong convergence |
| Slugify | 0.3 | 0.08 | 0.16 | Moderate convergence |
| Fibonacci | 0.3 | 0.02 | 0.02 | Near-saturated |
| Binary-Search | 0.5 | 0.00 | 0.00 | No convergence (AST-level limit) |
| Euclid-GCD | 0.3 | 0.00 | 0.00 | Pre-saturated |

## Notes

- **Thresholds**: [0.05, 0.1, 0.15, 0.2] are configurable in `src/metrics.py` line 27
- **Monotonicity**: Δμ should always be ≥ 0 due to monotonic repair constraint
- **Saturation**: For tasks where LLM already produces identical outputs, Δμ ≈ 0 (nothing to improve)
- **Zero-gain tasks**: When transformations can't reduce distance, ΔP_τ ≈ 0 for all τ
