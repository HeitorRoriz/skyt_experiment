import os
import json
import pandas as pd
import datetime
import hashlib
from config import RESULTS_FILE
from config import RESULTS_DIR

# --- Excel Summary Logging ---

def log_results(contract: dict) -> None:
    # Fill in missing fields for non-contract mode
    if not contract.get("timestamp"):
        contract["timestamp"] = datetime.datetime.now().isoformat()
    if not contract.get("hash") and contract.get("prompt"):
        contract["hash"] = hashlib.sha256(contract["prompt"].encode('utf-8')).hexdigest()
    
    data = {
        "contract_id": contract.get("id"),
        "timestamp": contract.get("timestamp"),
        "model": contract.get("model"),
        "temperature": contract.get("temperature"),
        "prompt": contract.get("prompt"),
        "run_id": contract.get("run_id"),
        "hash": contract.get("hash"),
        "raw_output": contract.get("raw_output"),
        "normalized_output": contract.get("normalized_output"),
        "lines_added": contract.get("delta", {}).get("lines_added"),
        "lines_removed": contract.get("delta", {}).get("lines_removed"),
        "changed_lines": contract.get("delta", {}).get("changed_lines"),
        "similarity_score": contract.get("delta", {}).get("similarity_score")
    }

    df = pd.DataFrame([data])

    if os.path.exists(RESULTS_FILE):
        existing_df = pd.read_excel(RESULTS_FILE, engine='openpyxl')
        df = pd.concat([existing_df, df], ignore_index=True)

    try:
        df.to_excel(RESULTS_FILE, index=False, engine='openpyxl')
    except Exception as e:
        print(f"Error saving results to {RESULTS_FILE}: {e}")

# --- Console Result Logging ---

def log_experiment_result(contract_id, attempt, compliant, code, reflection, normalized_dev_intent=None, normalized_user_intent=None):
    print(f"[{contract_id}] Attempt {attempt} — {' Compliant' if compliant else ' Not compliant'}")
    if normalized_dev_intent:
        print(f"Normalized Dev Intent: {normalized_dev_intent}")
    if normalized_user_intent:
        print(f"Normalized User Intent: {normalized_user_intent}")
    print("Reflection:", reflection)
    print("Code:", code[:60], "...")

# --- Per-Contract, Per-Run File-Based Logging ---

def _make_contract_dir(contract):
    # Accept dict or PromptContract
    if hasattr(contract, "function_name"):
        cname = contract.function_name
    elif isinstance(contract, dict):
        cname = contract.get("function_name") or contract.get("id", "unknown_contract")
    else:
        cname = "unknown_contract"
    contract_dir = os.path.join(RESULTS_DIR, cname)
    os.makedirs(contract_dir, exist_ok=True)
    return contract_dir

def save_raw_output(contract, run, raw_output):
    contract_dir = _make_contract_dir(contract)
    with open(os.path.join(contract_dir, f"raw_output_run{run+1}.py"), "w", encoding="utf-8") as f:
        f.write(raw_output)
    # Save contract snapshot
    path = os.path.join(contract_dir, "contract.json")
    try:
        cdict = contract.to_dict() if hasattr(contract, "to_dict") else dict(contract)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cdict, f, indent=2)
    except Exception as e:
        print(f"Warning: could not save contract.json ({e})")

def save_compliance(contract, run, compliance, stage):
    contract_dir = _make_contract_dir(contract)
    fname = f"compliance_{stage}_run{run+1}.json"
    with open(os.path.join(contract_dir, fname), "w", encoding="utf-8") as f:
        json.dump(compliance, f, indent=2)

def save_normalized(contract, run, normalized_code, corrections):
    contract_dir = _make_contract_dir(contract)
    with open(os.path.join(contract_dir, f"normalized_run{run+1}.py"), "w", encoding="utf-8") as f:
        f.write(normalized_code)
    with open(os.path.join(contract_dir, f"corrections_run{run+1}.json"), "w", encoding="utf-8") as f:
        json.dump({"corrections": corrections}, f, indent=2)

def save_final(contract, run, final_code, status):
    contract_dir = _make_contract_dir(contract)
    if final_code:
        with open(os.path.join(contract_dir, f"final_run{run+1}.py"), "w", encoding="utf-8") as f:
            f.write(final_code)
    with open(os.path.join(contract_dir, f"final_status_run{run+1}.txt"), "w", encoding="utf-8") as f:
        f.write(status)
