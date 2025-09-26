# src/middleware/contract_enforcer.py
"""
[TODO contract_enforcer.py]
Goal: single oracle entry point. No code.

1. oracle_check(output_text, contract) -> (bool pass, str reason).
2. Encapsulate rules used by normalize and current contract prompt:
   - Function name and signature exact.
   - No comments or docstrings.
   - Recursion required when specified.
   - Output only code, no fences.
3. Version this oracle. Expose ORACLE_VERSION const for logs.
4. Acceptance: identical text always yields same pass/fail. No nondeterminism.
"""

import ast
import re
from typing import Dict, Any, Tuple
from .schema import ORACLE_VERSION

def oracle_check(output_text: str, contract: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Single oracle entry point for contract compliance checking
    
    Args:
        output_text: Normalized Python code string
        contract: Contract specification dict
    
    Returns:
        Tuple of (pass: bool, reason: str)
    
    Note:
        This function MUST be deterministic. Identical inputs
        always produce identical pass/fail results.
    """
    reasons = []
    
    # Check 1: Function name and signature exact
    function_name = contract.get("enforce_function_name")
    if function_name:
        if not _check_function_name(output_text, function_name):
            reasons.append(f"missing_function_{function_name}")
    
    # Check 2: No comments or docstrings (should be stripped by normalization)
    if _has_comments_or_docstrings(output_text):
        reasons.append("contains_comments_or_docstrings")
    
    # Check 3: Recursion required when specified
    if contract.get("requires_recursion", False):
        if not _check_recursion(output_text, function_name):
            reasons.append("missing_required_recursion")
    
    # Check 4: Output only code, no fences (should be stripped by normalization)
    if _has_markdown_fences(output_text):
        reasons.append("contains_markdown_fences")
    
    # Check 5: Valid Python syntax
    if not _check_valid_syntax(output_text):
        reasons.append("invalid_python_syntax")
    
    # Check 6: Function signature matches if specified
    expected_signature = contract.get("signature")
    if expected_signature and function_name:
        if not _check_function_signature(output_text, function_name, expected_signature):
            reasons.append(f"incorrect_signature_{function_name}")
    
    # Overall pass/fail
    oracle_pass = len(reasons) == 0
    reason = "; ".join(reasons) if reasons else "oracle_pass"
    
    return oracle_pass, reason

def _check_function_name(code: str, expected_name: str) -> bool:
    """
    Check if code contains function with expected name
    
    Args:
        code: Python code string
        expected_name: Expected function name
    
    Returns:
        True if function exists with exact name
    """
    try:
        tree = ast.parse(code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == expected_name:
                return True
        
        return False
    
    except SyntaxError:
        return False

def _check_function_signature(code: str, function_name: str, expected_signature: str) -> bool:
    """
    Check if function signature matches expected signature
    
    Args:
        code: Python code string
        function_name: Function name to check
        expected_signature: Expected signature pattern
    
    Returns:
        True if signature matches
    """
    try:
        tree = ast.parse(code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                # Extract actual signature
                args = [arg.arg for arg in node.args.args]
                actual_sig = f"{function_name}({', '.join(args)})"
                
                # Simple string comparison for now
                # TODO: More sophisticated signature matching
                return actual_sig == expected_signature
        
        return False
    
    except SyntaxError:
        return False

def _check_recursion(code: str, function_name: str) -> bool:
    """
    Check if function uses recursion (calls itself)
    
    Args:
        code: Python code string
        function_name: Function name to check for recursion
    
    Returns:
        True if function calls itself
    """
    if not function_name:
        return False
    
    try:
        tree = ast.parse(code)
        
        # Find the function definition
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                # Check if function calls itself
                for child in ast.walk(node):
                    if (isinstance(child, ast.Call) and 
                        isinstance(child.func, ast.Name) and 
                        child.func.id == function_name):
                        return True
        
        return False
    
    except SyntaxError:
        return False

def _has_comments_or_docstrings(code: str) -> bool:
    """
    Check if code contains comments or docstrings
    
    Args:
        code: Python code string
    
    Returns:
        True if comments or docstrings found
    """
    # Check for line comments
    if re.search(r'#.*', code):
        return True
    
    # Check for docstrings using AST
    try:
        tree = ast.parse(code)
        
        for node in ast.walk(tree):
            # Module docstring
            if (isinstance(node, ast.Module) and 
                node.body and 
                isinstance(node.body[0], ast.Expr) and 
                isinstance(node.body[0].value, ast.Constant) and 
                isinstance(node.body[0].value.value, str)):
                return True
            
            # Function docstring
            if (isinstance(node, ast.FunctionDef) and 
                node.body and 
                isinstance(node.body[0], ast.Expr) and 
                isinstance(node.body[0].value, ast.Constant) and 
                isinstance(node.body[0].value.value, str)):
                return True
        
        return False
    
    except SyntaxError:
        return False

def _has_markdown_fences(code: str) -> bool:
    """
    Check if code contains markdown fences
    
    Args:
        code: Code string
    
    Returns:
        True if markdown fences found
    """
    fence_patterns = [
        r'```python',
        r'```',
        r'~~~python',
        r'~~~'
    ]
    
    for pattern in fence_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return True
    
    return False

def _check_valid_syntax(code: str) -> bool:
    """
    Check if code has valid Python syntax
    
    Args:
        code: Python code string
    
    Returns:
        True if syntax is valid
    """
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False
