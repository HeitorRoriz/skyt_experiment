"""
Arithmetic Expression Normalizer - Structural Transformation
Normalizes algebraically equivalent arithmetic expressions to canonical form

Handles cases like:
- (a + b) // 2 → a + (b - a) // 2 (overflow-safe midpoint)
- Other algebraically equivalent expressions
"""

import ast
from typing import Optional, Dict, Any
from ..transformation_base import TransformationBase


class ArithmeticExpressionNormalizer(TransformationBase):
    """Normalizes algebraically equivalent arithmetic expressions"""
    
    def __init__(self):
        super().__init__(
            name="ArithmeticExpressionNormalizer",
            description="Normalizes algebraically equivalent arithmetic expressions"
        )
        
        # Define transformation patterns
        self.patterns = [
            {
                'name': 'simple_midpoint_to_overflow_safe',
                'match': self._match_simple_midpoint,
                'description': '(a + b) // 2 → a + (b - a) // 2'
            }
        ]
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """Check if code contains patterns that need normalization"""
        
        # Check if there are arithmetic expression differences
        try:
            code_tree = ast.parse(code)
            canon_tree = ast.parse(canon_code)
            
            # Look for midpoint patterns in code
            code_has_simple_midpoint = self._has_simple_midpoint_pattern(code_tree)
            canon_has_overflow_safe = self._has_overflow_safe_midpoint_pattern(canon_tree)
            
            if code_has_simple_midpoint and canon_has_overflow_safe:
                self.log_debug("Found simple midpoint that needs overflow-safe conversion")
                return True
            
            # Check property diffs for operator precedence differences
            if property_diffs:
                for diff in property_diffs:
                    if diff['property'] == 'operator_precedence':
                        self.log_debug("Operator precedence difference detected")
                        return True
                    elif diff['property'] == 'algebraic_structure':
                        self.log_debug("Algebraic structure difference detected")
                        return True
            
            return False
            
        except Exception as e:
            self.log_debug(f"Error checking for arithmetic patterns: {e}")
            return False
    
    def _has_simple_midpoint_pattern(self, tree: ast.AST) -> bool:
        """Check if tree contains (a + b) // 2 pattern"""
        for node in ast.walk(tree):
            if self._match_simple_midpoint(node):
                return True
        return False
    
    def _has_overflow_safe_midpoint_pattern(self, tree: ast.AST) -> bool:
        """Check if tree contains a + (b - a) // 2 pattern"""
        for node in ast.walk(tree):
            if self._match_overflow_safe_midpoint(node):
                return True
        return False
    
    def _match_simple_midpoint(self, node: ast.AST) -> Optional[Dict[str, str]]:
        """
        Match: (left + right) // 2
        AST: BinOp(BinOp(left, Add, right), FloorDiv, 2)
        
        Returns dict with variable names if matched, None otherwise
        """
        if not isinstance(node, ast.BinOp):
            return None
        
        # Must be floor division
        if not isinstance(node.op, ast.FloorDiv):
            return None
        
        # Right side must be constant 2
        if not (isinstance(node.right, ast.Constant) and node.right.value == 2):
            return None
        
        # Left side must be addition
        if not isinstance(node.left, ast.BinOp):
            return None
        if not isinstance(node.left.op, ast.Add):
            return None
        
        # Extract variable names
        left_var = self._get_name(node.left.left)
        right_var = self._get_name(node.left.right)
        
        if left_var and right_var:
            return {'left': left_var, 'right': right_var}
        
        return None
    
    def _match_overflow_safe_midpoint(self, node: ast.AST) -> Optional[Dict[str, str]]:
        """
        Match: left + (right - left) // 2
        AST: BinOp(left, Add, BinOp(BinOp(right, Sub, left), FloorDiv, 2))
        """
        if not isinstance(node, ast.BinOp):
            return None
        
        # Must be addition
        if not isinstance(node.op, ast.Add):
            return None
        
        # Left side must be a name
        left_var = self._get_name(node.left)
        if not left_var:
            return None
        
        # Right side must be (right - left) // 2
        if not isinstance(node.right, ast.BinOp):
            return None
        if not isinstance(node.right.op, ast.FloorDiv):
            return None
        if not (isinstance(node.right.right, ast.Constant) and node.right.right.value == 2):
            return None
        
        # The dividend must be (right - left)
        if not isinstance(node.right.left, ast.BinOp):
            return None
        if not isinstance(node.right.left.op, ast.Sub):
            return None
        
        right_var = self._get_name(node.right.left.left)
        left_var_check = self._get_name(node.right.left.right)
        
        if right_var and left_var_check and left_var == left_var_check:
            return {'left': left_var, 'right': right_var}
        
        return None
    
    def _get_name(self, node: ast.AST) -> Optional[str]:
        """Extract variable name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        return None
    
    def _remove_tuple_assignment_parens(self, code: str) -> str:
        """
        Remove unnecessary parentheses from tuple assignments
        
        Converts: left, right = (0, len(...))
        To: left, right = 0, len(...)
        
        This is needed because ast.unparse() adds extra parentheses
        """
        import re
        
        # Pattern: variable_list = (value1, value2, ...)
        # Where variable_list contains commas (tuple unpacking)
        pattern = r'(\w+(?:\s*,\s*\w+)+)\s*=\s*\(([^()]+(?:\([^)]*\)[^()]*)*)\)(?=\s*(?:\n|$))'
        
        def replace_func(match):
            vars_part = match.group(1)
            values_part = match.group(2)
            return f"{vars_part} = {values_part}"
        
        # Apply the replacement
        result = re.sub(pattern, replace_func, code)
        
        return result
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """Apply arithmetic expression normalization"""
        
        self.log_debug("Applying arithmetic expression normalization")
        
        try:
            tree = ast.parse(code)
            
            # Apply transformations
            transformer = ArithmeticNormalizer(self)
            new_tree = transformer.visit(tree)
            
            # Fix missing locations
            ast.fix_missing_locations(new_tree)
            
            # Convert back to code
            transformed_code = ast.unparse(new_tree)
            
            # Post-process: Remove unnecessary tuple parentheses in assignments
            # ast.unparse adds parentheses like: left, right = (0, len(...))
            # We want: left, right = 0, len(...)
            transformed_code = self._remove_tuple_assignment_parens(transformed_code)
            
            self.log_debug("Arithmetic normalization successful")
            return transformed_code
            
        except Exception as e:
            self.log_debug(f"Arithmetic normalization failed: {e}")
            return code


class ArithmeticNormalizer(ast.NodeTransformer):
    """AST transformer for arithmetic expression normalization"""
    
    def __init__(self, normalizer: ArithmeticExpressionNormalizer):
        self.normalizer = normalizer
    
    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        """Visit binary operations and apply transformations"""
        
        # First, recursively visit children
        self.generic_visit(node)
        
        # Try to match and transform patterns
        for pattern in self.normalizer.patterns:
            match = pattern['match'](node)
            if match:
                self.normalizer.log_debug(f"Matched pattern: {pattern['description']}")
                return self._transform_simple_to_overflow_safe(match)
        
        return node
    
    def _transform_simple_to_overflow_safe(self, match_info: Dict[str, str]) -> ast.BinOp:
        """
        Transform: (left + right) // 2 → left + (right - left) // 2
        
        Args:
            match_info: Dict with 'left' and 'right' variable names
        
        Returns:
            New AST node for overflow-safe midpoint calculation
        """
        left_name = match_info['left']
        right_name = match_info['right']
        
        # Build: left + (right - left) // 2
        new_node = ast.BinOp(
            left=ast.Name(id=left_name, ctx=ast.Load()),
            op=ast.Add(),
            right=ast.BinOp(
                left=ast.BinOp(
                    left=ast.Name(id=right_name, ctx=ast.Load()),
                    op=ast.Sub(),
                    right=ast.Name(id=left_name, ctx=ast.Load())
                ),
                op=ast.FloorDiv(),
                right=ast.Constant(value=2)
            )
        )
        
        return new_node
