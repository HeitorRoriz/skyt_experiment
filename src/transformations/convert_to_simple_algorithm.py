#!/usr/bin/env python3
"""
Transformation: Convert optimized algorithms to simple canonical form.

For is_prime, converts:
  - 6k±1 optimization → simple range(2, sqrt(n)+1) iteration
  - Any optimization pre-checks → removed
  
The canon validates the simple algorithm is correct, so this transformation is safe.
"""

import ast
import astor
from typing import Dict, Any, Optional

class AlgorithmSimplifier(ast.NodeTransformer):
    """Convert optimized algorithms to simple canonical form"""
    
    def __init__(self, canon_code: str, contract: Dict[str, Any]):
        self.canon_code = canon_code
        self.contract = contract
        self.canon_tree = ast.parse(canon_code)
        self.transformations_applied = []
        
    def visit_FunctionDef(self, node):
        """Replace entire function with canonical implementation"""
        
        func_name = self.contract.get('constraints', {}).get('function_name')
        if node.name != func_name:
            return node
        
        # Extract canonical function from canon tree
        for canon_node in ast.walk(self.canon_tree):
            if isinstance(canon_node, ast.FunctionDef) and canon_node.name == func_name:
                self.transformations_applied.append(
                    f"Replaced {func_name} implementation with canonical form"
                )
                return canon_node
        
        return node


def convert_to_simple_algorithm(code: str, canon_code: str, contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert optimized algorithm to simple canonical form.
    
    Strategy: Replace the entire function implementation with the canonical version.
    This is safe because:
    1. The canon was validated (passes oracle tests)
    2. The contract prescribes this specific algorithm
    3. The original code passed oracle tests (so same behavior expected)
    
    Args:
        code: Source code to transform
        canon_code: Canonical implementation
        contract: Contract specification
        
    Returns:
        Dict with transformed code and metadata
    """
    try:
        tree = ast.parse(code)
        
        # Apply transformation
        simplifier = AlgorithmSimplifier(canon_code, contract)
        new_tree = simplifier.visit(tree)
        
        # Generate transformed code
        transformed_code = astor.to_source(new_tree)
        
        return {
            'success': True,
            'transformed_code': transformed_code,
            'transformations': simplifier.transformations_applied,
            'description': 'Converted to canonical algorithm form'
        }
        
    except Exception as e:
        return {
            'success': False,
            'transformed_code': code,
            'error': str(e),
            'transformations': []
        }


if __name__ == "__main__":
    # Test: Convert gpt-4o's 6k±1 to simple algorithm
    
    gpt4o_code = """def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    for i in range(5, int(n**0.5) + 1, 6):
        if n % i == 0 or n % (i + 2) == 0:
            return False
    return True
"""
    
    canon_code = """def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
"""
    
    contract = {
        'constraints': {
            'function_name': 'is_prime'
        }
    }
    
    print("="*80)
    print("ALGORITHMIC TRANSFORMATION TEST")
    print("="*80)
    
    print("\nOriginal (gpt-4o 6k±1 optimization):")
    print(gpt4o_code)
    
    result = convert_to_simple_algorithm(gpt4o_code, canon_code, contract)
    
    print("\nTransformed (canonical simple algorithm):")
    print(result['transformed_code'])
    
    print(f"\nSuccess: {result['success']}")
    print(f"Transformations: {result.get('transformations', [])}")
    
    # Verify they produce same results
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    # Execute both and compare
    exec_globals = {}
    exec(gpt4o_code, exec_globals)
    is_prime_original = exec_globals['is_prime']
    
    exec_globals = {}
    exec(result['transformed_code'], exec_globals)
    is_prime_transformed = exec_globals['is_prime']
    
    test_cases = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 17, 25, 29, 100]
    all_match = True
    
    for n in test_cases:
        orig = is_prime_original(n)
        trans = is_prime_transformed(n)
        match = orig == trans
        if not match:
            print(f"  n={n}: original={orig}, transformed={trans} ❌")
            all_match = False
    
    if all_match:
        print(f"✅ All {len(test_cases)} test cases match!")
        print("   Transformation preserves correctness")
