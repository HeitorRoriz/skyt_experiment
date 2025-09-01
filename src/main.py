# src/main.py
"""
Main entry point for SKYT pipeline experiments
Drives experiment execution via matrix-based scheduling
"""

import sys
import os
from typing import Optional
from .config import OUTPUT_DIR_TEMPLATE
from .matrix import ExperimentMatrix
from .experiment import run_experiment, load_anchor_signatures
from .contract import load_contract_from_template


def main(max_experiments: Optional[int] = None):
    """
    Main experiment runner
    
    Args:
        max_experiments: Maximum number of experiments to run (None for all)
    """
    # Initialize anchor canonicalization system
    print("SKYT Pipeline Experiment Runner (Anchor Canon Mode)")
    print("=" * 50)
    
    print("Loading existing anchor signatures...")
    load_anchor_signatures()
    
    matrix = ExperimentMatrix()
    
    status = matrix.get_status_summary()
    print(f"Experiment Status: {status}")
    
    experiments_run = 0
    
    while True:
        if max_experiments and experiments_run >= max_experiments:
            break
            
        exp = matrix.get_next_experiment()
        if not exp:
            print("No more pending experiments")
            break
        
        print(f"\nRunning: {exp['prompt_id']} (T={exp['temperature']}, mode={exp['mode']})")
        
        try:
            # Mark as running
            matrix.mark_experiment_running(
                exp["prompt_id"], 
                exp["temperature"], 
                exp["mode"]
            )
            
            # Determine output path
            output_dir = OUTPUT_DIR_TEMPLATE.format(
                mode=exp["mode"],
                temperature=exp["temperature"]
            )
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "results.csv")
            
            # Load contract template path if using contracts
            contract_template_path = None
            if exp["mode"] == "with_contract":
                contract_template_path = "contracts/templates.json"
            
            # Run experiment
            result = run_experiment(
                prompt_id=exp["prompt_id"],
                prompt=_get_prompt_for_id(exp["prompt_id"]),
                model=exp["model"],
                temperature=exp["temperature"],
                contract_template_path=contract_template_path
            )
            
            # Update result with output path
            from .log import write_execution_record
            write_execution_record(result, output_path)
            
            # Mark as completed
            matrix.mark_experiment_completed(
                exp["prompt_id"],
                exp["temperature"], 
                exp["mode"]
            )
            
            print(f"✓ Completed: {result['contract_pass']}")
            experiments_run += 1
            
        except Exception as e:
            print(f"✗ Failed: {str(e)}")
            matrix.mark_experiment_failed(
                exp["prompt_id"],
                exp["temperature"],
                exp["mode"], 
                str(e)
            )
    
    print(f"\nCompleted {experiments_run} experiments")
    final_status = matrix.get_status_summary()
    print(f"Final Status: {final_status}")


def _get_prompt_for_id(prompt_id: str) -> str:
    """Get prompt text for given prompt ID"""
    import json
    
    templates_path = "contracts/templates.json"
    if os.path.exists(templates_path):
        with open(templates_path, 'r') as f:
            templates = json.load(f)
        
        for template in templates:
            if template["id"] == prompt_id:
                return template["prompt"]
    
    # Fallback
    return f"Generate Python code for {prompt_id}"


if __name__ == "__main__":
    max_exp = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(max_exp)
