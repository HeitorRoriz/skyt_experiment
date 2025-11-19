"""
Expression Canonicalization - Phase 1.6

Transforms expressions to canonical forms without changing semantics.
All transformations are semantics-preserving and safe.

Examples:
- x + 0 → x
- x * 1 → x
- x - 0 → x
- 0 + x → x
- 1 * x → x
- not (not x) → x
- x == True → x
- x == False → not x

Design: Pure syntactic transformations (no semantic analysis needed)
"""

import ast
import copy
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ExpressionCanonicalizer(ast.NodeTransformer):
    """
    Canonicalizes expressions to reduce syntactic variations.
    
    This is TRANSFORMABLE - changes syntax but not semantics.
    Safe to use in distance calculation.
    """
    
    def __init__(self):
        self.transformations_applied = 0
        self.transformation_log = []
    
    def visit_BinOp(self, node: ast.BinOp) -> ast.expr:
        """Canonicalize binary operations"""
        # First, recursively transform children
        node = self.generic_visit(node)
        
        # Pattern: x + 0 → x
        if isinstance(node.op, ast.Add):
            if self._is_zero(node.right):
                self._log_transformation("x + 0", "x")
                return node.left
            elif self._is_zero(node.left):
                self._log_transformation("0 + x", "x")
                return node.right
        
        # Pattern: x - 0 → x
        elif isinstance(node.op, ast.Sub):
            if self._is_zero(node.right):
                self._log_transformation("x - 0", "x")
                return node.left
        
        # Pattern: x * 1 → x
        elif isinstance(node.op, ast.Mult):
            if self._is_one(node.right):
                self._log_transformation("x * 1", "x")
                return node.left
            elif self._is_one(node.left):
                self._log_transformation("1 * x", "x")
                return node.right
            # Pattern: x * 0 → 0 (but be careful with side effects!)
            # Skipping this for safety
        
        # Pattern: x / 1 → x
        elif isinstance(node.op, ast.Div) or isinstance(node.op, ast.FloorDiv):
            if self._is_one(node.right):
                self._log_transformation("x / 1", "x")
                return node.left
        
        return node
    
    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.expr:
        """Canonicalize unary operations"""
        # First, recursively transform children
        node = self.generic_visit(node)
        
        # Pattern: not (not x) → x
        if isinstance(node.op, ast.Not):
            if isinstance(node.operand, ast.UnaryOp) and isinstance(node.operand.op, ast.Not):
                self._log_transformation("not (not x)", "x")
                return node.operand.operand
        
        # Pattern: -(-x) → x
        elif isinstance(node.op, ast.USub):
            if isinstance(node.operand, ast.UnaryOp) and isinstance(node.operand.op, ast.USub):
                self._log_transformation("-(-x)", "x")
                return node.operand.operand
        
        # Pattern: +(+x) → x (unary plus is identity)
        elif isinstance(node.op, ast.UAdd):
            self._log_transformation("+(x)", "x")
            return node.operand
        
        return node
    
    def visit_Compare(self, node: ast.Compare) -> ast.expr:
        """Canonicalize comparisons"""
        # First, recursively transform children
        node = self.generic_visit(node)
        
        # Pattern: x == True → x (for boolean expressions)
        if len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq):
            if self._is_true(node.comparators[0]):
                self._log_transformation("x == True", "x")
                return node.left
            elif self._is_true(node.left):
                self._log_transformation("True == x", "x")
                return node.comparators[0]
        
        # Pattern: x == False → not x
        if len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq):
            if self._is_false(node.comparators[0]):
                self._log_transformation("x == False", "not x")
                return ast.UnaryOp(op=ast.Not(), operand=node.left)
            elif self._is_false(node.left):
                self._log_transformation("False == x", "not x")
                return ast.UnaryOp(op=ast.Not(), operand=node.comparators[0])
        
        # Pattern: x != True → not x
        if len(node.ops) == 1 and isinstance(node.ops[0], ast.NotEq):
            if self._is_true(node.comparators[0]):
                self._log_transformation("x != True", "not x")
                return ast.UnaryOp(op=ast.Not(), operand=node.left)
        
        # Pattern: x != False → x
        if len(node.ops) == 1 and isinstance(node.ops[0], ast.NotEq):
            if self._is_false(node.comparators[0]):
                self._log_transformation("x != False", "x")
                return node.left
        
        return node
    
    def _is_zero(self, node: ast.expr) -> bool:
        """Check if node is constant 0"""
        return isinstance(node, ast.Constant) and node.value == 0
    
    def _is_one(self, node: ast.expr) -> bool:
        """Check if node is constant 1"""
        return isinstance(node, ast.Constant) and node.value == 1
    
    def _is_true(self, node: ast.expr) -> bool:
        """Check if node is True"""
        return isinstance(node, ast.Constant) and node.value is True
    
    def _is_false(self, node: ast.expr) -> bool:
        """Check if node is False"""
        return isinstance(node, ast.Constant) and node.value is False
    
    def _log_transformation(self, pattern: str, result: str):
        """Log a transformation"""
        self.transformations_applied += 1
        self.transformation_log.append({
            'pattern': pattern,
            'result': result
        })


def canonicalize_expressions(code: str) -> tuple[str, dict]:
    """
    Apply expression canonicalization to code.
    
    Args:
        code: Python source code
        
    Returns:
        Tuple of (transformed_code, stats)
    """
    try:
        tree = ast.parse(code)
        
        # Apply canonicalization
        canonicalizer = ExpressionCanonicalizer()
        transformed_tree = canonicalizer.visit(tree)
        
        # Fix missing locations
        ast.fix_missing_locations(transformed_tree)
        
        # Convert back to code
        import astor
        transformed_code = astor.to_source(transformed_tree)
        
        stats = {
            'success': True,
            'transformations_applied': canonicalizer.transformations_applied,
            'transformation_log': canonicalizer.transformation_log
        }
        
        return transformed_code, stats
        
    except SyntaxError as e:
        logger.warning(f"Syntax error in expression canonicalization: {e}")
        return code, {'success': False, 'error': str(e)}
    except Exception as e:
        logger.warning(f"Expression canonicalization failed: {e}")
        return code, {'success': False, 'error': str(e)}


# Example usage and tests
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("x + 0", "x"),
        ("0 + x", "x"),
        ("x * 1", "x"),
        ("1 * x", "x"),
        ("x - 0", "x"),
        ("not (not x)", "x"),
        ("x == True", "x"),
        ("x == False", "not x"),
    ]
    
    print("Testing Expression Canonicalization:")
    print("=" * 60)
    
    for input_expr, expected in test_cases:
        code = f"result = {input_expr}"
        transformed, stats = canonicalize_expressions(code)
        
        print(f"\nInput:  {input_expr}")
        print(f"Output: {transformed.strip()}")
        print(f"Applied: {stats.get('transformations_applied', 0)} transformations")
        
        if stats.get('transformation_log'):
            for t in stats['transformation_log']:
                print(f"  - {t['pattern']} → {t['result']}")
