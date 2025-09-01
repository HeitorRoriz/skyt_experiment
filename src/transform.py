# src/transform.py
"""
Code transformation and prompt building for SKYT pipeline
Handles LLM prompt generation and code repair attempts
"""

import ast
from typing import Dict, Any, Optional, List


def build_llm_prompt_for_code(contract: Dict[str, Any], dev_intent: Optional[str] = None, user_intent: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Build LLM prompt messages from contract and intents
    
    Args:
        contract: Contract specification dict
        dev_intent: Developer implementation intent
        user_intent: User behavioral intent
    
    Returns:
        List of message dicts for LLM API
    """
    system_message = compose_system_message(contract)
    
    # Build user prompt from contract
    user_prompt = contract.get("prompt", "")
    
    # Enhance with intents if provided
    if dev_intent:
        user_prompt += f"\n\nImplementation approach: {dev_intent}"
    
    if user_intent:
        user_prompt += f"\n\nExpected behavior: {user_intent}"
    
    # Add contract constraints
    constraints = []
    if contract.get("function_name"):
        constraints.append(f"Function must be named '{contract['function_name']}'")
    
    if contract.get("requires_recursion"):
        constraints.append("Implementation must use recursion")
    
    if contract.get("language"):
        constraints.append(f"Use {contract['language']} language")
    
    if constraints:
        user_prompt += f"\n\nConstraints:\n" + "\n".join(f"- {c}" for c in constraints)
    
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt}
    ]


def compose_system_message(contract: Dict[str, Any]) -> str:
    """
    Compose system message for LLM based on contract
    
    Args:
        contract: Contract specification
    
    Returns:
        System message string
    """
    base_message = "You are a helpful programming assistant. Generate clean, working Python code that meets the specified requirements."
    
    # Add contract-specific instructions
    if contract.get("requires_recursion"):
        base_message += " Use recursive implementation where specified."
    
    if contract.get("function_name"):
        base_message += f" Ensure the main function is named '{contract['function_name']}'."
    
    base_message += " Provide only the code without additional explanation unless requested."
    
    return base_message


def try_repair(code: str, contract: Dict[str, Any]) -> Optional[str]:
    """
    Attempt to repair code to meet contract requirements using safe, deterministic micro-fixes
    
    Args:
        code: Python code string that failed compliance
        contract: Contract specification
    
    Returns:
        Repaired code string or None if repair not possible
    """
    import ast
    from .canon import emit_ast_stable
    
    try:
        tree = ast.parse(code)
        repaired = False
        
        # Repair 1: Rename function to required name
        required_function = contract.get("function_name")
        if required_function:
            tree, renamed = _repair_function_name(tree, required_function)
            repaired = repaired or renamed
        
        # Repair 2: Normalize function signature
        expected_signature = contract.get("signature")
        if expected_signature and required_function:
            tree, sig_fixed = _repair_function_signature(tree, required_function, expected_signature)
            repaired = repaired or sig_fixed
        
        # Repair 3: Strip top-level prints for pure functions
        if _is_pure_function_contract(contract):
            tree, prints_removed = _repair_remove_prints(tree)
            repaired = repaired or prints_removed
        
        if repaired:
            return emit_ast_stable(tree)
        
    except (SyntaxError, ValueError):
        # Cannot repair invalid syntax
        pass
    
    return None


def _repair_function_name(tree: ast.AST, required_name: str) -> tuple[ast.AST, bool]:
    """Repair function name to match contract requirement"""
    repaired = False
    
    class FunctionNameRepairer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            nonlocal repaired
            # Look for common function name patterns that should be renamed
            if node.name in ['fib', 'fibonacci', 'fibo', 'fibonacci_sequence', 'main', 'solution']:
                node.name = required_name
                repaired = True
            return self.generic_visit(node)
    
    repairer = FunctionNameRepairer()
    tree = repairer.visit(tree)
    return tree, repaired


def _repair_function_signature(tree: ast.AST, function_name: str, expected_sig: str) -> tuple[ast.AST, bool]:
    """Repair function signature to match expected form"""
    # Parse expected signature to extract parameter names
    try:
        # Simple signature parsing: "func_name(param1, param2)"
        if '(' in expected_sig and ')' in expected_sig:
            params_part = expected_sig.split('(')[1].split(')')[0]
            expected_params = [p.strip() for p in params_part.split(',') if p.strip()]
        else:
            return tree, False
    except:
        return tree, False
    
    repaired = False
    
    class SignatureRepairer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            nonlocal repaired
            if node.name == function_name:
                current_params = [arg.arg for arg in node.args.args]
                if len(current_params) == len(expected_params):
                    # Rename parameters to match expected names
                    for i, expected_param in enumerate(expected_params):
                        if i < len(node.args.args):
                            node.args.args[i].arg = expected_param
                            repaired = True
            return self.generic_visit(node)
    
    repairer = SignatureRepairer()
    tree = repairer.visit(tree)
    return tree, repaired


def _repair_remove_prints(tree: ast.AST) -> tuple[ast.AST, bool]:
    """Remove top-level print statements for pure functions"""
    repaired = False
    
    class PrintRemover(ast.NodeTransformer):
        def visit_Module(self, node):
            nonlocal repaired
            new_body = []
            
            for stmt in node.body:
                # Remove top-level print calls
                if (isinstance(stmt, ast.Expr) and 
                    isinstance(stmt.value, ast.Call) and
                    isinstance(stmt.value.func, ast.Name) and
                    stmt.value.func.id == 'print'):
                    repaired = True
                    continue  # Skip this statement
                else:
                    new_body.append(stmt)
            
            node.body = new_body
            return self.generic_visit(node)
    
    remover = PrintRemover()
    tree = remover.visit(tree)
    return tree, repaired


def _is_pure_function_contract(contract: Dict[str, Any]) -> bool:
    """Check if contract implies a pure function (no side effects)"""
    # Heuristic: if no explicit I/O requirements and has function_name, assume pure
    return (contract.get("function_name") and 
            not contract.get("requires_io", False) and
            not contract.get("requires_print", False))
