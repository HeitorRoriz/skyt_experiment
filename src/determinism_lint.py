# src/determinism_lint.py

import ast
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from contract import PromptContract

@dataclass
class DeterminismViolation:
    rule: str
    line: int
    column: int
    message: str
    node_type: str

class DeterminismLinter:
    """AST-based linter that enforces determinism rules from contract"""
    
    def __init__(self, contract: PromptContract):
        self.contract = contract
        self.violations = []
        
        # Default determinism rules if not specified in contract
        self.default_rules = {
            "allowed_imports": ["math", "typing", "dataclasses", "functools", "itertools"],
            "forbidden_calls": ["print", "input", "open", "eval", "exec"],
            "side_effects_policy": "none",
            "output_ordering_policy": "deterministic"
        }
        
        # Get rules from contract or use defaults
        self.rules = contract.determinism or self.default_rules
    
    def lint_code(self, code: str) -> Tuple[bool, List[DeterminismViolation]]:
        """
        Lint code for determinism violations
        Returns (is_deterministic, violations_list)
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
                message=f"Syntax error: {e.msg}",
                node_type="SyntaxError"
            ))
        
        return len(self.violations) == 0, self.violations
    
    def visit_tree(self, tree: ast.AST):
        """Visit all nodes in the AST and check for violations"""
        for node in ast.walk(tree):
            self._check_imports(node)
            self._check_function_calls(node)
            self._check_side_effects(node)
            self._check_nondeterministic_constructs(node)
    
    def _check_imports(self, node: ast.AST):
        """Check import statements against allowlist"""
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.rules["allowed_imports"]:
                        self._add_violation(
                            node, "forbidden_import",
                            f"Import '{alias.name}' not in allowed imports: {self.rules['allowed_imports']}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module not in self.rules["allowed_imports"]:
                    self._add_violation(
                        node, "forbidden_import",
                        f"Import from '{module}' not in allowed imports: {self.rules['allowed_imports']}"
                    )
    
    def _check_function_calls(self, node: ast.AST):
        """Check function calls against forbidden list"""
        if isinstance(node, ast.Call):
            func_name = self._get_function_name(node.func)
            if func_name in self.rules["forbidden_calls"]:
                self._add_violation(
                    node, "forbidden_call",
                    f"Call to '{func_name}' is forbidden: {self.rules['forbidden_calls']}"
                )
    
    def _check_side_effects(self, node: ast.AST):
        """Check for side effects based on policy"""
        if self.rules["side_effects_policy"] == "none":
            # Check for global variable assignments
            if isinstance(node, ast.Global):
                self._add_violation(
                    node, "side_effect_global",
                    "Global variable modification forbidden by side_effects_policy"
                )
            
            # Check for nonlocal variable assignments  
            if isinstance(node, ast.Nonlocal):
                self._add_violation(
                    node, "side_effect_nonlocal",
                    "Nonlocal variable modification forbidden by side_effects_policy"
                )
    
    def _check_nondeterministic_constructs(self, node: ast.AST):
        """Check for inherently nondeterministic constructs"""
        # Check for set literals in return statements
        if isinstance(node, ast.Return) and node.value:
            if self._contains_set_literal(node.value):
                self._add_violation(
                    node, "nondeterministic_return",
                    "Set literal in return statement - use sorted list instead"
                )
        
        # Check for dict iteration without explicit ordering
        if isinstance(node, ast.For):
            if isinstance(node.iter, ast.Call):
                func_name = self._get_function_name(node.iter.func)
                if func_name in ["keys", "values", "items"]:
                    self._add_violation(
                        node, "nondeterministic_iteration",
                        "Dict iteration without explicit ordering - use sorted() wrapper"
                    )
    
    def _contains_set_literal(self, node: ast.AST) -> bool:
        """Check if node contains set literals"""
        if isinstance(node, ast.Set):
            return True
        for child in ast.walk(node):
            if isinstance(child, ast.Set):
                return True
        return False
    
    def _get_function_name(self, node: ast.AST) -> str:
        """Extract function name from call node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        else:
            return ""
    
    def _add_violation(self, node: ast.AST, rule: str, message: str):
        """Add a violation to the list"""
        self.violations.append(DeterminismViolation(
            rule=rule,
            line=getattr(node, 'lineno', 0),
            column=getattr(node, 'col_offset', 0),
            message=message,
            node_type=type(node).__name__
        ))

def lint_for_determinism(code: str, contract: PromptContract) -> Tuple[bool, List[DeterminismViolation]]:
    """
    Convenience function to lint code for determinism violations
    """
    linter = DeterminismLinter(contract)
    return linter.lint_code(code)
