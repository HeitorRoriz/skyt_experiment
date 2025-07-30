# src/main_with_repeatability.py

from contract import PromptContract
from llm import call_llm
from compliance_checker import check_compliance
from prompt_builder import build_prompt_from_contract
from normalizer import normalize_code
import log
from config import NUM_RUNS, CONTRACTS_DIR
from contract_generator import generate_contracts_from_prompts
from repeatability import calculate_all_repeatability_scores, save_repeatability_report
import os
import sys

def run_experiments_with_repeatability():
    """Run the complete experiment workflow with repeatability calculation"""
    
    print("="*60)
    print("SKYT EXPERIMENT - WITH REPEATABILITY ANALYSIS")
    print("="*60)
    
    # Step 1: Generate contracts from prompts in config.py
    print("Step 1: Generating contracts from experiment templates...")
    try:
        generated_contracts = generate_contracts_from_prompts()
        print(f"Successfully generated {len(generated_contracts)} contracts")
    except Exception as e:
        print(f"Error generating contracts: {e}")
        return
    
    print("\n" + "-"*40)
    
    # Step 2: Load contracts from JSON files
    print("Step 2: Loading contracts for experiments...")
    experiment_contracts = []

    if not os.path.exists(CONTRACTS_DIR):
        print(f"[ERROR] Contract directory '{CONTRACTS_DIR}' does not exist.")
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
            print(f"Loaded contract: {contract.function_name}")
        except Exception as e:
            print(f"[WARNING] Failed to load contract from '{fpath}': {e}")

    if not experiment_contracts:
        print(f"[ERROR] No valid contracts loaded. Please check your contract files.")
        sys.exit(1)

    print(f"Loaded {len(experiment_contracts)} contracts for experiments")
    print("\n" + "-"*40)
    
    # Step 3: Run experiments
    print("Step 3: Running experiments...")
    total_runs = len(experiment_contracts) * NUM_RUNS
    current_run = 0
    
    for contract in experiment_contracts:
        print(f"\nRunning experiments for contract: {contract.function_name}")
        
        for run in range(NUM_RUNS):
            current_run += 1
            print(f"  Run {run+1}/{NUM_RUNS} (Overall: {current_run}/{total_runs})")

            prompt = build_prompt_from_contract(contract)
            # Create proper contract structure for LLM call
            llm_contract = {
                "system_message": "You are a professional software engineer. Generate code that fulfills the following requirements.",
                "user_prompt": prompt
            }
            raw_output = call_llm(llm_contract)

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
            
            print(f"    Status: {status}")
    
    print("\n" + "-"*40)
    
    # Step 4: Calculate repeatability scores
    print("Step 4: Calculating repeatability scores...")
    try:
        scores = calculate_all_repeatability_scores()
        if scores:
            save_repeatability_report(scores)
            print("Repeatability analysis completed successfully!")
        else:
            print("No repeatability scores could be calculated - check if experiments ran successfully")
    except Exception as e:
        print(f"Error calculating repeatability scores: {e}")
    
    print("\n" + "="*60)
    print("EXPERIMENT COMPLETED")
    print("="*60)

if __name__ == "__main__":
    run_experiments_with_repeatability()
