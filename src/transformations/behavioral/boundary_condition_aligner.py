"""
Boundary Condition Aligner - Behavioral Transformation
Aligns boundary condition handling to match canonical logic

Handles patterns like:
- Different edge case handling approaches
- Boundary value normalization
- Return pattern consistency
"""

import re
from typing import Dict, List
from ..transformation_base import TransformationBase


class BoundaryConditionAligner(TransformationBase):
    """Aligns boundary condition handling to canonical form"""
    
    def __init__(self):
        super().__init__(
            name="BoundaryConditionAligner",
            description="Aligns boundary condition logic to match canonical approach"
        )
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """Check if boundary conditions differ from canonical form"""
        
        # Extract boundary conditions from both codes
        code_conditions = self._extract_boundary_conditions(code)
        canon_conditions = self._extract_boundary_conditions(canon_code)
        
        # Check if they differ
        return code_conditions != canon_conditions
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """Apply boundary condition alignment"""
        
        self.log_debug("Applying boundary condition alignment")
        
        # Extract canonical boundary patterns
        canon_conditions = self._extract_boundary_conditions(canon_code)
        
        # Transform boundary conditions to match canonical form
        transformed = self._align_boundary_conditions(code, canon_conditions)
        
        return transformed
    
    def _extract_boundary_conditions(self, code: str) -> List[Dict[str, str]]:
        """Extract boundary condition patterns from code"""
        conditions = []
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Look for if/elif conditions with return statements
            if_match = re.match(r'(if|elif)\s+(.+):', stripped)
            if if_match:
                condition_type = if_match.group(1)
                condition_expr = if_match.group(2)
                
                # Look for return statement in next few lines
                return_value = None
                for j in range(i + 1, min(i + 4, len(lines))):
                    next_line = lines[j].strip()
                    return_match = re.match(r'return\s+(.+)', next_line)
                    if return_match:
                        return_value = return_match.group(1)
                        break
                    elif next_line and not next_line.startswith('return') and condition_type == 'if':
                        # Hit non-return statement, stop looking
                        break
                
                if return_value is not None:
                    conditions.append({
                        'type': condition_type,
                        'condition': condition_expr,
                        'return_value': return_value,
                        'line': i
                    })
        
        return conditions
    
    def _align_boundary_conditions(self, code: str, canon_conditions: List[Dict[str, str]]) -> str:
        """
        Align boundary conditions to match canonical patterns
        
        CRITICAL: Only aligns OPERATORS and CONSTANTS, never variable names
        Variable renaming is VariableRenamer's responsibility
        """
        
        if not canon_conditions:
            return code
        
        # CONSERVATIVE APPROACH: Only align very specific boundary patterns
        # DO NOT copy canonical conditions verbatim (that includes variable names!)
        
        # For now, disable this transformer to prevent corruption
        # It needs a complete rewrite to handle boundary logic without touching variables
        self.log_debug("BoundaryConditionAligner disabled to prevent variable name corruption")
        return code
