#!/usr/bin/env python3
"""
Check if the contract prescribes a SPECIFIC algorithm or just general constraints.
"""

import json

with open('contracts/templates.json', 'r', encoding='utf-8') as f:
    contracts = json.load(f)

contract = contracts['is_prime_strict']

print("="*80)
print("CONTRACT ANALYSIS: is_prime_strict")
print("="*80)

print("\n## NASA P10-2 Requirement:")
p10_2 = contract['constraints']['nasa_power_of_10']['p10_2']
print(f"  '{p10_2}'")

print("\n## Interpretation:")
print("\nThe contract states: 'Bounded loop: for i in range(2, int(n**0.5) + 1)'")
print("\nNote: int(n**0.5) means int(sqrt(n)) - the integer square root")

print("\n## Is this PRESCRIPTIVE (specific algorithm) or DESCRIPTIVE (example)?")

print("\nOption A: PRESCRIPTIVE")
print("  - The contract REQUIRES: for i in range(2, int(n**0.5) + 1)")
print("  - Start at 2, end at sqrt(n), step by 1")
print("  - Any other range violates the contract")
print("  - Example: range(5, ..., 6) would be NON-COMPLIANT")

print("\nOption B: DESCRIPTIVE")
print("  - The contract REQUIRES: a bounded loop using 'for i in range'")
print("  - The specific parameters are just an example")
print("  - Any bounded range is acceptable")
print("  - Example: range(5, ..., 6) would be COMPLIANT")

print("\n" + "="*80)
print("CHECKING THE PROMPT")
print("="*80)

prompt = contract['prompt']
print("\nPrompt says:")
print("  'P10-2: Use bounded loop: for i in range(2, int(n**0.5) + 1)'")

print("\n## Analysis:")
print("\nThe phrase 'Use bounded loop: for i in range(2, int(n**0.5) + 1)'")
print("suggests this is PRESCRIPTIVE - it says 'Use' this specific loop.")

print("\n" + "="*80)
print("VERDICT")
print("="*80)

print("\n✅ The contract IS PRESCRIPTIVE")
print("\nIt specifies:")
print("  - EXACT loop: for i in range(2, int(n**0.5) + 1)")
print("  - Start: 2")
print("  - End: int(n**0.5) + 1")
print("  - Step: 1 (default)")

print("\n## Compliance Check:")

models_loops = {
    'gpt-4o-mini': 'for i in range(2, int(n**0.5) + 1):',
    'gpt-4o': 'for i in range(5, int(n**0.5) + 1, 6):',
    'claude': 'for i in range(2, int(n**0.5) + 1):'
}

for model, loop in models_loops.items():
    required = 'for i in range(2, int(n**0.5) + 1)'
    compliant = required in loop
    print(f"\n  {model}:")
    print(f"    Loop: {loop}")
    print(f"    {'✅ COMPLIANT' if compliant else '❌ NON-COMPLIANT'}")
    if not compliant:
        print(f"    Reason: Different loop parameters")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

print("\nBased on user's rule:")
print("  'If contract specifies specific algorithmic logic,")
print("   code must adhere to it'")

print("\n✅ gpt-4o-mini: COMPLIANT (uses exact loop)")
print("❌ gpt-4o: NON-COMPLIANT (uses range(5, ..., 6))")
print("✅ Claude: COMPLIANT (uses exact loop)")

print("\n## Action Required:")
print("\ngpt-4o outputs need TRANSFORMATION:")
print("  - Change: for i in range(5, int(n**0.5) + 1, 6)")
print("  - To:     for i in range(2, int(n**0.5) + 1)")
print("  - Remove: 6k±1 optimization logic")
print("  - Remove: Pre-checks for n % 2 and n % 3")

print("\nThis is a SEMANTIC transformation (algorithm change)")
print("Current transformation pipeline CANNOT do this")
print("Need to enhance transformer or accept non-compliance")
