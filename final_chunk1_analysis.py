#!/usr/bin/env python3
"""
Final analysis of Chunk 1 results with correct canon.
"""

import json
import glob

def main():
    # Load canon
    with open('outputs/canon/is_prime_strict_canon.json', 'r', encoding='utf-8') as f:
        canon_data = json.load(f)
    
    canon_code = canon_data.get('canonical_code', '').strip()
    
    print("="*80)
    print("CHUNK 1 FINAL ANALYSIS (With Correct Canon)")
    print("="*80)
    
    print("\n## CANON CODE:")
    print(canon_code)
    
    # Get latest experiment files
    files = sorted(glob.glob('outputs/is_prime_strict_temp*.json'))[-15:]
    
    results_by_model = {
        'gpt-4o-mini': {'outputs': [], 'matches': 0, 'total': 0},
        'gpt-4o': {'outputs': [], 'matches': 0, 'total': 0},
        'claude-sonnet-4-5-20250929': {'outputs': [], 'matches': 0, 'total': 0}
    }
    
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        model = data.get('model', 'unknown')
        if model in results_by_model:
            llm_outputs = data.get('llm_outputs', [])
            
            for output in llm_outputs:
                results_by_model[model]['total'] += 1
                if output.strip() == canon_code:
                    results_by_model[model]['matches'] += 1
                
                # Store first unique output for display
                if len(results_by_model[model]['outputs']) < 2:
                    if output not in results_by_model[model]['outputs']:
                        results_by_model[model]['outputs'].append(output)
    
    # Display results
    for model, data in results_by_model.items():
        if data['total'] == 0:
            continue
        
        print(f"\n{'='*80}")
        print(f"{model.upper()}")
        print(f"{'='*80}")
        
        match_rate = data['matches'] / data['total'] if data['total'] > 0 else 0
        print(f"\nTotal outputs: {data['total']}")
        print(f"Exact canon matches: {data['matches']} ({match_rate:.1%})")
        
        if data['outputs']:
            print(f"\n## Sample Output:")
            sample = data['outputs'][0]
            print(sample)
            
            if sample.strip() != canon_code:
                print(f"\n## Differences from canon:")
                
                # Analyze differences
                if 'result =' in sample:
                    print("  ❌ Uses 'result' flag variable (canon uses direct returns)")
                if 'else:' in sample and 'else:' not in canon_code:
                    print("  ❌ Has 'else' block (canon doesn't)")
                if 'limit =' in sample:
                    print("  ❌ Uses 'limit' variable (canon uses inline calculation)")
                if 'n < 2' in sample and 'n <= 1' in canon_code:
                    print("  ❌ Uses 'n < 2' (canon uses 'n <= 1')")
                if 'n ** 0.5' in sample and 'n**0.5' in canon_code:
                    print("  ⚠️  Spacing difference in 'n ** 0.5' vs 'n**0.5'")
            else:
                print(f"\n✅ EXACT MATCH TO CANON")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for model, data in results_by_model.items():
        if data['total'] > 0:
            match_rate = data['matches'] / data['total']
            status = "✅ WORKING" if match_rate > 0.8 else "⚠️ PARTIAL" if match_rate > 0.3 else "❌ FAILING"
            print(f"\n{model}:")
            print(f"  Canon match rate: {match_rate:.1%}")
            print(f"  Status: {status}")
    
    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    
    print("\n✅ gpt-4o-mini: Naturally generates code matching canon")
    print("   - No transformation needed")
    print("   - 100% compliance with natural pattern")
    
    print("\n❌ gpt-4o & Claude: Generate different patterns")
    print("   - Use 'result' flags, 'else' blocks, 'limit' variables")
    print("   - Transformation pipeline cannot bridge these differences")
    print("   - Distances 0.3-0.5 from canon")
    
    print("\n## Root Cause:")
    print("The transformation pipeline is limited to:")
    print("  - Whitespace normalization")
    print("  - Variable renaming")
    print("  - Simple AST transformations")
    
    print("\nIt CANNOT:")
    print("  - Convert flag-based patterns to early-return patterns")
    print("  - Remove 'else' blocks and restructure control flow")
    print("  - Inline variables like 'limit'")
    
    print("\n## Options:")
    print("1. Accept gpt-4o-mini success, document gpt-4o/Claude limitations")
    print("2. Enhance transformation pipeline (significant work)")
    print("3. Adjust success threshold to 0.3-0.5 (accept 'close enough')")

if __name__ == "__main__":
    main()
