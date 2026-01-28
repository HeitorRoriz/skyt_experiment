#!/usr/bin/env python3
"""
Analyze the actual distances being calculated for transformations.
"""

import json
import glob

def main():
    print("="*80)
    print("TRANSFORMATION DISTANCE ANALYSIS")
    print("="*80)
    
    files = sorted(glob.glob('outputs/is_prime_strict_temp*.json'))[-15:]
    
    by_model = {
        'gpt-4o-mini': [],
        'gpt-4o': [],
        'claude-sonnet-4-5-20250929': []
    }
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            model = data.get('model', 'unknown')
            if model in by_model:
                trans_results = data.get('transformation_results', [])
                for t in trans_results:
                    if t.get('transformation_needed', False):
                        by_model[model].append({
                            'success': t.get('transformation_success', False),
                            'final_distance': t.get('final_distance', 999),
                            'transformations_applied': len(t.get('transformations_applied', []))
                        })
        except:
            pass
    
    for model, results in by_model.items():
        if not results:
            continue
        
        print(f"\n{'='*80}")
        print(f"{model}")
        print(f"{'='*80}")
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        print(f"\nTotal transformations: {len(results)}")
        print(f"Successful (distance < 0.1): {len(successful)}")
        print(f"Failed (distance >= 0.1): {len(failed)}")
        
        if successful:
            distances = [r['final_distance'] for r in successful]
            print(f"\nSuccessful transformations:")
            print(f"  Distance range: {min(distances):.4f} - {max(distances):.4f}")
            print(f"  Average distance: {sum(distances)/len(distances):.4f}")
        
        if failed:
            distances = [r['final_distance'] for r in failed]
            print(f"\nFailed transformations:")
            print(f"  Distance range: {min(distances):.4f} - {max(distances):.4f}")
            print(f"  Average distance: {sum(distances)/len(distances):.4f}")
            
            # Show distribution
            bins = [0, 0.1, 0.2, 0.3, 0.5, 1.0, 999]
            bin_labels = ['0-0.1', '0.1-0.2', '0.2-0.3', '0.3-0.5', '0.5-1.0', '>1.0']
            
            print(f"\n  Distance distribution:")
            for i in range(len(bins)-1):
                count = sum(1 for d in distances if bins[i] <= d < bins[i+1])
                if count > 0:
                    print(f"    {bin_labels[i]}: {count} ({100*count/len(distances):.1f}%)")
    
    print("\n" + "="*80)
    print("DIAGNOSIS")
    print("="*80)
    print("\nThe threshold for 'success' is: final_distance < 0.1")
    print("\nIf most failed transformations have distances just above 0.1,")
    print("the threshold may be too strict.")
    print("\nIf distances are much higher (>0.5), there's a real transformation problem.")

if __name__ == "__main__":
    main()
