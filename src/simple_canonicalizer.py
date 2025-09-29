# src/simple_canonicalizer.py
"""
Simple canonicalizer for SKYT experiments
Provides basic structural normalization for R_canon metric calculation
"""

import ast
import re
from typing import Optional


class SimpleCanonicalizer:
    """Basic AST-based code canonicalizer"""
    
    def canonicalize(self, code: str) -> str:
        """
        Apply basic canonicalization to code
        
        Args:
            code: Raw Python code string
            
        Returns:
            Canonicalized code string
        """
        try:
            # Parse to AST to validate syntax
            tree = ast.parse(code)
            
            # Apply canonicalization transformations
            canonical_code = code
            canonical_code = self._remove_comments_and_docstrings(canonical_code)
            canonical_code = self._normalize_whitespace(canonical_code)
            canonical_code = self._normalize_function_names(canonical_code)
            canonical_code = self._remove_empty_lines(canonical_code)
            
            return canonical_code.strip()
            
        except SyntaxError:
            # Return original code if unparseable
            return code
    
    def _remove_comments_and_docstrings(self, code: str) -> str:
        """Remove comments and docstrings"""
        lines = []
        in_multiline_string = False
        quote_char = None
        
        for line in code.split('\n'):
            # Handle multiline strings/docstrings
            if '"""' in line or "'''" in line:
                if not in_multiline_string:
                    quote_char = '"""' if '"""' in line else "'''"
                    in_multiline_string = True
                    continue
                elif quote_char in line:
                    in_multiline_string = False
                    continue
            
            if in_multiline_string:
                continue
            
            # Remove inline comments
            if '#' in line:
                line = line[:line.index('#')]
            
            # Skip empty lines after comment removal
            if line.strip():
                lines.append(line)
        
        return '\n'.join(lines)
    
    def _normalize_whitespace(self, code: str) -> str:
        """Normalize whitespace and indentation"""
        lines = []
        for line in code.split('\n'):
            if line.strip():  # Skip empty lines
                # Normalize indentation to 4 spaces
                stripped = line.lstrip()
                if stripped:
                    indent_level = (len(line) - len(stripped)) // 4
                    normalized_line = '    ' * indent_level + stripped
                    lines.append(normalized_line)
        
        return '\n'.join(lines)
    
    def _normalize_function_names(self, code: str) -> str:
        """Normalize common function name variations"""
        # Common normalizations for fibonacci
        normalizations = {
            r'\bfib\b': 'fibonacci',
            r'\bfibonacci_sequence\b': 'fibonacci',
            r'\bfib_seq\b': 'fibonacci',
            r'\bgenerate_fibonacci\b': 'fibonacci'
        }
        
        normalized = code
        for pattern, replacement in normalizations.items():
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized
    
    def _remove_empty_lines(self, code: str) -> str:
        """Remove empty lines"""
        lines = [line for line in code.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    def are_equivalent(self, code1: str, code2: str) -> bool:
        """
        Check if two code snippets are canonically equivalent
        
        Args:
            code1: First code snippet
            code2: Second code snippet
            
        Returns:
            True if canonically equivalent
        """
        canon1 = self.canonicalize(code1)
        canon2 = self.canonicalize(code2)
        
        return canon1 == canon2
