#!/usr/bin/env python3
"""
Transformation: Remove optimization pre-checks that don't fundamentally change the algorithm.

For example, in is_prime:
  - Remove: if n <= 3: return True
  - Remove: if n % 2 == 0 or n % 3 == 0: return False
  
These are performance optimizations that don't change correctness.
The required loop will handle these cases anyway.
"""

import ast
import astor
from typing import Dict, Any, Optional

class OptimizationPreCheckRemover(ast.NodeTransformer):
    """Remove optimization pre-checks that are redundant with main loop logic"""
    
    def __init__(self, contract: Dict[str, Any]):
        self.contract = contract
        self.removed_nodes = []
        
    def visit_FunctionDef(self, node):
        """Process function and remove optimization pre-checks"""
        
        # Only process if this is the target function
        func_name = self.contract.get('constraints', {}).get('function_name')
        if node.name != func_name:
            return node
        
        # Filter out optimization pre-checks
        new_body = []
        for stmt in node.body:
            if self._is_optimization_precheck(stmt):
                self.removed_nodes.append(stmt)
            else:
                new_body.append(self.visit(stmt))
        
        node.body = new_body if new_body else [ast.Pass()]
        return node
    
    def _is_optimization_precheck(self, node) -> bool:
        """Detect if a statement is an optimization pre-check"""
        
        if not isinstance(node, ast.If):
            return False
        
        # Pattern 1: if n <= 3: return True
        # (Early exit for small primes)
        if self._matches_small_prime_check(node):
            return True
        
        # Pattern 2: if n % 2 == 0 or n % 3 == 0: return False
        # (Early exit for even numbers and multiples of 3)
        if self._matches_divisibility_check(node):
            return True
        
        return False
    
    def _matches_small_prime_check(self, node: ast.If) -> bool:
        """Check if this is: if n <= 3: return True"""
        
        # Check condition: n <= 3
        if not isinstance(node.test, ast.Compare):
            return False
        
        if not (isinstance(node.test.left, ast.Name) and 
                node.test.left.id == 'n'):
            return False
        
        if not (len(node.test.ops) == 1 and 
                isinstance(node.test.ops[0], ast.LtE)):
            return False
        
        if not (len(node.test.comparators) == 1 and
                isinstance(node.test.comparators[0], ast.Constant) and
                node.test.comparators[0].value == 3):
            return False
        
        # Check body: return True
        if not (len(node.body) == 1 and
                isinstance(node.body[0], ast.Return)):
            return False
        
        return_val = node.body[0].value
        if not (isinstance(return_val, ast.Constant) and
                return_val.value is True):
            return False
        
        return True
    
    def _matches_divisibility_check(self, node: ast.If) -> bool:
        """Check if this is: if n % 2 == 0 or n % 3 == 0: return False"""
        
        # Check condition: n % 2 == 0 or n % 3 == 0
        if not isinstance(node.test, ast.BoolOp):
            return False
        
        if not isinstance(node.test.op, ast.Or):
            return False
        
        # Should have two comparisons
        if len(node.test.values) != 2:
            return False
        
        # Check both are modulo comparisons
        for val in node.test.values:
            if not isinstance(val, ast.Compare):
                return False
            
            # Should be: n % X == 0
            if not isinstance(val.left, ast.BinOp):
                return False
            
            if not isinstance(val.left.op, ast.Mod):
                return False
        
        # Check body: return False
        if not (len(node.body) == 1 and
                isinstance(node.body[0], ast.Return)):
            return False
        
        return_val = node.body[0].value
        if not (isinstance(return_val, ast.Constant) and
                return_val.value is False):
            return False
        
        return True


def remove_optimization_prechecks(code: str, contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove optimization pre-checks from code.
    
    Args:
        code: Source code to transform
        contract: Contract specification
        
    Returns:
        Dict with transformed code and metadata
    """
    try:
        tree = ast.parse(code)
        
        # Apply transformation
        remover = OptimizationPreCheckRemover(contract)
        new_tree = remover.visit(tree)
        
        # Generate transformed code
        transformed_code = astor.to_source(new_tree)
        
        return {
            'success': True,
            'transformed_code': transformed_code,
            'removed_count': len(remover.removed_nodes),
            'description': f'Removed {len(remover.removed_nodes)} optimization pre-checks'
        }
        
    except Exception as e:
        return {
            'success': False,
            'transformed_code': code,
            'error': str(e),
            'removed_count': 0
        }


if __name__ == "__main__":
    # Test the transformation
    test_code = """def is_prime(n):
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
"""
    
    contract = {
        'constraints': {
            'function_name': 'is_prime'
        }
    }
    
    result = remove_optimization_prechecks(test_code, contract)
    
    print("Original:")
    print(test_code)
    print("\nTransformed:")
    print(result['transformed_code'])
    print(f"\nRemoved {result['removed_count']} optimization pre-checks")
