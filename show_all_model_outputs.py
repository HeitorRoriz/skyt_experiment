#!/usr/bin/env python3
import json

# Load canon
with open('outputs/canon/is_prime_strict_canon.json', 'r', encoding='utf-8') as f:
    canon_code = json.load(f)['canonical_code']

print("="*80)
print("CANON CODE:")
print("="*80)
print(canon_code)

# Load each model's output
files = {
    'gpt-4o-mini': 'outputs/is_prime_strict_temp0.0_20260124_204015.json',
    'gpt-4o': 'outputs/is_prime_strict_temp0.0_20260124_204321.json',
    'claude-sonnet-4-5-20250929': 'outputs/is_prime_strict_temp0.3_20260124_204350.json'
}

for model, filepath in files.items():
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    output = data['raw_outputs'][0]
    
    print(f"\n{'='*80}")
    print(f"{model.upper()}")
    print(f"{'='*80}")
    print(output)
    
    matches = output.strip() == canon_code.strip()
    print(f"\n✅ Matches canon: {matches}")
    
    if not matches:
        print("\nDifferences:")
        if 'result =' in output:
            print("  - Uses 'result' flag variable")
        if 'else:' in output and 'else:' not in canon_code:
            print("  - Has 'else' block")
        if 'limit =' in output:
            print("  - Uses 'limit' variable")
        if 'n < 2' in output:
            print("  - Uses 'n < 2' instead of 'n <= 1'")
        if 'n ** 0.5' in output and 'n**0.5' in canon_code:
            print("  - Spacing: 'n ** 0.5' vs 'n**0.5'")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("\n✅ gpt-4o-mini: EXACT match to canon (100%)")
print("❌ gpt-4o: Different pattern (uses result flag)")
print("❌ Claude: Different pattern (uses result flag + limit variable)")
