# 🚀 Quick Start: SKYT Metrics Collection

## Run Your First Experiment

```bash
# 1. Run a single experiment
python -m src.main experiment \
  --contract-path contracts/templates.json \
  --contract-id fibonacci_basic \
  --num-runs 100 \
  --temperature 0.7

# 2. Run a temperature sweep
python -m src.main sweep \
  --contract-path contracts/templates.json \
  --contract-id fibonacci_basic \
  --temperatures 0.0 0.5 1.0

# 3. Analyze results
python analyze_metrics.py
```

## What Gets Collected

### ✅ Automatically Collected Metrics

Every experiment run collects:

1. **R_raw** - Raw LLM repeatability (byte-identical outputs)
2. **R_anchor_pre** - Pre-repair exact canon matches
3. **R_anchor_post** - Post-repair exact canon matches
4. **Δ_rescue** - Improvement from repair (post - pre)
5. **R_repair@k** - Tolerance-based repeatability at k ∈ {0.05, 0.1, 0.15, 0.2}
6. **Δμ** - Mean distance reduction
7. **ΔPτ** - Partial repeatability deltas
8. **Canon coverage** - Fraction passing oracle tests
9. **Rescue rate** - Successful repair fraction
10. **R_behavioral** - Behavioral equivalence
11. **R_structural** - Structural equivalence

### ✅ Automatically Generated Visualizations

1. **Pre/Post Bell Curves** - Overlaid distributions showing variance reduction
2. **Bar Charts** - R_anchor and Δ_rescue comparison
3. **Violin Plots** - Distribution shape comparison
4. **Box Plots** - Statistical summary
5. **R_repair@k Chart** - Tolerance-based repeatability bars

## Where to Find Results

```
outputs/
├── metrics_summary.csv              # ← ALL METRICS (paper-ready)
├── analysis/
│   ├── pre_post_comparison_*.png   # ← Section 5 figures
│   ├── temperature_effects.png     # ← Temperature sweep analysis
│   └── metric_correlations.png     # ← Correlation heatmap
├── metrics_table.tex                # ← LaTeX table for paper
└── {experiment_id}.json             # ← Detailed results per experiment
```

## Quick Analysis

```python
import pandas as pd

# Load all metrics
df = pd.read_csv('outputs/metrics_summary.csv')

# Check Δ_rescue (improvement from repair)
print(f"Average Δ_rescue: {df['Delta_rescue'].mean():.3f}")

# Check if SKYT helps
improvement = df['R_anchor_post'] - df['R_anchor_pre']
print(f"Average improvement: {improvement.mean():.3f}")

# Filter by temperature
high_temp = df[df['decoding_temperature'] >= 0.7]
print(f"High temp Δ_rescue: {high_temp['Delta_rescue'].mean():.3f}")
```

## For Your Paper (Section 5)

### Key Metrics to Report

1. **R_raw** - Baseline LLM repeatability
2. **R_anchor_post** - Final repeatability after SKYT
3. **Δ_rescue** - SKYT's improvement
4. **Δμ** - Distance reduction
5. **Rescue rate** - Repair success rate

### Key Figures to Include

1. **Figure 1**: Pre/post bell curves (variance reduction)
   - File: `outputs/analysis/pre_post_comparison_*.png`
   
2. **Figure 2**: R_anchor bar chart (pre vs post)
   - Embedded in pre/post comparison plot
   
3. **Figure 3**: R_repair@k comparison
   - Embedded in pre/post comparison plot
   
4. **Table 1**: Metrics summary by contract/temperature
   - File: `outputs/metrics_table.tex`

## Example Results Interpretation

```
R_raw = 0.18          → LLM produces identical output 18% of the time
R_anchor_pre = 0.22   → 22% of raw outputs match canon exactly
R_anchor_post = 0.47  → 47% of repaired outputs match canon exactly
Δ_rescue = 0.25       → SKYT improved exact matches by 25 percentage points
Δμ = 0.20             → Average distance reduced by 0.20
Rescue rate = 0.65    → 65% of non-canonical outputs successfully repaired
```

**Interpretation**: SKYT significantly improves repeatability, rescuing near-canonical outputs into exact canon matches.

## Troubleshooting

### No metrics_summary.csv?
→ Run an experiment first: `python -m src.main experiment ...`

### Empty CSV?
→ Check experiment logs for errors
→ Ensure contract templates exist in `contracts/templates.json`

### Missing visualizations?
→ Run `python analyze_metrics.py` after experiments

### Need more runs?
→ Increase `--num-runs` (default: 5, recommended: 100+ for paper)

## Advanced: Custom Analysis

```python
from src.bell_curve_analysis import BellCurveAnalyzer
import json

# Load experiment result
with open('outputs/fibonacci_basic_temp0.7_*.json') as f:
    result = json.load(f)

# Get distances
distances_pre = result['metrics']['distances_pre']
distances_post = result['metrics']['distances_post']

# Generate custom visualization
analyzer = BellCurveAnalyzer()
viz = analyzer.plot_pre_post_comparison(
    distances_pre, distances_post,
    experiment_id="custom_analysis",
    title="Custom Pre/Post Analysis"
)

print(f"Saved to: {viz['plot_path']}")
```

## Next Steps

1. ✅ Run experiments with multiple contracts
2. ✅ Run temperature sweeps (0.0, 0.5, 1.0, 1.5)
3. ✅ Collect 100+ runs per configuration
4. ✅ Run `analyze_metrics.py` for summary
5. ✅ Use generated figures in paper Section 5
6. ✅ Include LaTeX table in results

---

**Everything is ready for your paper! 🎉**
