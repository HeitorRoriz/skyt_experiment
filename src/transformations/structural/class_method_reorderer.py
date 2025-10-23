"""
Class Method Reorderer - Structural Transformation
Reorders class methods to match canonical order

Handles cases like:
- Methods defined in different orders (put before get, etc.)
- Ensures consistent method ordering across implementations
"""

import ast
from typing import List, Tuple
from ..transformation_base import TransformationBase


class ClassMethodReorderer(TransformationBase):
    """Reorders class methods to canonical order"""
    
    # Canonical method order (special methods first, then alphabetically)
    CANONICAL_METHOD_ORDER = [
        '__new__',
        '__init__',
        '__del__',
        '__repr__',
        '__str__',
        '__bytes__',
        '__format__',
        '__lt__',
        '__le__',
        '__eq__',
        '__ne__',
        '__gt__',
        '__ge__',
        '__hash__',
        '__bool__',
        '__getattr__',
        '__getattribute__',
        '__setattr__',
        '__delattr__',
        '__dir__',
        '__get__',
        '__set__',
        '__delete__',
        '__call__',
        '__len__',
        '__getitem__',
        '__setitem__',
        '__delitem__',
        '__iter__',
        '__next__',
        '__reversed__',
        '__contains__',
    ]
    
    def __init__(self):
        super().__init__(
            name="ClassMethodReorderer",
            description="Reorders class methods to canonical order"
        )
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """Check if method ordering differs"""
        
        try:
            code_tree = ast.parse(code)
            canon_tree = ast.parse(canon_code)
            
            # Extract method orders from both
            code_methods = self._extract_method_order(code_tree)
            canon_methods = self._extract_method_order(canon_tree)
            
            # If no classes or methods, no transformation needed
            if not code_methods or not canon_methods:
                return False
            
            # Check if method orders differ
            if code_methods != canon_methods:
                self.log_debug(f"Method order differs: {code_methods} vs {canon_methods}")
                return True
            
            # Check property diffs for statement ordering differences
            if property_diffs:
                for diff in property_diffs:
                    if diff['property'] == 'statement_ordering':
                        # Check if it's specifically about method ordering
                        curr = diff.get('current_value', {})
                        canon = diff.get('canon_value', {})
                        
                        curr_types = curr.get('statement_types', [])
                        canon_types = canon.get('statement_types', [])
                        
                        # If there are FunctionDef statements in different positions
                        if 'FunctionDef' in curr_types and 'FunctionDef' in canon_types:
                            if curr_types != canon_types:
                                self.log_debug("Statement ordering difference includes methods")
                                return True
            
            return False
            
        except Exception as e:
            self.log_debug(f"Error checking method ordering: {e}")
            return False
    
    def _extract_method_order(self, tree: ast.AST) -> List[Tuple[str, str]]:
        """
        Extract method order from AST
        
        Returns:
            List of (class_name, method_name) tuples in order
        """
        method_order = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_order.append((class_name, item.name))
        
        return method_order
    
    def _get_method_priority(self, method_name: str) -> Tuple[int, int, str]:
        """
        Get sort priority for a method
        
        Returns:
            (priority_group, canonical_index, method_name) tuple
            - priority_group: 0 for special methods in canonical order, 1 for others
            - canonical_index: index in canonical order or 0 for alphabetical
            - method_name: for alphabetical sorting within group
        """
        if method_name in self.CANONICAL_METHOD_ORDER:
            return (0, self.CANONICAL_METHOD_ORDER.index(method_name), method_name)
        else:
            # Non-special methods sorted alphabetically
            return (1, 0, method_name)
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """Apply method reordering transformation"""
        
        self.log_debug("Applying class method reordering")
        
        try:
            tree = ast.parse(code)
            
            # Apply reordering
            reorderer = MethodReorderer(self)
            new_tree = reorderer.visit(tree)
            
            # Fix missing locations
            ast.fix_missing_locations(new_tree)
            
            # Convert back to code
            transformed_code = ast.unparse(new_tree)
            
            self.log_debug("Method reordering successful")
            return transformed_code
            
        except Exception as e:
            self.log_debug(f"Method reordering failed: {e}")
            return code


class MethodReorderer(ast.NodeTransformer):
    """AST transformer for method reordering"""
    
    def __init__(self, reorderer: ClassMethodReorderer):
        self.reorderer = reorderer
    
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Visit class definitions and reorder methods"""
        
        # First, recursively visit children
        self.generic_visit(node)
        
        # Separate methods from other class members
        methods = []
        other_members = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item)
            else:
                other_members.append(item)
        
        # Sort methods by canonical order
        methods.sort(key=lambda m: self.reorderer._get_method_priority(m.name))
        
        # Reconstruct body: other members first, then sorted methods
        node.body = other_members + methods
        
        return node
