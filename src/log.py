import os
import json
import pandas as pd
import datetime
import hashlib
from typing import Dict, List, Optional, Any
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

def save_final(contract, run: int, final_code: str, status: str, 
               audit_trail: Optional[Dict[str, Any]] = None):
    """
    Enhanced save_final with comprehensive audit trail for raw vs canonical tracking
    
    Args:
        contract: Contract object or dict
        run: Run number (0-indexed)
        final_code: Final processed code
        status: Processing status ('raw', 'normalized', 'repaired', 'failed')
        audit_trail: Comprehensive audit information including:
            - raw_code: Original LLM output
            - canonical_hash: Hash of canonical form
            - behavior_hash: Hash of behavioral equivalence
            - repair_steps: List of repair operations applied
            - determinism_violations: List of determinism issues found
            - canonicalization_transformations: List of canonicalization steps
            - cache_hit: Whether result came from cache
            - execution_metadata: Execution environment info
    """
    contract_dir = _make_contract_dir(contract)
    
    # Save the final code
    if final_code:
        with open(os.path.join(contract_dir, f"final_run{run+1}.py"), "w", encoding="utf-8") as f:
            f.write(final_code)
    
    # Save basic status (backward compatibility)
    with open(os.path.join(contract_dir, f"final_status_run{run+1}.txt"), "w", encoding="utf-8") as f:
        f.write(status)
    
    # Save comprehensive audit trail if provided
    if audit_trail:
        audit_file = os.path.join(contract_dir, f"audit_trail_run{run+1}.json")
        
        # Enhance audit trail with metadata
        enhanced_audit = {
            "run_number": run + 1,
            "timestamp": datetime.datetime.now().isoformat(),
            "final_status": status,
            "processing_pipeline": {
                "raw_code_length": len(audit_trail.get("raw_code", "")),
                "final_code_length": len(final_code) if final_code else 0,
                "repair_steps_applied": audit_trail.get("repair_steps", []),
                "canonicalization_transformations": audit_trail.get("canonicalization_transformations", []),
                "determinism_violations": audit_trail.get("determinism_violations", [])
            },
            "hashes": {
                "canonical_hash": audit_trail.get("canonical_hash"),
                "behavior_hash": audit_trail.get("behavior_hash"),
                "raw_code_hash": hashlib.sha256(
                    audit_trail.get("raw_code", "").encode('utf-8')
                ).hexdigest()[:16] if audit_trail.get("raw_code") else None
            },
            "cache_info": {
                "cache_hit": audit_trail.get("cache_hit", False),
                "cache_key": audit_trail.get("cache_key"),
                "cache_source": audit_trail.get("cache_source")
            },
            "execution_metadata": audit_trail.get("execution_metadata", {}),
            "repeatability_metrics": {
                "is_deterministic": audit_trail.get("is_deterministic", False),
                "canonicalization_successful": status in ['raw', 'normalized', 'repaired'],
                "repair_complexity": len(audit_trail.get("repair_steps", [])),
                "transformation_count": len(audit_trail.get("canonicalization_transformations", []))
            }
        }
        
        # Add the original audit trail data
        enhanced_audit.update(audit_trail)
        
        try:
            with open(audit_file, "w", encoding="utf-8") as f:
                json.dump(enhanced_audit, f, indent=2)
        except Exception as e:
            print(f"Warning: could not save audit trail ({e})")

def save_repeatability_analysis(contract, run_results: List[Dict[str, Any]], 
                              metrics: Dict[str, float]):
    """
    Save comprehensive repeatability analysis across all runs
    
    Args:
        contract: Contract object or dict
        run_results: List of audit trails from all runs
        metrics: Computed repeatability metrics (R_intrinsic, cache_rescue_rate, etc.)
    """
    contract_dir = _make_contract_dir(contract)
    
    analysis = {
        "timestamp": datetime.datetime.now().isoformat(),
        "contract_name": getattr(contract, "function_name", "unknown"),
        "total_runs": len(run_results),
        "repeatability_metrics": metrics,
        "run_summary": [],
        "cross_run_analysis": {
            "unique_canonical_hashes": len(set(
                r.get("canonical_hash") for r in run_results if r.get("canonical_hash")
            )),
            "unique_behavior_hashes": len(set(
                r.get("behavior_hash") for r in run_results if r.get("behavior_hash")
            )),
            "status_distribution": {},
            "repair_step_frequency": {},
            "determinism_violation_frequency": {}
        }
    }
    
    # Analyze each run
    status_counts = {}
    repair_step_counts = {}
    violation_counts = {}
    
    for i, result in enumerate(run_results):
        run_summary = {
            "run_number": i + 1,
            "status": result.get("final_status", "unknown"),
            "canonical_hash": result.get("canonical_hash"),
            "behavior_hash": result.get("behavior_hash"),
            "repair_steps_count": len(result.get("repair_steps", [])),
            "determinism_violations_count": len(result.get("determinism_violations", [])),
            "cache_hit": result.get("cache_hit", False)
        }
        analysis["run_summary"].append(run_summary)
        
        # Count frequencies
        status = result.get("final_status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        
        for step in result.get("repair_steps", []):
            repair_step_counts[step] = repair_step_counts.get(step, 0) + 1
        
        for violation in result.get("determinism_violations", []):
            rule = violation.get("rule", "unknown") if isinstance(violation, dict) else str(violation)
            violation_counts[rule] = violation_counts.get(rule, 0) + 1
    
    analysis["cross_run_analysis"]["status_distribution"] = status_counts
    analysis["cross_run_analysis"]["repair_step_frequency"] = repair_step_counts
    analysis["cross_run_analysis"]["determinism_violation_frequency"] = violation_counts
    
    # Save analysis
    analysis_file = os.path.join(contract_dir, "repeatability_analysis.json")
    try:
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2)
    except Exception as e:
        print(f"Warning: could not save repeatability analysis ({e})")
