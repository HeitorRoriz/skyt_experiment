"""
Type Checker - Enhanced type analysis using mypy

Provides static type checking and inference to complement AST-based contract extraction.
Follows Single Responsibility Principle: only analyzes types.
"""

import tempfile
import subprocess
import json
import ast
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Check if mypy is available (use python -m mypy for portability)
try:
    import sys
    result = subprocess.run(
        [sys.executable, '-m', 'mypy', '--version'],
        capture_output=True,
        text=True,
        timeout=1
    )
    MYPY_AVAILABLE = result.returncode == 0
except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
    MYPY_AVAILABLE = False


class TypeChecker:
    """
    Analyzes code types using mypy static type checker.
    
    Provides:
    - Type error detection
    - Type inference (even without annotations)
    - Function signature extraction
    
    Design principles:
    - Single Responsibility: Only type analysis
    - Fail gracefully: Returns None if mypy unavailable
    - No side effects: Pure function, no state mutation
    """
    
    def __init__(self):
        """Initialize type checker and verify mypy availability"""
        self.available = MYPY_AVAILABLE
        if not self.available:
            logger.warning(
                "mypy not available. Install with: pip install mypy"
            )
    
    def analyze(self, code: str) -> Dict[str, Any]:
        """
        Analyze code types using mypy.
        
        Args:
            code: Python source code string
            
        Returns:
            Dictionary with type analysis results
            
        Example:
            >>> checker = TypeChecker()
            >>> result = checker.analyze("def f(n: int) -> int: return n")
            >>> result['type_errors']
            []
        """
        if not self.available:
            return self._unavailable_result()
        
        try:
            return {
                **self._check_types(code),
                **self._extract_signatures(code),
            }
        except Exception as e:
            logger.error(f"Type checking failed: {e}")
            return self._error_result(str(e))
    
    def _check_types(self, code: str) -> Dict[str, Any]:
        """
        Run mypy to detect type errors.
        
        Uses mypy's type inference engine to find:
        - Return type mismatches
        - Argument type mismatches
        - Invalid operations on incompatible types
        - Missing type annotations (if strict mode)
        """
        # Write code to temporary file
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            # Run mypy with lenient settings (allows unannotated code)
            import sys
            result = subprocess.run(
                [
                    sys.executable, '-m', 'mypy',
                    '--no-error-summary',
                    '--no-color-output',
                    '--show-column-numbers',
                    '--show-error-codes',
                    temp_path
                ],
                capture_output=True,
                text=True,
                timeout=5.0
            )
            
            # Parse errors from output
            type_errors = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line and '.py:' in line:
                        error = self._parse_mypy_error(line)
                        if error:
                            type_errors.append(error)
            
            return {
                "type_errors": type_errors,
                "total_type_errors": len(type_errors),
                "has_type_errors": len(type_errors) > 0,
                "type_safe": len(type_errors) == 0,
            }
            
        except subprocess.TimeoutExpired:
            logger.warning("mypy timeout")
            return {
                "type_errors": [],
                "total_type_errors": 0,
                "has_type_errors": False,
                "type_safe": None,
                "timeout": True
            }
        finally:
            # Clean up temp file
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass
    
    def _parse_mypy_error(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse mypy error line.
        
        Format: filename.py:line:col: error: message [code]
        """
        try:
            # Split on first colon after filename
            parts = line.split(':', 3)
            if len(parts) < 4:
                return None
            
            line_num = parts[1].strip()
            col_num = parts[2].strip()
            message_part = parts[3].strip()
            
            # Extract error code if present
            error_code = None
            if '[' in message_part and ']' in message_part:
                code_start = message_part.rfind('[')
                code_end = message_part.rfind(']')
                error_code = message_part[code_start+1:code_end]
                message = message_part[:code_start].strip()
            else:
                message = message_part
            
            # Remove 'error:' prefix if present
            if message.startswith('error:'):
                message = message[6:].strip()
            
            return {
                "line": int(line_num) if line_num.isdigit() else None,
                "column": int(col_num) if col_num.isdigit() else None,
                "message": message,
                "error_code": error_code,
                "severity": "error"
            }
        except Exception as e:
            logger.debug(f"Failed to parse mypy error: {line} - {e}")
            return None
    
    def _extract_signatures(self, code: str) -> Dict[str, Any]:
        """
        Extract function signatures from AST.
        
        This provides type information even for unannotated code
        by combining AST inspection with mypy inference.
        """
        try:
            tree = ast.parse(code)
            signatures = {}
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    sig = self._extract_function_signature(node)
                    signatures[node.name] = sig
            
            return {
                "function_signatures": signatures,
                "total_functions": len(signatures),
                "annotated_functions": sum(
                    1 for sig in signatures.values() 
                    if sig.get("has_annotations", False)
                ),
                "annotation_coverage": (
                    sum(1 for sig in signatures.values() if sig.get("has_annotations", False))
                    / len(signatures)
                    if signatures else 0.0
                ),
            }
            
        except Exception as e:
            logger.error(f"Signature extraction failed: {e}")
            return {
                "function_signatures": {},
                "total_functions": 0,
                "annotated_functions": 0,
                "annotation_coverage": 0.0,
            }
    
    def _extract_function_signature(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """
        Extract detailed signature for a function.
        
        Returns:
            Dict with parameter info, return type, etc.
        """
        # Extract parameters
        parameters = []
        for arg in node.args.args:
            param = {
                "name": arg.arg,
                "annotation": self._annotation_to_string(arg.annotation),
                "has_annotation": arg.annotation is not None,
            }
            parameters.append(param)
        
        # Extract return annotation
        return_annotation = None
        if node.returns:
            return_annotation = self._annotation_to_string(node.returns)
        
        # Determine if function has any annotations
        has_annotations = (
            any(p["has_annotation"] for p in parameters) or 
            return_annotation is not None
        )
        
        return {
            "parameters": parameters,
            "return_annotation": return_annotation,
            "has_annotations": has_annotations,
            "total_params": len(parameters),
            "annotated_params": sum(1 for p in parameters if p["has_annotation"]),
        }
    
    def _annotation_to_string(self, annotation: Optional[ast.AST]) -> Optional[str]:
        """Convert AST annotation to string"""
        if annotation is None:
            return None
        
        try:
            # Use ast.unparse if available (Python 3.9+)
            if hasattr(ast, 'unparse'):
                return ast.unparse(annotation)
            else:
                # Fallback: simple name extraction
                if isinstance(annotation, ast.Name):
                    return annotation.id
                elif isinstance(annotation, ast.Constant):
                    return str(annotation.value)
                else:
                    return ast.dump(annotation)
        except Exception:
            return None
    
    def _unavailable_result(self) -> Dict[str, Any]:
        """Return result when mypy is not available"""
        return {
            "mypy_available": False,
            "type_errors": [],
            "total_type_errors": 0,
            "has_type_errors": False,
            "type_safe": None,
            "function_signatures": {},
            "total_functions": 0,
            "annotated_functions": 0,
            "annotation_coverage": 0.0,
        }
    
    def _error_result(self, error_msg: str) -> Dict[str, Any]:
        """Return result when analysis fails"""
        return {
            "mypy_available": True,
            "analysis_error": error_msg,
            "type_errors": [],
            "total_type_errors": 0,
            "has_type_errors": False,
            "type_safe": None,
            "function_signatures": {},
            "total_functions": 0,
            "annotated_functions": 0,
            "annotation_coverage": 0.0,
        }
