#!/usr/bin/env python3
"""
Chunk 4: lru_cache_strict (gpt-4o + Claude × 5 temps = 10 configs)
Estimated time: ~25 minutes
"""

import subprocess
import sys
from datetime import datetime

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
    print("="*80)
    print("STRICT CONTRACT EXPERIMENTS - CHUNK 4")
    print("="*80)
    
    contracts = ['lru_cache_strict']
    models = ['gpt-4o', 'claude-sonnet-4-5-20250929']
    temperatures = [0.0, 0.3, 0.5, 0.7, 1.0]
    runs = 20
    
    total_configs = len(contracts) * len(models) * len(temperatures)
    
    print(f"Contracts: {contracts}")
    print(f"Models: {models}")
    print(f"Temperatures: {temperatures}")
    print(f"Runs per config: {runs}")
    print(f"Total configs: {total_configs}")
    print(f"Total generations: {total_configs * runs}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    completed = 0
    failed = 0
    start_time = datetime.now()
    
    for contract_idx, contract in enumerate(contracts, 1):
        print(f"\n{'='*80}")
        print(f"CONTRACT {contract_idx}/{len(contracts)}: {contract}")
        print(f"{'='*80}")
        
        for model_idx, model in enumerate(models, 1):
            print(f"\n  Model {model_idx}/{len(models)}: {model}")
            print(f"  {'-'*76}")
            
            for temp_idx, temp in enumerate(temperatures, 1):
                config_num = (contract_idx-1)*len(models)*len(temperatures) + (model_idx-1)*len(temperatures) + temp_idx
                
                elapsed = (datetime.now() - start_time).total_seconds() / 60
                if completed > 0:
                    avg_time = elapsed / completed
                    remaining = avg_time * (total_configs - completed)
                    print(f"    [{config_num}/{total_configs}] Temp {temp}... ", end='', flush=True)
                else:
                    print(f"    [{config_num}/{total_configs}] Temp {temp}... ", end='', flush=True)
                
                success = run_experiment(contract, model, temp, runs)
                
                if success:
                    print("OK")
                    completed += 1
                else:
                    print("FAILED")
                    failed += 1
            
            if completed > 0:
                elapsed = (datetime.now() - start_time).total_seconds() / 60
                avg_time = elapsed / completed
                remaining = avg_time * (total_configs - completed)
                print(f"\n    Elapsed: {elapsed:.1f}m, Remaining: ~{remaining:.1f}m")
    
    print(f"\n{'='*80}")
    print("CHUNK 4 COMPLETE")
    print(f"{'='*80}")
    print(f"Total configurations: {total_configs}")
    print(f"Completed: {completed}")
    print(f"Failed: {failed}")
    print(f"Total time: {(datetime.now() - start_time).total_seconds() / 60:.1f} minutes")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
