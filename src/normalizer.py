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
    if "No explanation" in [c.lower().capitalize() for c in contract.constraints] or contract.output_format == "code only":
        if not check_code_only(code_str):
            code_str = strip_non_code(code_str)
            corrections.append("Removed non-code/explanation text")
    # Output type
    if not check_output_type(code_str, contract.output_type):
        code_str = enforce_output_type(code_str, contract.output_type)
        corrections.append(f"Attempted to enforce output type '{contract.output_type}'")
    # Add more normalization steps as your contract evolves
    return code_str, corrections

# Additional normalization functions migrated from normalize.py

def normalize_code_output(code: str) -> str:
    """
    Normalize Python code for repeatability checks:
    - Remove markdown code block markers (triple backticks, etc.)
    - Remove docstrings (triple quotes)
    - Remove comments
    - Normalize indentation (convert tabs to spaces)
    - Remove blank lines and strip each line
    """
    if not code:
        return ""
    # Remove markdown code block markers (```python ... ```)
    code = re.sub(r"^```(?:python)?\s*", "", code.strip(), flags=re.MULTILINE)
    code = re.sub(r"```$", "", code, flags=re.MULTILINE)
    # Remove docstrings (triple quotes)
    code = re.sub(r'("""[\s\S]*?"""|\'\'\'\'[\s\S]*?\'\'\')', '', code)
    # Remove comments
    code = re.sub(r'#.*', '', code)
    # Normalize indentation: replace tabs with 4 spaces
    code = code.replace('\t', '    ')
    # Remove blank lines and strip each line
    lines = [line.strip() for line in code.splitlines() if line.strip()]
    normalized = '\n'.join(lines)
    return normalized


def extract_code(output):
    match = re.search(r"```python(.*?)```", output, re.DOTALL)
    return match.group(1).strip() if match else ""

def extract_reflection(output):
    match = re.search(r"\{.*?\}", output, re.DOTALL)
    return match.group(0).strip() if match else ""

def is_code_compliant(code: str, contract=None) -> bool:
    """
    Check if code is compliant with contract requirements.
    If no contract provided, returns True (backward compatibility).
    """
    if not contract:
        return True
    
    # Check if function is defined with correct name
    function_pattern = rf"def\s+{re.escape(contract.function_name)}\s*\("
    defines_function = bool(re.search(function_pattern, code, re.IGNORECASE))
    
    # Check required logic if specified
    uses_required_logic = True
    if contract.required_logic:
        if contract.required_logic.lower() == "recursion":
            # Check if function calls itself recursively
            recursive_call_pattern = rf"{re.escape(contract.function_name)}\s*\("
            uses_required_logic = "return" in code and bool(re.search(recursive_call_pattern, code, re.IGNORECASE))
        # Add more logic types as needed (e.g., "iteration", "list comprehension")
    
    return bool(defines_function and uses_required_logic)

# Dictionary mapping known variants to canonical string
CANONICAL_INTENT_MAP = {
    # Generic patterns for common programming tasks
    re.compile(r".*generate.*function.*", re.IGNORECASE): "generate a function",
    re.compile(r".*write.*function.*", re.IGNORECASE): "write a function",
    re.compile(r".*implement.*function.*", re.IGNORECASE): "implement a function",
    # Add more canonical mappings as needed based on actual contract requirements
}

# Fallback canonicalization for synonyms
SYNONYM_MAP = [
    (re.compile(r"produce|compute|return|implement|create|write", re.IGNORECASE), "generate"),
    (re.compile(r"function to|function that|function which|function for", re.IGNORECASE), ""),
    (re.compile(r"python code to|python code that|python code for", re.IGNORECASE), "python code to"),
]

FILLER_WORDS = [
    r"a ", r"the ", r"to ", r"that ", r"which ", r"for ", r"of ", r"and ", r"with "
]

def normalize_intent(intent: str) -> str:
    if not intent or not isinstance(intent, str):
        return ""
    s = intent.lower().strip()
    # Remove filler words
    for word in FILLER_WORDS:
        s = s.replace(word, " ")
    # Apply synonym replacements
    for pattern, repl in SYNONYM_MAP:
        s = pattern.sub(repl, s)
    # Canonicalize using regex dictionary
    for pattern, canonical in CANONICAL_INTENT_MAP.items():
        if pattern.match(s):
            return canonical
    # Remove extra whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s

def normalize_intents(intents: dict) -> dict:
    """
    Given a dict with 'developer_intent' and 'user_intent' (each a dict with a 'goal' field),
    normalize both to a canonical string and return a new dict with 'normalized_developer_intent' and 'normalized_user_intent'.
    """
    result = intents.copy()
    if 'developer_intent' in intents and 'goal' in intents['developer_intent']:
        result['normalized_developer_intent'] = normalize_intent(intents['developer_intent']['goal'])
    if 'user_intent' in intents and 'goal' in intents['user_intent']:
        result['normalized_user_intent'] = normalize_intent(intents['user_intent']['goal'])
    return result

# Import compliance checks
from compliance_checker import (
    check_function_name, check_no_comments, check_code_only, check_output_type
)
