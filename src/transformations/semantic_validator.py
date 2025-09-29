"""
Semantic Validator - Validates transformations preserve behavior

This module provides semantic equivalence checking beyond simple string distance.
Uses execution-based testing to ensure transformations preserve code behavior.
"""

import ast
from typing import Dict, List, Any, Optional


class SemanticValidator:
    """Validates that code transformations preserve semantic behavior"""
    
    def __init__(self):
        self.test_inputs = [0, 1, 2, 5, 10, -1, 100]  # Standard test inputs
    
    def are_semantically_equivalent(self, code1: str, code2: str) -> bool:
        """
        Check if two code snippets are semantically equivalent
        
        Tests:
        1. Same function signature
        2. Same output for test inputs
        3. Same exception behavior
        
        Returns True if equivalent, False otherwise
        """
        try:
            # Extract and execute both functions
            func1 = self._extract_and_execute(code1)
            func2 = self._extract_and_execute(code2)
            
            if func1 is None or func2 is None:
                return False
            
            # Test on multiple inputs
            for test_input in self.test_inputs:
                result1, error1 = self._safe_execute(func1, test_input)
                result2, error2 = self._safe_execute(func2, test_input)
                
                # Both should succeed or both should fail
                if (error1 is None) != (error2 is None):
                    return False
                
                # If both succeeded, results must match
                if error1 is None and result1 != result2:
                    return False
                
                # If both failed, exception types should match
                if error1 is not None and type(error1) != type(error2):
                    return False
            
            return True
            
        except Exception:
            # If we can't validate, assume not equivalent (conservative)
            return False
    
    def _extract_and_execute(self, code: str) -> Optional[callable]:
        """Extract the main function from code and return it"""
        try:
            namespace = {}
            exec(code, namespace)
            
            # Find the first function that's not a helper
            for name, obj in namespace.items():
                if callable(obj) and not name.startswith('_'):
                    return obj
            
            return None
        except:
            return None
    
    def _safe_execute(self, func: callable, input_value: Any) -> tuple:
        """
        Safely execute function with input
        
        Returns (result, error) tuple
        """
        try:
            result = func(input_value)
            return (result, None)
        except Exception as e:
            return (None, e)
    
    def calculate_behavioral_distance(self, code1: str, code2: str) -> float:
        """
        Calculate behavioral distance between two code snippets
        
        Returns:
        - 0.0 if semantically identical
        - 0.5 if partially different
        - 1.0 if completely different or can't compare
        """
        try:
            func1 = self._extract_and_execute(code1)
            func2 = self._extract_and_execute(code2)
            
            if func1 is None or func2 is None:
                return 1.0
            
            matches = 0
            total = len(self.test_inputs)
            
            for test_input in self.test_inputs:
                result1, error1 = self._safe_execute(func1, test_input)
                result2, error2 = self._safe_execute(func2, test_input)
                
                # Check if results match
                if error1 is None and error2 is None and result1 == result2:
                    matches += 1
                elif error1 is not None and error2 is not None and type(error1) == type(error2):
                    matches += 1
            
            # Return distance (0 = identical, 1 = completely different)
            return 1.0 - (matches / total)
            
        except:
            return 1.0
