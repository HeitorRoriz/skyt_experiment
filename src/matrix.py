import pandas as pd
import os
from config import EXPERIMENT_MATRIX_FILE, EXPERIMENT_TEMPLATES, NUM_RUNS

def ensure_experiment_matrix_exists():
    def is_valid_matrix(df):
        required_columns = {"prompt", "model", "temperature", "status", "run_id"}
        return required_columns.issubset(set(df.columns))

    if not os.path.exists(EXPERIMENT_MATRIX_FILE):
        expanded = []
        for template in EXPERIMENT_TEMPLATES:
            for run_id in range(1, NUM_RUNS + 1):
                entry = template.copy()
                entry["run_id"] = run_id
                expanded.append(entry)
        df = pd.DataFrame(expanded)
        df.to_excel(EXPERIMENT_MATRIX_FILE, index=False, engine='openpyxl')
    else:
        try:
            df = pd.read_excel(EXPERIMENT_MATRIX_FILE, engine='openpyxl')
            if not is_valid_matrix(df):
                raise ValueError("Missing required columns")
        except Exception as e:
            backup_path = EXPERIMENT_MATRIX_FILE + ".backup"
            os.rename(EXPERIMENT_MATRIX_FILE, backup_path)
            print(f"Backed up corrupted experiment matrix to {backup_path} due to error: {e}")
            expanded = []
            for template in EXPERIMENT_TEMPLATES:
                for run_id in range(1, NUM_RUNS + 1):
                    entry = template.copy()
                    entry["run_id"] = run_id
                    expanded.append(entry)
            df = pd.DataFrame(expanded)
        df.to_excel(EXPERIMENT_MATRIX_FILE, index=False, engine='openpyxl')

def get_next_experiment() -> dict:
    ensure_experiment_matrix_exists()
    df = pd.read_excel(EXPERIMENT_MATRIX_FILE, engine='openpyxl')
    pending = df[df["status"] == "pending"]

    if pending.empty:
        raise Exception("All experiments completed.")

    next_exp = pending.iloc[0]
    df.loc[next_exp.name, "status"] = "running"
    df.to_excel(EXPERIMENT_MATRIX_FILE, index=False, engine='openpyxl')

    return next_exp.to_dict()

def mark_experiment_completed(experiment: dict):
    df = pd.read_excel(EXPERIMENT_MATRIX_FILE, engine='openpyxl')
    idx = df.index[(df["prompt"] == experiment["prompt"]) & (df["run_id"] == experiment["run_id"])].tolist()
    if idx:
        df.loc[idx[0], "status"] = "completed"
        df.to_excel(EXPERIMENT_MATRIX_FILE, index=False, engine='openpyxl')
