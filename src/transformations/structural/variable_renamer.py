"""
Variable Renamer - Structural Transformation
Systematically renames variables to match canonical form using AST analysis

This is the CRITICAL transformer for handling cases like:
- left_half, right_half → left, right
- sorted_list → result  
- left_index, right_index → i, j
"""

import ast
import re
from typing import Dict, Set
from ..transformation_base import TransformationBase


class VariableRenamer(TransformationBase):
    """Renames variables to match canonical form"""
    
    def __init__(self):
        super().__init__(
            name="VariableRenamer",
            description="Systematically renames variables to match canonical naming"
        )
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """Check if variable names differ (PROPERTY-DRIVEN)"""
        
        # Use normalized_ast_structure property - if alpha-renamed hashes match but
        # regular hashes don't, it means only variable names differ
        if property_diffs:
            for diff in property_diffs:
                if diff['property'] == 'normalized_ast_structure':
                    curr = diff.get('current_value', {})
                    canon = diff.get('canon_value', {})
                    
                    # Check if structures match when alpha-renamed but differ otherwise
                    alpha_curr = curr.get('alpha_renamed_hash')
                    alpha_canon = canon.get('alpha_renamed_hash')
                    hash_curr = curr.get('ast_hash')
                    hash_canon = canon.get('ast_hash')
                    
                    if alpha_curr == alpha_canon and hash_curr != hash_canon:
                        self.log_debug("Variable names differ but structure matches!")
                        return True
        
        # Fallback: simple check for common variable pattern differences
        return self._has_variable_differences(code, canon_code)
    
    def _has_variable_differences(self, code: str, canon_code: str) -> bool:
        """Simple heuristic check for variable differences"""
        code_vars = set(re.findall(r'\b[a-z_][a-z0-9_]*\b', code))
        canon_vars = set(re.findall(r'\b[a-z_][a-z0-9_]*\b', canon_code))
        
        # Filter out keywords and built-ins
        keywords = {'if', 'else', 'for', 'while', 'def', 'return', 'len', 'range', 'in', 'and', 'or', 'not'}
        code_vars -= keywords
        canon_vars -= keywords
        
        # If there's significant difference in variable names
        overlap = len(code_vars & canon_vars)
        total = len(code_vars | canon_vars)
        
        return total > 0 and (overlap / total) < 0.7  # Less than 70% overlap
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """Apply variable renaming transformation"""
        
        self.log_debug("Applying systematic variable renaming")
        
        try:
            # Extract variable mapping from canon
            canon_var_map = self._extract_variable_structure(canon_code)
            code_var_map = self._extract_variable_structure(code)
            
            self.log_debug(f"Canon variables: {canon_var_map}")
            self.log_debug(f"Code variables: {code_var_map}")
            
            # Build rename mapping based on position/role
            rename_map = self._build_rename_mapping(code_var_map, canon_var_map)
            
            if not rename_map:
                self.log_debug("No rename mapping could be built")
                return code
            
            self.log_debug(f"Rename mapping: {rename_map}")
            
            # Apply renaming
            renamed_code = self._apply_rename_mapping(code, rename_map)
            
            return renamed_code
            
        except Exception as e:
            self.log_debug(f"Variable renaming failed: {e}")
            return code
    
    def _extract_variable_structure(self, code: str) -> Dict[str, list]:
        """Extract variables categorized by their role"""
        try:
            tree = ast.parse(code)
        except:
            return {}
        
        structure = {
            'parameters': [],
            'local_vars': [],
            'loop_vars': []
        }
        
        class VarExtractor(ast.NodeVisitor):
            def __init__(self):
                self.in_function = False
                self.current_function = None
                
            def visit_FunctionDef(self, node):
                # Extract parameters
                for arg in node.args.args:
                    if arg.arg not in structure['parameters']:
                        structure['parameters'].append(arg.arg)
                
                old_function = self.current_function
                self.current_function = node.name
                self.in_function = True
                self.generic_visit(node)
                self.current_function = old_function
                self.in_function = False
            
            def visit_Assign(self, node):
                if self.in_function:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if target.id not in structure['local_vars'] and target.id not in structure['parameters']:
                                structure['local_vars'].append(target.id)
                        elif isinstance(target, ast.Tuple):
                            for elt in target.elts:
                                if isinstance(elt, ast.Name):
                                    if elt.id not in structure['local_vars'] and elt.id not in structure['parameters']:
                                        structure['local_vars'].append(elt.id)
                self.generic_visit(node)
            
            def visit_For(self, node):
                if isinstance(node.target, ast.Name):
                    if node.target.id not in structure['loop_vars']:
                        structure['loop_vars'].append(node.target.id)
                self.generic_visit(node)
        
        extractor = VarExtractor()
        extractor.visit(tree)
        
        return structure
    
    def _build_rename_mapping(self, code_vars: Dict, canon_vars: Dict) -> Dict[str, str]:
        """Build mapping from code variables to canon variables by position"""
        mapping = {}
        
        # Map parameters by position
        for i, code_param in enumerate(code_vars.get('parameters', [])):
            if i < len(canon_vars.get('parameters', [])):
                canon_param = canon_vars['parameters'][i]
                if code_param != canon_param:
                    mapping[code_param] = canon_param
        
        # Map local variables by position (heuristic)
        for i, code_var in enumerate(code_vars.get('local_vars', [])):
            if i < len(canon_vars.get('local_vars', [])):
                canon_var = canon_vars['local_vars'][i]
                if code_var != canon_var and code_var not in mapping:
                    mapping[code_var] = canon_var
        
        # Map loop variables by position
        for i, code_var in enumerate(code_vars.get('loop_vars', [])):
            if i < len(canon_vars.get('loop_vars', [])):
                canon_var = canon_vars['loop_vars'][i]
                if code_var != canon_var and code_var not in mapping:
                    mapping[code_var] = canon_var
        
        return mapping
    
    def _apply_rename_mapping(self, code: str, rename_map: Dict[str, str]) -> str:
        """Apply variable renaming using AST transformation"""
        try:
            tree = ast.parse(code)
        except:
            return code
        
        class VariableRenamer(ast.NodeTransformer):
            def __init__(self, mapping):
                self.mapping = mapping
            
            def visit_Name(self, node):
                if node.id in self.mapping:
                    node.id = self.mapping[node.id]
                return node
            
            def visit_arg(self, node):
                if node.arg in self.mapping:
                    node.arg = self.mapping[node.arg]
                return node
        
        renamer = VariableRenamer(rename_map)
        new_tree = renamer.visit(tree)
        
        # Convert back to code
        try:
            return ast.unparse(new_tree)
        except:
            # Python < 3.9 fallback
            import astor
            return astor.to_source(new_tree)
