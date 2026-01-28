#!/usr/bin/env python3
import json
import glob

files = sorted(glob.glob('outputs/is_prime_strict_temp0.0_*.json'))[-2:]

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("="*80)
    print(f"File: {filepath.split('/')[-1]}")
    print("="*80)
    print(f"Model: {data['model']}")
    print(f"Successful runs: {data['successful_runs']}/{data['num_runs']}")
    
    if data.get('raw_outputs'):
        print(f"\nFirst raw output:")
        print(data['raw_outputs'][0])
    
    print(f"\nMetrics:")
    print(f"  R_raw: {data['metrics']['R_raw']}")
    print(f"  R_anchor_post: {data['metrics']['R_anchor_post']}")
    print(f"  Rescue_rate: {data['metrics']['rescue_rate']}")
    
    print(f"\nTransformation results:")
    trans = data.get('transformation_results', [])
    if trans:
        success_count = sum(1 for t in trans if t.get('transformation_success', False))
        print(f"  Successful: {success_count}/{len(trans)}")
        print(f"  Distances: {[t.get('final_distance', 0) for t in trans]}")
    print()
