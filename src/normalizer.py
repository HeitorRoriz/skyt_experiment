# src/normalizer.py

import ast
import re
from contract import PromptContract

def rename_function(code_str, expected_name):
    try:
        tree = ast.parse(code_str)
        class Renamer(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                node.name = expected_name
                return node
        new_tree = Renamer().visit(tree)
        new_code = ast.unparse(new_tree) if hasattr(ast, "unparse") else code_str  # Fallback for old Python
        return new_code
    except Exception:
        return code_str  # Fail gracefully

def remove_comments(code_str):
    return "\n".join(
        line for line in code_str.split('\n') if not re.match(r'^\s*#', line)
    )

def strip_non_code(code_str):
    # Remove lines that are not code (simple: no letters + no def/class/import/return)
    code_lines = []
    for line in code_str.split('\n'):
        if line.strip().startswith("#"):
            continue
        # Allow lines that look like Python code
        if (re.match(r'^\s*(def |class |import |return |for |if |else|elif|while|print\()', line) or
            re.match(r'^\s*\w+\s*=', line)):
            code_lines.append(line)
        elif line.strip() == '':
            code_lines.append(line)
    return "\n".join(code_lines)

def enforce_output_type(code_str, output_type):
    # Not easily fixable; log as unable if no type annotation
    # Advanced: can add return annotation if missing (Python 3.9+)
    # Here: just return as-is
    return code_str

def normalize_code(code_str, contract: PromptContract):
    """
    Try to normalize code_str to match the contract.
    Returns (normalized_code, list_of_corrections_made)
    """
    corrections = []
    # Function name
    if not check_function_name(code_str, contract.function_name):
        code_str = rename_function(code_str, contract.function_name)
        corrections.append(f"Renamed function to '{contract.function_name}'")
    # Remove comments
    if "No comments" in [c.lower().capitalize() for c in contract.constraints]:
        if not check_no_comments(code_str):
            code_str = remove_comments(code_str)
            corrections.append("Removed comments")
    # Strip explanations
    if "No ex
