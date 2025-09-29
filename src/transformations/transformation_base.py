"""
Base class for all SKYT transformations
Provides common interface and utilities
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import ast


class TransformationResult:
    """Result of a transformation attempt"""
    
    def __init__(self, 
                 transformed_code: str,
                 success: bool,
                 original_code: str,
                 transformation_name: str,
                 distance_improvement: float = 0.0,
                 error_message: Optional[str] = None):
        self.transformed_code = transformed_code
        self.success = success
        self.original_code = original_code
        self.transformation_name = transformation_name
        self.distance_improvement = distance_improvement
        self.error_message = error_message
        
    def __repr__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"TransformationResult({self.transformation_name}: {status}, improvement: {self.distance_improvement:.3f})"


class TransformationBase(ABC):
    """Base class for all code transformations"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.debug_mode = False
        
    def enable_debug(self):
        """Enable debug logging for this transformation"""
        self.debug_mode = True
        
    def log_debug(self, message: str):
        """Log debug message if debug mode is enabled"""
        if self.debug_mode:
            print(f"[{self.name}] {message}")
            
    @abstractmethod
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """Check if this transformation can be applied to the code"""
        pass
        
    @abstractmethod
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """Apply the transformation to the code"""
        pass
        
    def transform(self, code: str, canon_code: str, property_diffs: list = None) -> TransformationResult:
        """
        Main transformation method with error handling and logging
        
        Args:
            code: Code to transform
            canon_code: Canonical reference code
            property_diffs: List of property differences from pipeline
            
        Returns:
            TransformationResult with success status and transformed code
        """
        self.log_debug(f"Attempting transformation on code:\n{code}")
        
        try:
            # Check if transformation is applicable
            if not self.can_transform(code, canon_code, property_diffs=property_diffs):
                self.log_debug("Transformation not applicable")
                return TransformationResult(
                    transformed_code=code,
                    success=False,
                    original_code=code,
                    transformation_name=self.name,
                    error_message="Transformation not applicable"
                )
            
            # Apply transformation
            transformed_code = self._apply_transformation(code, canon_code)
            
            # Check if transformation actually changed the code
            if transformed_code == code:
                self.log_debug("No changes made by transformation")
                return TransformationResult(
                    transformed_code=code,
                    success=False,
                    original_code=code,
                    transformation_name=self.name,
                    error_message="No changes made"
                )
            
            self.log_debug(f"Transformation successful:\n{transformed_code}")
            return TransformationResult(
                transformed_code=transformed_code,
                success=True,
                original_code=code,
                transformation_name=self.name
            )
            
        except Exception as e:
            error_msg = f"Transformation failed: {str(e)}"
            self.log_debug(error_msg)
            return TransformationResult(
                transformed_code=code,
                success=False,
                original_code=code,
                transformation_name=self.name,
                error_message=error_msg
            )
    
    def safe_parse_ast(self, code: str) -> Optional[ast.AST]:
        """Safely parse code to AST, return None if fails"""
        try:
            return ast.parse(code)
        except SyntaxError as e:
            self.log_debug(f"AST parsing failed: {e}")
            return None
            
    def normalize_whitespace(self, code: str) -> str:
        """Normalize whitespace for comparison"""
        lines = []
        for line in code.split('\n'):
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
        return '\n'.join(lines)
