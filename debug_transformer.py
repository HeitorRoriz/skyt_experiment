#!/usr/bin/env python3
"""
Debug script to test SKYT transformation issues
"""

import ast
import sys
sys.path.append('src')

from code_transformer import CodeTransformer
from canon_system import CanonSystem

def test_error_handling_transformation():
    """Test error handling alignment transformation"""
    
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
    
    print("=== DEBUGGING ERROR HANDLING TRANSFORMATION ===")
    print(f"Canon code:\n{canon_code}\n")
    print(f"Problem code:\n{problem_code}\n")
    
    # Test AST parsing
    try:
        canon_tree = ast.parse(canon_code)
        problem_tree = ast.parse(problem_code)
        print("✅ AST parsing successful")
    except Exception as e:
        print(f"❌ AST parsing failed: {e}")
        return
    
    # Test pattern extraction
    try:
        transformer = CodeTransformer(CanonSystem("outputs"))
        patterns = transformer._extract_error_patterns(canon_tree)
        print(f"✅ Canon patterns extracted: {patterns}")
    except Exception as e:
        print(f"❌ Pattern extraction failed: {e}")
        return
    
    # Test transformation
    try:
        params = {"contract_id": "fibonacci_basic"}
        result = transformer._align_error_handling(problem_code, params)
        print(f"✅ Transformation result:\n{result}")
        
        if result == problem_code:
            print("⚠️  WARNING: No transformation applied (returned original)")
        else:
            print("✅ Transformation applied successfully")
            
    except Exception as e:
        print(f"❌ Transformation failed: {e}")
        import traceback
        traceback.print_exc()

def test_redundant_else_transformation():
    """Test redundant else clause removal"""
    
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
    
    print("\n=== DEBUGGING REDUNDANT ELSE TRANSFORMATION ===")
    print(f"Problem code:\n{problem_code}\n")
    
    try:
        transformer = CodeTransformer(CanonSystem("outputs"))
        params = {"contract_id": "fibonacci_basic"}
        result = transformer._remove_redundant_clauses(problem_code, params)
        print(f"✅ Transformation result:\n{result}")
        
        if "else:" in result:
            print("⚠️  WARNING: Redundant else clause not removed")
        else:
            print("✅ Redundant else clause removed successfully")
            
    except Exception as e:
        print(f"❌ Transformation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_error_handling_transformation()
    test_redundant_else_transformation()
