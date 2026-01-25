#!/usr/bin/env python3
"""
Run strict MISRA/DO-178C contracts and compare with simple versions.
3 contracts × 3 models × 5 temps × 20 runs = 900 generations
Estimated time: ~1 hour
"""

import subprocess
import sys
import time
from datetime import datetime

# Strict contracts to test
CONTRACTS = [
    "is_prime_strict",
    "binary_search_strict",
    "lru_cache_strict"
]

MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "claude-sonnet-4-5-20250929"
]

TEMPERATURES = [0.0, 0.3, 0.5, 0.7, 1.0]
RUNS_PER_CONFIG = 20

def run_experiment(contract, model, temperature, runs):
    """Run a single experiment configuration"""
    import os
    
    cmd = [
        sys.executable, "main.py",
        "--contract", contract,
        "--model", model,
        "--temperature", str(temperature),
        "--runs", str(runs)
    ]
    
    # Set UTF-8 encoding for subprocess to handle emoji output
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            encoding='utf-8',
            errors='replace',
            env=env
        )
        if result.returncode != 0:
            print(f"\n    STDERR: {result.stderr[:500]}")
            print(f"    STDOUT: {result.stdout[-500:]}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    total_configs = len(CONTRACTS) * len(MODELS) * len(TEMPERATURES)
    completed = 0
    failed = 0
    start_time = time.time()
    
    print("=" * 80)
    print("STRICT MISRA/DO-178C CONTRACT EXPERIMENT")
    print("=" * 80)
    print(f"Contracts: {CONTRACTS}")
    print(f"Models: {len(MODELS)}")
    print(f"Temperatures: {TEMPERATURES}")
    print(f"Runs per config: {RUNS_PER_CONFIG}")
    print(f"Total configs: {total_configs}")
    print(f"Total generations: {total_configs * RUNS_PER_CONFIG}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    for c_idx, contract in enumerate(CONTRACTS, 1):
        print(f"\n{'='*80}")
        print(f"CONTRACT {c_idx}/{len(CONTRACTS)}: {contract}")
        print("=" * 80)
        
        for m_idx, model in enumerate(MODELS, 1):
            print(f"\n  Model {m_idx}/{len(MODELS)}: {model}")
            print("  " + "-" * 76)
            
            for temp in TEMPERATURES:
                completed += 1
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                remaining = (total_configs - completed) / rate if rate > 0 else 0
                
                print(f"    [{completed}/{total_configs}] Temp {temp}...", end=" ", flush=True)
                
                success = run_experiment(contract, model, temp, RUNS_PER_CONFIG)
                
                if success:
                    print("OK")
                else:
                    print("FAILED")
                    failed += 1
            
            print(f"\n    Elapsed: {elapsed/60:.1f}m, Remaining: ~{remaining/60:.1f}m")
    
    end_time = time.time()
    total_time = (end_time - start_time) / 60
    
    print("\n" + "=" * 80)
    print("STRICT CONTRACT EXPERIMENT COMPLETE")
    print("=" * 80)
    print(f"Total configurations: {total_configs}")
    print(f"Completed: {completed - failed}")
    print(f"Failed: {failed}")
    print(f"Total time: {total_time:.1f} minutes")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
