# src/determinism_lint.py
"""
Determinism linter with structural rules to forbid:
- Randomness (random, uuid, etc.)
- Async operations
- Sleep/delays
- Network requests
- File I/O
- System calls
"""

import ast
from typing import List, Dict, Set
from dataclasses import dataclass


@dataclass
class DeterminismViolation:
    """Represents a determinism rule violation"""
    rule: str
    line: int
    column: int
    message: str


class DeterminismLinter(ast.NodeVisitor):
    """AST visitor that checks for determinism violations"""
    
    # Forbidden imports
    FORBIDDEN_MODULES = {
        'random', 'uuid', 'time', 'datetime', 'os', 'sys', 'subprocess',
        'requests', 'urllib', 'http', 'socket', 'asyncio', 'threading',
        'multiprocessing', 'concurrent', 'tempfile', 'shutil', 'glob'
    }
    
    # Forbidden function calls
    FORBIDDEN_FUNCTIONS = {
        'open', 'input', 'print', 'exec', 'eval', 'compile',
        'hash', 'id', 'vars', 'globals', 'locals'
    }
    
    # Forbidden attributes/methods
    FORBIDDEN_ATTRIBUTES = {
        'now', 'today', 'random', 'randint', 'choice', 'shuffle',
        'sleep', 'wait', 'delay'
    }
    
    def __init__(self):
        self.violations: List[DeterminismViolation] = []
    
    def visit_Import(self, node: ast.Import) -> None:
        """Check for forbidden imports"""
        for alias in node.names:
            module_name = alias.name.split('.')[0]  # Get root module
            if module_name in self.FORBIDDEN_MODULES:
                self.violations.append(DeterminismViolation(
                    rule="forbidden_import",
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Forbidden import: {alias.name}"
                ))
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check for forbidden from imports"""
        if node.module:
            module_name = node.module.split('.')[0]  # Get root module
            if module_name in self.FORBIDDEN_MODULES:
                self.violations.append(DeterminismViolation(
                    rule="forbidden_import",
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Forbidden import from: {node.module}"
                ))
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call) -> None:
        """Check for forbidden function calls"""
        # Direct function calls
        if isinstance(node.func, ast.Name):
            if node.func.id in self.FORBIDDEN_FUNCTIONS:
                self.violations.append(DeterminismViolation(
                    rule="forbidden_function",
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Forbidden function call: {node.func.id}"
                ))
        
        # Method calls
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in self.FORBIDDEN_ATTRIBUTES:
                self.violations.append(DeterminismViolation(
                    rule="forbidden_method",
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Forbidden method call: {node.func.attr}"
                ))
        
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Check for forbidden attribute access"""
        if node.attr in self.FORBIDDEN_ATTRIBUTES:
            self.violations.append(DeterminismViolation(
                rule="forbidden_attribute",
                line=node.lineno,
                column=node.col_offset,
                message=f"Forbidden attribute access: {node.attr}"
            ))
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Check for async functions"""
        self.violations.append(DeterminismViolation(
            rule="async_function",
            line=node.lineno,
            column=node.col_offset,
            message=f"Async function not allowed: {node.name}"
        ))
        self.generic_visit(node)
    
    def visit_Await(self, node: ast.Await) -> None:
        """Check for await expressions"""
        self.violations.append(DeterminismViolation(
            rule="await_expression",
            line=node.lineno,
            column=node.col_offset,
            message="Await expressions not allowed"
        ))
        self.generic_visit(node)
    
    def visit_With(self, node: ast.With) -> None:
        """Check for context managers (often used for file I/O)"""
        # This is a stricter rule - you might want to allow some context managers
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                if isinstance(item.context_expr.func, ast.Name):
                    if item.context_expr.func.id == 'open':
                        self.violations.append(DeterminismViolation(
                            rule="file_io",
                            line=node.lineno,
                            column=node.col_offset,
                            message="File I/O not allowed in with statement"
                        ))
        self.generic_visit(node)


def lint_code(code: str) -> List[DeterminismViolation]:
    """
    Lint Python code for determinism violations
    
    Args:
        code: Python source code to lint
        
    Returns:
        List of determinism violations found
    """
    try:
        tree = ast.parse(code)
        linter = DeterminismLinter()
        linter.visit(tree)
        return linter.violations
    except SyntaxError as e:
        return [DeterminismViolation(
            rule="syntax_error",
            line=e.lineno or 0,
            column=e.offset or 0,
            message=f"Syntax error: {e.msg}"
        )]


def is_deterministic(code: str) -> bool:
    """
    Check if code is deterministic (no violations found)
    
    Args:
        code: Python source code to check
        
    Returns:
        True if code is deterministic, False otherwise
    """
    violations = lint_code(code)
    return len(violations) == 0


def format_violations(violations: List[DeterminismViolation]) -> str:
    """
    Format violations for human-readable output
    
    Args:
        violations: List of violations to format
        
    Returns:
        Formatted string describing all violations
    """
    if not violations:
        return "No determinism violations found."
    
    lines = [f"Found {len(violations)} determinism violation(s):"]
    for i, violation in enumerate(violations, 1):
        lines.append(f"{i}. Line {violation.line}, Column {violation.column}: {violation.message} (Rule: {violation.rule})")
    
    return "\n".join(lines)
