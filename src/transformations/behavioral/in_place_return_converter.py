"""
In-Place Return Converter - Behavioral Transformation
Converts between in-place mutation and return-based sorting styles

Handles patterns like:
- In-place: arr.sort() / function mutates arr, returns None
- Return-based: return sorted(arr) / function returns new sorted list
"""

import ast
import re
from typing import Dict
from ..transformation_base import TransformationBase


class InPlaceReturnConverter(TransformationBase):
    """Converts between in-place and return-based styles"""
    
    def __init__(self):
        super().__init__(
            name="InPlaceReturnConverter",
            description="Normalizes in-place vs return-based sorting semantics"
        )
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """Check if mutation styles differ (PROPERTY-DRIVEN)"""
        
        # Use property differences to detect style mismatches
        if property_diffs:
            for diff in property_diffs:
                if diff['property'] == 'function_contracts' and diff['distance'] > 0:
                    # Check if the difference is in return behavior
                    curr_val = diff.get('current_value', {})
                    canon_val = diff.get('canon_value', {})
                    # Only transform if actual return mismatch detected
                    if curr_val and canon_val and curr_val != canon_val:
                        return True
        
        # Fallback check, but be conservative to avoid infinite loops
        code_style = self._detect_style(code)
        canon_style = self._detect_style(canon_code)
        
        # CRITICAL: Only transform if styles truly differ AND not both return-based
        return code_style != canon_style and not (code_style == "return_based" and canon_style == "return_based")
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """Apply style conversion"""
        
        self.log_debug("Applying in-place/return conversion")
        
        code_style = self._detect_style(code)
        canon_style = self._detect_style(canon_code)
        
        self.log_debug(f"Converting from {code_style} to {canon_style}")
        
        if code_style == "in_place" and canon_style == "return_based":
            return self._convert_inplace_to_return(code)
        elif code_style == "return_based" and canon_style == "in_place":
            return self._convert_return_to_inplace(code)
        
        return code
    
    def _detect_style(self, code: str) -> str:
        """Detect if code is in-place or return-based"""
        
        try:
            tree = ast.parse(code)
            
            class StyleDetector(ast.NodeVisitor):
                def __init__(self):
                    self.has_return_none = False
                    self.has_return_list = False
                    self.has_mutation = False
                    
                def visit_FunctionDef(self, node):
                    # Check returns
                    for stmt in ast.walk(node):
                        if isinstance(stmt, ast.Return):
                            if stmt.value is None or (isinstance(stmt.value, ast.Constant) and stmt.value.value is None):
                                self.has_return_none = True
                            elif isinstance(stmt.value, (ast.Name, ast.List, ast.Call)):
                                self.has_return_list = True
                    
                    # Check for in-place mutations
                    for stmt in ast.walk(node):
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Subscript):
                                    self.has_mutation = True
                    
                    self.generic_visit(node)
            
            detector = StyleDetector()
            detector.visit(tree)
            
            if detector.has_mutation or detector.has_return_none:
                return "in_place"
            elif detector.has_return_list:
                return "return_based"
            
            return "unknown"
            
        except:
            return "unknown"
    
    def _convert_inplace_to_return(self, code: str) -> str:
        """Convert in-place mutation to return-based"""
        
        # Ensure function returns the array at the end
        lines = code.split('\n')
        
        # Find the main function
        func_indent = 0
        in_function = False
        result_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if stripped.startswith('def '):
                in_function = True
                func_indent = len(line) - len(line.lstrip())
                result_lines.append(line)
                
                # Extract param name
                match = re.search(r'def\s+\w+\s*\((\w+)', line)
                if match:
                    param_name = match.group(1)
            
            elif in_function and stripped and len(line) - len(line.lstrip()) == func_indent and stripped[0].isalpha():
                # End of function, ensure we return the array
                if not any('return' in result_lines[-j] for j in range(1, min(4, len(result_lines)))):
                    result_lines.append(' ' * (func_indent + 4) + f'return {param_name}')
                result_lines.append(line)
                in_function = False
                
            else:
                result_lines.append(line)
        
        # Add return if function ends without one
        if in_function:
            result_lines.append(' ' * (func_indent + 4) + f'return {param_name}')
        
        return '\n'.join(result_lines)
    
    def _convert_return_to_inplace(self, code: str) -> str:
        """Convert return-based to in-place mutation"""
        
        # This is more complex and risky - for now, keep as is
        # In practice, return-based is more canonical
        self.log_debug("Return-to-inplace conversion not implemented (risky)")
        return code
