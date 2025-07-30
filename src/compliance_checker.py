# src/compliance_checker.py

import ast
import re
from contract import PromptContract

def check_function_name(code_str, expected_name):
    try:
        tree = ast.parse(code_str)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node.name == expected_name
        return False
    except Exception as e:
        return False

def check_output_type(code_str, expected_type):
    # For Python, can check return type annotation if present
    # Advanced: can run the code and inspect the output
    # Here, only check for list in return annotation (simplified)
    try:
        tree = ast.parse(code_str)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.returns and isinstance(node.returns, ast.Name):
                    return node.returns.id.lower() == 'list'
        # If no annotation, fallback: check if 'return [' is present
        return "return [" in code_str
    except Exception:
        return False

def check_no_comments(code_str):
    # Returns True if no Python comments found
    return not bool(re.search(r'^\s*#', code_str, flags=re.MULTILINE))

def check_code_only(code_str):
    # True if code_str contains only code (no explanation text)
    return not bool(re.search(r'^[^\s#]*[a-zA-Z ]+:', code_str, re.MULTILINE))

def check_required_logic(code_str, required_logic):
    if required_logic is None:
        return True
    if required_logic.lower() == "recursion":
        # Simple heuristic: function calls itself
        try:
            tree = ast.parse(code_str)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    fname = node.name
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call) and hasattr(child.func, 'id') and child.func.id == fname:
                            return True
            return False
        except Exception:
            return False
    # Add more logic checks as needed
    return True

def check_constraints(code_str, constraints, contract):
    # Evaluate all relevant constraints
    results = {}
    for constraint in constraints:
        if constraint.lower() == "no comments":
            results["no_comments"] = check_no_comments(code_str)
        if constraint.lower() == "no explanation":
            results["code_only"] = check_code_only(code_str)
        if constraint.lower() == "use recursion":
            results["uses_recursion"] = check_required_logic(code_str, "recursion")
        # Add more as needed
    return results

def check_compliance(code_str, contract: PromptContract):
    # Main entry point: returns dict of contract field compliance
    results = {
        "function_name": check_function_name(code_str, contract.function_name),
        "output_type": check_output_type(code_str, contract.output_type),
    }
    # Constraints
    constraint_results = check_constraints(code_str, contract.constraints, contract)
    results.update(constraint_results)
    return results
