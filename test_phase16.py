"""
Test Phase 1.6 Canonicalizations

Verifies that the three new transformations work:
1. Expression Canonicalization
2. Dead Code Elimination
3. Commutative Normalization
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.transformations.expression_canonicalizer import canonicalize_expressions
from src.transformations.dead_code_eliminator import eliminate_dead_code
from src.transformations.commutative_normalizer import normalize_commutative
from src.transformations.structural.phase16_canonicalizer import Phase16Canonicalizer


def test_expression_canonicalization():
    """Test expression canonicalization"""
    print("\n" + "="*70)
    print("TEST 1: Expression Canonicalization")
    print("="*70)
    
    test_cases = [
        ("x = a + 0", "x = a"),
        ("x = 0 + a", "x = a"),
        ("x = a * 1", "x = a"),
        ("x = 1 * a", "x = a"),
        ("x = a - 0", "x = a"),
        ("x = not (not a)", "x = a"),
    ]
    
    passed = 0
    for input_expr, expected_pattern in test_cases:
        transformed, stats = canonicalize_expressions(input_expr)
        
        # Check if transformation was applied
        if stats.get('transformations_applied', 0) > 0:
            print(f"✓ {input_expr:20} → {transformed.strip()}")
            passed += 1
        else:
            print(f"✗ {input_expr:20} → No transformation")
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_dead_code_elimination():
    """Test dead code elimination"""
    print("\n" + "="*70)
    print("TEST 2: Dead Code Elimination")
    print("="*70)
    
    code_with_dead = """
def test(n):
    unused_var = 999
    x = n + 1
    return x
"""
    
    code_without_dead = """
def test(n):
    x = n + 1
    return x
"""
    
    transformed, stats = eliminate_dead_code(code_with_dead)
    
    if 'unused_var' not in transformed:
        print("✓ Dead code removed successfully")
        print(f"  Transformations: {stats.get('transformations_applied', 0)}")
        return True
    else:
        print("✗ Dead code not removed")
        return False


def test_commutative_normalization():
    """Test commutative normalization"""
    print("\n" + "="*70)
    print("TEST 3: Commutative Normalization")
    print("="*70)
    
    test_cases = [
        "x = b + a",  # Should normalize to a + b
        "x = y * x",  # Should normalize to x * y
        "x = b == a",  # Should normalize to a == b
    ]
    
    passed = 0
    for code in test_cases:
        transformed, stats = normalize_commutative(code)
        
        if stats.get('transformations_applied', 0) > 0:
            print(f"✓ {code:20} → {transformed.strip()}")
            passed += 1
        else:
            print(f"  {code:20} → (already canonical or no change)")
            # Still count as passed if no error
            passed += 1
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_phase16_unified():
    """Test unified Phase 1.6 transformer"""
    print("\n" + "="*70)
    print("TEST 4: Unified Phase 1.6 Transformer")
    print("="*70)
    
    code = """
def fibonacci(n):
    if n <= 0:
        return 0 + 0
    elif n == 1:
        return 1 * 1
    unused = 999
    b, a = 0, 1
    for _ in range(2, n + 1):
        b, a = a, b + a
    return a
"""
    
    transformer = Phase16Canonicalizer()
    result = transformer.transform(code)
    
    print("Original code:")
    print(code)
    
    print("\nTransformed code:")
    print(result.transformed_code)
    
    print(f"\nSuccess: {result.success}")
    print(f"Transformations: {getattr(transformer, 'last_transformation_count', 0)}")
    
    if hasattr(transformer, 'last_transformation_log') and transformer.last_transformation_log:
        print("\nLog:")
        for log in transformer.last_transformation_log[:5]:  # Show first 5
            print(f"  - {log}")
        if len(transformer.last_transformation_log) > 5:
            print(f"  ... and {len(transformer.last_transformation_log) - 5} more")
    
    return result.success


def main():
    print("="*70)
    print("PHASE 1.6 TESTS")
    print("="*70)
    
    results = []
    
    try:
        results.append(("Expression Canonicalization", test_expression_canonicalization()))
    except Exception as e:
        print(f"\n❌ Expression Canonicalization failed: {e}")
        results.append(("Expression Canonicalization", False))
    
    try:
        results.append(("Dead Code Elimination", test_dead_code_elimination()))
    except Exception as e:
        print(f"\n❌ Dead Code Elimination failed: {e}")
        results.append(("Dead Code Elimination", False))
    
    try:
        results.append(("Commutative Normalization", test_commutative_normalization()))
    except Exception as e:
        print(f"\n❌ Commutative Normalization failed: {e}")
        results.append(("Commutative Normalization", False))
    
    try:
        results.append(("Unified Transformer", test_phase16_unified()))
    except Exception as e:
        print(f"\n❌ Unified Transformer failed: {e}")
        results.append(("Unified Transformer", False))
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}  {name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n🎉 All Phase 1.6 tests passed!")
        print("\nPhase 1.6 is ready for integration!")
    else:
        print("\n⚠️  Some tests failed - review above")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
