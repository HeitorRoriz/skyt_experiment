#!/usr/bin/env python3
"""Check what Claude data we have for strict contracts"""

import json
import glob
import os

print("="*80)
print("CLAUDE DATA AVAILABILITY FOR STRICT CONTRACTS")
print("="*80)

# Strict contracts we care about
strict_contracts = ['is_prime_strict', 'binary_search_strict', 'lru_cache_strict']

# Check each strict contract
for contract in strict_contracts:
    print(f"\n{'='*80}")
    print(f"CONTRACT: {contract}")
    print(f"{'='*80}")
    
    # Find all files for this contract
    pattern = f"outputs/{contract}_temp*.json"
    files = sorted(glob.glob(pattern))
    
    if not files:
        print(f"  ❌ No data files found")
        continue
    
    print(f"\n  Found {len(files)} experiment files")
    
    # Check each file for Claude data
    claude_data = []
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            model = data.get('model', 'unknown')
            temp = data.get('temperature', 'unknown')
            runs = data.get('successful_runs', 0)
            total = data.get('num_runs', 0)
            
            if 'claude' in model.lower():
                claude_data.append({
                    'file': os.path.basename(filepath),
                    'model': model,
                    'temp': temp,
                    'runs': f"{runs}/{total}",
                    'timestamp': filepath.split('_')[-1].replace('.json', '')
                })
        except Exception as e:
            print(f"  ⚠️  Error reading {filepath}: {e}")
    
    if claude_data:
        print(f"\n  ✅ Found {len(claude_data)} Claude experiments:")
        for d in claude_data:
            print(f"    - Temp {d['temp']}: {d['runs']} runs ({d['timestamp']})")
    else:
        print(f"\n  ❌ No Claude data found for this contract")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

# Overall summary
total_claude_files = 0
for contract in strict_contracts:
    pattern = f"outputs/{contract}_temp*.json"
    files = glob.glob(pattern)
    
    claude_count = 0
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'claude' in data.get('model', '').lower():
                claude_count += 1
        except:
            pass
    
    total_claude_files += claude_count
    status = "✅" if claude_count > 0 else "❌"
    print(f"{status} {contract}: {claude_count} Claude experiments")

print(f"\n{'='*80}")
print(f"TOTAL: {total_claude_files} Claude experiments across all strict contracts")

if total_claude_files == 0:
    print("\n❌ NO CLAUDE DATA AVAILABLE FOR STRICT CONTRACTS")
    print("\nTo collect data, you need to:")
    print("  1. Add Anthropic API credits")
    print("  2. Run: python main.py --contract is_prime_strict --model claude-sonnet-4-5-20250929 --temperature 0.0 --runs 20")
    print("  3. Repeat for other temperatures: 0.3, 0.5, 0.7, 1.0")
    print("  4. Repeat for other strict contracts: binary_search_strict, lru_cache_strict")
else:
    print(f"\n✅ You have {total_claude_files} Claude experiments")
    print("\nCheck if you need more data for specific temperatures or contracts.")
