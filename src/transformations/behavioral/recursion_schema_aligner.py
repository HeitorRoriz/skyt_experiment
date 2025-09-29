"""
Recursion Schema Aligner - Behavioral Transformation
Normalizes recursive structure to match canonical form

Handles patterns like:
- Different base case predicates (len(arr) <= 1 vs not arr vs len(arr) < 2)
- Recursion depth and structure
- Divide-and-conquer partitioning
"""

import ast
import re
from typing import Dict, List
from ..transformation_base import TransformationBase


class RecursionSchemaAligner(TransformationBase):
    """Aligns recursive structure to match canonical pattern"""
    
    def __init__(self):
        super().__init__(
            name="RecursionSchemaAligner",
            description="Normalizes recursive structure and base cases"
        )
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """Check if recursion schemas differ (PROPERTY-DRIVEN)"""
        
        # Use property differences to detect recursion schema mismatches
        if property_diffs:
            for diff in property_diffs:
                if diff['property'] == 'recursion_schema' and diff['distance'] > 0.1:
                    return True
        
        return False
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """Apply recursion schema alignment"""
        
        self.log_debug("Applying recursion schema alignment")
        
        # Extract canonical base case pattern
        canon_base_pattern = self._extract_base_case_pattern(canon_code)
        self.log_debug(f"Canon base case: {canon_base_pattern}")
        
        # Transform base cases
        transformed = self._normalize_base_cases(code, canon_base_pattern)
        
        return transformed
    
    def _has_recursion(self, code: str) -> bool:
        """Check if code contains recursion"""
        try:
            tree = ast.parse(code)
            
            class RecursionChecker(ast.NodeVisitor):
                def __init__(self):
                    self.function_name = None
                    self.has_recursion = False
                    
                def visit_FunctionDef(self, node):
                    old_name = self.function_name
                    self.function_name = node.name
                    self.generic_visit(node)
                    self.function_name = old_name
                    
                def visit_Call(self, node):
                    if isinstance(node.func, ast.Name):
                        if node.func.id == self.function_name:
                            self.has_recursion = True
                    self.generic_visit(node)
            
            checker = RecursionChecker()
            checker.visit(tree)
            return checker.has_recursion
            
        except:
            return False
    
    def _extract_base_case_pattern(self, code: str) -> str:
        """Extract base case predicate pattern"""
        
        # Common patterns for sorting algorithms
        patterns = [
            r'if\s+len\(\w+\)\s*<=\s*1\s*:',
            r'if\s+len\(\w+\)\s*<\s*2\s*:',
            r'if\s+not\s+\w+\s*:',
            r'if\s+len\(\w+\)\s*==\s*0\s*:',
            r'if\s+\w+\s*==\s*\[\]\s*:',
        ]
        
        for pattern in patterns:
            if re.search(pattern, code):
                return pattern
        
        return "unknown"
    
    def _normalize_base_cases(self, code: str, canon_pattern: str) -> str:
        """Normalize base case to match canonical pattern"""
        
        # Define normalization rules
        # Canon: if len(arr) <= 1: return arr
        canonical_base = "if len(arr) <= 1:\n        return arr"
        
        lines = code.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Detect base case patterns
            if (stripped.startswith('if') and 
                any(keyword in stripped for keyword in ['len(', 'not ', '== []'])):
                
                # Check if this is a base case (has return in next line)
                if i + 1 < len(lines) and 'return' in lines[i + 1]:
                    self.log_debug(f"Found base case: {stripped}")
                    
                    # Replace with canonical base case
                    indent = len(line) - len(line.lstrip())
                    result_lines.append(' ' * indent + canonical_base.split('\n')[0])
                    result_lines.append(' ' * indent + canonical_base.split('\n')[1])
                    
                    # Skip original base case lines
                    i += 2
                    continue
            
            result_lines.append(line)
            i += 1
        
        return '\n'.join(result_lines)
