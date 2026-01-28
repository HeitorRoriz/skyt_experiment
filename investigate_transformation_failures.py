#!/usr/bin/env python3
"""
Deep investigation into why gpt-4o and Claude transformations are failing
even after removing Rule 15.5.
"""

import json
import glob
import os

def analyze_latest_experiments():
    print("="*80)
    print("INVESTIGATING TRANSFORMATION FAILURES")
    print("="*80)
    
    # Get latest is_prime_strict experiments
    files = sorted(glob.glob('outputs/is_prime_strict_temp*.json'))
    
    if not files:
        print("No experiment files found!")
        return
    
    # Analyze last 15 files (5 per model)
    latest_files = files[-15:]
    
    print(f"\nAnalyzing {len(latest_files)} latest experiment files...")
    
    by_model = {
        'gpt-4o-mini': [],
        'gpt-4o': [],
        'claude-sonnet-4-5-20250929': []
    }
    
    for filepath in latest_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            model = data.get('model', 'unknown')
            if model in by_model:
                by_model[model].append({
                    'file': os.path.basename(filepath),
                    'data': data
                })
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
    
    print("\n" + "="*80)
    print("ANALYSIS BY MODEL")
    print("="*80)
    
    for model, experiments in by_model.items():
        if not experiments:
            continue
        
        print(f"\n{'='*80}")
        print(f"{model.upper()}")
        print(f"{'='*80}")
        print(f"Experiments analyzed: {len(experiments)}")
        
        # Check canon
        exp = experiments[0]['data']
        canon_data = exp.get('canon_data', {})
        
        print(f"\n## Canon Information:")
        print(f"  Canon created: {exp.get('canon_created', False)}")
        print(f"  Canon ID: {canon_data.get('canon_id', 'N/A')}")
        
        if canon_data.get('code'):
            canon_code = canon_data['code']
            print(f"  Canon code length: {len(canon_code)} chars")
            print(f"  Canon code preview:")
            print("  " + "\n  ".join(canon_code.split('\n')[:15]))
        
        # Analyze transformations
        print(f"\n## Transformation Analysis:")
        
        total_attempts = 0
        successful = 0
        failed = 0
        
        failure_reasons = {}
        
        for exp_data in experiments:
            data = exp_data['data']
            trans_results = data.get('transformation_results', [])
            
            for t in trans_results:
                total_attempts += 1
                
                if t.get('transformation_success', False):
                    successful += 1
                else:
                    failed += 1
                    reason = t.get('error', 'Unknown error')
                    failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        
        print(f"  Total transformation attempts: {total_attempts}")
        print(f"  Successful: {successful} ({100*successful/total_attempts if total_attempts > 0 else 0:.1f}%)")
        print(f"  Failed: {failed} ({100*failed/total_attempts if total_attempts > 0 else 0:.1f}%)")
        
        if failure_reasons:
            print(f"\n  Failure reasons:")
            for reason, count in sorted(failure_reasons.items(), key=lambda x: -x[1]):
                print(f"    - {reason}: {count} times")
        
        # Sample a failed transformation
        print(f"\n## Sample Failed Transformation:")
        for exp_data in experiments:
            data = exp_data['data']
            trans_results = data.get('transformation_results', [])
            
            for t in trans_results:
                if not t.get('transformation_success', False):
                    print(f"  File: {exp_data['file']}")
                    print(f"  Output index: {t.get('output_index', 'N/A')}")
                    print(f"  Error: {t.get('error', 'N/A')}")
                    
                    original = t.get('original_code', '')
                    if original:
                        print(f"\n  Original code:")
                        print("  " + "\n  ".join(original.split('\n')[:15]))
                    
                    transformed = t.get('transformed_code', '')
                    if transformed:
                        print(f"\n  Transformed code:")
                        print("  " + "\n  ".join(transformed.split('\n')[:15]))
                    
                    break
            else:
                continue
            break
    
    print("\n" + "="*80)
    print("KEY QUESTIONS TO ANSWER")
    print("="*80)
    print("\n1. Is the canon being created correctly?")
    print("2. What patterns are in the canon code?")
    print("3. What patterns are in the failing outputs?")
    print("4. What specific transformation errors are occurring?")
    print("5. Is the transformation pipeline even being invoked?")

if __name__ == "__main__":
    analyze_latest_experiments()
