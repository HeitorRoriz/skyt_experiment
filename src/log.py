import pandas as pd
import os
from config import RESULTS_FILE, USE_PROMPT_CONTRACT
import datetime
import hashlib

def log_results(contract: dict) -> None:
    # Fill in missing fields for non-contract mode
    if not contract.get("timestamp"):
        contract["timestamp"] = datetime.datetime.now().isoformat()
    if not contract.get("hash") and contract.get("prompt"):
        contract["hash"] = hashlib.sha256(contract["prompt"].encode('utf-8')).hexdigest()
    
    data = {
        "contract_id": contract["id"],
        "timestamp": contract["timestamp"],
        "model": contract["model"],
        "temperature": contract["temperature"],
        "prompt": contract["prompt"],
        "run_id": contract["run_id"],
        "hash": contract["hash"],
        "raw_output": contract["raw_output"],
        "normalized_output": contract["normalized_output"],
        "lines_added": contract["delta"]["lines_added"],
        "lines_removed": contract["delta"]["lines_removed"],
        "changed_lines": contract["delta"]["changed_lines"],
        "similarity_score": contract["delta"]["similarity_score"]
    }

    df = pd.DataFrame([data])

    if os.path.exists(RESULTS_FILE):
        existing_df = pd.read_excel(RESULTS_FILE, engine='openpyxl')
        df = pd.concat([existing_df, df], ignore_index=True)

    try:
        df.to_excel(RESULTS_FILE, index=False, engine='openpyxl')
    except Exception as e:
        print(f"Error saving results to {RESULTS_FILE}: {e}")

def log_experiment_result(contract_id, attempt, compliant, code, reflection, normalized_dev_intent=None, normalized_user_intent=None):
    print(f"[{contract_id}] Attempt {attempt} — {' Compliant' if compliant else ' Not compliant'}")
    if normalized_dev_intent:
        print(f"Normalized Dev Intent: {normalized_dev_intent}")
    if normalized_user_intent:
        print(f"Normalized User Intent: {normalized_user_intent}")
    print("Reflection:", reflection)
    print("Code:", code[:60], "...")
