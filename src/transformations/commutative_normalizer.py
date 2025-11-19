"""
Commutative Operation Normalization - Phase 1.6

Normalizes commutative operations to canonical order.
Reduces false differences from operand ordering.

Examples:
- a + b vs b + a → sorted alphabetically
- a * b vs b * a → sorted alphabetically
- a == b vs b == a → sorted alphabetically

Design: Sort operands by a canonical key (AST structure, then alphabetically)
"""

import ast
from typing import Any
import logging

logger = logging.getLogger(__name__)


class CommutativeNormalizer(ast.NodeTransformer):
    """
    Normalizes commutative operations to canonical order.
    
    This eliminates differences like (a + b) vs (b + a).
    """
    
    def __init__(self):
        self.transformations_applied = 0
        self.transformation_log = []
    
    def visit_BinOp(self, node: ast.BinOp) -> ast.BinOp:
        """Normalize commutative binary operations"""
        # First, recursively transform children
        node = self.generic_visit(node)
        
        # Check if operation is commutative
        if self._is_commutative(node.op):
            # Sort operands by canonical key
            left_key = self._node_sort_key(node.left)
            right_key = self._node_sort_key(node.right)
            
            if right_key < left_key:
                # Swap operands
                node.left, node.right = node.right, node.left
                self._log_transformation(f"Normalized commutative: {ast.unparse(node)}")
        
        return node
    
    def visit_Compare(self, node: ast.Compare) -> ast.Compare:
        """Normalize commutative comparisons"""
        # First, recursively transform children
        node = self.generic_visit(node)
        
        # Only handle single comparisons (not chained)
        if len(node.ops) == 1 and len(node.comparators) == 1:
            op = node.ops[0]
            
            # Check if comparison is commutative
            if self._is_commutative_comparison(op):
                left_key = self._node_sort_key(node.left)
                right_key = self._node_sort_key(node.comparators[0])
                
                if right_key < left_key:
                    # Swap operands
                    node.left, node.comparators[0] = node.comparators[0], node.left
                    self._log_transformation(f"Normalized comparison: {ast.unparse(node)}")
        
        return node
    
    def _is_commutative(self, op: ast.operator) -> bool:
        """Check if binary operator is commutative"""
        return isinstance(op, (
            ast.Add,      # a + b = b + a
            ast.Mult,     # a * b = b * a
            ast.BitOr,    # a | b = b | a
            ast.BitXor,   # a ^ b = b ^ a
            ast.BitAnd,   # a & b = b & a
        ))
    
    def _is_commutative_comparison(self, op: ast.cmpop) -> bool:
        """Check if comparison operator is commutative"""
        return isinstance(op, (
            ast.Eq,       # a == b = b == a
            ast.NotEq,    # a != b = b != a
        ))
        # Note: <, >, <=, >= are NOT commutative
    
    def _node_sort_key(self, node: ast.expr) -> tuple:
        """
        Generate a canonical sort key for an AST node.
        
        Returns tuple: (priority, name/value, structure)
        This ensures consistent ordering across equivalent expressions.
        """
        # Priority order: constants < names < complex expressions
        if isinstance(node, ast.Constant):
            # Constants first, sorted by value
            return (0, str(node.value), "")
        
        elif isinstance(node, ast.Name):
            # Names second, sorted alphabetically
            return (1, node.id, "")
        
        elif isinstance(node, ast.BinOp):
            # Binary operations, sorted by unparsed form
            try:
                unparsed = ast.unparse(node)
                return (2, unparsed, "binop")
            except:
                return (2, "", "binop")
        
        elif isinstance(node, ast.Call):
            # Function calls
            try:
                if isinstance(node.func, ast.Name):
                    return (3, node.func.id, "call")
                else:
                    return (3, ast.unparse(node.func), "call")
            except:
                return (3, "", "call")
        
        else:
            # Everything else, try to unparse
            try:
                unparsed = ast.unparse(node)
                return (4, unparsed, type(node).__name__)
            except:
                return (5, "", type(node).__name__)
    
    def _log_transformation(self, description: str):
        """Log a transformation"""
        self.transformations_applied += 1
        self.transformation_log.append(description)


def normalize_commutative(code: str) -> tuple[str, dict]:
    """
    Normalize commutative operations to canonical order.
    
    Args:
        code: Python source code
        
    Returns:
        Tuple of (transformed_code, stats)
    """
    try:
        tree = ast.parse(code)
        
        # Apply commutative normalization
        normalizer = CommutativeNormalizer()
        transformed_tree = normalizer.visit(tree)
        
        # Fix missing locations
        ast.fix_missing_locations(transformed_tree)
        
        # Convert back to code
        import astor
        transformed_code = astor.to_source(transformed_tree)
        
        stats = {
            'success': True,
            'transformations_applied': normalizer.transformations_applied,
            'transformation_log': normalizer.transformation_log
        }
        
        return transformed_code, stats
        
    except SyntaxError as e:
        logger.warning(f"Syntax error in commutative normalization: {e}")
        return code, {'success': False, 'error': str(e)}
    except Exception as e:
        logger.warning(f"Commutative normalization failed: {e}")
        return code, {'success': False, 'error': str(e)}


# Example usage
if __name__ == "__main__":
    test_cases = [
        "result = b + a",  # Should normalize to a + b
        "result = y * x",  # Should normalize to x * y
        "result = b == a",  # Should normalize to a == b
        "result = 5 + x",  # Should stay 5 + x (constant first)
        "result = z + 1",  # Should normalize to 1 + z
    ]
    
    print("Testing Commutative Normalization:")
    print("=" * 60)
    
    for test_code in test_cases:
        print(f"\nOriginal:  {test_code}")
        transformed, stats = normalize_commutative(test_code)
        print(f"Transformed: {transformed.strip()}")
        print(f"Applied: {stats.get('transformations_applied', 0)} transformations")
        
        if stats.get('transformation_log'):
            for log in stats['transformation_log']:
                print(f"  - {log}")
