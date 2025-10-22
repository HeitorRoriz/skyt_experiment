"""
Statement Chain Normalizer - Normalizes chained method calls vs separate statements
Handles differences like `x = y.strip()` vs `x = y; x = x.strip()`
"""

import ast
import logging
from typing import Optional
from .transformation_base import TransformationBase

logger = logging.getLogger(__name__)


class StatementChainNormalizer(TransformationBase):
    """
    A transformer that normalizes statement chains to match the canon.
    Converts between chained calls and separate statements.
    """
    
    def __init__(self):
        super().__init__(
            name="StatementChainNormalizer",
            description="Normalizes chained method calls to match canonical form"
        )
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """
        Check if statement chain normalization is needed.
        """
        if not canon_code:
            return False
        
        try:
            # Simple heuristic: check if there are differences in chaining patterns
            code_has_chains = '.strip(' in code and ').strip(' in code
            canon_has_chains = '.strip(' in canon_code and ').strip(' in canon_code
            
            # If patterns differ, transformation might be needed
            return code_has_chains != canon_has_chains
        except Exception as e:
            if self.debug_mode:
                logger.warning(f"Error in can_transform: {e}")
            return False
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """
        Apply statement chain normalization.
        This is a simple implementation that handles common cases.
        """
        try:
            # Parse both to understand the pattern
            code_tree = ast.parse(code)
            canon_tree = ast.parse(canon_code)
            
            # Check if canon uses separate statements or chained calls
            canon_uses_chain = self._uses_chained_strip(canon_tree)
            code_uses_chain = self._uses_chained_strip(code_tree)
            
            if canon_uses_chain and not code_uses_chain:
                # Convert separate statements to chain
                new_code = self._convert_to_chain(code)
                return new_code if new_code != code else code
            elif not canon_uses_chain and code_uses_chain:
                # Convert chain to separate statements
                new_code = self._convert_to_separate(code)
                return new_code if new_code != code else code
            
            return code
        
        except Exception as e:
            error_msg = f"Error in statement chain normalization: {str(e)}"
            if self.debug_mode:
                logger.error(error_msg)
            return code
    
    def _uses_chained_strip(self, tree: ast.AST) -> bool:
        """Check if code uses chained .strip() calls"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for pattern like: re.sub(...).strip(...)
                if (isinstance(node.func, ast.Attribute) and
                    node.func.attr == 'strip' and
                    isinstance(node.func.value, ast.Call)):
                    return True
        return False
    
    def _convert_to_chain(self, code: str) -> str:
        """
        Convert separate strip() statement to chained call.
        Example: text = re.sub(...); return text.strip('-')
        To: text = re.sub(...).strip('-'); return text
        """
        try:
            tree = ast.parse(code)
            
            class ChainConverter(ast.NodeTransformer):
                def __init__(self):
                    self.modified = False
                    self.last_assign = None
                    self.last_assign_target = None
                
                def visit_FunctionDef(self, node):
                    new_body = []
                    i = 0
                    while i < len(node.body):
                        stmt = node.body[i]
                        
                        # Check for pattern: assign + return with strip
                        if (isinstance(stmt, ast.Assign) and
                            i + 1 < len(node.body) and
                            isinstance(node.body[i + 1], ast.Return)):
                            
                            next_stmt = node.body[i + 1]
                            assign_target = stmt.targets[0].id if isinstance(stmt.targets[0], ast.Name) else None
                            
                            # Check if return uses .strip() on the assigned variable
                            if (assign_target and isinstance(next_stmt.value, ast.Call) and
                                isinstance(next_stmt.value.func, ast.Attribute) and
                                next_stmt.value.func.attr == 'strip' and
                                isinstance(next_stmt.value.func.value, ast.Name) and
                                next_stmt.value.func.value.id == assign_target):
                                
                                # Chain the strip to the assignment
                                new_assign_value = ast.Call(
                                    func=ast.Attribute(
                                        value=stmt.value,
                                        attr='strip',
                                        ctx=ast.Load()
                                    ),
                                    args=next_stmt.value.args,
                                    keywords=next_stmt.value.keywords
                                )
                                stmt.value = new_assign_value
                                new_body.append(stmt)
                                
                                # Update return to just return the variable
                                new_return = ast.Return(value=ast.Name(id=assign_target, ctx=ast.Load()))
                                new_body.append(new_return)
                                self.modified = True
                                i += 2
                                continue
                        
                        new_body.append(self.visit(stmt))
                        i += 1
                    
                    node.body = new_body
                    return node
            
            converter = ChainConverter()
            new_tree = converter.visit(tree)
            
            if converter.modified:
                return ast.unparse(new_tree)
            return code
        
        except Exception as e:
            if self.debug_mode:
                logger.error(f"Error converting to chain: {e}")
            return code
    
    def _convert_to_separate(self, code: str) -> str:
        """
        Convert chained strip() to separate statement.
        Example: text = re.sub(...).strip('-'); return text
        To: text = re.sub(...); return text.strip('-')
        """
        try:
            tree = ast.parse(code)
            
            class SeparateConverter(ast.NodeTransformer):
                def __init__(self):
                    self.modified = False
                
                def visit_Assign(self, node):
                    # Check for chained .strip() in assignment
                    if (isinstance(node.value, ast.Call) and
                        isinstance(node.value.func, ast.Attribute) and
                        node.value.func.attr == 'strip' and
                        isinstance(node.value.func.value, ast.Call)):
                        
                        # Split into two statements
                        # This is complex, so for now just return as-is
                        pass
                    
                    return node
            
            # For now, return unchanged (this is complex to implement correctly)
            return code
        
        except Exception as e:
            if self.debug_mode:
                logger.error(f"Error converting to separate: {e}")
            return code
