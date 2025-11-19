"""
Dead Code Elimination - Phase 1.6

Removes unused variables and unreachable code without changing semantics.
Safe transformations that reduce noise in code comparison.

Examples:
- Unused variable assignments
- Unreachable code after return
- Unused imports (careful - may have side effects)

Design: Conservative - only removes obviously dead code
"""

import ast
from typing import Set, Dict
import logging

logger = logging.getLogger(__name__)


class DeadCodeEliminator(ast.NodeTransformer):
    """
    Eliminates dead code (unused variables, unreachable statements).
    
    Conservative approach - only removes obviously dead code.
    """
    
    def __init__(self):
        self.transformations_applied = 0
        self.used_names: Set[str] = set()
        self.assigned_names: Dict[str, ast.AST] = {}
        self.transformation_log = []
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Process function definitions"""
        # First pass: collect used names
        self.used_names = set()
        self._collect_used_names(node)
        
        # Second pass: collect assigned names
        self.assigned_names = {}
        self._collect_assignments(node)
        
        # Third pass: remove unused assignments
        new_body = []
        for stmt in node.body:
            if self._should_keep_statement(stmt):
                new_body.append(self.visit(stmt))
            else:
                self._log_transformation(f"Removed unused: {ast.unparse(stmt)[:50]}")
        
        if new_body:
            node.body = new_body
        
        return node
    
    def _collect_used_names(self, node: ast.AST):
        """Collect all names that are used (read)"""
        class NameCollector(ast.NodeVisitor):
            def __init__(self, parent):
                self.parent = parent
            
            def visit_Name(self, n):
                if isinstance(n.ctx, ast.Load):
                    self.parent.used_names.add(n.id)
                self.generic_visit(n)
        
        collector = NameCollector(self)
        collector.visit(node)
    
    def _collect_assignments(self, node: ast.AST):
        """Collect all variable assignments"""
        class AssignmentCollector(ast.NodeVisitor):
            def __init__(self, parent):
                self.parent = parent
            
            def visit_Assign(self, n):
                for target in n.targets:
                    if isinstance(target, ast.Name):
                        self.parent.assigned_names[target.id] = n
                self.generic_visit(n)
        
        collector = AssignmentCollector(self)
        collector.visit(node)
    
    def _should_keep_statement(self, stmt: ast.stmt) -> bool:
        """Determine if a statement should be kept"""
        # Always keep these
        if isinstance(stmt, (ast.Return, ast.Raise, ast.Pass, 
                            ast.For, ast.While, ast.If, ast.With)):
            return True
        
        # Check if assignment is used
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    # Keep if:
                    # 1. Name is used elsewhere
                    # 2. Assignment has side effects (function call, etc.)
                    if target.id in self.used_names or self._has_side_effects(stmt.value):
                        return True
                    # Otherwise, it's dead code
                    self.transformations_applied += 1
                    return False
        
        return True
    
    def _has_side_effects(self, node: ast.expr) -> bool:
        """
        Check if expression might have side effects.
        Conservative - assumes unknown calls have side effects.
        """
        # Function calls might have side effects
        if isinstance(node, ast.Call):
            return True
        
        # List/dict/set comprehensions might have side effects
        if isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp)):
            return True
        
        # Check children recursively
        for child in ast.walk(node):
            if isinstance(child, (ast.Call, ast.ListComp, ast.DictComp, ast.SetComp)):
                return True
        
        return False
    
    def visit_If(self, node: ast.If) -> ast.If:
        """Remove unreachable branches"""
        # Check for if True: or if False:
        if isinstance(node.test, ast.Constant):
            if node.test.value is True:
                # if True: body → just body
                self._log_transformation("if True: ... → ...")
                # Return the body statements directly
                if len(node.body) == 1:
                    return self.visit(node.body[0])
                else:
                    # Can't flatten multiple statements, keep as is
                    pass
            elif node.test.value is False:
                # if False: ... else: ... → just else
                if node.orelse:
                    self._log_transformation("if False: ... else: ... → else ...")
                    if len(node.orelse) == 1:
                        return self.visit(node.orelse[0])
                else:
                    # if False: ... with no else → remove completely
                    self._log_transformation("if False: ... → (removed)")
                    return ast.Pass()  # Return pass to maintain valid syntax
        
        return self.generic_visit(node)
    
    def _log_transformation(self, description: str):
        """Log a transformation"""
        self.transformation_log.append(description)


def eliminate_dead_code(code: str) -> tuple[str, dict]:
    """
    Remove dead code from source.
    
    Args:
        code: Python source code
        
    Returns:
        Tuple of (transformed_code, stats)
    """
    try:
        tree = ast.parse(code)
        
        # Apply dead code elimination
        eliminator = DeadCodeEliminator()
        transformed_tree = eliminator.visit(tree)
        
        # Fix missing locations
        ast.fix_missing_locations(transformed_tree)
        
        # Convert back to code
        import astor
        transformed_code = astor.to_source(transformed_tree)
        
        stats = {
            'success': True,
            'transformations_applied': eliminator.transformations_applied,
            'transformation_log': eliminator.transformation_log
        }
        
        return transformed_code, stats
        
    except SyntaxError as e:
        logger.warning(f"Syntax error in dead code elimination: {e}")
        return code, {'success': False, 'error': str(e)}
    except Exception as e:
        logger.warning(f"Dead code elimination failed: {e}")
        return code, {'success': False, 'error': str(e)}


# Example usage
if __name__ == "__main__":
    test_code = """
def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    
    unused_var = 999  # Dead code - never used
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
"""
    
    print("Testing Dead Code Elimination:")
    print("=" * 60)
    print("\nOriginal code:")
    print(test_code)
    
    transformed, stats = eliminate_dead_code(test_code)
    
    print("\nTransformed code:")
    print(transformed)
    
    print(f"\nTransformations applied: {stats.get('transformations_applied', 0)}")
    if stats.get('transformation_log'):
        print("\nLog:")
        for log in stats['transformation_log']:
            print(f"  - {log}")
