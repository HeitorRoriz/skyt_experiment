# src/summarize_results.py

import os
import json
import pandas as pd
from config import RESULTS_FILE

RESULTS_DIR = "results"

def summarize_compliance():
    """
    Scans the results directory and prints compliance rates.
    """
    summary = []
    for contract_name in os.listdir(RESULTS_DIR):
        contract_dir = os.path.join(RESULTS_DIR, contract_name)
        if not os.path.isdir(contract_dir):
            continue
        runs = [f for f in os.listdir(contract_dir) if f.startswith("final_status_run")]
        total_runs = len(runs)
        compliant_raw = 0
        compliant_norm = 0
        failed = 0
        for run_file in runs:
            run_id = int(run_file.split("_run")[1].split(".")[0])
            try:
                with open(os.path.join(contract_dir, f"final_status_run{run_id}.txt")) as f:
                    status = f.read().strip()
                if status == "raw":
                    compliant_raw += 1
                elif status == "normalized":
                    compliant_norm += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"Error reading {run_file}: {e}")
        summary.append({
            "contract": contract_name,
            "runs": total_runs,
            "compliant_raw": compliant_raw,
            "compliant_norm": compliant_norm,
            "failed": failed
        })
    df = pd.DataFrame(summary)
    print(df)
    return df

def summarize_excel():
    """
    Reads the Excel summary and prints aggregate stats.
    """
    if not os.path.exists(RESULTS_FILE):
        print(f"No summary file found at {RESULTS_FILE}.")
        return
    df = pd.read_excel(RESULTS_FILE, engine='openpyxl')
    # Example: Compliance rate by contract
    if "contract_id" in df.columns and "similarity_score" in df.columns:
        summary = df.groupby("contract_id").agg(
            runs=("run_id", "count"),
            avg_similarity=("similarity_score", "mean")
        )
        print(summary)
    else:
        print(df.head())

if __name__ == "__main__":
    print("Summary from result folders:")
    summarize_compliance()
    print("\nSummary from Excel results:")
    summarize_excel()
