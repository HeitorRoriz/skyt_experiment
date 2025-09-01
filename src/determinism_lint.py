# src/determinism_lint.py
"""
Determinism linting for SKYT pipeline
Fast-fail detection of determinism rule violations
"""

import ast
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class DeterminismViolation:
    """Represents a determinism rule violation"""
    rule: str
    line: int
    column: int
    message: str
    severity: str  # "error", "warning"


class DeterminismLinter:
    """AST-based determinism rule checker"""
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.violations = []
    
    def lint_code(self, code: str) -> List[DeterminismViolation]:
        """
        Lint code for determinism violations
        
        Args:
            code: Python code string
        
        Returns:
            List of determinism violations
        """
        self.violations = []
        
        try:
            tree = ast.parse(code)
            self.visit_tree(tree)
        except SyntaxError as e:
            self.violations.append(DeterminismViolation(
                rule="syntax_error",
                line=e.lineno or 0,
                column=e.offset or 0,
                message=f"Syntax error: {str(e)}",
                severity="error"
            ))
        
        return self.violations
    
    def visit_tree(self, tree: ast.AST):
        """Visit AST nodes and check for violations"""
        for node in ast.walk(tree):
            self._check_random_operations(node)
            self._check_time_operations(node)
            self._check_os_operations(node)
            self._check_io_operations(node)
            self._check_hash_operations(node)
            self._check_global_state(node)
    
    def _check_random_operations(self, node: ast.AST):
        """Check for random/non-deterministic operations"""
        if isinstance(node, ast.Call):
            func_name = self._get_function_name(node)
            random_patterns = {
                'random', 'randint', 'choice', 'shuffle', 'sample',
                'uuid4', 'uuid1', 'urandom'
            }
            
            if func_name in random_patterns:
                self.violations.append(DeterminismViolation(
                    rule="random_operation",
                    line=getattr(node, 'lineno', 0),
                    column=getattr(node, 'col_offset', 0),
                    message=f"Non-deterministic random operation: {func_name}",
                    severity="error"
                ))
    
    def _check_time_operations(self, node: ast.AST):
        """Check for time-dependent operations"""
        if isinstance(node, ast.Call):
            func_name = self._get_function_name(node)
            time_patterns = {
                'time', 'now', 'today', 'datetime', 'timestamp',
                'clock', 'perf_counter'
            }
            
            if func_name in time_patterns:
                self.violations.append(DeterminismViolation(
                    rule="time_operation",
                    line=getattr(node, 'lineno', 0),
                    column=getattr(node, 'col_offset', 0),
                    message=f"Time-dependent operation: {func_name}",
                    severity="error"
                ))
    
    def _check_os_operations(self, node: ast.AST):
        """Check for OS/system operations"""
        if isinstance(node, ast.Call):
            func_name = self._get_function_name(node)
            os_patterns = {
                'getenv', 'environ', 'system', 'popen', 'subprocess',
                'platform', 'uname', 'getcwd', 'listdir'
            }
            
            if func_name in os_patterns:
                self.violations.append(DeterminismViolation(
                    rule="os_operation",
                    line=getattr(node, 'lineno', 0),
                    column=getattr(node, 'col_offset', 0),
                    message=f"OS-dependent operation: {func_name}",
                    severity="error"
                ))
    
    def _check_io_operations(self, node: ast.AST):
        """Check for I/O operations"""
        if isinstance(node, ast.Call):
            func_name = self._get_function_name(node)
            io_patterns = {'open', 'read', 'write', 'input'}
            
            if func_name in io_patterns:
                severity = "warning" if not self.strict_mode else "error"
                self.violations.append(DeterminismViolation(
                    rule="io_operation",
                    line=getattr(node, 'lineno', 0),
                    column=getattr(node, 'col_offset', 0),
                    message=f"I/O operation: {func_name}",
                    severity=severity
                ))
    
    def _check_hash_operations(self, node: ast.AST):
        """Check for hash operations that may be non-deterministic"""
        if isinstance(node, ast.Call):
            func_name = self._get_function_name(node)
            
            if func_name == 'hash':
                self.violations.append(DeterminismViolation(
                    rule="hash_operation",
                    line=getattr(node, 'lineno', 0),
                    column=getattr(node, 'col_offset', 0),
                    message="Built-in hash() may be non-deterministic across runs",
                    severity="warning"
                ))
    
    def _check_global_state(self, node: ast.AST):
        """Check for global state modifications"""
        if isinstance(node, ast.Global):
            self.violations.append(DeterminismViolation(
                rule="global_state",
                line=getattr(node, 'lineno', 0),
                column=getattr(node, 'col_offset', 0),
                message="Global state modification detected",
                severity="warning"
            ))
    
    def _get_function_name(self, call_node: ast.Call) -> Optional[str]:
        """Extract function name from call node"""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return None


def lint_determinism(code: str, strict_mode: bool = True) -> Dict[str, Any]:
    """
    Lint code for determinism violations
    
    Args:
        code: Python code string
        strict_mode: Whether to use strict determinism rules
    
    Returns:
        Dict with violations and pass status
    """
    linter = DeterminismLinter(strict_mode=strict_mode)
    violations = linter.lint_code(code)
    
    # Categorize violations
    errors = [v for v in violations if v.severity == "error"]
    warnings = [v for v in violations if v.severity == "warning"]
    
    determinism_pass = len(errors) == 0
    
    return {
        "determinism_pass": determinism_pass,
        "violations": violations,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "violation_summary": _summarize_violations(violations)
    }


def _summarize_violations(violations: List[DeterminismViolation]) -> str:
    """Create summary string of violations"""
    if not violations:
        return "no_violations"
    
    rule_counts = {}
    for violation in violations:
        rule_counts[violation.rule] = rule_counts.get(violation.rule, 0) + 1
    
    summary_parts = []
    for rule, count in sorted(rule_counts.items()):
        summary_parts.append(f"{rule}:{count}")
    
    return "|".join(summary_parts)
