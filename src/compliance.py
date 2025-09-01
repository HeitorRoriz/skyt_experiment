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
    
    # Oracle check - contract-driven oracle
    oracle_result = _run_contract_oracle(code, contract)
    oracle_pass = oracle_result["pass"]
    oracle_msg = oracle_result["message"]
    
    # Overall contract pass
    contract_pass = canonicalization_ok and structural_ok and oracle_pass
    
    # Generate stable effect signature
    effect_signature = _generate_effect_signature(code, contract)
    
    return {
        "canonicalization_ok": canonicalization_ok,
        "structural_ok": structural_ok,
        "oracle_pass": oracle_pass,
        "contract_pass": contract_pass,
        "reasons": reasons,
        "oracle_msg": oracle_msg,
        "effect_signature": effect_signature
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


def _generate_effect_signature(code: str, contract: Dict[str, Any]) -> str:
    """
    Generate stable effect signature from code analysis
    
    Args:
        code: Python code string
        contract: Contract specification
    
    Returns:
        Stable effect signature string
    """
    effects = []
    
    try:
        tree = ast.parse(code)
        
        # Check for I/O operations
        if _has_io_operations(tree):
            effects.append("io_operations")
        
        # Check for random/non-deterministic operations
        if _has_random_operations(tree):
            effects.append("random_ops")
        
        # Check for time-dependent operations
        if _has_time_operations(tree):
            effects.append("time_ops")
        
        # Check for system/OS operations
        if _has_system_operations(tree):
            effects.append("system_ops")
        
        # Check for global state modifications
        if _has_global_modifications(tree):
            effects.append("global_mods")
            
    except (SyntaxError, ValueError):
        effects.append("parse_error")
    
    return "|".join(sorted(effects)) if effects else "pure_function"


def _has_io_operations(tree: ast.AST) -> bool:
    """Check for I/O operations in AST"""
    io_functions = {'print', 'input', 'open', 'read', 'write', 'readline', 'readlines'}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in io_functions:
                return True
    return False


def _has_random_operations(tree: ast.AST) -> bool:
    """Check for random/non-deterministic operations"""
    random_patterns = {'random', 'randint', 'choice', 'shuffle', 'uuid', 'hash'}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in random_patterns:
                return True
            elif isinstance(node.func, ast.Attribute) and node.func.attr in random_patterns:
                return True
    return False


def _has_time_operations(tree: ast.AST) -> bool:
    """Check for time-dependent operations"""
    time_patterns = {'time', 'datetime', 'now', 'today', 'sleep'}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in time_patterns:
                return True
            elif isinstance(node.func, ast.Attribute) and node.func.attr in time_patterns:
                return True
    return False


def _has_system_operations(tree: ast.AST) -> bool:
    """Check for system/OS operations"""
    system_patterns = {'os', 'sys', 'subprocess', 'platform', 'environ'}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in system_patterns:
                return True
            elif isinstance(node.func, ast.Attribute) and node.func.attr in system_patterns:
                return True
    return False


def _has_global_modifications(tree: ast.AST) -> bool:
    """Check for global state modifications"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Global):
            return True
        elif isinstance(node, ast.Nonlocal):
            return True
    return False


def _run_contract_oracle(code: str, contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run contract-driven oracle tests
    
    Args:
        code: Python code string
        contract: Contract specification
    
    Returns:
        Dict with pass status and message
    """
    oracle_examples = contract.get("oracle_examples")
    if not oracle_examples:
        return {"pass": True, "message": "no_oracle_examples"}
    
    function_name = contract.get("function_name")
    if not function_name:
        return {"pass": False, "message": "oracle_requires_function_name"}
    
    try:
        # Execute code in isolated namespace
        namespace = {}
        exec(code, namespace)
        
        if function_name not in namespace:
            return {"pass": False, "message": f"function_{function_name}_not_found"}
        
        func = namespace[function_name]
        
        # Run oracle examples
        for i, example in enumerate(oracle_examples):
            inputs = example.get("input", [])
            expected = example.get("output")
            
            try:
                if isinstance(inputs, list):
                    actual = func(*inputs)
                else:
                    actual = func(inputs)
                
                if actual != expected:
                    return {
                        "pass": False, 
                        "message": f"oracle_fail_example_{i}: expected {expected}, got {actual}"
                    }
                    
            except Exception as e:
                return {
                    "pass": False,
                    "message": f"oracle_error_example_{i}: {str(e)}"
                }
        
        return {"pass": True, "message": f"oracle_pass_{len(oracle_examples)}_examples"}
        
    except Exception as e:
        return {"pass": False, "message": f"oracle_exec_error: {str(e)}"}
