#!/usr/bin/env python3
"""
Phase 2 Full Experiment Runner
12 contracts × 3 models × 5 temps × 20 runs = 3,600 generations
Estimated time: 7-9 hours
Estimated cost: ~$16
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Configuration
CONTRACTS = [
    "fibonacci_basic",
    "fibonacci_recursive",
    "slugify",
    "balanced_brackets",
    "gcd",
    "binary_search",
    "lru_cache",
    "merge_sort",
    "quick_sort",
    "factorial",
    "is_palindrome",
    "is_prime"
]

MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "claude-sonnet-4-5-20250929"
]

TEMPERATURES = [0.0, 0.3, 0.5, 0.7, 1.0]
RUNS_PER_CONFIG = 20

def run_experiment(contract, model, temperature, runs):
    """Run single experiment configuration"""
    cmd = [
        "python", "main.py",
        "--contract", contract,
        "--runs", str(runs),
        "--temperature", str(temperature),
        "--model", model
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout per config
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            print(f"    FAILED (exit code: {result.returncode})")
            print(f"    Error: {result.stderr[:200]}")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print(f"    TIMEOUT (>10 minutes)")
        return False
    except Exception as e:
        print(f"    EXCEPTION: {e}")
        return False

def main():
    """Run full Phase 2 experiment"""
    
    start_time = time.time()
    
    print("=" * 80)
    print("SKYT PHASE 2 FULL EXPERIMENT")
    print("=" * 80)
    print(f"Contracts: {len(CONTRACTS)}")
    print(f"Models: {len(MODELS)}")
    print(f"Temperatures: {len(TEMPERATURES)}")
    print(f"Runs per config: {RUNS_PER_CONFIG}")
    print(f"Total generations: {len(CONTRACTS) * len(MODELS) * len(TEMPERATURES) * RUNS_PER_CONFIG}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    total_configs = len(CONTRACTS) * len(MODELS) * len(TEMPERATURES)
    completed_configs = 0
    failed_configs = 0
    
    # Run all configurations
    for contract_idx, contract in enumerate(CONTRACTS, 1):
        print(f"\n{'='*80}")
        print(f"CONTRACT {contract_idx}/{len(CONTRACTS)}: {contract}")
        print(f"{'='*80}")
        
        for model_idx, model in enumerate(MODELS, 1):
            print(f"\n  Model {model_idx}/{len(MODELS)}: {model}")
            print(f"  {'-'*76}")
            
            for temp_idx, temp in enumerate(TEMPERATURES, 1):
                config_num = completed_configs + failed_configs + 1
                progress = (config_num / total_configs) * 100
                
                print(f"    [{config_num}/{total_configs}] ({progress:.1f}%) Temp {temp}...", end=" ", flush=True)
                
                success = run_experiment(contract, model, temp, RUNS_PER_CONFIG)
                
                if success:
                    completed_configs += 1
                    print("OK")
                else:
                    failed_configs += 1
                    print("FAILED - STOPPING (stop-on-error mode)")
                    
                    # Print summary
                    elapsed = time.time() - start_time
                    print(f"\n{'='*80}")
                    print("EXPERIMENT STOPPED ON ERROR")
                    print(f"{'='*80}")
                    print(f"Completed: {completed_configs}/{total_configs}")
                    print(f"Failed: {failed_configs}")
                    print(f"Elapsed time: {elapsed/3600:.2f} hours")
                    print(f"{'='*80}")
                    
                    sys.exit(1)
                
                # Rate limiting (200ms between configs)
                time.sleep(0.2)
                
                # Progress update every 10 configs
                if config_num % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = config_num / elapsed if elapsed > 0 else 0
                    remaining = (total_configs - config_num) / rate if rate > 0 else 0
                    print(f"\n    Progress: {config_num}/{total_configs} configs")
                    print(f"    Elapsed: {elapsed/3600:.2f}h, Remaining: ~{remaining/3600:.1f}h")
    
    # Final summary
    elapsed = time.time() - start_time
    print(f"\n{'='*80}")
    print("PHASE 2 FULL EXPERIMENT COMPLETE")
    print(f"{'='*80}")
    print(f"Total configurations: {total_configs}")
    print(f"Completed: {completed_configs}")
    print(f"Failed: {failed_configs}")
    print(f"Total time: {elapsed/3600:.2f} hours")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nResults saved to: outputs/")
    print(f"Metrics summary: outputs/metrics_summary.csv")
    print(f"{'='*80}")
    
    return 0 if failed_configs == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
