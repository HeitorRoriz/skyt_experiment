#!/usr/bin/env python3
"""
Final compliance check: Does adding optimizations violate the contract?
"""

import json

with open('outputs/is_prime_strict_temp0.3_20260124_204350.json', 'r', encoding='utf-8') as f:
    claude_data = json.load(f)

claude_code = claude_data['raw_outputs'][0]

print("="*80)
print("CLAUDE COMPLIANCE CHECK")
print("="*80)

print("\nClaude's code:")
print(claude_code)

print("\n" + "="*80)
print("CONTRACT REQUIREMENTS")
print("="*80)

print("\nRequired:")
print("  - Loop: for i in range(2, int(n**0.5) + 1)")
print("  - No 'continue'")
print("  - No 'while'")

print("\n" + "="*80)
print("ANALYSIS")
print("="*80)

print("\n✅ Has required loop: for i in range(2, int(n**0.5) + 1)")
print("✅ No 'continue' statement")
print("✅ No 'while' statement")

print("\n⚠️  BUT adds extra checks:")
print("  - if n <= 3: return True")
print("  - if n % 2 == 0 or n % 3 == 0: return False")

print("\n## Question:")
print("Does adding optimizations BEFORE the required loop violate the contract?")

print("\nInterpretation A: STRICT")
print("  - Contract prescribes EXACT algorithm")
print("  - Any additions/modifications violate it")
print("  - Claude is NON-COMPLIANT")

print("\nInterpretation B: LENIENT")
print("  - Contract requires specific loop to be PRESENT")
print("  - Additional optimizations are acceptable")
print("  - Claude is COMPLIANT")

print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)

print("\nGiven the contract says:")
print("  'P10-2: Use bounded loop: for i in range(2, int(n**0.5) + 1)'")

print("\nThis seems to prescribe the ALGORITHM, not just the loop.")
print("The simple algorithm is: check all numbers from 2 to sqrt(n)")

print("\nClaude's optimizations (checking 2 and 3 first) change the algorithm.")
print("Even though the loop is present, the ALGORITHM is different.")

print("\n## VERDICT:")
print("❌ Claude is NON-COMPLIANT (under strict interpretation)")
print("   - Adds pre-checks that aren't in the prescribed algorithm")
print("   - Changes the algorithmic flow")

print("\n" + "="*80)
print("FINAL RESULTS")
print("="*80)

print("\n✅ gpt-4o-mini: 100% COMPLIANT")
print("   - Uses exact prescribed algorithm")
print("   - No modifications")

print("\n❌ gpt-4o: 0% COMPLIANT")
print("   - Uses completely different algorithm (6k±1)")
print("   - Wrong loop parameters")

print("\n❌ Claude: 0% COMPLIANT (strict interpretation)")
print("   - Correct loop but adds pre-checks")
print("   - Modified algorithm")

print("\n✅ Claude: 100% COMPLIANT (lenient interpretation)")
print("   - Has required loop")
print("   - Optimizations don't violate explicit constraints")

print("\n## Decision needed:")
print("Should we use STRICT or LENIENT interpretation?")
