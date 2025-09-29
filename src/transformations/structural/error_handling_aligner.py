"""
Error Handling Aligner - Structural Transformation
Converts error handling patterns to match canonical form

Handles patterns like:
- if n < 0: raise ValueError(...) -> if n <= 0: return 0
- Different boundary conditions and error responses
"""

import re
from typing import List, Tuple
from ..transformation_base import TransformationBase


class ErrorHandlingAligner(TransformationBase):
    """Aligns error handling patterns to match canonical form"""
    
    def __init__(self):
        super().__init__(
            name="ErrorHandlingAligner",
            description="Converts error handling to match canonical boundary checks"
        )
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """Check if code has error handling that differs from canon (PROPERTY-DRIVEN)"""
        
        # Use property differences instead of hardcoded Fibonacci checks
        if property_diffs:
            # Check if side effect profile differs (raise statements are side effects)
            for diff in property_diffs:
                if diff['property'] == 'side_effect_profile' and diff['distance'] > 0:
                    return True
                
                # Check if termination properties differ (error handling vs boundary checks)
                if diff['property'] == 'termination_properties' and diff['distance'] > 0:
                    return True
        
        # Fallback: generic check for raise statement differences
        has_raise = 'raise ' in code
        canon_has_raise = 'raise ' in canon_code
        
        return has_raise != canon_has_raise
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """Apply error handling alignment transformation"""
        
        self.log_debug("Applying error handling alignment")
        
        # Extract canonical boundary pattern
        canon_boundary = self._extract_boundary_pattern(canon_code)
        self.log_debug(f"Canon boundary pattern: {canon_boundary}")
        
        # Transform the code
        transformed = self._transform_error_handling(code, canon_boundary)
        
        return transformed
    
    def _extract_boundary_pattern(self, canon_code: str) -> dict:
        """Extract boundary condition pattern from canonical code"""
        
        pattern = {
            'condition': None,
            'return_value': None,
            'has_error_handling': False
        }
        
        lines = canon_code.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Look for boundary conditions
            if 'if n <' in stripped or 'if n>' in stripped or 'if n ==' in stripped:
                pattern['condition'] = stripped
                
                # Look for return value in next few lines
                for j in range(i+1, min(i+4, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.startswith('return '):
                        pattern['return_value'] = next_line
                        break
                    elif 'raise ' in next_line:
                        pattern['has_error_handling'] = True
                        break
                break
        
        return pattern
    
    def _transform_error_handling(self, code: str, canon_pattern: dict) -> str:
        """Transform error handling to match canonical pattern"""
        
        lines = code.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            # Pattern 1: if n < 0: raise ValueError(...) or similar error conditions
            if self._is_error_condition_line(stripped):
                self.log_debug(f"Found error condition: {stripped}")
                
                # Replace with canonical boundary check
                if canon_pattern['condition'] and canon_pattern['return_value']:
                    # Extract the canonical condition and return
                    canon_condition = canon_pattern['condition'].replace('if ', '').replace(':', '')
                    canon_return = canon_pattern['return_value']
                    
                    result_lines.append(' ' * indent + f'if {canon_condition}:')
                    result_lines.append(' ' * (indent + 4) + canon_return)
                    
                    # Skip all lines that are part of this error handling block
                    i += 1
                    while i < len(lines):
                        next_line = lines[i].strip()
                        next_indent = len(lines[i]) - len(lines[i].lstrip()) if lines[i].strip() else 0
                        
                        # Skip lines that are part of the error handling (indented more or raise statements)
                        if (next_indent > indent and next_line) or 'raise ' in next_line:
                            self.log_debug(f"Skipping error handling line: {next_line}")
                            i += 1
                        # Skip elif n == 0 if we converted to n <= 0
                        elif next_line.startswith('elif n == 0:') and 'n <= 0' in canon_condition:
                            self.log_debug(f"Skipping redundant elif n == 0")
                            i += 1
                            # Also skip the return statement that follows
                            if i < len(lines) and 'return 0' in lines[i].strip():
                                i += 1
                        else:
                            break
                    continue
                else:
                    result_lines.append(line)
            
            # Skip standalone raise statements (shouldn't happen after above logic)
            elif 'raise ValueError' in stripped or 'raise Exception' in stripped:
                self.log_debug(f"Skipping standalone raise statement: {stripped}")
                i += 1
                continue
            
            else:
                result_lines.append(line)
            
            i += 1
        
        return '\n'.join(result_lines)
    
    def _is_error_condition_line(self, line: str) -> bool:
        """Check if line is an error condition that should be transformed"""
        patterns = [
            r'if\s+n\s*<\s*0\s*:',
            r'if\s+n\s*<\s*1\s*:',
        ]
        
        for pattern in patterns:
            if re.search(pattern, line):
                return True
        return False
    
    def _count_lines_to_skip(self, lines: List[str], current_index: int) -> int:
        """Count how many lines to skip after an error condition"""
        skip_count = 0
        
        for i in range(current_index + 1, min(current_index + 5, len(lines))):
            line = lines[i].strip()
            
            if ('raise ' in line or 
                line.startswith('elif n == 0:') or
                (line.startswith('return ') and 'raise ' in lines[max(0, i-2):i+1])):
                skip_count += 1
            else:
                break
                
        return skip_count
    
    def _is_part_of_error_handling(self, previous_lines: List[str]) -> bool:
        """Check if current raise statement is part of error handling we're replacing"""
        if len(previous_lines) < 2:
            return False
            
        # Check last few lines for error condition patterns
        recent_lines = previous_lines[-3:]
        for line in recent_lines:
            if ('if n <' in line and ':' in line):
                return True
        return False
    
    def _has_n_less_equal_condition(self, lines: List[str]) -> bool:
        """Check if we recently added an 'if n <= 0:' condition"""
        if len(lines) < 2:
            return False
            
        recent_lines = lines[-3:]
        for line in recent_lines:
            if 'if n <= 0:' in line:
                return True
        return False
