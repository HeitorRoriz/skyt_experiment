#!/usr/bin/env python3
"""
Simple test of the modular transformation system
"""

import sys
import os
sys.path.append('src')

# Test the individual transformations directly
def test_error_handling_direct():
    """Test error handling transformation directly"""
    
    print("=== DIRECT ERROR HANDLING TEST ===")
    
    from transformations.structural.error_handling_aligner import ErrorHandlingAligner
    
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
    
    # Problematic code (input)
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
    
    transformer = ErrorHandlingAligner()
    transformer.enable_debug()
    
    print("Canon code:")
    print(canon_code)
    print("\nProblem code:")
    print(problem_code)
    
    # Test can_transform
    can_transform = transformer.can_transform(problem_code, canon_code)
    print(f"\nCan transform: {can_transform}")
    
    if can_transform:
        # Test transformation
        result = transformer.transform(problem_code, canon_code)
        print(f"\nTransformation success: {result.success}")
        print(f"Transformed code:\n{result.transformed_code}")
        
        if result.success:
            print("✅ ERROR HANDLING TRANSFORMATION WORKS!")
            return True
        else:
            print(f"❌ Transformation failed: {result.error_message}")
            return False
    else:
        print("❌ Cannot transform this code")
        return False

if __name__ == "__main__":
    print("🧪 Simple Modular Transformation Test")
    print("=" * 40)
    
    success = test_error_handling_direct()
    
    if success:
        print("\n🎉 Modular transformation system is working!")
    else:
        print("\n⚠️ Modular transformation system needs debugging")
