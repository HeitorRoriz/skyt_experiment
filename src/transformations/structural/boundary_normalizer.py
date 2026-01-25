"""
Boundary Condition Normalizer
Normalizes equivalent boundary conditions to match canon
e.g., n < 2 -> n <= 1, n >= 1 -> n > 0
"""

import ast
from typing import Optional, Dict, List, Tuple
from ..transformation_base import TransformationBase, TransformationResult


class BoundaryNormalizer(TransformationBase):
    """
    Normalizes boundary conditions to match canonical form.
    
    Handles equivalent comparisons:
    - n < 2  <->  n <= 1
    - n > 0  <->  n >= 1
    - n < 1  <->  n <= 0
    etc.
    """
    
    def __init__(self):
        super().__init__(
            name="BoundaryNormalizer",
            description="Normalize equivalent boundary conditions to match canon"
        )
        
        # Equivalent transformations: (op, delta) -> (new_op, new_delta)
        # For integer comparisons: x < n is equivalent to x <= n-1
        self.equivalences = {
            (ast.Lt, 1): (ast.LtE, 0),      # < n  -> <= n-1
            (ast.LtE, -1): (ast.Lt, 0),     # <= n -> < n+1
            (ast.Gt, -1): (ast.GtE, 0),     # > n  -> >= n+1
            (ast.GtE, 1): (ast.Gt, 0),      # >= n -> > n-1
        }
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """Check if there are boundary condition differences"""
        if not canon_code:
            return False
        
        tree = self.safe_parse_ast(code)
        canon_tree = self.safe_parse_ast(canon_code)
        
        if not tree or not canon_tree:
            return False
        
        # Find comparison nodes in both
        code_comparisons = self._extract_comparisons(tree)
        canon_comparisons = self._extract_comparisons(canon_tree)
        
        # Check if any can be normalized to match
        for code_comp in code_comparisons:
            for canon_comp in canon_comparisons:
                if self._are_equivalent(code_comp, canon_comp):
                    return True
        
        return False
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """Normalize boundary conditions to match canon"""
        tree = self.safe_parse_ast(code)
        canon_tree = self.safe_parse_ast(canon_code)
        
        if not tree or not canon_tree:
            return code
        
        # Extract canon comparisons as targets
        canon_comparisons = self._extract_comparisons(canon_tree)
        
        transformer = BoundaryNodeTransformer(canon_comparisons)
        new_tree = transformer.visit(tree)
        
        if transformer.modified:
            ast.fix_missing_locations(new_tree)
            try:
                return ast.unparse(new_tree)
            except:
                return code
        return code
    
    def _extract_comparisons(self, tree: ast.AST) -> List[Dict]:
        """Extract comparison info from AST"""
        comparisons = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                if len(node.ops) == 1 and len(node.comparators) == 1:
                    left = node.left
                    op = node.ops[0]
                    right = node.comparators[0]
                    
                    # Only handle simple variable vs constant comparisons
                    if isinstance(left, ast.Name) and isinstance(right, ast.Constant):
                        comparisons.append({
                            'var': left.id,
                            'op': type(op),
                            'value': right.value
                        })
                    elif isinstance(right, ast.Name) and isinstance(left, ast.Constant):
                        # Flip: 2 > n -> n < 2
                        flipped_op = self._flip_op(type(op))
                        if flipped_op:
                            comparisons.append({
                                'var': right.id,
                                'op': flipped_op,
                                'value': left.value
                            })
        return comparisons
    
    def _flip_op(self, op_type):
        """Flip comparison operator"""
        flips = {
            ast.Lt: ast.Gt,
            ast.Gt: ast.Lt,
            ast.LtE: ast.GtE,
            ast.GtE: ast.LtE,
        }
        return flips.get(op_type)
    
    def _are_equivalent(self, comp1: Dict, comp2: Dict) -> bool:
        """Check if two comparisons are semantically equivalent"""
        if comp1['var'] != comp2['var']:
            return False
        
        # Same comparison
        if comp1['op'] == comp2['op'] and comp1['value'] == comp2['value']:
            return False  # Already identical, no transform needed
        
        # Check for equivalent forms
        # x < n is equivalent to x <= n-1
        v1, v2 = comp1['value'], comp2['value']
        op1, op2 = comp1['op'], comp2['op']
        
        # < n == <= n-1
        if op1 == ast.Lt and op2 == ast.LtE and v1 == v2 + 1:
            return True
        if op1 == ast.LtE and op2 == ast.Lt and v1 == v2 - 1:
            return True
        
        # > n == >= n+1
        if op1 == ast.Gt and op2 == ast.GtE and v1 == v2 - 1:
            return True
        if op1 == ast.GtE and op2 == ast.Gt and v1 == v2 + 1:
            return True
        
        return False


class BoundaryNodeTransformer(ast.NodeTransformer):
    """AST transformer for boundary condition normalization"""
    
    def __init__(self, canon_comparisons: List[Dict]):
        self.canon_comparisons = canon_comparisons
        self.modified = False
    
    def visit_Compare(self, node: ast.Compare) -> ast.Compare:
        """Transform comparisons to match canon"""
        if len(node.ops) != 1 or len(node.comparators) != 1:
            return node
        
        left = node.left
        op = node.ops[0]
        right = node.comparators[0]
        
        # Handle variable < constant
        if isinstance(left, ast.Name) and isinstance(right, ast.Constant):
            var_name = left.id
            value = right.value
            op_type = type(op)
            
            # Find matching canon comparison
            for canon in self.canon_comparisons:
                if canon['var'] == var_name:
                    # Check if we need to transform
                    if self._should_transform(op_type, value, canon['op'], canon['value']):
                        # Transform to canon form
                        node.ops = [canon['op']()]
                        node.comparators = [ast.Constant(value=canon['value'])]
                        self.modified = True
                        return node
        
        return node
    
    def _should_transform(self, code_op, code_val, canon_op, canon_val) -> bool:
        """Check if transformation is needed and valid"""
        if code_op == canon_op and code_val == canon_val:
            return False  # Already matches
        
        # < n == <= n-1
        if code_op == ast.Lt and canon_op == ast.LtE and code_val == canon_val + 1:
            return True
        if code_op == ast.LtE and canon_op == ast.Lt and code_val == canon_val - 1:
            return True
        
        # > n == >= n+1  
        if code_op == ast.Gt and canon_op == ast.GtE and code_val == canon_val - 1:
            return True
        if code_op == ast.GtE and canon_op == ast.Gt and code_val == canon_val + 1:
            return True
        
        return False
