# src/compliance.py
"""
Contract compliance checking for SKYT pipeline
Validates code against contract specifications
"""

import ast
from typing import Dict, Any, Optional, List


def check_contract_compliance(code: str, contract: Dict[str, Any], canon: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check code compliance against contract specifications
    
    Args:
        code: Raw Python code string
        contract: Contract specification dict
        canon: Canonicalization result from canon.apply_canon()
    
    Returns:
        Dict with canonicalization_ok, structural_ok, oracle_pass, contract_pass, reasons
    """
    reasons = []
    
    # Extract canonicalization status
    canonicalization_ok = canon.get("structural_ok", False)
    if not canonicalization_ok:
        reasons.append(f"canonicalization_failed: {canon.get('notes', 'unknown')}")
    
    # Perform structural checks
    structural_checks = _check_structural_requirements(code, contract)
    structural_ok = structural_checks["ok"]
    if not structural_ok:
        reasons.extend(structural_checks["errors"])
    
    # Oracle check (stub for now)
    oracle_pass = True
    oracle_msg = "oracle_not_implemented"
    
    # Overall contract pass
    contract_pass = canonicalization_ok and structural_ok and oracle_pass
    
    return {
        "canonicalization_ok": canonicalization_ok,
        "structural_ok": structural_ok,
        "oracle_pass": oracle_pass,
        "contract_pass": contract_pass,
        "reasons": reasons,
        "oracle_msg": oracle_msg
    }


def _check_structural_requirements(code: str, contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check structural requirements from contract
    
    Args:
        code: Python code string
        contract: Contract specification
    
    Returns:
        Dict with ok status and list of errors
    """
    errors = []
    
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"ok": False, "errors": [f"syntax_error: {str(e)}"]}
    
    # Check required function name
    required_function = contract.get("function_name")
    if required_function:
        if not _has_function(tree, required_function):
            errors.append(f"missing_required_function: {required_function}")
    
    # Check recursion requirement
    if contract.get("requires_recursion", False):
        if required_function and not _is_recursive(tree, required_function):
            errors.append(f"recursion_required_but_missing: {required_function}")
    
    # Check language constraint
    language = contract.get("language", "python")
    if language.lower() != "python":
        errors.append(f"unsupported_language: {language}")
    
    # Check function signature if specified
    expected_signature = contract.get("signature")
    if expected_signature and required_function:
        actual_signature = _get_function_signature(tree, required_function)
        if actual_signature != expected_signature:
            errors.append(f"signature_mismatch: expected {expected_signature}, got {actual_signature}")
    
    return {"ok": len(errors) == 0, "errors": errors}


def _has_function(tree: ast.AST, function_name: str) -> bool:
    """Check if AST contains a function with the given name"""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return True
    return False


def _is_recursive(tree: ast.AST, function_name: str) -> bool:
    """Check if function calls itself (simple recursion detection)"""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            # Look for calls to the same function within the function body
            for child in ast.walk(node):
                if (isinstance(child, ast.Call) and 
                    isinstance(child.func, ast.Name) and 
                    child.func.id == function_name):
                    return True
    return False


def _get_function_signature(tree: ast.AST, function_name: str) -> Optional[str]:
    """Extract function signature as string"""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            args = [arg.arg for arg in node.args.args]
            return f"{function_name}({', '.join(args)})"
    return None
