"""
Contract Compliance Checker

Validates that code adheres to contract specifications beyond just
passing oracle tests. Checks algorithm, structure, constraints, etc.

Key Principle:
- Contract = Specification = Compliance Requirements
- If contract specifies something, it MUST be validated
- No workarounds, no special cases
"""

import ast
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ComplianceResult:
    """Result of contract compliance check"""
    fully_compliant: bool
    score: float  # 0.0 to 1.0
    violations: List[str]
    details: Dict[str, Any]


class ContractComplianceChecker:
    """
    Checks if code complies with contract specifications.
    
    Validates:
    - Function/class names (constraints.function_name, constraints.class_name)
    - Required methods (constraints.methods)
    - Required classes (constraints.required_classes)
    - Required attributes (constraints.required_attributes)
    - Implementation style (constraints.implementation_style)
    - Recursion requirements (constraints.requires_recursion)
    - Algorithm specification (constraints.algorithm)
    
    Philosophy:
    - Every field in contract is a requirement
    - No optional validation - if specified, must be checked
    - Return clear violations for debugging
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def check_compliance(self, code: str, contract: Dict) -> ComplianceResult:
        """
        Check if code complies with contract requirements.
        
        Args:
            code: Python code to validate
            contract: Contract specification
        
        Returns:
            ComplianceResult with compliance status and violations
        """
        violations = []
        checks = {}
        
        # Parse code
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return ComplianceResult(
                fully_compliant=False,
                score=0.0,
                violations=[f"Syntax error: {e}"],
                details={"parse_error": str(e)}
            )
        
        # Get constraints from contract
        constraints = contract.get("constraints", {})
        
        # If no constraints specified, code is compliant by default
        if not constraints:
            return ComplianceResult(
                fully_compliant=True,
                score=1.0,
                violations=[],
                details={"note": "No constraints specified in contract"}
            )
        
        # 1. Check function name (if specified)
        if "function_name" in constraints:
            check = self._check_function_name(tree, constraints["function_name"])
            checks["function_name"] = check
            if not check["compliant"]:
                violations.extend(check["violations"])
        
        # 2. Check class name (if specified)
        if "class_name" in constraints:
            check = self._check_class_name(tree, constraints["class_name"])
            checks["class_name"] = check
            if not check["compliant"]:
                violations.extend(check["violations"])
        
        # 3. Check required methods (if specified)
        if "methods" in constraints:
            check = self._check_methods(tree, constraints["methods"])
            checks["methods"] = check
            if not check["compliant"]:
                violations.extend(check["violations"])
        
        # 4. Check required classes (if specified)
        if "required_classes" in constraints:
            check = self._check_required_classes(tree, constraints["required_classes"])
            checks["required_classes"] = check
            if not check["compliant"]:
                violations.extend(check["violations"])
        
        # 5. Check required attributes (if specified)
        if "required_attributes" in constraints:
            check = self._check_required_attributes(tree, constraints["required_attributes"])
            checks["required_attributes"] = check
            if not check["compliant"]:
                violations.extend(check["violations"])
        
        # 6. Check recursion requirement (if specified)
        if "requires_recursion" in constraints:
            check = self._check_recursion(tree, constraints["requires_recursion"])
            checks["requires_recursion"] = check
            if not check["compliant"]:
                violations.extend(check["violations"])
        
        # 7. Check algorithm (if specified)
        if "algorithm" in constraints:
            check = self._check_algorithm(tree, constraints["algorithm"])
            checks["algorithm"] = check
            if not check["compliant"]:
                violations.extend(check["violations"])
        
        # Calculate compliance score
        if checks:
            total_checks = len(checks)
            passed_checks = sum(1 for c in checks.values() if c["compliant"])
            score = passed_checks / total_checks
        else:
            score = 1.0  # No checks = compliant by default
        
        fully_compliant = len(violations) == 0
        
        if self.debug:
            logger.info(f"Compliance check: {score:.2f} ({passed_checks}/{total_checks} checks passed)")
            if violations:
                logger.warning(f"Violations: {violations}")
        
        return ComplianceResult(
            fully_compliant=fully_compliant,
            score=score,
            violations=violations,
            details=checks
        )
    
    # ============================================
    # Individual Check Methods
    # ============================================
    
    def _check_function_name(self, tree: ast.AST, required_name: str) -> Dict:
        """Check if code has function with required name"""
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        if required_name in functions:
            return {"compliant": True, "violations": []}
        else:
            return {
                "compliant": False,
                "violations": [f"Missing required function: '{required_name}'"],
                "found": functions
            }
    
    def _check_class_name(self, tree: ast.AST, required_name: str) -> Dict:
        """Check if code has class with required name"""
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        if required_name in classes:
            return {"compliant": True, "violations": []}
        else:
            return {
                "compliant": False,
                "violations": [f"Missing required class: '{required_name}'"],
                "found": classes
            }
    
    def _check_methods(self, tree: ast.AST, required_methods: List[str]) -> Dict:
        """Check if code has all required methods"""
        violations = []
        
        # Get all method names from all classes
        methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)
        
        for method in required_methods:
            if method not in methods:
                violations.append(f"Missing required method: '{method}'")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "found": methods
        }
    
    def _check_required_classes(self, tree: ast.AST, required_classes: List[str]) -> Dict:
        """Check if code has all required classes"""
        violations = []
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        for cls in required_classes:
            if cls not in classes:
                violations.append(f"Missing required class: '{cls}'")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "found": classes
        }
    
    def _check_required_attributes(self, tree: ast.AST, required_attributes: Dict[str, List[str]]) -> Dict:
        """
        Check if classes have required attributes.
        
        required_attributes format:
        {
            "ClassName": ["attr1", "attr2"],
            "Node": ["prev", "next"]
        }
        """
        violations = []
        class_attributes = {}
        
        # Extract attributes per class
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                attributes = set()
                
                # Look for __init__ method
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        # Extract self.attribute assignments
                        for stmt in ast.walk(item):
                            if isinstance(stmt, ast.Assign):
                                for target in stmt.targets:
                                    if isinstance(target, ast.Attribute):
                                        if isinstance(target.value, ast.Name) and target.value.id == "self":
                                            attributes.add(target.attr)
                
                class_attributes[class_name] = attributes
        
        # Check required attributes
        for cls, attrs in required_attributes.items():
            if cls not in class_attributes:
                violations.append(f"Class '{cls}' not found (required for attribute check)")
            else:
                for attr in attrs:
                    if attr not in class_attributes[cls]:
                        violations.append(f"Class '{cls}' missing required attribute: '{attr}'")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "found": class_attributes
        }
    
    def _check_recursion(self, tree: ast.AST, requires_recursion: bool) -> Dict:
        """Check if code is/isn't recursive as required"""
        is_recursive = self._is_recursive(tree)
        
        if requires_recursion and not is_recursive:
            return {
                "compliant": False,
                "violations": ["Must be recursive (contract requirement)"],
                "is_recursive": False
            }
        elif not requires_recursion and is_recursive:
            return {
                "compliant": False,
                "violations": ["Must not be recursive (contract requirement)"],
                "is_recursive": True
            }
        else:
            return {"compliant": True, "violations": [], "is_recursive": is_recursive}
    
    def _check_algorithm(self, tree: ast.AST, algorithm: str) -> Dict:
        """
        Check if code uses the specified algorithm.
        
        Pattern matching for common algorithms:
        - "doubly-linked list" or "doubly linked list"
        - "binary search"
        - "euclidean algorithm"
        - "stack-based matching"
        - etc.
        """
        algo_lower = algorithm.lower()
        violations = []
        
        # Pattern: Doubly-linked list
        if "doubly" in algo_lower and "linked" in algo_lower:
            if not self._has_doubly_linked_list_pattern(tree):
                violations.append(f"Does not use doubly-linked list (required: '{algorithm}')")
        
        # Pattern: Binary search
        elif "binary search" in algo_lower:
            if not self._has_binary_search_pattern(tree):
                violations.append(f"Does not use binary search (required: '{algorithm}')")
        
        # Pattern: Euclidean algorithm
        elif "euclidean" in algo_lower:
            if not self._has_euclidean_pattern(tree):
                violations.append(f"Does not use Euclidean algorithm (required: '{algorithm}')")
        
        # Pattern: Stack-based
        elif "stack" in algo_lower:
            if not self._has_stack_pattern(tree):
                violations.append(f"Does not use stack-based approach (required: '{algorithm}')")
        
        # For other algorithms, we accept any implementation that passes oracle
        # (Can extend pattern matching as needed)
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "algorithm_required": algorithm
        }
    
    # ============================================
    # Pattern Detection Helpers
    # ============================================
    
    def _is_recursive(self, tree: ast.AST) -> bool:
        """Check if any function calls itself"""
        for func in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            func_name = func.name
            for node in ast.walk(func):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == func_name:
                        return True
        return False
    
    def _has_doubly_linked_list_pattern(self, tree: ast.AST) -> bool:
        """
        Detect doubly-linked list pattern.
        
        Requirements:
        - Node class exists
        - Node has 'prev' and 'next' attributes
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "Node":
                # Check for prev/next attributes in __init__
                has_prev = False
                has_next = False
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        for stmt in item.body:
                            if isinstance(stmt, ast.Assign):
                                for target in stmt.targets:
                                    if isinstance(target, ast.Attribute):
                                        if isinstance(target.value, ast.Name) and target.value.id == "self":
                                            if target.attr == "prev":
                                                has_prev = True
                                            elif target.attr == "next":
                                                has_next = True
                
                if has_prev and has_next:
                    return True
        
        return False
    
    def _has_binary_search_pattern(self, tree: ast.AST) -> bool:
        """
        Detect binary search pattern.
        
        Requirements:
        - While or for loop exists
        - Mid-point calculation: mid = (left + right) // 2
        """
        for node in ast.walk(tree):
            if isinstance(node, (ast.While, ast.For)):
                # Look for mid calculation in loop body
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Assign):
                        # Check if it's assigning to 'mid' or 'm'
                        for target in stmt.targets:
                            if isinstance(target, ast.Name) and target.id in ["mid", "m", "middle"]:
                                # Check if value is floor division
                                if isinstance(stmt.value, ast.BinOp):
                                    if isinstance(stmt.value.op, ast.FloorDiv):
                                        return True
        return False
    
    def _has_euclidean_pattern(self, tree: ast.AST) -> bool:
        """
        Detect Euclidean algorithm pattern.
        
        Requirements:
        - Uses modulo operator (%)
        - While loop with swap pattern
        """
        has_modulo = False
        has_while = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
                has_modulo = True
            if isinstance(node, ast.While):
                has_while = True
        
        return has_modulo and has_while
    
    def _has_stack_pattern(self, tree: ast.AST) -> bool:
        """
        Detect stack-based pattern.
        
        Requirements:
        - Variable named 'stack'
        - append() and pop() calls
        """
        has_stack_var = False
        has_append = False
        has_pop = False
        
        for node in ast.walk(tree):
            # Check for stack variable
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and "stack" in target.id.lower():
                        has_stack_var = True
            
            # Check for append/pop calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == "append":
                        has_append = True
                    elif node.func.attr == "pop":
                        has_pop = True
        
        return has_stack_var and has_append and has_pop
