#!/usr/bin/env python3
"""
Analyze if Claude's pre-checks fundamentally change the algorithm or are just optimizations.
"""

def is_prime_simple(n):
    """Simple algorithm - as prescribed by contract"""
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def is_prime_claude(n):
    """Claude's version with pre-checks"""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

print("="*80)
print("ANALYZING CLAUDE'S PRE-CHECKS")
print("="*80)

print("\n## Claude's additions:")
print("  1. if n <= 3: return True")
print("  2. if n % 2 == 0 or n % 3 == 0: return False")

print("\n## Do these change the algorithm fundamentally?")

print("\n### Pre-check 1: if n <= 3: return True")
print("  - Handles: n=2 (prime), n=3 (prime)")
print("  - Effect: Early exit for small primes")
print("  - Algorithmic impact: NONE - just optimization")
print("  - The loop would give the same result")

print("\n### Pre-check 2: if n % 2 == 0 or n % 3 == 0: return False")
print("  - Handles: even numbers and multiples of 3")
print("  - Effect: Early exit for obvious composites")
print("  - Algorithmic impact: NONE - just optimization")
print("  - The loop would find these divisors anyway")

print("\n" + "="*80)
print("VERIFICATION: Do they give same results?")
print("="*80)

test_cases = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 17, 25, 29, 100]

all_match = True
for n in test_cases:
    simple = is_prime_simple(n)
    claude = is_prime_claude(n)
    match = simple == claude
    if not match:
        all_match = False
        print(f"  n={n}: simple={simple}, claude={claude} ❌ MISMATCH")

if all_match:
    print(f"\n✅ ALL {len(test_cases)} test cases match!")
    print("   Claude's pre-checks don't change the results")

print("\n" + "="*80)
print("ANALYSIS")
print("="*80)

print("\nClaude's pre-checks are:")
print("  ✅ Mathematically correct")
print("  ✅ Don't change the output")
print("  ✅ Just performance optimizations")
print("  ✅ The required loop is still present")

print("\n## Can we remove them to match the contract?")

print("\nYES! We can remove:")
print("  - if n <= 3: return True")
print("  - if n % 2 == 0 or n % 3 == 0: return False")

print("\nResult after removal:")
print("  def is_prime(n):")
print("      if n <= 1:")
print("          return False")
print("      for i in range(2, int(n**0.5) + 1):")
print("          if n % i == 0:")
print("              return False")
print("      return True")

print("\nThis would:")
print("  ✅ Match the contract exactly")
print("  ✅ Still pass all oracle tests")
print("  ✅ Not break the contract")
print("  ✅ Not fundamentally change the algorithm")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

print("\n✅ Claude's pre-checks CAN be removed safely")
print("\nThey are:")
print("  - Performance optimizations only")
print("  - Don't change correctness")
print("  - Don't affect the core algorithm")

print("\n## Transformation needed:")
print("  Remove lines: if n <= 3 and if n % 2/3 checks")
print("  Keep: Everything else")
print("  Result: Contract-compliant code")

print("\n## This is a SIMPLE transformation:")
print("  - Remove specific lines")
print("  - No algorithmic restructuring needed")
print("  - Current transformer COULD do this")

print("\n" + "="*80)
print("USER'S RULE INTERPRETATION")
print("="*80)

print("\nUser said: 'We can remove/add lines as long as we don't:'")
print("  a) Break the contract")
print("  b) Change the algorithm fundamentally")
print("  c) Fail oracle tests")

print("\nFor Claude's pre-checks:")
print("  a) ✅ Removing them doesn't break contract")
print("  b) ✅ Doesn't change algorithm fundamentally")
print("  c) ✅ Still passes all oracle tests")

print("\n✅ VERDICT: Claude's code CAN be transformed to match contract")
print("   by removing the optimization pre-checks")
