"""
Redundant Clause Remover - Structural Transformation
Removes unnecessary else/elif clauses that don't affect behavior

Handles patterns like:
- if condition: return X elif condition2: return Y else: ... -> if condition: return X elif condition2: return Y ...
- Nested redundant conditions
"""

import ast
from typing import List
from ..transformation_base import TransformationBase


class RedundantClauseRemover(TransformationBase):
    """Removes redundant else/elif clauses"""
    
    def __init__(self):
        super().__init__(
            name="RedundantClauseRemover", 
            description="Removes unnecessary else/elif clauses"
        )
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """Check if code has redundant clauses that canon doesn't have"""
        
        # Simple heuristic: check for else clauses
        code_has_else = ' else:' in code or '\telse:' in code
        canon_has_else = ' else:' in canon_code or '\telse:' in canon_code
        
        # Transform if code has else but canon doesn't
        return code_has_else and not canon_has_else
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """Remove redundant else clauses"""
        
        self.log_debug("Applying redundant clause removal")
        
        # Try AST-based approach first
        try:
            transformed = self._ast_based_removal(code)
            if transformed != code:
                return transformed
        except Exception as e:
            self.log_debug(f"AST approach failed: {e}")
        
        # Fallback to line-based approach
        return self._line_based_removal(code)
    
    def _ast_based_removal(self, code: str) -> str:
        """Use AST to remove redundant else clauses"""
        
        tree = ast.parse(code)
        
        class RedundantElseRemover(ast.NodeTransformer):
            def visit_If(self, node):
                # Process nested nodes first
                self.generic_visit(node)
                
                # Check for redundant else after if/elif with returns
                if node.orelse and not isinstance(node.orelse[0], ast.If):
                    # This is an else clause, check if it's redundant
                    if self._has_return_in_all_branches(node):
                        self.log_debug("Removing redundant else clause")
                        node.orelse = []
                
                return node
            
            def _has_return_in_all_branches(self, if_node):
                """Check if all if/elif branches have return statements"""
                
                # Check main if branch
                if not self._branch_has_return(if_node.body):
                    return False
                
                # Check elif branches
                current = if_node
                while current.orelse and isinstance(current.orelse[0], ast.If):
                    elif_node = current.orelse[0]
                    if not self._branch_has_return(elif_node.body):
                        return False
                    current = elif_node
                
                return True
            
            def _branch_has_return(self, body):
                """Check if a branch has a return statement"""
                for stmt in body:
                    if isinstance(stmt, ast.Return):
                        return True
                return False
        
        remover = RedundantElseRemover()
        transformed_tree = remover.visit(tree)
        
        import astor
        return astor.to_source(transformed_tree)
    
    def _line_based_removal(self, code: str) -> str:
        """Simple line-based redundant else removal"""
        
        lines = code.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Look for else clauses
            if stripped == 'else:':
                # Check if this else is redundant
                if self._is_redundant_else(lines, i):
                    self.log_debug(f"Removing redundant else at line {i}")
                    # Skip the else line and move its content up one level
                    i += 1
                    
                    # Add the else body content with reduced indentation
                    while i < len(lines) and (lines[i].startswith('    ') or lines[i].strip() == ''):
                        if lines[i].strip():  # Skip empty lines
                            # Reduce indentation by 4 spaces
                            content = lines[i][4:] if lines[i].startswith('    ') else lines[i]
                            result_lines.append(content)
                        i += 1
                    continue
                else:
                    result_lines.append(line)
            else:
                result_lines.append(line)
            
            i += 1
        
        return '\n'.join(result_lines)
    
    def _is_redundant_else(self, lines: List[str], else_index: int) -> bool:
        """Check if an else clause is redundant"""
        
        # Look backwards to find the if/elif structure
        current_indent = len(lines[else_index]) - len(lines[else_index].lstrip())
        
        # Check previous branches for returns
        has_returns_in_all_branches = True
        
        for i in range(else_index - 1, -1, -1):
            line = lines[i]
            line_indent = len(line) - len(line.lstrip())
            stripped = line.strip()
            
            # Stop when we reach the same indentation level with if/elif
            if (line_indent == current_indent and 
                (stripped.startswith('if ') or stripped.startswith('elif '))):
                
                # Check if this branch has a return
                branch_has_return = self._branch_has_return_simple(lines, i)
                if not branch_has_return:
                    has_returns_in_all_branches = False
                    break
                
                # If this is the main if, we're done checking
                if stripped.startswith('if '):
                    break
            
            # Stop if we've gone too far back
            elif line_indent < current_indent:
                break
        
        return has_returns_in_all_branches
    
    def _branch_has_return_simple(self, lines: List[str], branch_start: int) -> bool:
        """Check if a branch has a return statement (simple version)"""
        
        branch_indent = len(lines[branch_start]) - len(lines[branch_start].lstrip())
        
        # Look forward in this branch for return statements
        for i in range(branch_start + 1, len(lines)):
            line = lines[i]
            line_indent = len(line) - len(line.lstrip())
            stripped = line.strip()
            
            # If we've reached the same or lower indentation, we're out of this branch
            if stripped and line_indent <= branch_indent:
                break
            
            # Check for return statement
            if stripped.startswith('return '):
                return True
        
        return False
