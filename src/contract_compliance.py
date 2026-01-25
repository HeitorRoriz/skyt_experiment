"""
Contract Compliance Checker
Validates code against contract rules (MISRA C, NASA P10, etc.)
"""

import ast
from typing import Dict, Any, List, Tuple


def check_contract_compliance(code: str, contract: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if code complies with contract rules (MISRA C, NASA P10, forbidden/required patterns)
    
    Args:
        code: The code to check
        contract: Contract data with constraints
        
    Returns:
        Tuple of (is_compliant, list_of_violations)
    """
    violations = []
    constraints = contract.get('constraints', {})
    
    # Check forbidden patterns (string-based)
    forbidden = constraints.get('forbidden_patterns', [])
    for pattern in forbidden:
        if pattern in code:
            violations.append(f"Forbidden pattern: '{pattern}'")
    
    # Check required patterns (string-based)
    required = constraints.get('required_patterns', [])
    for pattern in required:
        if pattern not in code:
            violations.append(f"Missing required pattern: '{pattern}'")
    
    # Check MISRA C rules
    misra_rules = constraints.get('misra_c_rules', {})
    if misra_rules:
        misra_violations = _check_misra_rules(code, misra_rules)
        violations.extend(misra_violations)
    
    # Check NASA P10 rules
    nasa_rules = constraints.get('nasa_power_of_10', {})
    if nasa_rules:
        nasa_violations = _check_nasa_p10_rules(code, nasa_rules)
        violations.extend(nasa_violations)
    
    is_compliant = len(violations) == 0
    return is_compliant, violations


def _check_misra_rules(code: str, rules: Dict[str, str]) -> List[str]:
    """Check MISRA C rules"""
    violations = []
    
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ["Code has syntax errors"]
    
    # MISRA 15.5: Single exit point
    if 'rule_15_5' in rules:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
                if len(returns) > 1:
                    violations.append("MISRA 15.5: Multiple return statements (should have single exit point)")
                # Check for early returns (return not at end of function)
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.If):
                        for child in stmt.body:
                            if isinstance(child, ast.Return):
                                violations.append("MISRA 15.5: Early return inside conditional")
                                break
    
    # MISRA 15.4: No break/continue
    if 'rule_15_4' in rules:
        for node in ast.walk(tree):
            if isinstance(node, ast.Break):
                violations.append("MISRA 15.4: break statement not allowed")
            if isinstance(node, ast.Continue):
                violations.append("MISRA 15.4: continue statement not allowed")
    
    # MISRA 17.2: No recursion
    if 'rule_17_2' in rules:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                for call in ast.walk(node):
                    if isinstance(call, ast.Call):
                        if isinstance(call.func, ast.Name) and call.func.id == func_name:
                            violations.append(f"MISRA 17.2: Recursive call to {func_name}")
    
    # MISRA 21.3: No dynamic memory (stdlib imports)
    if 'rule_21_3' in rules:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'collections':
                        violations.append("MISRA 21.3: collections import not allowed")
            if isinstance(node, ast.ImportFrom):
                if node.module and 'collections' in node.module:
                    violations.append("MISRA 21.3: collections import not allowed")
    
    return violations


def _check_nasa_p10_rules(code: str, rules: Dict[str, str]) -> List[str]:
    """Check NASA Power of 10 rules"""
    violations = []
    
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ["Code has syntax errors"]
    
    # P10-1: No recursion (same as MISRA 17.2)
    if 'p10_1' in rules:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                for call in ast.walk(node):
                    if isinstance(call, ast.Call):
                        if isinstance(call.func, ast.Name) and call.func.id == func_name:
                            violations.append(f"NASA P10-1: Recursive call to {func_name}")
    
    # P10-3: No dynamic memory imports
    if 'p10_3' in rules:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'collections':
                        violations.append("NASA P10-3: collections import not allowed")
            if isinstance(node, ast.ImportFrom):
                if node.module and 'collections' in node.module:
                    violations.append("NASA P10-3: collections import not allowed")
    
    return violations


def make_compliant(code: str, contract: Dict[str, Any]) -> str:
    """
    Transform code to be compliant with contract rules.
    Uses SingleExitTransformer and BreakRemover in the right order.
    
    Args:
        code: Code to transform
        contract: Contract with rules
        
    Returns:
        Transformed compliant code
    """
    from .transformations.structural.single_exit_transformer import SingleExitTransformer
    from .transformations.structural.break_remover import BreakRemover
    
    current_code = code
    
    # Apply SingleExitTransformer FIRST - it handles multiple returns and adds flag if needed
    # This creates the proper structure for loop termination
    single_exit = SingleExitTransformer()
    if single_exit.can_transform(current_code, ""):
        result = single_exit.transform(current_code, "")
        if result.success:
            current_code = result.transformed_code
    
    # Apply BreakRemover SECOND - removes any remaining break/continue statements
    # By this point, the flag variable structure is already in place if needed
    break_remover = BreakRemover()
    if break_remover.can_transform(current_code, ""):
        result = break_remover.transform(current_code, "")
        if result.success:
            current_code = result.transformed_code
    
    return current_code
