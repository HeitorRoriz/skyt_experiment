# src/main.py

from contract import PromptContract
from llm import call_llm
from compliance_checker import check_compliance
from prompt_builder import build_prompt_from_contract
from normalizer import normalize_code
import log
from config import NUM_RUNS
from config import CONTRACTS_DIR
import os
import sys

# 1. Robustly load contracts from JSON files
experiment_contracts = []

if not os.path.exists(CONTRACTS_DIR):
    print(f"[ERROR] Contract directory '{CONTRACTS_DIR}' does not exist. Please create it and add contract JSON files.")
    sys.exit(1)

contract_files = [
    os.path.join(CONTRACTS_DIR, fname)
    for fname in os.listdir(CONTRACTS_DIR)
    if fname.endswith(".json")
]

if not contract_files:
    print(f"[ERROR] No contract JSON files found in '{CONTRACTS_DIR}'.")
    sys.exit(1)

for fpath in contract_files:
    try:
        contract = PromptContract.from_json(fpath)
        experiment_contracts.append(contract)
    except Exception as e:
        print(f"[WARNING] Failed to load contract from '{fpath}': {e}")

if not experiment_contracts:
    print(f"[ERROR] No valid contracts loaded. Please check your contract files.")
    sys.exit(1)

# 2. Main experiment loop
for contract in experiment_contracts:
    for run in range(NUM_RUNS):
        print(f"Running contract '{contract.function_name}' (run {run+1}/{NUM_RUNS})")

        prompt = build_prompt_from_contract(contract)
        # Create proper contract structure for LLM call
        llm_contract = {
            "system_message": "You are a professional software engineer. Generate code that fulfills the following requirements.",
            "user_prompt": prompt
        }
        raw_output = call_llm(llm_contract)

        # log the prompt to stdout
        print(f"[Prompt - {contract.function_name} - Run {run+1}]\n{prompt}\n")

        log.save_raw_output(contract, run, raw_output)
        compliance = check_compliance(raw_output, contract)
        log.save_compliance(contract, run, compliance, "raw")

        if not all(compliance.values()):
            normalized_code, corrections = normalize_code(raw_output, contract)
            compliance_norm = check_compliance(normalized_code, contract)
            log.save_normalized(contract, run, normalized_code, corrections)
            log.save_compliance(contract, run, compliance_norm, "normalized")
            if all(compliance_norm.values()):
                final_code = normalized_code
                status = "normalized"
            else:
                final_code = None
                status = "failed"
        else:
            final_code = raw_output
            status = "raw"

        log.save_final(contract, run, final_code, status)
        
        # Create Excel summary log entry
        excel_log = {
            "id": f"{contract.function_name}-{run+1}",
            "model": "gpt-3.5-turbo",
            "temperature": 0.0,
            "prompt": prompt,
            "run_id": run+1,
            "raw_output": raw_output,
            "normalized_output": normalized_code if status == "normalized" else raw_output
        }
        log.log_results(excel_log)
        
        print(f"Run {run+1}: Status = {status}")

