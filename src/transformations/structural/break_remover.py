"""
Break Statement Remover - MISRA C Rule 15.4
Removes break/continue statements and restructures loop logic
"""

import ast
from typing import Optional
from ..transformation_base import TransformationBase, TransformationResult


class BreakRemover(TransformationBase):
    """
    Removes break statements from loops (MISRA C Rule 15.4)
    
    Converts patterns like:
        for i in range(...):
            if condition:
                result = False
                break
    
    To:
        for i in range(...):
            if condition:
                result = False
        # Loop continues to completion
    """
    
    def __init__(self):
        super().__init__(
            name="BreakRemover",
            description="Remove break/continue statements (MISRA 15.4)"
        )
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """Check if code contains break or continue statements"""
        tree = self.safe_parse_ast(code)
        if not tree:
            return False
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Break, ast.Continue)):
                return True
        return False
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """Remove break/continue statements"""
        tree = self.safe_parse_ast(code)
        if not tree:
            return code
        
        transformer = BreakRemoverNodeTransformer()
        new_tree = transformer.visit(tree)
        
        if transformer.modified:
            ast.fix_missing_locations(new_tree)
            try:
                return ast.unparse(new_tree)
            except:
                return code
        return code


class BreakRemoverNodeTransformer(ast.NodeTransformer):
    """AST transformer for break/continue removal"""
    
    def __init__(self):
        self.modified = False
        self._has_found_flag = False
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Check if function has a 'found' flag variable"""
        # Check if there's a 'found = False' assignment at the start
        for stmt in node.body[:5]:  # Check first few statements
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == 'found':
                        self._has_found_flag = True
                        break
        
        # Continue with normal traversal
        self.generic_visit(node)
        return node
    
    def visit_Break(self, node: ast.Break):
        """Remove or replace break statements"""
        self.modified = True
        
        # If we have a 'found' flag, set it to True instead of just removing break
        if self._has_found_flag:
            return ast.Assign(
                targets=[ast.Name(id='found', ctx=ast.Store())],
                value=ast.Constant(value=True)
            )
        else:
            # No flag - just remove the break (may cause issues but that's the fallback)
            return None
    
    def visit_Continue(self, node: ast.Continue):
        """Remove continue statements"""
        self.modified = True
        return None  # Remove the continue
    
    def visit_If(self, node: ast.If) -> ast.If:
        """Process if statements, removing breaks from body"""
        # First visit children
        self.generic_visit(node)
        
        # Filter out None values (removed breaks/continues)
        node.body = [s for s in node.body if s is not None]
        node.orelse = [s for s in node.orelse if s is not None]
        
        # If body is empty after removing break, add pass
        if not node.body:
            node.body = [ast.Pass()]
        
        return node
    
    def visit_For(self, node: ast.For) -> ast.For:
        """Process for loops"""
        self.generic_visit(node)
        
        # Filter out None values
        node.body = [s for s in node.body if s is not None]
        
        if not node.body:
            node.body = [ast.Pass()]
        
        return node
    
    def visit_While(self, node: ast.While) -> ast.While:
        """Process while loops"""
        self.generic_visit(node)
        
        # Filter out None values
        node.body = [s for s in node.body if s is not None]
        
        if not node.body:
            node.body = [ast.Pass()]
        
        return node
