"""
Snap-to-Canon Finalizer - Final normalization pass
Handles harmless differences that don't affect semantics:
- Variable naming
- Whitespace
- Equivalent expressions
- Import order
- Quote style
"""

import ast
import re
from typing import Dict, List, Tuple
from ..transformation_base import TransformationBase


class SnapToCanonFinalizer(TransformationBase):
    """
    Final pass to normalize harmless differences to match canonical form.
    
    This transformer handles:
    1. Variable name normalization (bracket_map → brackets) - respects contract constraints
    2. Whitespace normalization
    3. Equivalent expression normalization (len(x) == 0 → not x)
    4. Return statement normalization
    
    Respects contract's variable_naming constraints:
    - fixed_variables: Must NOT be renamed
    - flexible_variables: Can be renamed to match canon
    - naming_policy: "flexible" allows renaming, "strict" prevents it
    """
    
    def __init__(self, contract: dict = None):
        super().__init__(
            name="SnapToCanonFinalizer",
            description="Normalizes harmless differences to match canon"
        )
        self.contract = contract
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """Check if there are minor differences that can be normalized"""
        
        # Always try as a final pass if there are any property differences
        if property_diffs:
            for diff in property_diffs:
                if diff['distance'] > 0:
                    return True
        
        # Fallback: check for obvious differences
        return code.strip() != canon_code.strip()
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """Apply snap-to-canon normalization"""
        
        self.log_debug("Applying snap-to-canon normalization")
        
        try:
            # Parse both codes
            code_tree = ast.parse(code)
            canon_tree = ast.parse(canon_code)
            
            # Step 1: Extract variable mapping from canon
            canon_vars = self._extract_variable_names(canon_tree)
            code_vars = self._extract_variable_names(code_tree)
            
            self.log_debug(f"Canon variables: {canon_vars}")
            self.log_debug(f"Code variables: {code_vars}")
            
            # Step 2: Create variable mapping (code vars → canon vars)
            var_mapping = self._create_variable_mapping(code_vars, canon_vars)
            
            if var_mapping:
                self.log_debug(f"Variable mapping: {var_mapping}")
                code = self._apply_variable_renaming(code, var_mapping)
            
            # Step 3: Normalize expressions
            code = self._normalize_expressions(code, canon_code)
            
            # Step 4: Normalize whitespace
            code = self._normalize_whitespace(code, canon_code)
            
            self.log_debug("Snap-to-canon normalization complete")
            return code
            
        except Exception as e:
            self.log_debug(f"Snap-to-canon failed: {e}")
            return code  # Return original on error
    
    def _extract_variable_names(self, tree: ast.AST) -> Dict[str, List[str]]:
        """Extract variable names from AST"""
        
        class VarExtractor(ast.NodeVisitor):
            def __init__(self):
                self.function_params = []
                self.local_vars = []
                self.dict_vars = []
                
            def visit_FunctionDef(self, node):
                for arg in node.args.args:
                    self.function_params.append(arg.arg)
                self.generic_visit(node)
            
            def visit_Assign(self, node):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.local_vars.append(target.id)
                    elif isinstance(target, ast.Tuple):
                        for elt in target.elts:
                            if isinstance(elt, ast.Name):
                                self.local_vars.append(elt.id)
                
                # Check if it's a dict assignment
                if isinstance(node.value, ast.Dict):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.dict_vars.append(target.id)
                
                self.generic_visit(node)
        
        extractor = VarExtractor()
        extractor.visit(tree)
        
        return {
            'params': extractor.function_params,
            'locals': extractor.local_vars,
            'dicts': extractor.dict_vars
        }
    
    def _create_variable_mapping(self, code_vars: Dict, canon_vars: Dict) -> Dict[str, str]:
        """Create mapping from code variables to canon variables (respects contract constraints)"""
        
        mapping = {}
        
        # Get contract constraints
        fixed_vars, flexible_vars, naming_policy = self._get_naming_constraints()
        
        # If naming policy is strict, don't rename anything
        if naming_policy == "strict":
            self.log_debug("Naming policy is strict - no variable renaming allowed")
            return mapping
        
        # Map dictionary variables (e.g., bracket_map → brackets)
        if code_vars['dicts'] and canon_vars['dicts']:
            if len(code_vars['dicts']) == len(canon_vars['dicts']):
                for code_var, canon_var in zip(code_vars['dicts'], canon_vars['dicts']):
                    if code_var != canon_var:
                        # Check if variable is allowed to be renamed
                        if self._can_rename_variable(code_var, fixed_vars, flexible_vars):
                            mapping[code_var] = canon_var
                            self.log_debug(f"Mapping dict variable: {code_var} → {canon_var}")
                        else:
                            self.log_debug(f"Skipping fixed variable: {code_var}")
        
        # Map local variables (match by position/usage)
        # Only map if names are similar (e.g., both contain 'stack', 'bracket', etc.)
        code_locals = [v for v in code_vars['locals'] if v not in code_vars['params']]
        canon_locals = [v for v in canon_vars['locals'] if v not in canon_vars['params']]
        
        if code_locals and canon_locals:
            for code_var in code_locals:
                for canon_var in canon_locals:
                    # Match if they share common substrings
                    if (self._vars_similar(code_var, canon_var) and 
                        code_var != canon_var and
                        code_var not in mapping):
                        # Check if variable is allowed to be renamed
                        if self._can_rename_variable(code_var, fixed_vars, flexible_vars):
                            mapping[code_var] = canon_var
                            self.log_debug(f"Mapping local variable: {code_var} → {canon_var}")
                            break
                        else:
                            self.log_debug(f"Skipping fixed variable: {code_var}")
        
        return mapping
    
    def _get_naming_constraints(self) -> Tuple[List[str], List[str], str]:
        """Extract variable naming constraints from contract"""
        
        if not self.contract:
            return [], [], "flexible"
        
        constraints = self.contract.get("constraints", {})
        var_naming = constraints.get("variable_naming", {})
        
        fixed_vars = var_naming.get("fixed_variables", [])
        flexible_vars = var_naming.get("flexible_variables", [])
        naming_policy = var_naming.get("naming_policy", "flexible")
        
        return fixed_vars, flexible_vars, naming_policy
    
    def _can_rename_variable(self, var_name: str, fixed_vars: List[str], flexible_vars: List[str]) -> bool:
        """Check if a variable can be renamed according to contract constraints"""
        
        # If variable is in fixed list, cannot rename
        if var_name in fixed_vars:
            return False
        
        # If flexible list is specified and variable is in it, can rename
        if flexible_vars and var_name in flexible_vars:
            return True
        
        # If flexible list is specified but variable is not in it, cannot rename
        if flexible_vars:
            return False
        
        # If no lists specified, allow renaming (default flexible)
        return True
    
    def _vars_similar(self, var1: str, var2: str) -> bool:
        """Check if two variable names are semantically similar"""
        
        # Same base words (bracket, stack, etc.)
        common_words = ['bracket', 'stack', 'map', 'dict', 'list', 'arr', 'result']
        
        for word in common_words:
            if word in var1.lower() and word in var2.lower():
                return True
        
        # Both are single letters
        if len(var1) == 1 and len(var2) == 1:
            return True
        
        return False
    
    def _apply_variable_renaming(self, code: str, mapping: Dict[str, str]) -> str:
        """Rename variables in code according to mapping"""
        
        if not mapping:
            return code
        
        # Use word boundaries to avoid partial matches
        for old_name, new_name in mapping.items():
            # Match whole words only
            pattern = r'\b' + re.escape(old_name) + r'\b'
            code = re.sub(pattern, new_name, code)
        
        return code
    
    def _normalize_expressions(self, code: str, canon_code: str) -> str:
        """Normalize equivalent expressions"""
        
        # Check if canon uses 'not x' pattern for return
        if re.search(r'return\s+not\s+\w+', canon_code):
            # Replace 'return len(x) == 0' with 'return not x'
            code = re.sub(r'return\s+len\((\w+)\)\s*==\s*0', r'return not \1', code)
            # Replace 'return len(x) != 0' with 'return x' (though less common)
            code = re.sub(r'return\s+len\((\w+)\)\s*!=\s*0', r'return \1', code)
        
        # Check if canon uses 'len(x) == 0' pattern for return
        elif re.search(r'return\s+len\(\w+\)\s*==\s*0', canon_code):
            # Replace 'return not x' with 'return len(x) == 0'
            code = re.sub(r'return\s+not\s+(\w+)', r'return len(\1) == 0', code)
        
        # Also handle inline conditions (not just returns)
        if 'not stack' in canon_code:
            # Replace len(x) == 0 with not x (for any context)
            code = re.sub(r'len\((\w+)\)\s*==\s*0', r'not \1', code)
        
        return code
    
    def _normalize_whitespace(self, code: str, canon_code: str) -> str:
        """Normalize whitespace to match canon style"""
        
        # Count blank lines in canon
        canon_lines = canon_code.split('\n')
        code_lines = code.split('\n')
        
        # Normalize blank lines between statements
        # Remove excessive blank lines (more than 1 consecutive)
        normalized_lines = []
        prev_blank = False
        
        for line in code_lines:
            is_blank = line.strip() == ''
            
            if is_blank:
                if not prev_blank:
                    normalized_lines.append(line)
                prev_blank = True
            else:
                normalized_lines.append(line)
                prev_blank = False
        
        code = '\n'.join(normalized_lines)
        
        # Normalize trailing whitespace
        code = '\n'.join(line.rstrip() for line in code.split('\n'))
        
        return code
