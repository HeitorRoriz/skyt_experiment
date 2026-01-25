#!/usr/bin/env python3
"""
Phase 1 Pilot - Simple Direct Implementation
Saves all outputs properly for inspection
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.llm_client import LLMClient
from src.contract import Contract
from src.oracle_system import OracleSystem
from src.canon_system import CanonSystem
from src.code_transformer import CodeTransformer

def main():
    """Run Phase 1 pilot with proper output saving"""
    
    # Configuration
    models = [
        "gpt-4o-mini",
        "gpt-4o",
        "claude-3-5-sonnet-20241022"
    ]
    
    contract_id = "fibonacci_basic"
    temperatures = [0.0, 0.7]
    runs_per_config = 5
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_output_dir = Path("outputs") / f"pilot_{timestamp}"
    base_output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("SKYT PHASE 1 PILOT EXPERIMENT")
    print("=" * 80)
    print(f"Contract: {contract_id}")
    print(f"Models: {', '.join(models)}")
    print(f"Temperatures: {temperatures}")
    print(f"Runs per config: {runs_per_config}")
    print(f"Total generations: {len(models) * len(temperatures) * runs_per_config}")
    print(f"Output directory: {base_output_dir}")
    print("=" * 80)
    print()
    
    # Load contract
    contract = Contract.from_template("contracts/templates.json", contract_id)
    print(f"✓ Contract loaded: {contract.data['task_intent']}\n")
    
    # Initialize systems
    oracle_system = OracleSystem()
    canon_system = CanonSystem(str(base_output_dir / "canon"))
    transformer = CodeTransformer(canon_system)
    
    # Track all results
    all_results = []
    total_calls = 0
    successful_calls = 0
    
    # Run for each model
    for model in models:
        print(f"\n{'='*80}")
        print(f"MODEL: {model}")
        print(f"{'='*80}\n")
        
        # Initialize LLM client
        try:
            llm_client = LLMClient(model=model)
        except Exception as e:
            print(f"✗ Failed to initialize {model}: {e}")
            print("  Stopping experiment (stop-on-error mode)")
            sys.exit(1)
        
        for temp in temperatures:
            print(f"\nTemperature: {temp}")
            print("-" * 40)
            
            # Create output directories
            raw_dir = base_output_dir / "raw_outputs" / model / f"temp_{temp}"
            repaired_dir = base_output_dir / "repaired_outputs" / model / f"temp_{temp}"
            raw_dir.mkdir(parents=True, exist_ok=True)
            repaired_dir.mkdir(parents=True, exist_ok=True)
            
            for run_num in range(1, runs_per_config + 1):
                total_calls += 1
                config_id = f"{contract_id}_{model}_temp{temp}_run{run_num}"
                
                try:
                    # Generate code
                    print(f"  Run {run_num}/{runs_per_config}...", end=" ", flush=True)
                    prompt = contract.data["prompt"]
                    raw_code = llm_client.generate_code(prompt, temperature=temp)
                    
                    # Save raw output
                    raw_file = raw_dir / f"run_{run_num:02d}.py"
                    raw_file.write_text(raw_code)
                    
                    # Test with oracle
                    oracle_result = oracle_system.run_oracle_tests(raw_code, contract.data)
                    oracle_passed = oracle_result["passed"]
                    
                    # Check contract adherence
                    contract_adherent = contract.validate_code(raw_code)
                    
                    # Transform if valid
                    repaired_code = raw_code
                    transformation_success = False
                    
                    if oracle_passed and contract_adherent:
                        # Get or set canon
                        canon_code = canon_system.get_or_set_anchor(contract_id, raw_code)
                        
                        # Transform
                        repaired_code, transform_result = transformer.transform(
                            raw_code,
                            canon_code,
                            contract
                        )
                        
                        transformation_success = transform_result.get("success", False)
                        
                        # Save repaired output
                        repaired_file = repaired_dir / f"run_{run_num:02d}.py"
                        repaired_file.write_text(repaired_code)
                    
                    # Track result
                    result = {
                        "config_id": config_id,
                        "model": model,
                        "temperature": temp,
                        "run_number": run_num,
                        "oracle_passed": oracle_passed,
                        "contract_adherent": contract_adherent,
                        "transformation_success": transformation_success,
                        "raw_file": str(raw_file.relative_to(base_output_dir)),
                        "repaired_file": str(repaired_file.relative_to(base_output_dir)) if oracle_passed and contract_adherent else None
                    }
                    all_results.append(result)
                    successful_calls += 1
                    
                    # Print status
                    status = "✓" if oracle_passed else "✗"
                    print(f"{status} (oracle: {oracle_passed}, contract: {contract_adherent})")
                    
                    # Rate limiting (200ms)
                    time.sleep(0.2)
                    
                except Exception as e:
                    print(f"✗ FAILED: {e}")
                    print(f"  Stopping experiment (stop-on-error mode)")
                    
                    # Save partial results
                    results_file = base_output_dir / "results.json"
                    with open(results_file, 'w') as f:
                        json.dump(all_results, f, indent=2)
                    
                    sys.exit(1)
            
            # Summary for this temperature
            temp_results = [r for r in all_results if r["model"] == model and r["temperature"] == temp]
            oracle_pass_rate = sum(1 for r in temp_results if r["oracle_passed"]) / len(temp_results)
            print(f"  Summary: {len(temp_results)} runs, {oracle_pass_rate:.0%} oracle pass rate")
    
    # Save final results
    results_file = base_output_dir / "results.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Calculate summary statistics
    summary = {
        "total_calls": total_calls,
        "successful_calls": successful_calls,
        "oracle_pass_rate": sum(1 for r in all_results if r["oracle_passed"]) / len(all_results),
        "contract_adherence_rate": sum(1 for r in all_results if r["contract_adherent"]) / len(all_results),
        "transformation_success_rate": sum(1 for r in all_results if r["transformation_success"]) / sum(1 for r in all_results if r["contract_adherent"]) if any(r["contract_adherent"] for r in all_results) else 0
    }
    
    summary_file = base_output_dir / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "=" * 80)
    print("PHASE 1 PILOT COMPLETE")
    print("=" * 80)
    print(f"Total calls: {total_calls}")
    print(f"Successful calls: {successful_calls}")
    print(f"Oracle pass rate: {summary['oracle_pass_rate']:.1%}")
    print(f"Contract adherence rate: {summary['contract_adherence_rate']:.1%}")
    print(f"Transformation success rate: {summary['transformation_success_rate']:.1%}")
    print(f"\nResults saved to: {base_output_dir}")
    print("=" * 80)

if __name__ == "__main__":
    main()
