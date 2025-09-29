#!/usr/bin/env python3
"""
Test script for behavioral transformations
"""

import sys
sys.path.append('src')

from transformations.behavioral.algorithm_optimizer import AlgorithmOptimizer
from transformations.behavioral.boundary_condition_aligner import BoundaryConditionAligner
from transformations.transformation_pipeline import TransformationPipeline


def test_algorithm_optimizer():
    """Test algorithm optimization (variable naming)"""
    
    print("=== TESTING ALGORITHM OPTIMIZER ===")
    
    # Canonical code (target) - uses a, b variables
    canon_code = '''def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b'''
    
    # Code with different variable names - uses fib1, fib2
    problem_code = '''def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    fib1, fib2 = 0, 1
    for _ in range(2, n + 1):
        fib1, fib2 = fib2, fib1 + fib2
    return fib2'''
    
    transformer = AlgorithmOptimizer()
    transformer.enable_debug()
    
    print("Canon code:")
    print(canon_code)
    print("\nProblem code:")
    print(problem_code)
    
    # Test transformation
    result = transformer.transform(problem_code, canon_code)
    
    print(f"\nTransformation success: {result.success}")
    print(f"Transformed code:\n{result.transformed_code}")
    
    if result.success:
        # Check if variables were renamed correctly
        if 'fib1' not in result.transformed_code and 'fib2' not in result.transformed_code:
            if 'a, b' in result.transformed_code:
                print("✅ ALGORITHM OPTIMIZER WORKS! Variables renamed correctly.")
                return True
        
    print(f"❌ Algorithm optimizer failed: {result.error_message}")
    return False


def test_boundary_condition_aligner():
    """Test boundary condition alignment"""
    
    print("\n=== TESTING BOUNDARY CONDITION ALIGNER ===")
    
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
    
    # Code with different boundary conditions
    problem_code = '''def fibonacci(n):
    if n < 1:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b'''
    
    transformer = BoundaryConditionAligner()
    transformer.enable_debug()
    
    print("Canon code:")
    print(canon_code)
    print("\nProblem code:")
    print(problem_code)
    
    # Test transformation
    result = transformer.transform(problem_code, canon_code)
    
    print(f"\nTransformation success: {result.success}")
    print(f"Transformed code:\n{result.transformed_code}")
    
    if result.success:
        # Check if boundary condition was aligned
        if 'if n <= 0:' in result.transformed_code and 'if n < 1:' not in result.transformed_code:
            print("✅ BOUNDARY CONDITION ALIGNER WORKS! Condition aligned correctly.")
            return True
        
    print(f"❌ Boundary condition aligner failed: {result.error_message}")
    return False


def test_full_behavioral_pipeline():
    """Test complete behavioral transformation pipeline"""
    
    print("\n=== TESTING FULL BEHAVIORAL PIPELINE ===")
    
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
    
    # Complex code with multiple behavioral issues
    complex_problem_code = '''def fibonacci(n):
    if n < 1:
        return 0
    elif n == 1:
        return 1
    fib1, fib2 = 0, 1
    for i in range(2, n + 1):
        fib1, fib2 = fib2, fib1 + fib2
    return fib2'''
    
    # Test pipeline with only behavioral transformations
    pipeline = TransformationPipeline(debug_mode=True)
    
    # Remove structural transformations for this test
    pipeline.transformations = [
        AlgorithmOptimizer(),
        BoundaryConditionAligner(),
    ]
    
    for t in pipeline.transformations:
        t.enable_debug()
    
    result = pipeline.transform_code(complex_problem_code, canon_code)
    
    print(f"\nPipeline Results:")
    print(f"Transformation success: {result['transformation_success']}")
    print(f"Successful transformations: {result['successful_transformations']}")
    print(f"Final code:\n{result['final_code']}")
    
    # Check if both behavioral issues were fixed
    final_code = result['final_code']
    variables_fixed = 'fib1' not in final_code and 'fib2' not in final_code and 'a, b' in final_code
    boundary_fixed = 'if n <= 0:' in final_code and 'if n < 1:' not in final_code
    
    if variables_fixed and boundary_fixed:
        print("✅ FULL BEHAVIORAL PIPELINE WORKS!")
        return True
    else:
        print(f"❌ Behavioral pipeline incomplete:")
        print(f"  Variables fixed: {variables_fixed}")
        print(f"  Boundary fixed: {boundary_fixed}")
        return False


if __name__ == "__main__":
    print("🧠 Testing Behavioral Transformation System")
    print("=" * 50)
    
    # Run all tests
    test1 = test_algorithm_optimizer()
    test2 = test_boundary_condition_aligner()
    test3 = test_full_behavioral_pipeline()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 BEHAVIORAL TEST SUMMARY:")
    print(f"Algorithm Optimizer: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Boundary Condition Aligner: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Full Behavioral Pipeline: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 All behavioral tests PASSED! System handles algorithmic variations!")
    else:
        print("\n⚠️  Some behavioral tests FAILED. Check output for details.")
