#!/usr/bin/env python3
"""
Analyze the impact of removing MISRA C Rule 15.5 (single exit point / no break)
from strict contracts.
"""

import json

def analyze_impact():
    """Analyze what changes if we remove Rule 15.5"""
    
    print("="*80)
    print("IMPACT ANALYSIS: REMOVING MISRA C RULE 15.5")
    print("="*80)
    
    print("\n## What Rule 15.5 Enforces:")
    print("- Single exit point (one return at end)")
    print("- No break or continue statements")
    print("- Forces use of flag variables (found, done, etc.)")
    
    print("\n## Current Strict Contracts:")
    contracts = ["is_prime_strict", "binary_search_strict", "lru_cache_strict"]
    
    for contract in contracts:
        print(f"\n### {contract}:")
        
        if contract == "is_prime_strict":
            print("  Current requirements:")
            print("    - result = True initially")
            print("    - result = False if divisor found")
            print("    - No break (must check all divisors)")
            print("    - Single return at end")
            print("\n  WITHOUT Rule 15.5:")
            print("    ✅ Can use: return False when divisor found")
            print("    ✅ Can use: break to exit loop early")
            print("    ✅ No need for flag variables")
            print("    ✅ More natural/efficient code")
            
        elif contract == "binary_search_strict":
            print("  Current requirements:")
            print("    - found = False flag variable")
            print("    - while left <= right and not found")
            print("    - found = True when target found")
            print("    - Single return at end")
            print("\n  WITHOUT Rule 15.5:")
            print("    ✅ Can use: return mid when target found")
            print("    ✅ Can use: break to exit loop")
            print("    ✅ No need for found flag")
            print("    ✅ Simpler loop condition: while left <= right")
            
        elif contract == "lru_cache_strict":
            print("  Current requirements:")
            print("    - Single return per method (get/put)")
            print("    - result variable for get method")
            print("    - No early returns")
            print("\n  WITHOUT Rule 15.5:")
            print("    ✅ Can use: return value directly")
            print("    ✅ Can use: early returns for edge cases")
            print("    ✅ No need for result variable")
    
    print("\n" + "="*80)
    print("TRANSFORMATION IMPACT")
    print("="*80)
    
    print("\n## Current Problem:")
    print("- Canon created from transformed code (with flag)")
    print("- Raw outputs don't have flag")
    print("- Transformation can't add semantic features (flags)")
    print("- Result: 92.3% transformation failure for Claude/gpt-4o")
    
    print("\n## After Removing Rule 15.5:")
    print("✅ Models generate natural code (break/return)")
    print("✅ Canon created from natural code (no flag)")
    print("✅ Transformations can succeed (no semantic gap)")
    print("✅ Metrics become meaningful")
    
    print("\n" + "="*80)
    print("EXPERIMENT VALIDITY")
    print("="*80)
    
    print("\n## What We Keep:")
    print("✅ MISRA C Rule 15.4: No continue (still enforced)")
    print("✅ MISRA C Rule 17.2: No recursion (still enforced)")
    print("✅ MISRA C Rule 14.2: Loop counter not modified (still enforced)")
    print("✅ NASA P10-2: Bounded loops (still enforced)")
    print("✅ NASA P10-6: Result variable usage (still enforced)")
    print("✅ Variable naming constraints (still enforced)")
    
    print("\n## What We Lose:")
    print("❌ Single exit point enforcement")
    print("❌ No break statement enforcement")
    
    print("\n## Experiment Still Valid?")
    print("✅ YES - We still test:")
    print("   - Contract compliance (other rules)")
    print("   - Transformation capability")
    print("   - Repeatability improvement")
    print("   - Model differences")
    print("\n✅ Contracts are still 'strict' with:")
    print("   - Bounded loops")
    print("   - No recursion")
    print("   - Fixed variable names")
    print("   - No continue statements")
    
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    print("\n✅ REMOVE Rule 15.5 (single exit / no break)")
    print("\nReasons:")
    print("1. Makes transformation feasible (no semantic gap)")
    print("2. Allows natural code patterns (break/return)")
    print("3. Maintains other strict requirements")
    print("4. Experiment remains valid and meaningful")
    print("5. Metrics will reflect actual transformation capability")
    
    print("\n⚠️  Alternative: Keep Rule 15.5 but document limitation")
    print("   - Accept 90%+ transformation failure")
    print("   - Note that semantic transformations not supported")
    print("   - Focus on models that naturally comply (gpt-4o-mini)")
    
    print("\n" + "="*80)
    print("IMPLEMENTATION CHANGES NEEDED")
    print("="*80)
    
    print("\n1. Update contract prompts:")
    print("   - Remove 'no break' requirement")
    print("   - Remove 'single return' requirement")
    print("   - Allow natural loop exit strategies")
    
    print("\n2. Update contract constraints:")
    print("   - Remove rule_15_5 from misra_c_rules")
    print("   - Remove 'break' from forbidden_patterns")
    print("   - Remove 'return True/False' from forbidden_patterns")
    
    print("\n3. Update contract compliance checker:")
    print("   - Remove checks for single exit point")
    print("   - Remove checks for break statements")
    
    print("\n4. Re-run experiments:")
    print("   - Delete old canons")
    print("   - Re-run all 56 strict contract experiments")
    print("   - Expect much higher transformation success rates")

if __name__ == "__main__":
    analyze_impact()
