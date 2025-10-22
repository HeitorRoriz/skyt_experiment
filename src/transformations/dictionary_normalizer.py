"""
Dictionary Normalizer - Normalizes dictionary key ordering to match canonical form
Handles structural differences in dictionary literals that don't affect functionality
"""

import ast
import logging
from typing import Optional, Tuple, Dict, List
from .transformation_base import TransformationBase, TransformationResult

logger = logging.getLogger(__name__)


class DictionaryNormalizer(TransformationBase):
    """
    A transformer that normalizes dictionary key ordering to match the canon.
    This addresses structural differences in dictionary literals that don't affect functionality.
    """
    
    def __init__(self):
        super().__init__(
            name="DictionaryNormalizer",
            description="Normalizes dictionary key ordering to match canonical form"
        )
        self.canon_dict_order: Optional[Dict[str, List[str]]] = None
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """
        Check if dictionary normalization is needed by comparing dictionary key orders.
        """
        if not canon_code:
            return False
        
        try:
            # Extract dictionary order from canon
            self.canon_dict_order = self._extract_dict_order(canon_code)
            if not self.canon_dict_order:
                return False
            
            # Check if code has dictionaries with different ordering
            code_dict_order = self._extract_dict_order(code)
            if not code_dict_order:
                return False
            
            # Compare orders
            for var_name, canon_keys in self.canon_dict_order.items():
                if var_name in code_dict_order:
                    code_keys = code_dict_order[var_name]
                    if set(code_keys) == set(canon_keys) and code_keys != canon_keys:
                        return True  # Same keys, different order
            
            return False
        except Exception as e:
            if self.debug_mode:
                logger.warning(f"Error in can_transform: {e}")
            return False
    
    def _extract_dict_order(self, code: str) -> Dict[str, List[str]]:
        """
        Extract dictionary key ordering from code.
        Returns a mapping of dictionary variable names to their key order.
        """
        try:
            tree = ast.parse(code)
            dict_order = {}
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            if isinstance(node.value, ast.Dict):
                                keys = []
                                for key in node.value.keys:
                                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                        keys.append(key.value)
                                if keys:
                                    dict_order[var_name] = keys
            
            return dict_order
        except Exception as e:
            if self.debug_mode:
                logger.warning(f"Failed to extract dictionary order: {e}")
            return {}
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """
        Apply dictionary key normalization by reordering dictionary keys to match the canon.
        """
        try:
            tree = ast.parse(code)
            modified = False
            changes_made = []
            
            class DictNormalizer(ast.NodeTransformer):
                def __init__(self, canon_dict_order):
                    self.canon_dict_order = canon_dict_order
                    self.modified = False
                    self.changes = []
                
                def visit_Assign(self, node):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id in self.canon_dict_order:
                            if isinstance(node.value, ast.Dict):
                                # Extract current keys and values
                                current_keys = []
                                current_values = []
                                key_value_map = {}
                                
                                for i, key in enumerate(node.value.keys):
                                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                        current_keys.append(key.value)
                                        key_value_map[key.value] = (node.value.keys[i], node.value.values[i])
                                
                                canon_order = self.canon_dict_order[target.id]
                                
                                # Check if reordering is needed
                                if set(current_keys) == set(canon_order) and current_keys != canon_order:
                                    # Reorder to match canon
                                    new_keys = []
                                    new_values = []
                                    for canon_key in canon_order:
                                        if canon_key in key_value_map:
                                            key_node, value_node = key_value_map[canon_key]
                                            new_keys.append(key_node)
                                            new_values.append(value_node)
                                    
                                    node.value.keys = new_keys
                                    node.value.values = new_values
                                    self.modified = True
                                    self.changes.append(f"Reordered dictionary '{target.id}' keys to match canon: {canon_order}")
                    
                    return self.generic_visit(node)
            
            transformer = DictNormalizer(self.canon_dict_order)
            new_tree = transformer.visit(tree)
            modified = transformer.modified
            changes_made = transformer.changes
            
            if modified:
                new_code = ast.unparse(new_tree)
                self.log_debug(f"Normalized dictionary key ordering: {changes_made}")
                return new_code
            else:
                # Return original code if no changes
                return code
        
        except Exception as e:
            error_msg = f"Error in dictionary normalization: {str(e)}"
            if self.debug_mode:
                logger.error(error_msg)
            # Return original code on error
            return code
