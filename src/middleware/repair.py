# src/middleware/repair.py
"""
[TODO repair.py]
Goal: bounded, monotone, idempotent repair. No code.

1. Inputs: raw output text, canon, contract, oracle.
2. Steps (in order):
   a) Canonicalize formatting using existing normalization (idempotent).
   b) Enforce contract deltas: exact function name/signature, remove comments, ensure recursion if required, remove extra prints.
   c) Minimal edits only. No semantic rewrites beyond contract compliance.
3. Monotonicity: compute d after each step. Require d_new ≤ d_prev. If violated, revert step and stop.
4. Bounded rescue: stop at MAX_REPAIR_STEPS from config. If not at d=0, mark failure with reason.
5. Output: repaired text or failure, plus a RepairRecord for repairs.csv.
6. Acceptance: when d=0 at entry, no changes are performed.
"""

import ast
import re
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from .schema import RepairRecord, MAX_REPAIR_STEPS
from .distance import compute_signature, compute_distance
from .contract_enforcer import oracle_check

class RepairResult:
    """Result of repair operation"""
    def __init__(self, success: bool, repaired_text: str, steps: int, reason: str):
        self.success = success
        self.repaired_text = repaired_text
        self.steps = steps
        self.reason = reason

def repair_code(raw_output: str, canon_text: str, contract: Dict[str, Any],
                run_id: str, sample_id: str) -> Tuple[RepairResult, RepairRecord]:
    """
    Perform bounded, monotonic, idempotent repair
    
    Args:
        raw_output: Raw LLM output text
        canon_text: Canonical reference text
        contract: Contract specification
        run_id: Run identifier
        sample_id: Sample identifier
    
    Returns:
        Tuple of (RepairResult, RepairRecord for logging)
    """
    # Import here to avoid circular dependency
    from ..normalize import extract_code
    
    # Step 0: Extract and normalize code (idempotent)
    current_text = extract_code(raw_output)
    
    # Compute initial distance and signature
    initial_signature = compute_signature(current_text)
    initial_distance = compute_distance(current_text, canon_text)
    
    # If d=0 at entry, no changes needed (idempotence)
    if initial_distance == 0.0:
        repair_record = RepairRecord(
            run_id=run_id,
            sample_id=sample_id,
            before_signature=initial_signature,
            after_signature=initial_signature,
            d_before=initial_distance,
            d_after=initial_distance,
            steps=0,
            success=True,
            reason="no_repair_needed_d_zero",
            timestamp=datetime.now()
        )
        
        return RepairResult(True, current_text, 0, "no_repair_needed"), repair_record
    
    # Track repair progress
    best_text = current_text
    best_distance = initial_distance
    steps_taken = 0
    
    # Repair steps in order
    repair_steps = [
        ("fix_function_name", _fix_function_name),
        ("remove_comments", _remove_comments),
        ("remove_docstrings", _remove_docstrings),
        ("remove_extra_prints", _remove_extra_prints),
        ("ensure_recursion", _ensure_recursion),
    ]
    
    for step_name, step_func in repair_steps:
        if steps_taken >= MAX_REPAIR_STEPS:
            break
        
        # Apply repair step
        try:
            repaired_text = step_func(best_text, contract)
            
            # Skip if no change
            if repaired_text == best_text:
                continue
            
            # Compute new distance
            new_distance = compute_distance(repaired_text, canon_text)
            
            # Monotonicity check: d_new ≤ d_prev
            if new_distance <= best_distance:
                best_text = repaired_text
                best_distance = new_distance
                steps_taken += 1
                
                # Early exit if perfect match
                if new_distance == 0.0:
                    break
            else:
                # Monotonicity violated, stop repair
                break
        
        except Exception:
            # Step failed, continue with next step
            continue
    
    # Determine success
    final_signature = compute_signature(best_text)
    oracle_pass, oracle_reason = oracle_check(best_text, contract)
    
    success = (best_distance == 0.0) or oracle_pass
    reason = "repair_success" if success else f"repair_incomplete_{oracle_reason}"
    
    # Create repair record
    repair_record = RepairRecord(
        run_id=run_id,
        sample_id=sample_id,
        before_signature=initial_signature,
        after_signature=final_signature,
        d_before=initial_distance,
        d_after=best_distance,
        steps=steps_taken,
        success=success,
        reason=reason,
        timestamp=datetime.now()
    )
    
    return RepairResult(success, best_text, steps_taken, reason), repair_record

def _fix_function_name(code: str, contract: Dict[str, Any]) -> str:
    """
    Fix function name to match contract requirement
    
    Args:
        code: Python code string
        contract: Contract specification
    
    Returns:
        Code with corrected function name
    """
    expected_name = contract.get("enforce_function_name")
    if not expected_name:
        return code
    
    try:
        tree = ast.parse(code)
        
        # Find function definitions and rename them
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name != expected_name:
                # Simple string replacement for function name
                # This is a minimal edit approach
                old_pattern = rf'\bdef\s+{re.escape(node.name)}\s*\('
                new_replacement = f'def {expected_name}('
                code = re.sub(old_pattern, new_replacement, code)
                
                # Also replace function calls within the same code
                call_pattern = rf'\b{re.escape(node.name)}\s*\('
                call_replacement = f'{expected_name}('
                code = re.sub(call_pattern, call_replacement, code)
                
                break  # Only fix first function found
        
        return code
    
    except SyntaxError:
        return code

def _remove_comments(code: str, contract: Dict[str, Any]) -> str:
    """
    Remove line comments from code
    
    Args:
        code: Python code string
        contract: Contract specification (unused)
    
    Returns:
        Code with comments removed
    """
    lines = code.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove inline comments but preserve strings
        in_string = False
        quote_char = None
        result = []
        i = 0
        
        while i < len(line):
            char = line[i]
            
            if not in_string and char == '#':
                # Found comment, truncate line here
                break
            elif char in ['"', "'"]:
                if not in_string:
                    in_string = True
                    quote_char = char
                elif char == quote_char:
                    in_string = False
                    quote_char = None
            
            result.append(char)
            i += 1
        
        cleaned_line = ''.join(result).rstrip()
        cleaned_lines.append(cleaned_line)
    
    return '\n'.join(cleaned_lines)

def _remove_docstrings(code: str, contract: Dict[str, Any]) -> str:
    """
    Remove docstrings from code
    
    Args:
        code: Python code string
        contract: Contract specification (unused)
    
    Returns:
        Code with docstrings removed
    """
    try:
        tree = ast.parse(code)
        
        # Remove module docstring
        if (tree.body and 
            isinstance(tree.body[0], ast.Expr) and 
            isinstance(tree.body[0].value, ast.Constant) and 
            isinstance(tree.body[0].value.value, str)):
            tree.body.pop(0)
        
        # Remove function docstrings
        for node in ast.walk(tree):
            if (isinstance(node, ast.FunctionDef) and 
                node.body and 
                isinstance(node.body[0], ast.Expr) and 
                isinstance(node.body[0].value, ast.Constant) and 
                isinstance(node.body[0].value.value, str)):
                node.body.pop(0)
        
        # Convert back to source code
        import astor
        return astor.to_source(tree)
    
    except (SyntaxError, ImportError):
        # Fallback: simple regex removal
        # Remove triple-quoted strings at start of lines
        code = re.sub(r'^\s*""".*?"""\s*$', '', code, flags=re.MULTILINE | re.DOTALL)
        code = re.sub(r"^\s*'''.*?'''\s*$", '', code, flags=re.MULTILINE | re.DOTALL)
        return code

def _remove_extra_prints(code: str, contract: Dict[str, Any]) -> str:
    """
    Remove top-level print statements
    
    Args:
        code: Python code string
        contract: Contract specification (unused)
    
    Returns:
        Code with top-level prints removed
    """
    try:
        tree = ast.parse(code)
        
        # Remove top-level print calls
        new_body = []
        for node in tree.body:
            if (isinstance(node, ast.Expr) and 
                isinstance(node.value, ast.Call) and 
                isinstance(node.value.func, ast.Name) and 
                node.value.func.id == 'print'):
                continue  # Skip print statements
            else:
                new_body.append(node)
        
        tree.body = new_body
        
        # Convert back to source code
        import astor
        return astor.to_source(tree)
    
    except (SyntaxError, ImportError):
        # Fallback: regex removal
        lines = code.split('\n')
        filtered_lines = []
        
        for line in lines:
            stripped = line.strip()
            if not (stripped.startswith('print(') and stripped.endswith(')')):
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)

def _ensure_recursion(code: str, contract: Dict[str, Any]) -> str:
    """
    Ensure recursion if required by contract
    
    Args:
        code: Python code string
        contract: Contract specification
    
    Returns:
        Code with recursion ensured (minimal change)
    
    Note:
        This is a placeholder. Actual recursion enforcement
        would require sophisticated code analysis and rewriting.
        For now, we only validate that recursion exists.
    """
    if not contract.get("requires_recursion", False):
        return code
    
    function_name = contract.get("enforce_function_name")
    if not function_name:
        return code
    
    # Check if recursion already exists
    from .contract_enforcer import _check_recursion
    if _check_recursion(code, function_name):
        return code
    
    # For minimal repair, we cannot safely add recursion
    # This would require semantic rewriting beyond contract compliance
    # Return unchanged code and let oracle fail
    return code
