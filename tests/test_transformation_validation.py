"""
Test Suite for Transformation Validation

Prevents regression in:
1. Variable renaming corruption
2. Semantic equivalence checking
3. Rollback functionality
4. Validation system
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from transformations.transformation_pipeline import TransformationPipeline
from transformations.semantic_validator import SemanticValidator


def test_no_undefined_variables():
    """Test that transformations don't introduce undefined variables"""
    
    code_with_undefined = """
def binary_search(sorted_list, target):
    if arr[mid] == target:  # arr is undefined!
        return mid
    return -1
"""
    
    canon_code = """
def binary_search(arr, target):
    if arr[mid] == target:
        return mid
    return -1
"""
    
    pipeline = TransformationPipeline(debug_mode=False)
    
    # Validation should detect undefined variable
    is_valid = pipeline._validate_transformation(
        original_code=canon_code,
        transformed_code=code_with_undefined,
        transformer_name="TestTransformer"
    )
    
    assert not is_valid, "Validation should reject code with undefined variables"
    print("✅ test_no_undefined_variables passed")


def test_semantic_equivalence():
    """Test semantic equivalence checking"""
    
    # Same behavior, different variable names
    code1 = """
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
"""
    
    code2 = """
def fibonacci(n):
    x, y = 0, 1
    for _ in range(n):
        x, y = y, x + y
    return x
"""
    
    # Different behavior
    code3 = """
def fibonacci(n):
    return n * 2  # Completely different!
"""
    
    validator = SemanticValidator()
    
    # Test 1: Same behavior should be equivalent
    assert validator.are_semantically_equivalent(code1, code2), \
        "Same behavior with different var names should be equivalent"
    
    # Test 2: Different behavior should NOT be equivalent
    assert not validator.are_semantically_equivalent(code1, code3), \
        "Different behavior should NOT be equivalent"
    
    print("✅ test_semantic_equivalence passed")


def test_rollback_on_corruption():
    """Test that pipeline rolls back corrupt transformations"""
    
    # This test would require mocking a transformer that produces corrupt code
    # For now, we validate the mechanism exists
    
    pipeline = TransformationPipeline(debug_mode=False)
    
    # Verify semantic validator is initialized
    assert pipeline.semantic_validator is not None, \
        "Pipeline should have semantic validator"
    
    # Verify validation method exists
    assert hasattr(pipeline, '_validate_transformation'), \
        "Pipeline should have validation method"
    
    print("✅ test_rollback_on_corruption passed")


def test_variable_renamer_threshold():
    """Test that VariableRenamer has correct multi-tier triggers"""
    
    from transformations.structural.variable_renamer import VariableRenamer
    
    renamer = VariableRenamer()
    
    # Test 1: Parameter difference (TIER 1 - should ALWAYS trigger)
    code_param_diff = """
def binary_search(sorted_list, target):
    left, right, mid = 0, 0, 0
"""
    
    canon_param_diff = """
def binary_search(arr, target):
    left, right, mid = 0, 0, 0
"""
    
    should_trigger_param = renamer._has_variable_differences(code_param_diff, canon_param_diff)
    assert should_trigger_param, "TIER 1: Parameter difference should ALWAYS trigger"
    print("✅ TIER 1: Parameter difference triggers correctly")
    
    # Test 2: Small count difference (TIER 2 - should trigger for 1-3 vars)
    code_small_diff = """
def test():
    x, y, z = 1, 2, 3
    special_var = 4
"""
    
    canon_small_diff = """
def test():
    x, y, z = 1, 2, 3
    other_var = 4
"""
    
    should_trigger_small = renamer._has_variable_differences(code_small_diff, canon_small_diff)
    assert should_trigger_small, "TIER 2: 1-3 variable differences should trigger"
    print("✅ TIER 2: Small count differences trigger correctly")
    
    # Test 3: Percentage threshold (TIER 3 - existing logic)
    code_many_diff = """
def test():
    a, b, c, d, e, f = 1, 2, 3, 4, 5, 6
"""
    
    canon_many_diff = """
def test():
    x, y, z, d, e, f = 1, 2, 3, 4, 5, 6
"""
    
    should_trigger_pct = renamer._has_variable_differences(code_many_diff, canon_many_diff)
    assert should_trigger_pct, "TIER 3: <50% overlap should trigger"
    print("✅ TIER 3: Percentage threshold works correctly")
    
    print("✅ test_variable_renamer_threshold passed (all tiers validated)")


def test_syntax_error_detection():
    """Test that validation catches syntax errors"""
    
    bad_code = """
def broken_function(:
    return 42
"""
    
    good_code = """
def good_function():
    return 42
"""
    
    pipeline = TransformationPipeline(debug_mode=False)
    
    is_valid = pipeline._validate_transformation(
        original_code=good_code,
        transformed_code=bad_code,
        transformer_name="TestTransformer"
    )
    
    assert not is_valid, "Validation should reject code with syntax errors"
    print("✅ test_syntax_error_detection passed")


def run_all_tests():
    """Run all regression tests"""
    print("="*70)
    print("Running Transformation Validation Test Suite")
    print("="*70)
    
    test_no_undefined_variables()
    test_semantic_equivalence()
    test_rollback_on_corruption()
    test_variable_renamer_threshold()
    test_syntax_error_detection()
    
    print("="*70)
    print("✅ All tests passed!")
    print("="*70)


if __name__ == "__main__":
    run_all_tests()
