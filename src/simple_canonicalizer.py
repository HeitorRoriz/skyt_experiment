# src/simple_canonicalizer.py
"""
Simplified Canonicalizer for SKYT Experiment
Basic structural normalization: strips comments, normalizes whitespace, enforces function names
"""

import ast
import re
from typing import Optional


def canonicalize_code(code: str, expected_function_name: str = "fibonacci") -> str:
    """
    Apply basic canonicalization transformations:
    1. Strip comments and docstrings
    2. Normalize whitespace and indentation
    3. Enforce expected function name
    4. AST round-trip for consistent formatting
    
    Args:
        code: Raw Python code string
        expected_function_name: Expected function name to enforce
    
    Returns:
        Canonicalized code string
    """
    if not code or not code.strip():
        return ""
    
    try:
        # Step 1: Parse AST to validate syntax
        tree = ast.parse(code)
        
        # Step 2: Apply transformations
        tree = _strip_docstrings(tree)
        tree = _enforce_function_name(tree, expected_function_name)
        
        # Step 3: Generate canonical code via AST round-trip
        canonical_code = ast.unparse(tree)
        
        # Step 4: Final cleanup
        canonical_code = _normalize_whitespace(canonical_code)
        
        return canonical_code
        
    except (SyntaxError, ValueError) as e:
        # If canonicalization fails, return cleaned raw code
        return _fallback_cleanup(code)


def _strip_docstrings(tree: ast.AST) -> ast.AST:
    """Remove docstrings from AST nodes"""
    class DocstringRemover(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            # Remove docstring if present (first statement is a string)
            if (node.body and 
                isinstance(node.body[0], ast.Expr) and 
                isinstance(node.body[0].value, ast.Constant) and 
                isinstance(node.body[0].value.value, str)):
                node.body = node.body[1:]
            
            return self.generic_visit(node)
        
        def visit_ClassDef(self, node):
            # Remove class docstrings
            if (node.body and 
                isinstance(node.body[0], ast.Expr) and 
                isinstance(node.body[0].value, ast.Constant) and 
                isinstance(node.body[0].value.value, str)):
                node.body = node.body[1:]
            
            return self.generic_visit(node)
    
    return DocstringRemover().visit(tree)


def _enforce_function_name(tree: ast.AST, expected_name: str) -> ast.AST:
    """Enforce consistent function naming"""
    class FunctionRenamer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            # Rename main function to expected name
            if node.name in ['fib', 'fibonacci', 'fibo', 'fibonacci_sequence']:
                node.name = expected_name
            return self.generic_visit(node)
    
    return FunctionRenamer().visit(tree)


def _normalize_whitespace(code: str) -> str:
    """Normalize whitespace and remove empty lines"""
    lines = code.split('\n')
    normalized_lines = []
    
    for line in lines:
        # Strip trailing whitespace but preserve indentation
        stripped = line.rstrip()
        if stripped:  # Skip empty lines
            normalized_lines.append(stripped)
    
    return '\n'.join(normalized_lines)


def _fallback_cleanup(code: str) -> str:
    """Fallback cleanup when AST parsing fails"""
    # Remove comments
    lines = code.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove inline comments (simple approach)
        if '#' in line:
            line = line[:line.index('#')]
        
        # Strip whitespace and skip empty lines
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def get_canonical_signature(code: str, expected_function_name: str = "fibonacci") -> str:
    """
    Generate a canonical signature hash for the code
    
    Args:
        code: Python code string
        expected_function_name: Expected function name
    
    Returns:
        SHA-256 hash of canonicalized code (first 16 chars)
    """
    import hashlib
    
    canonical_code = canonicalize_code(code, expected_function_name)
    return hashlib.sha256(canonical_code.encode('utf-8')).hexdigest()[:16]


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_codes = [
        '''
def fibonacci(n):
    """Calculate fibonacci number"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)  # Recursive approach
        ''',
        '''
def fib(n):
    # Base cases
    if n <= 1:
        return n
    # Recursive case
    return fib(n-1) + fib(n-2)
        ''',
        '''
def fibonacci_sequence(n):
    if n <= 1:
        return n
    else:
        return fibonacci_sequence(n-1) + fibonacci_sequence(n-2)
        '''
    ]
    
    print("Canonicalization Test:")
    print("=" * 50)
    
    for i, code in enumerate(test_codes, 1):
        canonical = canonicalize_code(code)
        signature = get_canonical_signature(code)
        
        print(f"\nTest {i}:")
        print(f"Signature: {signature}")
        print("Canonical form:")
        print(canonical)
        print("-" * 30)
