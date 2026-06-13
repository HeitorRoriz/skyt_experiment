# ✅ SKYT Comprehensive Metrics Implementation

## Overview

The SKYT experiment system now collects **ALL required metrics** for your paper, including:

- **Core Repeatability Metrics**: R_raw, R_anchor (pre/post), Δ_rescue, R_repair@k
- **Distributional Metrics**: Distance distributions, Δμ, ΔPτ
- **Complementary Metrics**: Canon coverage, rescue rate, structural/behavioral breakdown
- **Visualizations**: Pre/post bell curves, bar charts, violin plots, box plots, R_repair@k comparisons

---

> ## RECONCILIATION NOTE — 2026-06-13
>
> References to **"13 properties"** below reflect an earlier count; the code now has **14** active foundational properties (`src/foundational_properties.py`). Experiment scope differs by paper and is kept distinct: **SBES/CBSoft 2026** = 12 contracts / 3,600 generations (MISRA/P10 as inspiration only); **MSR 2026 (camera-ready)** = 15 tasks / 4,500 generations. The 3 `*_strict` variants were run but were not validated against an actual MISRA C / NASA Power-of-10 rule set — noted as a concern (2026-06-13). No data was deleted.

---

## 📊 Core Repeatability Metrics

### R_raw (Raw Repeatability)
- **Definition**: Modal probability mass of byte-identical outputs
- **Interpretation**: Baseline measure of how often the model reproduces exact same output
- **Measured**: Before any repair/canonicalization
- **Location**: `metrics['R_raw']`

### R_anchor_pre (Pre-Repair Anchor Repeatability)
- **Definition**: Probability mass of outputs with distance d=0 to canonical anchor (before repair)
- **Interpretation**: How many raw LLM outputs exactly match the canon
- **Location**: `metrics['R_anchor_pre']`

### R_anchor_post (Post-Repair Anchor Repeatability)
- **Definition**: Probability mass of outputs with distance d=0 to canonical anchor (after repair)
- **Interpretation**: How many repaired outputs exactly match the canon
- **Location**: `metrics['R_anchor_post']`

### Δ_rescue (Rescue Delta)
- **Definition**: `Δ_rescue = R_anchor_post - R_anchor_pre`
- **Interpretation**: Improvement in exact canon matches after SKYT's repair step
- **Indicates**: SKYT's ability to "rescue" near misses into canonical compliance
- **Location**: `metrics['Delta_rescue']`

### R_repair@k (Repair-at-K)
- **Definition**: Probability mass of outputs within distance ≤ k from canon
- **Interpretation**: Tolerance-based repeatability for near-canonical outputs
- **Thresholds**: k ∈ {0.05, 0.1, 0.15, 0.2}
- **Location**: 
  - Pre-repair: `metrics['R_repair_at_k_pre']['k=0.05']`, etc.
  - Post-repair: `metrics['R_repair_at_k_post']['k=0.05']`, etc.

---

## 📈 Distributional / Statistical Metrics

### Distance Distributions
- **Pre-repair distances**: `metrics['distances_pre']` (list of floats)
- **Post-repair distances**: `metrics['distances_post']` (list of floats)
- **Usage**: Generate bell curve visualizations showing variance reduction

### Δμ (Mean Distance Delta)
- **Definition**: `Δμ = mean_distance_pre - mean_distance_post`
- **Interpretation**: Reduction in average distance to canon after SKYT repair
- **Lower is better**: Indicates convergence toward canonical form
- **Location**: `metrics['Delta_mu']`

### ΔPτ (Partial Repeatability Delta)
- **Definition**: Difference in probability mass within threshold τ
- **Formula**: `ΔPτ = P(d ≤ τ | post) - P(d ≤ τ | pre)`
- **Interpretation**: Captures SKYT's effect when full canon matches are too strict
- **Thresholds**: τ ∈ {0.05, 0.1, 0.15, 0.2}
- **Location**: `metrics['Delta_P_tau']['tau=0.05']`, etc.

---

## 🎯 Complementary Metrics

### Canon Coverage
- **Definition**: Fraction of runs producing oracle-passing outputs
- **Interpretation**: How many outputs are functionally correct under contract
- **Location**: `metrics['canon_coverage']`

### Rescue Rate
- **Definition**: Fraction of non-canonical but oracle-passing outputs successfully repaired
- **Interpretation**: Demonstrates bounded, monotonic repair success
- **Location**: `metrics['rescue_rate']`

### R_behavioral (Behavioral Repeatability)
- **Definition**: Repeatability based on oracle test equivalence
- **Interpretation**: Functional sameness (same behavior, different structure)
- **Location**: `metrics['R_behavioral']`

### R_structural (Structural Repeatability)
- **Definition**: Repeatability based on foundational properties (13 properties)
- **Interpretation**: Structural sameness (same AST/control flow/complexity)
- **Location**: `metrics['R_structural']`

---

## 📁 CSV Output Schema

All metrics are automatically saved to `outputs/metrics_summary.csv` with the following columns:

```csv
experiment_id,repo_commit,contract_id,canon_id,model,decoding_temperature,runs,timestamp,
R_raw,R_anchor_pre,R_anchor_post,Delta_rescue,
R_repair_at_0.05_pre,R_repair_at_0.1_pre,R_repair_at_0.15_pre,R_repair_at_0.2_pre,
R_repair_at_0.05_post,R_repair_at_0.1_post,R_repair_at_0.15_post,R_repair_at_0.2_post,
mean_distance_pre,std_distance_pre,mean_distance_post,std_distance_post,Delta_mu,
Delta_P_tau_0.05,Delta_P_tau_0.1,Delta_P_tau_0.15,Delta_P_tau_0.2,
canon_coverage,rescue_rate,R_behavioral,R_structural,sweep_id,notes
```

---

## 🎨 Visualization Plan (Section 5 of Paper)

### 1. Overlaid Bell Curves (PRIMARY)
- **File**: `outputs/analysis/pre_post_comparison_{experiment_id}.png`
- **Content**: Red (pre-repair) and blue (post-repair) distributions overlaid
- **Shows**: Visual variance reduction, mean shift toward canon (green line at d=0)

### 2. Bar Chart - Core Metrics
- **Metrics**: R_anchor (pre), R_anchor (post), Δ_rescue
- **Shows**: Direct comparison of exact canon matches before/after repair

### 3. Violin Plots
- **Shows**: Full distribution shape comparison (pre vs post)
- **Highlights**: Median, quartiles, and distribution density

### 4. Box Plots
- **Shows**: Statistical summary (min, Q1, median, Q3, max)
- **Highlights**: Outliers and variance reduction

### 5. Statistical Summary Table
- **Content**: Δμ, Δσ, mean/std/min/max for pre and post
- **Tests**: Mann-Whitney U and Kolmogorov-Smirnov p-values

### 6. R_repair@k Comparison (BOTTOM PANEL)
- **Shows**: Bar pairs for each threshold (0.05, 0.1, 0.15, 0.2, 0.25, 0.3)
- **Demonstrates**: Tolerance-based repeatability improvement

---

## 🚀 Usage

### Running an Experiment

```python
from src.comprehensive_experiment import ComprehensiveExperiment

# Initialize experiment system
experiment = ComprehensiveExperiment()

# Run single experiment
result = experiment.run_full_experiment(
    contract_template_path="contracts/templates.json",
    contract_id="fibonacci_basic",
    num_runs=100,
    temperature=0.7
)

# Run temperature sweep
sweep_result = experiment.run_temperature_sweep(
    contract_template_path="contracts/templates.json",
    contract_id="fibonacci_basic",
    temperatures=[0.0, 0.5, 1.0]
)
```

### Accessing Metrics

```python
# From experiment result
metrics = result['metrics']

print(f"R_raw: {metrics['R_raw']:.3f}")
print(f"R_anchor (pre): {metrics['R_anchor_pre']:.3f}")
print(f"R_anchor (post): {metrics['R_anchor_post']:.3f}")
print(f"Δ_rescue: {metrics['Delta_rescue']:.3f}")
print(f"Δμ: {metrics['Delta_mu']:.3f}")
print(f"Canon coverage: {metrics['canon_coverage']:.3f}")
print(f"Rescue rate: {metrics['rescue_rate']:.3f}")
```

### Generating Visualizations

Visualizations are automatically generated during experiments and saved to:
- `outputs/analysis/pre_post_comparison_{experiment_id}.png`

You can also manually generate them:

```python
from src.bell_curve_analysis import BellCurveAnalyzer

analyzer = BellCurveAnalyzer()

# Pre/post comparison
result = analyzer.plot_pre_post_comparison(
    distances_pre=metrics['distances_pre'],
    distances_post=metrics['distances_post'],
    experiment_id="fibonacci_temp0.7",
    title="Pre vs Post Repair - Fibonacci"
)

print(f"Plot saved to: {result['plot_path']}")
```

---

## 📊 Reading the CSV

```python
import pandas as pd

# Load metrics summary
df = pd.read_csv('outputs/metrics_summary.csv')

# Filter by contract
fib_results = df[df['contract_id'] == 'fibonacci_basic']

# Calculate average Δ_rescue across temperatures
avg_rescue = fib_results['Delta_rescue'].mean()
print(f"Average Δ_rescue: {avg_rescue:.3f}")

# Plot temperature sweep
import matplotlib.pyplot as plt

plt.plot(fib_results['decoding_temperature'], fib_results['R_anchor_post'], 'o-')
plt.xlabel('Temperature')
plt.ylabel('R_anchor (post-repair)')
plt.title('Post-Repair Repeatability vs Temperature')
plt.savefig('outputs/temp_sweep_analysis.png')
```

---

## ✅ Implementation Status

| Component | Status | File |
|-----------|--------|------|
| **R_raw** | ✅ Implemented | `src/metrics.py` |
| **R_anchor (pre/post)** | ✅ Implemented | `src/metrics.py` |
| **Δ_rescue** | ✅ Implemented | `src/metrics.py` |
| **R_repair@k** | ✅ Implemented | `src/metrics.py` |
| **Distance distributions** | ✅ Implemented | `src/metrics.py` |
| **Δμ** | ✅ Implemented | `src/metrics.py` |
| **ΔPτ** | ✅ Implemented | `src/metrics.py` |
| **Canon coverage** | ✅ Implemented | `src/metrics.py` |
| **Rescue rate** | ✅ Implemented | `src/metrics.py` |
| **R_behavioral** | ✅ Implemented | `src/metrics.py` |
| **R_structural** | ✅ Implemented | `src/metrics.py` |
| **CSV export** | ✅ Implemented | `src/comprehensive_experiment.py` |
| **Pre/post bell curves** | ✅ Implemented | `src/bell_curve_analysis.py` |
| **Bar charts** | ✅ Implemented | `src/bell_curve_analysis.py` |
| **Violin plots** | ✅ Implemented | `src/bell_curve_analysis.py` |
| **Box plots** | ✅ Implemented | `src/bell_curve_analysis.py` |
| **R_repair@k visualization** | ✅ Implemented | `src/bell_curve_analysis.py` |

---

## 🎯 Key Benefits

1. **Complete Coverage**: All metrics from your specification are collected
2. **Automatic CSV Export**: Results saved in paper-ready format
3. **Publication-Quality Visualizations**: High-DPI (300 DPI) plots with proper labels
4. **Statistical Rigor**: Mann-Whitney U and Kolmogorov-Smirnov tests included
5. **Pre/Post Comparison**: Direct measurement of SKYT's effectiveness
6. **Reproducible**: All metrics stored with experiment metadata

---

## 📝 Notes

- **Pre-repair outputs**: Raw LLM outputs before any canonicalization
- **Post-repair outputs**: Outputs after SKYT's repair/canonicalization step
- **Canon**: First oracle-passing output serves as canonical anchor
- **Distance**: Calculated using 13 foundational properties (structural/semantic)
- **Thresholds**: Configurable in `metrics.py` (default: [0.05, 0.1, 0.15, 0.2])

---

## 🔧 Configuration

To modify repair thresholds:

```python
from src.metrics import ComprehensiveMetrics

metrics_calculator = ComprehensiveMetrics(canon_system)
metrics_calculator.repair_thresholds = [0.01, 0.05, 0.1, 0.2, 0.3]  # Custom thresholds
```

---

## ✨ Summary

The SKYT system now provides **complete metrics collection** for your paper, including:

- ✅ All core repeatability metrics (R_raw, R_anchor, Δ_rescue, R_repair@k)
- ✅ All distributional metrics (Δμ, ΔPτ, distance distributions)
- ✅ All complementary metrics (coverage, rescue rate, behavioral/structural)
- ✅ Automatic CSV export with all required columns
- ✅ Publication-ready visualizations (bell curves, bar charts, violin/box plots)
- ✅ Statistical tests (Mann-Whitney U, Kolmogorov-Smirnov)

**Everything is ready for Section 5 (Results) of your paper!** 🎉
