# Skyt: Prompt Contracts for Software Repeatability in LLM-Assisted Development

> **Anonymized artifact submission for MSR 2026 (Data & Tool Showcase)**  
> Repository link anonymized using [anonymous.4open.science](https://anonymous.4open.science/).  
> All organization names and author identifiers have been removed.

---

## Overview

**Skyt** is a lightweight middleware that measures **software repeatability** in LLM-assisted code generation.  
It treats repeatability as a **pinned-pipeline property**, defined by fixed model parameters and a schema-bound prompt contract.

The tool executes tasks under *pinned environments*, normalizes outputs, and computes:

- **R_raw** — raw repeatability (byte-identical outputs)  
- **R_canon** — canonical repeatability (contract-valid outputs sharing a canonical signature)  
- **Δ_rescue = R_canon − R_raw** — gain from canonization  
- **R_repair@k** — repeatability after up to *k* bounded repair attempts  

Skyt also reports coverage, Wilson 95 % confidence intervals, and a short-term Sigma proxy (Φ⁻¹(R_canon)).

---

## Repository Structure

```
skyt-msr-2026/
├── README.md
├── LICENSE
├── environment.yml        # or requirements.txt
├── configs/
│   ├── pins.json          # model, temp, decoding, runtime, seeds
│   ├── contract_basic.json
│   └── contract_enhanced.json
├── tasks/
│   ├── fibonacci20/
│   │   ├── oracle.py
│   │   └── prompts/
│   ├── slugify/
│   └── brackets/
├── runs/                  # sample outputs (anonymized)
│   ├── outputs.jsonl
│   ├── canon.jsonl
│   └── metrics.csv
├── skyt/
│   ├── cli.py
│   ├── metrics.py
│   └── canon.py
├── scripts/
│   ├── run_all.sh
│   └── plot_tables.py
└── results/
    ├── table_repeatability.csv
    └── table_repair.csv
```

---

## How to Reproduce the Results

### 1 – Environment Setup
```bash
conda env create -f environment.yml
conda activate skyt
# or:
pip install -r requirements.txt
```

### 2 – Run All Experiments
```bash
bash scripts/run_all.sh
```
This executes all tasks (Fibonacci-20, Slugify, Balanced-Brackets) across contract types and temperature grid,  
logs results to `runs/`, and regenerates Tables 1–2 as CSVs under `results/`.

### 3 – Generate Tables and Plots
```bash
python scripts/plot_tables.py
```
The script produces compact tables summarizing:

- R_raw, R_canon, Δ_rescue (Table 1)  
- R_repair@1, ΔR, and monotonicity M (Table 2)

---

## Data Description

Each row in `metrics.csv` contains:

| Field | Description |
|--------|-------------|
| task | task identifier (`fib20`, `slugify`, `brackets`) |
| contract | `basic` or `enhanced` |
| temperature | decoding temperature |
| run_id | 1–20 |
| r_raw | raw repeatability indicator (0/1) |
| r_canon | canonical repeatability indicator (0/1) |
| r_repair1 | post-repair indicator |
| delta_rescue | R_canon − R_raw |
| monotonicity | boolean monotonicity per run |
| timestamp | UTC ISO-8601 time of run |

All generations are normalized, deterministic post-processing; no personal or proprietary data included.

---

## Reproducibility Statement

This artifact includes all configuration pins (model, temperature, decoding, runtime, seeds),  
plus a one-click script to recompute every table in the paper.  
Running `bash scripts/run_all.sh` regenerates the dataset, metrics, and plots within one hour  
on a standard workstation (e.g., 8 GB RAM, 4 vCPUs).

---

## Limitations

- v1 evaluates three tasks and one model family.  
- Repair loop bounded to *k ≤ 2* iterations.  
- Schema authoring overhead not yet measured quantitatively.  
- Future work will extend to multi-language and multi-model settings.

---

## License and Data Availability

- **Code:** MIT License  
- **Data:** CC-BY-4.0 (anonymized synthetic code generations)  
- **Archive:** versioned artifact snapshot (Zenodo/OSF link redacted for review)

---

## Citation

```
@inproceedings{skyt2026,
  title     = {Skyt: Prompt Contracts for Software Repeatability in LLM-Assisted Development},
  booktitle = {MSR 2026 Data & Tool Showcase},
  year      = {2026},
  note      = {Anonymized submission; authors withheld for double-anonymous review.}
}
```

---

## Contact

Questions will be addressed after the review period, once anonymity is lifted.
