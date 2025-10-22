"""
Regex Pattern Normalizer - Normalizes equivalent regex patterns to match canonical form
Handles differences in regex patterns that are functionally equivalent or match canon
"""

import ast
import re
import logging
from typing import Optional, Dict, List
from .transformation_base import TransformationBase

logger = logging.getLogger(__name__)


class RegexPatternNormalizer(TransformationBase):
    """
    A transformer that normalizes regex patterns to match the canon.
    This addresses differences in regex patterns within re.sub() calls.
    """
    
    def __init__(self):
        super().__init__(
            name="RegexPatternNormalizer",
            description="Normalizes regex patterns to match canonical form"
        )
        self.canon_patterns: Dict[int, str] = {}  # Maps call position to pattern
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """
        Check if regex pattern normalization is needed.
        """
        if not canon_code:
            return False
        
        try:
            # Extract regex patterns from both codes
            canon_patterns = self._extract_regex_patterns(canon_code)
            code_patterns = self._extract_regex_patterns(code)
            
            if not canon_patterns or not code_patterns:
                return False
            
            # Check if there are differences in patterns
            for pos, canon_pattern in canon_patterns.items():
                if pos in code_patterns and code_patterns[pos] != canon_pattern:
                    self.canon_patterns = canon_patterns
                    return True
            
            return False
        except Exception as e:
            if self.debug_mode:
                logger.warning(f"Error in can_transform: {e}")
            return False
    
    def _extract_regex_patterns(self, code: str) -> Dict[int, str]:
        """
        Extract regex patterns from re.sub() calls.
        Returns a mapping of call position to pattern string.
        """
        try:
            tree = ast.parse(code)
            patterns = {}
            call_count = 0
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check if this is a re.sub() call
                    if (isinstance(node.func, ast.Attribute) and 
                        node.func.attr == 'sub' and
                        isinstance(node.func.value, ast.Name) and
                        node.func.value.id == 're'):
                        
                        # Extract the pattern (first argument)
                        if node.args and isinstance(node.args[0], ast.Constant):
                            pattern = node.args[0].value
                            if isinstance(pattern, str):
                                patterns[call_count] = pattern
                                call_count += 1
            
            return patterns
        except Exception as e:
            if self.debug_mode:
                logger.warning(f"Failed to extract regex patterns: {e}")
            return {}
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """
        Apply regex pattern normalization by replacing patterns to match the canon.
        """
        try:
            tree = ast.parse(code)
            modified = False
            
            class RegexNormalizer(ast.NodeTransformer):
                def __init__(self, canon_patterns):
                    self.canon_patterns = canon_patterns
                    self.call_count = 0
                    self.modified = False
                
                def visit_Call(self, node):
                    # Check if this is a re.sub() call
                    if (isinstance(node.func, ast.Attribute) and 
                        node.func.attr == 'sub' and
                        isinstance(node.func.value, ast.Name) and
                        node.func.value.id == 're'):
                        
                        # Check if we have a canon pattern for this position
                        if self.call_count in self.canon_patterns:
                            canon_pattern = self.canon_patterns[self.call_count]
                            
                            # Replace the pattern if different
                            if (node.args and isinstance(node.args[0], ast.Constant) and
                                isinstance(node.args[0].value, str) and
                                node.args[0].value != canon_pattern):
                                
                                node.args[0] = ast.Constant(value=canon_pattern)
                                self.modified = True
                        
                        self.call_count += 1
                    
                    return self.generic_visit(node)
            
            transformer = RegexNormalizer(self.canon_patterns)
            new_tree = transformer.visit(tree)
            modified = transformer.modified
            
            if modified:
                new_code = ast.unparse(new_tree)
                self.log_debug(f"Normalized regex patterns to match canon")
                return new_code
            else:
                return code
        
        except Exception as e:
            error_msg = f"Error in regex pattern normalization: {str(e)}"
            if self.debug_mode:
                logger.error(error_msg)
            return code
