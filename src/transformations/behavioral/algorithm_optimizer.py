"""
Algorithm Optimizer - Behavioral Transformation
Optimizes algorithmic patterns for efficiency and canonical form

Handles patterns like:
- Loop optimization and canonicalization
- Variable usage patterns (a,b vs fib1,fib2)
- Algorithmic approach alignment
"""

import ast
import re
from typing import Dict, List, Tuple
from ..transformation_base import TransformationBase


class AlgorithmOptimizer(TransformationBase):
    """Optimizes and canonicalizes algorithmic patterns"""
    
    def __init__(self):
        super().__init__(
            name="AlgorithmOptimizer",
            description="Optimizes algorithmic patterns to match canonical approach"
        )
    
    def can_transform(self, code: str, canon_code: str) -> bool:
        """Check if code has algorithmic patterns that differ from canon"""
        
        # Extract variable naming patterns
        code_vars = self._extract_variable_patterns(code)
        canon_vars = self._extract_variable_patterns(canon_code)
        
        # Check for different variable naming conventions
        has_different_vars = code_vars != canon_vars
        
        # Check for different loop patterns
        has_different_loops = self._has_different_loop_patterns(code, canon_code)
        
        return has_different_vars or has_different_loops
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """Apply algorithmic optimization transformation"""
        
        self.log_debug("Applying algorithm optimization")
        
        # Extract canonical patterns
        canon_vars = self._extract_variable_patterns(canon_code)
        canon_loop_pattern = self._extract_loop_pattern(canon_code)
        
        # Transform variable names
        transformed = self._normalize_variable_names(code, canon_vars)
        
        # Transform loop patterns
        transformed = self._normalize_loop_patterns(transformed, canon_loop_pattern)
        
        return transformed
    
    def _extract_variable_patterns(self, code: str) -> Dict[str, str]:
        """Extract variable naming patterns from code"""
        patterns = {}
        
        # Look for tuple assignments like a, b = 0, 1
        tuple_assignments = re.findall(r'(\w+),\s*(\w+)\s*=\s*(\d+),\s*(\d+)', code)
        for match in tuple_assignments:
            var1, var2, val1, val2 = match
            if val1 == '0' and val2 == '1':  # Fibonacci initialization pattern
                patterns['fib_var1'] = var1
                patterns['fib_var2'] = var2
        
        # Look for tuple swaps like a, b = b, a + b
        tuple_swaps = re.findall(r'(\w+),\s*(\w+)\s*=\s*(\w+),\s*(\w+)\s*\+\s*(\w+)', code)
        for match in tuple_swaps:
            var1, var2, right1, right2, right3 = match
            if right1 == var2 and right2 == var1 and right3 == var2:  # Fibonacci update pattern
                patterns['fib_var1'] = var1
                patterns['fib_var2'] = var2
        
        return patterns
    
    def _extract_loop_pattern(self, code: str) -> Dict[str, str]:
        """Extract loop patterns from code"""
        pattern = {}
        
        # Look for range patterns
        range_matches = re.findall(r'for\s+\w+\s+in\s+range\(([^)]+)\):', code)
        if range_matches:
            pattern['range_expr'] = range_matches[0]
        
        return pattern
    
    def _has_different_loop_patterns(self, code: str, canon_code: str) -> bool:
        """Check if loop patterns differ between code and canon"""
        code_pattern = self._extract_loop_pattern(code)
        canon_pattern = self._extract_loop_pattern(canon_code)
        
        return code_pattern != canon_pattern
    
    def _normalize_variable_names(self, code: str, canon_vars: Dict[str, str]) -> str:
        """Normalize variable names to match canonical form"""
        
        if not canon_vars:
            return code
        
        # Extract current variable patterns
        current_vars = self._extract_variable_patterns(code)
        
        if not current_vars:
            return code
        
        # Create mapping from current vars to canonical vars
        var_mapping = {}
        if 'fib_var1' in current_vars and 'fib_var1' in canon_vars:
            var_mapping[current_vars['fib_var1']] = canon_vars['fib_var1']
        if 'fib_var2' in current_vars and 'fib_var2' in canon_vars:
            var_mapping[current_vars['fib_var2']] = canon_vars['fib_var2']
        
        # Apply variable name replacements
        transformed = code
        for old_var, new_var in var_mapping.items():
            if old_var != new_var:
                self.log_debug(f"Renaming variable: {old_var} → {new_var}")
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(old_var) + r'\b'
                transformed = re.sub(pattern, new_var, transformed)
        
        return transformed
    
    def _normalize_loop_patterns(self, code: str, canon_loop_pattern: Dict[str, str]) -> str:
        """Normalize loop patterns to match canonical form"""
        
        if not canon_loop_pattern or 'range_expr' not in canon_loop_pattern:
            return code
        
        canon_range = canon_loop_pattern['range_expr']
        
        # Find current range expressions
        current_ranges = re.findall(r'for\s+(\w+)\s+in\s+range\(([^)]+)\):', code)
        
        for loop_var, current_range in current_ranges:
            if current_range != canon_range:
                self.log_debug(f"Normalizing range: {current_range} → {canon_range}")
                
                # Replace the range expression
                old_pattern = f'for {loop_var} in range({re.escape(current_range)}):'
                new_pattern = f'for {loop_var} in range({canon_range}):'
                code = code.replace(old_pattern, new_pattern)
        
        return code
