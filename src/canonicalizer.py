# src/canonicalizer.py
"""
Simplified canonicalizer that:
- Strips comments and docstrings
- Enforces function names
- Performs AST round-trip
- Generates SHA-256 signature
"""

import ast
import hashlib
import re
from typing import Optional


class CodeCanonicalizer(ast.NodeTransformer):
    """AST transformer for canonicalization"""
    
    def __init__(self, target_function_name: str = "fibonacci"):
        self.target_function_name = target_function_name
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Enforce function name and remove docstrings"""
        # Change function name to target name
        node.name = self.target_function_name
        
        # Remove docstring if present
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            node.body = node.body[1:]
        
        return self.generic_visit(node)
    
    def visit_Expr(self, node: ast.Expr) -> Optional[ast.Expr]:
        """Remove standalone string expressions (comments as strings)"""
        if (isinstance(node.value, ast.Constant) and 
            isinstance(node.value.value, str)):
            return None
        return self.generic_visit(node)


def strip_comments(code: str) -> str:
    """Remove Python comments from code"""
    lines = code.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove inline comments but preserve strings
        in_string = False
        quote_char = None
        result = ""
        i = 0
        
        while i < len(line):
            char = line[i]
            
            if not in_string and char == '#':
                # Found comment, stop processing this line
                break
            elif not in_string and char in ['"', "'"]:
                # Start of string
                in_string = True
                quote_char = char
                result += char
            elif in_string and char == quote_char:
                # End of string (simplified - doesn't handle escapes)
                in_string = False
                quote_char = None
                result += char
            else:
                result += char
            
            i += 1
        
        # Only keep non-empty lines
        if result.strip():
            cleaned_lines.append(result.rstrip())
    
    return '\n'.join(cleaned_lines)


def canonicalize_code(code: str, target_function_name: str = "fibonacci") -> Optional[str]:
    """
    Canonicalize Python code by:
    1. Stripping comments
    2. Parsing to AST
    3. Enforcing function name
    4. Removing docstrings
    5. Converting back to code
    6. Normalizing whitespace
    
    Returns None if canonicalization fails
    """
    try:
        # Step 1: Strip comments
        code_no_comments = strip_comments(code)
        
        # Step 2: Parse to AST
        tree = ast.parse(code_no_comments)
        
        # Step 3: Apply canonicalization transformations
        canonicalizer = CodeCanonicalizer(target_function_name)
        canonical_tree = canonicalizer.visit(tree)
        
        # Step 4: Convert back to code
        canonical_code = ast.unparse(canonical_tree)
        
        # Step 5: Normalize whitespace
        canonical_code = normalize_whitespace(canonical_code)
        
        return canonical_code
        
    except (SyntaxError, ValueError, TypeError) as e:
        # Canonicalization failed
        return None


def normalize_whitespace(code: str) -> str:
    """Normalize whitespace in code"""
    # Remove extra blank lines
    lines = [line.rstrip() for line in code.split('\n')]
    
    # Remove consecutive empty lines
    normalized_lines = []
    prev_empty = False
    
    for line in lines:
        if line.strip() == "":
            if not prev_empty:
                normalized_lines.append("")
            prev_empty = True
        else:
            normalized_lines.append(line)
            prev_empty = False
    
    # Remove trailing empty lines
    while normalized_lines and normalized_lines[-1] == "":
        normalized_lines.pop()
    
    return '\n'.join(normalized_lines)


def generate_signature(code: str) -> str:
    """Generate SHA-256 signature for code"""
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


def canonicalize_with_signature(code: str, target_function_name: str = "fibonacci") -> tuple[Optional[str], Optional[str]]:
    """
    Canonicalize code and return both canonical form and signature
    
    Returns:
        (canonical_code, signature) or (None, None) if canonicalization fails
    """
    canonical_code = canonicalize_code(code, target_function_name)
    
    if canonical_code is None:
        return None, None
    
    signature = generate_signature(canonical_code)
    return canonical_code, signature
