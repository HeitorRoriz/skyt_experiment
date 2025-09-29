#!/usr/bin/env python3
"""
Test script for the new modular transformation system
"""

import sys
sys.path.append('src')

from transformations.transformation_pipeline import TransformationPipeline
from transformations.structural.error_handling_aligner import ErrorHandlingAligner
from transformations.structural.redundant_clause_remover import RedundantClauseRemover


def test_error_handling_transformation():
    """Test error handling alignment"""
    
    print("=== TESTING ERROR HANDLING ALIGNMENT ===")
    
    # Canonical code (target)
    canon_code = '''def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b'''
    
    # Problematic code (input) - should have distance ~0.288
    problem_code = '''def fibonacci(n):
    if n < 0:
        raise ValueError("Input must be a non-negative integer.")
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b'''
    
    # Test individual transformer
    transformer = ErrorHandlingAligner()
    transformer.enable_debug()
    
    result = transformer.transform(problem_code, canon_code)
    
    print(f"Transformation success: {result.success}")
    print(f"Original code:\n{result.original_code}")
    print(f"Transformed code:\n{result.transformed_code}")
    
    if result.success:
        print("✅ Error handling transformation PASSED")
    else:
        print(f"❌ Error handling transformation FAILED: {result.error_message}")
    
    return result.success


def test_redundant_else_removal():
    """Test redundant else clause removal"""
    
    print("\n=== TESTING REDUNDANT ELSE REMOVAL ===")
    
    # Canonical code (no else)
    canon_code = '''def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b'''
    
    # Code with redundant else - should have distance ~0.160
    problem_code = '''def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b'''
    
    # Test individual transformer
    transformer = RedundantClauseRemover()
    transformer.enable_debug()
    
    result = transformer.transform(problem_code, canon_code)
    
    print(f"Transformation success: {result.success}")
    print(f"Original code:\n{result.original_code}")
    print(f"Transformed code:\n{result.transformed_code}")
    
    if result.success and 'else:' not in result.transformed_code:
        print("✅ Redundant else removal PASSED")
        return True
    else:
        print(f"❌ Redundant else removal FAILED: {result.error_message}")
        return False


def test_full_pipeline():
    """Test the complete transformation pipeline"""
    
    print("\n=== TESTING FULL TRANSFORMATION PIPELINE ===")
    
    # Canonical code
    canon_code = '''def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b'''
    
    # Complex problematic code with multiple issues
    complex_problem_code = '''def fibonacci(n):
    if n < 0:
        raise ValueError("Input should be a non-negative integer")
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b'''
    
    # Test pipeline
    pipeline = TransformationPipeline(debug_mode=True)
    
    result = pipeline.transform_code(complex_problem_code, canon_code)
    
    print(f"\nPipeline Results:")
    print(f"Transformation success: {result['transformation_success']}")
    print(f"Successful transformations: {result['successful_transformations']}")
    print(f"Iterations used: {result['iterations_used']}")
    print(f"Final code:\n{result['final_code']}")
    
    # Check if both issues were fixed
    final_code = result['final_code']
    error_handling_fixed = 'raise ValueError' not in final_code and 'if n <= 0:' in final_code
    redundant_else_fixed = 'else:' not in final_code
    
    if error_handling_fixed and redundant_else_fixed:
        print("✅ Full pipeline transformation PASSED")
        return True
    else:
        print(f"❌ Full pipeline transformation FAILED")
        print(f"  Error handling fixed: {error_handling_fixed}")
        print(f"  Redundant else fixed: {redundant_else_fixed}")
        return False


if __name__ == "__main__":
    print("🚀 Testing Modular Transformation System")
    print("=" * 50)
    
    # Run all tests
    test1 = test_error_handling_transformation()
    test2 = test_redundant_else_removal()
    test3 = test_full_pipeline()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY:")
    print(f"Error Handling Alignment: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Redundant Else Removal: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Full Pipeline: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 All tests PASSED! Modular transformation system is working!")
    else:
        print("\n⚠️  Some tests FAILED. Check the output above for details.")
