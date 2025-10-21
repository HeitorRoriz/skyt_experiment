# 🧮 Skyt Metrics Collection — Instructions

The file **`metrics_summary_template.csv`** defines the schema used to collect and summarize all experiment results for the paper.  
Each row corresponds to one *experiment block* (e.g., a single temperature sweep, model variant, or contract).  
Use it to ensure that metrics are consistent across all runs.

---

## 📁 File Location
```
outputs/metrics_summary.csv
```

---

## 🧩 Structure
The CSV contains the following main sections:

| Section | Purpose |
|----------|----------|
| **Experiment Metadata** | Identifies the run (commit, contract, model, environment). |
| **Core Repeatability Metrics** | Raw and canonical repeatability (R_raw, R_anchor). |
| **Repair/Rescue Metrics** | Improvement after canonicalization (Δ_rescue, R_repair@k). |
| **Distributional Stats** | Mean and std. of distances to the canon, before/after repair. |
| **Coverage & Repair Rates** | Oracle coverage and successful rescues. |
| **Structural / Behavioral Breakdown** | Repeatability measured separately for structure and behavior. |
| **Sweep Info** | Temperature sweep identifiers and notes. |

---

## ⚙️ How to Use

1. **After each experiment run**, copy or export the computed metrics (from `metrics.py` output) into a new row of `outputs/metrics_summary.csv`.  
   - If running multiple sweeps, one row per temperature value.  
   - Keep column names unchanged — these are used by `bell_curve_analysis.py`.

2. **Ensure the following fields are filled for each run:**
   ```
   experiment_id, repo_commit, contract_id, canon_id,
   model, decoding_temperature, runs, R_raw, R_anchor_pre, R_anchor_post, Delta_rescue
   ```
   These are mandatory for the paper’s figures.

3. **Optional but recommended fields:**
   ```
   R_repair_at_1_post, mean_distance_post, canon_coverage, rescue_rate
   ```
   These enrich the Δ metrics and visual plots.

4. **Keep all values normalized** between 0.0–1.0 (except distances, which are numeric).

5. Once all experiments are completed, run:
   ```bash
   python src/bell_curve_analysis.py
   ```
   This will aggregate the metrics, generate bell curve plots (pre vs post), and produce summary figures for the paper.

6. Commit the updated CSV to the repo so results remain reproducible:
   ```bash
   git add outputs/metrics_summary.csv
   git commit -m "Add updated metrics summary"
   ```

---

## 🧾 Example Row

| experiment_id | model | temp | runs | R_raw | R_anchor_pre | R_anchor_post | Δ_rescue |
|----------------|--------|------|-------|--------|----------------|-----------------|------------|
| exp_2025-10-21_T0 | gpt-5 | 0.2 | 100 | 0.18 | 0.22 | 0.47 | 0.25 |
