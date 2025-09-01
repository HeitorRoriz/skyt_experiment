# src/canon.py
"""
Canonicalization module for SKYT pipeline
Handles code normalization with configurable policies
"""

import ast
import re
import hashlib
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CanonPolicy:
    """Canonicalization policy configuration"""
    strip_fences: bool = True
    strip_docstrings: bool = True
    strip_comments: bool = True
    normalize_ws: bool = True
    format_black: bool = False  # Future: black formatting
    sort_imports: bool = False  # Future: import sorting
    ident_normalize: bool = True  # Normalize function names


def apply_canon(code: str, policy: CanonPolicy) -> Dict[str, Any]:
    """
    Apply canonicalization transformations to code
    
    Args:
        code: Raw Python code string
        policy: Canonicalization policy
    
    Returns:
        Dict with canon_code, signature, structural_ok, notes
    """
    if not code or not code.strip():
        return {
            "canon_code": "",
            "signature": "",
            "structural_ok": False,
            "notes": "Empty input code"
        }
    
    notes = []
    
    try:
        # Step 1: Strip fences if enabled
        if policy.strip_fences:
            code = _strip_code_fences(code)
            notes.append("stripped_fences")
        
        # Step 2: Parse AST to validate syntax
        tree = ast.parse(code)
        
        # Step 3: Apply AST transformations
        if policy.strip_docstrings:
            tree = _strip_docstrings(tree)
            notes.append("stripped_docstrings")
        
        if policy.ident_normalize:
            tree = _normalize_function_names(tree)
            notes.append("normalized_identifiers")
        
        # Step 4: Generate canonical code
        canon_code = ast.unparse(tree)
        
        # Step 5: Apply text-level transformations
        if policy.strip_comments:
            canon_code = _strip_comments(canon_code)
            notes.append("stripped_comments")
        
        if policy.normalize_ws:
            canon_code = _normalize_whitespace(canon_code)
            notes.append("normalized_whitespace")
        
        # Generate signature
        signature = canon_hash(canon_code, policy)
        
        return {
            "canon_code": canon_code,
            "signature": signature,
            "structural_ok": True,
            "notes": "; ".join(notes)
        }
        
    except (SyntaxError, ValueError) as e:
        # Fallback cleanup for invalid syntax
        fallback_code = _fallback_cleanup(code, policy)
        return {
            "canon_code": fallback_code,
            "signature": canon_hash(fallback_code, policy),
            "structural_ok": False,
            "notes": f"syntax_error_fallback: {str(e)}"
        }


def canon_hash(code: str, policy: CanonPolicy) -> str:
    """Generate canonical hash signature for code"""
    # Include policy in hash to ensure different policies produce different signatures
    policy_str = f"{policy.strip_fences}{policy.strip_docstrings}{policy.strip_comments}{policy.normalize_ws}{policy.ident_normalize}"
    combined = f"{code}|{policy_str}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]


def _strip_code_fences(code: str) -> str:
    """Remove markdown code fences and language specifiers"""
    # Remove opening fence with optional language
    code = re.sub(r'^```(?:python|py)?\s*\n', '', code, flags=re.MULTILINE)
    # Remove closing fence
    code = re.sub(r'\n```\s*$', '', code, flags=re.MULTILINE)
    return code.strip()


def _strip_docstrings(tree: ast.AST) -> ast.AST:
    """Remove docstrings from AST nodes"""
    class DocstringRemover(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if (node.body and 
                isinstance(node.body[0], ast.Expr) and 
                isinstance(node.body[0].value, ast.Constant) and 
                isinstance(node.body[0].value.value, str)):
                node.body = node.body[1:]
            return self.generic_visit(node)
        
        def visit_ClassDef(self, node):
            if (node.body and 
                isinstance(node.body[0], ast.Expr) and 
                isinstance(node.body[0].value, ast.Constant) and 
                isinstance(node.body[0].value.value, str)):
                node.body = node.body[1:]
            return self.generic_visit(node)
    
    return DocstringRemover().visit(tree)


def _normalize_function_names(tree: ast.AST) -> ast.AST:
    """Normalize function names to canonical forms"""
    class FunctionNormalizer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            # Normalize common fibonacci function names
            if node.name in ['fib', 'fibonacci', 'fibo', 'fibonacci_sequence']:
                node.name = 'fibonacci'
            return self.generic_visit(node)
    
    return FunctionNormalizer().visit(tree)


def _strip_comments(code: str) -> str:
    """Remove Python comments from code"""
    lines = code.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Simple comment removal (doesn't handle strings with # correctly)
        if '#' in line:
            line = line[:line.index('#')]
        cleaned_lines.append(line.rstrip())
    
    return '\n'.join(cleaned_lines)


def _normalize_whitespace(code: str) -> str:
    """Normalize whitespace and remove empty lines"""
    lines = code.split('\n')
    normalized_lines = []
    
    for line in lines:
        stripped = line.rstrip()
        if stripped:  # Skip empty lines
            normalized_lines.append(stripped)
    
    return '\n'.join(normalized_lines)


def _fallback_cleanup(code: str, policy: CanonPolicy) -> str:
    """Fallback cleanup when AST parsing fails"""
    if policy.strip_fences:
        code = _strip_code_fences(code)
    
    if policy.strip_comments:
        code = _strip_comments(code)
    
    if policy.normalize_ws:
        code = _normalize_whitespace(code)
    
    return code
