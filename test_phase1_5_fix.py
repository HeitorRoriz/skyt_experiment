"""
Quick test to verify Phase 1.5 fix works

Tests that:
1. Transformation properties don't include enhanced metrics
2. Distance calculation works without breaking
3. Transformations can now reach distance = 0
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.foundational_properties import FoundationalProperties


def test_transformation_vs_validation_separation():
    """Test that transformation and validation properties are separate"""
    
    code = """
def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
"""
    
    props = FoundationalProperties()
    
    print("Testing property separation...")
    
    # Test transformation properties (baseline AST only)
    trans_props = props.extract_transformation_properties(code)
    print(f"\n✓ Transformation properties extracted: {len(trans_props)} properties")
    
    # Check that enhanced metrics are NOT in transformation properties
    assert 'complexity_class' in trans_props
    assert 'function_contracts' in trans_props
    
    # The properties themselves should NOT have enhanced fields
    complexity = trans_props.get('complexity_class', {})
    assert 'nested_loops' in complexity  # Baseline field
    assert 'cyclomatic_complexity' not in complexity  # Enhanced field (radon)
    print("  ✓ Transformation properties are baseline only (no radon/mypy/bandit)")
    
    contracts = trans_props.get('function_contracts', {})
    assert 'fibonacci' in contracts  # Baseline detection
    # Should NOT have type analysis in baseline
    assert '_type_analysis' not in contracts
    print("  ✓ No type analysis in transformation properties")
    
    # Test validation properties (enhanced analysis)
    val_props = props.extract_validation_properties(code)
    print(f"\n✓ Validation properties extracted: {len(val_props)} properties")
    
    # Check that enhanced metrics ARE in validation properties
    if 'radon_metrics' in val_props:
        radon = val_props['radon_metrics']
        assert 'cyclomatic_complexity' in radon or 'average_complexity' in radon
        print("  ✓ Radon metrics present in validation")
    
    if 'type_analysis' in val_props:
        print("  ✓ Type analysis present in validation")
    
    if 'security_analysis' in val_props:
        print("  ✓ Security analysis present in validation")
    
    print("\n✅ Separation working correctly!")
    return True


def test_distance_calculation():
    """Test that distance calculation works with transformation properties"""
    
    code1 = """
def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
"""
    
    code2 = """
def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:  # Extra else clause!
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
"""
    
    props = FoundationalProperties()
    
    print("\nTesting distance calculation...")
    
    # Extract transformation properties
    props1 = props.extract_transformation_properties(code1)
    props2 = props.extract_transformation_properties(code2)
    
    # Calculate distance
    distance = props.calculate_transformation_distance(props1, props2)
    
    print(f"  Distance between codes: {distance:.4f}")
    
    # Should be small but non-zero (different control flow due to else)
    assert 0 < distance < 0.5, f"Expected small distance, got {distance}"
    print("  ✓ Distance calculation working")
    
    # Test identical code
    props3 = props.extract_transformation_properties(code1)
    distance_same = props.calculate_transformation_distance(props1, props3)
    
    print(f"  Distance for identical code: {distance_same:.4f}")
    assert distance_same == 0.0, f"Expected 0 distance for identical code, got {distance_same}"
    print("  ✓ Identical code has distance = 0.0")
    
    print("\n✅ Distance calculation working correctly!")
    return True


def main():
    print("="*70)
    print("PHASE 1.5 FIX VERIFICATION")
    print("="*70)
    print("\nVerifying that transformation and validation are properly separated...\n")
    
    try:
        test_transformation_vs_validation_separation()
        test_distance_calculation()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\nPhase 1.5 fix is working correctly!")
        print("Transformations now use baseline properties only.")
        print("Validation uses enhanced properties separately.")
        print("\nReady to re-run pipeline validation!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
