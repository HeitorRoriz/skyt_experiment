#!/usr/bin/env python3
import json
import glob

files = sorted(glob.glob('outputs/is_prime_strict_temp*.json'))[-15:]

print("="*80)
print("CANON CODE:")
print("="*80)
with open('outputs/canon/is_prime_strict_canon.json', 'r', encoding='utf-8') as f:
    canon = json.load(f)
    print(canon.get('canonical_code', ''))

models_shown = set()

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    model = data.get('model', 'unknown')
    
    if model not in models_shown:
        models_shown.add(model)
        llm_outputs = data.get('llm_outputs', [])
        
        if llm_outputs:
            print(f"\n{'='*80}")
            print(f"{model.upper()} - SAMPLE OUTPUT:")
            print(f"{'='*80}")
            print(llm_outputs[0])
            
            # Check if matches canon
            canon_code = canon.get('canonical_code', '').strip()
            output_code = llm_outputs[0].strip()
            
            print(f"\n✅ Matches canon: {canon_code == output_code}")
            
            if canon_code != output_code:
                print("\nDifferences:")
                if 'result =' in output_code:
                    print("  - Uses 'result' flag variable")
                if 'else:' in output_code:
                    print("  - Has 'else' block")
                if 'limit =' in output_code:
                    print("  - Uses 'limit' variable")
                if 'n < 2' in output_code:
                    print("  - Uses 'n < 2' instead of 'n <= 1'")
    
    if len(models_shown) == 3:
        break
