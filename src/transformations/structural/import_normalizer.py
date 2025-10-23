"""
Import Normalizer - Structural Transformation
Adds missing import statements to match canonical form

Handles cases like:
- Missing imports (e.g., OrderedDict for LRU Cache)
- Different import styles (from X import Y vs import X.Y)
- Import ordering
"""

import ast
from typing import Set, Tuple, Optional
from ..transformation_base import TransformationBase


class ImportNormalizer(TransformationBase):
    """Normalizes import statements to match canon"""
    
    def __init__(self):
        super().__init__(
            name="ImportNormalizer",
            description="Adds missing imports and normalizes import statements"
        )
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """Check if imports differ"""
        
        try:
            code_tree = ast.parse(code)
            canon_tree = ast.parse(canon_code)
            
            # Extract imports from both
            code_imports = self._extract_imports(code_tree)
            canon_imports = self._extract_imports(canon_tree)
            
            # Check if canon has imports that code doesn't
            missing_imports = canon_imports - code_imports
            
            if missing_imports:
                self.log_debug(f"Missing imports: {missing_imports}")
                return True
            
            # Check property diffs for statement ordering differences
            if property_diffs:
                for diff in property_diffs:
                    if diff['property'] == 'statement_ordering':
                        # Check if it involves imports
                        curr = diff.get('current_value', {})
                        canon = diff.get('canon_value', {})
                        
                        curr_types = curr.get('statement_types', [])
                        canon_types = canon.get('statement_types', [])
                        
                        # If canon has Import/ImportFrom but code doesn't
                        has_import_diff = (
                            ('Import' in canon_types or 'ImportFrom' in canon_types) and
                            curr_types != canon_types
                        )
                        
                        if has_import_diff:
                            self.log_debug("Import statement differences detected")
                            return True
            
            return False
            
        except Exception as e:
            self.log_debug(f"Error checking imports: {e}")
            return False
    
    def _extract_imports(self, tree: ast.AST) -> Set[Tuple]:
        """
        Extract set of import statements from AST
        
        Returns:
            Set of tuples representing imports:
            - ('import', module_name, alias) for import statements
            - ('from', module_name, name, alias) for from imports
        """
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(('import', alias.name, alias.asname))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.add(('from', module, alias.name, alias.asname))
        
        return imports
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """Apply import normalization"""
        
        self.log_debug("Applying import normalization")
        
        try:
            code_tree = ast.parse(code)
            canon_tree = ast.parse(canon_code)
            
            # Extract imports
            code_imports = self._extract_imports(code_tree)
            canon_imports = self._extract_imports(canon_tree)
            
            # Find missing imports
            missing_imports = canon_imports - code_imports
            
            if not missing_imports:
                self.log_debug("No missing imports to add")
                return code
            
            self.log_debug(f"Adding missing imports: {missing_imports}")
            
            # Create import nodes for missing imports
            import_nodes = []
            for imp in missing_imports:
                if imp[0] == 'import':
                    # import X as Y
                    _, module_name, alias = imp
                    import_node = ast.Import(
                        names=[ast.alias(name=module_name, asname=alias)]
                    )
                    import_nodes.append(import_node)
                elif imp[0] == 'from':
                    # from X import Y as Z
                    _, module_name, name, alias = imp
                    import_node = ast.ImportFrom(
                        module=module_name if module_name else None,
                        names=[ast.alias(name=name, asname=alias)],
                        level=0
                    )
                    import_nodes.append(import_node)
            
            # Add import nodes at the beginning of the module
            code_tree.body = import_nodes + code_tree.body
            
            # Fix missing locations
            ast.fix_missing_locations(code_tree)
            
            # Convert back to code
            transformed_code = ast.unparse(code_tree)
            
            self.log_debug("Import normalization successful")
            return transformed_code
            
        except Exception as e:
            self.log_debug(f"Import normalization failed: {e}")
            return code
