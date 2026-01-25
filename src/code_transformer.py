# src/code_transformer.py
"""
Code transformation and repair system for SKYT experiments
Transforms code to match canonical form using foundational properties
"""

import ast
import re
from typing import Dict, Any, List, Optional, Tuple
from .foundational_properties import FoundationalProperties
from .canon_system import CanonSystem


class CodeTransformer:
    """
    Transforms code to match canonical form based on foundational properties
    """
    
    def __init__(self, canon_system: CanonSystem):
        self.canon_system = canon_system
        self.properties_extractor = FoundationalProperties()
        
        # Import and initialize the new modular transformation system
        try:
            from .transformations.transformation_pipeline import TransformationPipeline
            # Pipeline will be created per-transform with contract
            self.use_modular_system = True
            self.modular_pipeline = None  # Created on-demand with contract
        except ImportError:
            print("Warning: Modular transformation system not available, using legacy system")
            self.modular_pipeline = None
            self.use_modular_system = False
        
        # Legacy transformations (kept for compatibility)
        self.transformations = [
            ("normalize_function_names", self._normalize_function_names),
            ("remove_comments_and_docstrings", self._remove_comments_and_docstrings),
            ("normalize_variable_names", self._normalize_variable_names),
            ("remove_print_statements", self._remove_print_statements),
            ("normalize_whitespace", self._normalize_whitespace)
        ]
    
    def transform_to_canon(self, code: str, contract_id: str, 
                          max_iterations: int = 5, contract: Dict[str, Any] = None,
                          oracle_system = None) -> Dict[str, Any]:
        """
        Transform code to match canonical form using intelligent transformation system
        
        Strategy:
        1. Calculate initial distance from canon
        2. If close enough (< 0.1): No transformation needed
        3. Try Level 2: Intelligent simplification (remove redundant statements)
        4. If still not matching, try Level 3: Replace with canonical algorithm
        5. Validate all transformations with oracle tests
        
        Args:
            code: Code to transform
            contract_id: Contract identifier for canon lookup
            max_iterations: Maximum transformation iterations (unused in new system)
            contract: Contract data for validation
            oracle_system: Oracle system for post-transformation validation
            
        Returns:
            Transformation results with success status and transformed code
        """
        # Get canonical data for comparison
        canon_data = self.canon_system.load_canon(contract_id)
        if not canon_data:
            return {
                "success": False,
                "error": "No canon found for contract",
                "original_code": code,
                "transformed_code": code,
                "transformations_applied": [],
                "final_distance": 1.0,
                "transformation_level": 0
            }
        
        canon_code = canon_data.get("canonical_code", "")
        canon_properties = canon_data.get("foundational_properties", {})
        
        # Calculate initial distance
        initial_properties = self.properties_extractor.extract_all_properties(code)
        initial_distance = self.properties_extractor.calculate_distance(
            canon_properties, initial_properties
        )
        
        # If already close enough, no transformation needed
        if initial_distance < 0.1:
            return {
                "success": True,
                "original_code": code,
                "transformed_code": code,
                "final_distance": initial_distance,
                "transformation_level": 0,
                "transformations_applied": [],
                "iterations": 0
            }
        
        # Try Level 2: Intelligent simplification (pattern-agnostic)
        try:
            from .transformations.intelligent_simplifier import intelligent_simplify
            
            if oracle_system and contract:
                level2_result = intelligent_simplify(code, canon_code, contract, oracle_system)
                
                if level2_result.get('success'):
                    # Check if it matches canon now
                    level2_properties = self.properties_extractor.extract_all_properties(
                        level2_result['transformed_code']
                    )
                    level2_distance = self.properties_extractor.calculate_distance(
                        canon_properties, level2_properties
                    )
                    
                    if level2_distance < 0.1:
                        # Success with Level 2!
                        return {
                            "success": True,
                            "original_code": code,
                            "transformed_code": level2_result['transformed_code'],
                            "final_distance": level2_distance,
                            "transformation_level": 2,
                            "transformations_applied": level2_result.get('removed_statements', []),
                            "iterations": 1
                        }
        except ImportError:
            pass  # Level 2 not available, continue to Level 3
        
        # Level 2 didn't work or not available, try Level 3: Replace with canon
        try:
            from .transformations.convert_to_simple_algorithm import convert_to_simple_algorithm
            
            level3_result = convert_to_simple_algorithm(code, canon_code, contract)
            
            if level3_result.get('success'):
                # Validate with oracle if available
                if oracle_system and contract:
                    oracle_result = oracle_system.run_oracle_tests(
                        level3_result['transformed_code'], 
                        contract
                    )
                    
                    if not oracle_result.get('passed', False):
                        # Transformation broke correctness - revert
                        return {
                            "success": False,
                            "error": "Transformation failed oracle validation",
                            "original_code": code,
                            "transformed_code": code,
                            "final_distance": initial_distance,
                            "transformation_level": 0,
                            "transformations_applied": [],
                            "iterations": 0
                        }
                
                # Success with Level 3!
                return {
                    "success": True,
                    "original_code": code,
                    "transformed_code": level3_result['transformed_code'],
                    "final_distance": 0.0,  # Exact match to canon
                    "transformation_level": 3,
                    "transformations_applied": level3_result.get('transformations', []),
                    "iterations": 1
                }
        except ImportError:
            pass  # Level 3 not available
        
        # All transformations failed
        final_properties = self.properties_extractor.extract_all_properties(code)
        final_distance = self.properties_extractor.calculate_distance(
            canon_properties, final_properties
        )
        
        return {
            "success": False,
            "error": "Could not transform to canonical form",
            "original_code": code,
            "transformed_code": code,
            "final_distance": final_distance,
            "transformation_level": 0,
            "transformations_applied": [],
            "iterations": 0
        }
    
    def _find_best_transformation(self, code: str, current_props: Dict[str, Any], 
                                canon_props: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find the best transformation rule to apply next"""
        
        # Analyze property differences to choose transformation
        differences = self.canon_system._find_property_differences(canon_props, current_props)
        
        if not differences:
            return None
        
        # Sort by severity and choose most impactful
        differences.sort(key=lambda x: x["distance"], reverse=True)
        
        for diff in differences:
            prop_name = diff["property"]
            
            # Map property differences to transformation rules
            if prop_name == "normalized_ast_structure":
                return {
                    "rule_name": "normalize_whitespace",
                    "transform_func": self._normalize_whitespace,
                    "params": {}
                }
            elif prop_name == "control_flow_signature":
                return {
                    "rule_name": "normalize_control_flow", 
                    "transform_func": self._normalize_control_flow,
                    "params": {"target_signature": diff["canon_value"]}
                }
            elif prop_name == "statement_ordering":
                return {
                    "rule_name": "normalize_statements",
                    "transform_func": self._normalize_statements,
                    "params": {}
                }
        
        # Default to whitespace normalization
        return {
            "rule_name": "normalize_whitespace",
            "transform_func": self._normalize_whitespace,
            "params": {}
        }
    
    def _normalize_whitespace(self, code: str, params: Dict[str, Any]) -> str:
        """Normalize whitespace and indentation"""
        lines = []
        for line in code.split('\n'):
            if line.strip():
                # Normalize indentation to 4 spaces
                stripped = line.lstrip()
                if stripped:
                    indent_level = (len(line) - len(stripped)) // 4
                    normalized_line = '    ' * indent_level + stripped
                    lines.append(normalized_line)
        
        return '\n'.join(lines)
    
    def _normalize_function_names(self, code: str, params: Dict[str, Any]) -> str:
        """Normalize function names to canonical forms"""
        # Common function name normalizations
        normalizations = {
            r'\bfib\b': 'fibonacci',
            r'\bfibonacci_sequence\b': 'fibonacci',
            r'\bfib_seq\b': 'fibonacci',
            r'\bgenerate_fibonacci\b': 'fibonacci',
            r'\bmerge_sort\b': 'merge_sort',
            r'\bmergesort\b': 'merge_sort',
            r'\bbinary_search\b': 'binary_search',
            r'\bbinsearch\b': 'binary_search'
        }
        
        normalized = code
        for pattern, replacement in normalizations.items():
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized
    
    def _remove_comments_and_docstrings(self, code: str, params: Dict[str, Any]) -> str:
        """Remove comments and docstrings"""
        try:
            tree = ast.parse(code)
            
            # Remove docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                    if (node.body and isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)):
                        node.body.pop(0)
            
            # Convert back to code
            import astor
            return astor.to_source(tree)
            
        except:
            # Fallback: remove comments manually
            lines = []
            for line in code.split('\n'):
                if '#' in line:
                    line = line[:line.index('#')]
                if line.strip():
                    lines.append(line)
            
            return '\n'.join(lines)
    
    def _remove_redundant_clauses(self, code: str, params: Dict[str, Any]) -> str:
        """Remove all types of redundant clauses that don't affect behavior"""
        try:
            tree = ast.parse(code)
            
            class RedundantClauseRemover(ast.NodeTransformer):
                def visit_If(self, node):
                    # Recursively process nested structures first
                    self.generic_visit(node)
                    
                    # Remove redundant else clauses
                    node = self._remove_redundant_else(node)
                    
                    # Remove redundant elif clauses
                    node = self._remove_redundant_elif(node)
                    
                    # Remove redundant nested conditions
                    node = self._remove_redundant_nested_conditions(node)
                    
                    return node
                
                def visit_Try(self, node):
                    # Remove redundant try-except blocks
                    self.generic_visit(node)
                    return self._remove_redundant_try_except(node)
                
                def visit_While(self, node):
                    # Remove redundant while loops (like while True with immediate break)
                    self.generic_visit(node)
                    return self._remove_redundant_while(node)
                
                def visit_For(self, node):
                    # Remove redundant for loops
                    self.generic_visit(node)
                    return self._remove_redundant_for(node)
                
                def _remove_redundant_else(self, node):
                    """Remove redundant else clauses"""
                    if not node.orelse:
                        return node
                    
                    # Case 1: if-elif-else where both if and elif have returns
                    if (len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If)):
                        elif_node = node.orelse[0]
                        if (elif_node.orelse and not isinstance(elif_node.orelse[0], ast.If)):
                            # Check if both branches return
                            if_has_return = any(isinstance(stmt, ast.Return) for stmt in node.body)
                            elif_has_return = any(isinstance(stmt, ast.Return) for stmt in elif_node.body)
                            
                            if if_has_return and elif_has_return:
                                # Remove the else clause as it's unreachable
                                elif_node.orelse = []
                    
                    # Case 2: Direct else after if with return
                    elif not isinstance(node.orelse[0], ast.If):
                        if_has_return = any(isinstance(stmt, ast.Return) for stmt in node.body)
                        if if_has_return:
                            # Check if else is just the same logic that would execute anyway
                            # For now, be conservative and only remove if else is empty or trivial
                            if (len(node.orelse) == 1 and 
                                isinstance(node.orelse[0], ast.Pass)):
                                node.orelse = []
                    
                    return node
                
                def _remove_redundant_elif(self, node):
                    """Remove redundant elif clauses"""
                    if not node.orelse:
                        return node
                    
                    # Check for elif conditions that are always false given previous conditions
                    # This is complex, so we'll implement basic cases
                    
                    # Case: if n <= 0: ... elif n < 0: ... (second condition is redundant)
                    if (len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If)):
                        elif_node = node.orelse[0]
                        
                        # Simple pattern matching for common redundancies
                        if (isinstance(node.test, ast.Compare) and 
                            isinstance(elif_node.test, ast.Compare)):
                            
                            # Check if conditions are on same variable
                            if (hasattr(node.test.left, 'id') and 
                                hasattr(elif_node.test.left, 'id') and
                                node.test.left.id == elif_node.test.left.id):
                                
                                # Pattern: if n <= 0 elif n < 0 (redundant)
                                if (len(node.test.ops) == 1 and len(elif_node.test.ops) == 1):
                                    if_op = node.test.ops[0]
                                    elif_op = elif_node.test.ops[0]
                                    
                                    if (isinstance(if_op, ast.LtE) and isinstance(elif_op, ast.Lt) and
                                        isinstance(node.test.comparators[0], ast.Constant) and
                                        isinstance(elif_node.test.comparators[0], ast.Constant) and
                                        node.test.comparators[0].value == elif_node.test.comparators[0].value):
                                        # Remove redundant elif
                                        node.orelse = elif_node.orelse
                    
                    return node
                
                def _remove_redundant_nested_conditions(self, node):
                    """Remove redundant nested conditions"""
                    # Pattern: if condition: if same_condition: ... -> if condition: ...
                    if (len(node.body) == 1 and isinstance(node.body[0], ast.If)):
                        nested_if = node.body[0]
                        
                        # Check if conditions are the same (simplified check)
                        if ast.dump(node.test) == ast.dump(nested_if.test):
                            # Flatten the nested structure
                            node.body = nested_if.body
                            if nested_if.orelse:
                                node.orelse = nested_if.orelse
                    
                    return node
                
                def _remove_redundant_try_except(self, node):
                    """Remove redundant try-except blocks"""
                    # Remove try blocks that don't actually need exception handling
                    # This is conservative - only remove obvious cases
                    
                    # Case: try block with only safe operations and generic except
                    if (len(node.handlers) == 1 and 
                        not node.handlers[0].type and  # Generic except
                        len(node.handlers[0].body) == 1 and
                        isinstance(node.handlers[0].body[0], ast.Pass)):
                        # If try block has no risky operations, remove try-except
                        has_risky_ops = False
                        for stmt in ast.walk(node):
                            if isinstance(stmt, (ast.Raise, ast.Call)):
                                has_risky_ops = True
                                break
                        
                        if not has_risky_ops:
                            # Return just the try body
                            return node.body
                    
                    return node
                
                def _remove_redundant_while(self, node):
                    """Remove redundant while loops"""
                    # Pattern: while True: ... break -> just the body (if appropriate)
                    if (isinstance(node.test, ast.Constant) and node.test.value is True):
                        # Check if loop has immediate break
                        if (len(node.body) > 0 and 
                            isinstance(node.body[-1], ast.Break)):
                            # This is effectively just the statements before break
                            return node.body[:-1]
                    
                    return node
                
                def _remove_redundant_for(self, node):
                    """Remove redundant for loops"""
                    # Pattern: for _ in range(1): ... -> just the body
                    if (isinstance(node.iter, ast.Call) and
                        isinstance(node.iter.func, ast.Name) and
                        node.iter.func.id == 'range' and
                        len(node.iter.args) == 1 and
                        isinstance(node.iter.args[0], ast.Constant) and
                        node.iter.args[0].value == 1):
                        # Single iteration loop - just return the body
                        return node.body
                    
                    return node
            
            remover = RedundantClauseRemover()
            modified_tree = remover.visit(tree)
            
            # Convert back to code
            import astor
            return astor.to_source(modified_tree)
            
        except Exception:
            # If transformation fails, return original code
            return code
    
    def _align_error_handling(self, code: str, params: Dict[str, Any]) -> str:
        """Align error handling to match canonical form exactly"""
        try:
            # Get canonical code for comparison
            canon_data = self.canon_system.load_canon(params.get("contract_id", ""))
            if not canon_data:
                return code
            
            canon_code = canon_data.get("canonical_code", "")
            if not canon_code:
                return code
            
            # Parse both current code and canonical code
            current_tree = ast.parse(code)
            canon_tree = ast.parse(canon_code)
            
            # Extract error handling patterns from canonical code
            canon_error_patterns = self._extract_error_patterns(canon_tree)
            
            # Transform current code to match canonical error handling
            class ErrorHandlingAligner(ast.NodeTransformer):
                def __init__(self, canon_patterns):
                    self.canon_patterns = canon_patterns
                
                def visit_FunctionDef(self, node):
                    # Only process the main function
                    if node.name in self.canon_patterns:
                        canon_pattern = self.canon_patterns[node.name]
                        node = self._align_function_error_handling(node, canon_pattern)
                    
                    self.generic_visit(node)
                    return node
                
                def _align_function_error_handling(self, func_node, canon_pattern):
                    """Align function's error handling to canonical pattern"""
                    
                    # If canon has no error handling, remove all error handling
                    if not canon_pattern["has_error_handling"]:
                        func_node.body = self._remove_error_handling(func_node.body)
                    
                    # If canon has specific error handling, match it exactly
                    elif canon_pattern["has_error_handling"]:
                        func_node.body = self._match_error_handling(func_node.body, canon_pattern)
                    
                    return func_node
                
                def _remove_error_handling(self, body):
                    """Remove all error handling (raise statements and error conditions)"""
                    new_body = []
                    
                    for stmt in body:
                        if isinstance(stmt, ast.Raise):
                            # Skip raise statements entirely
                            continue
                        elif isinstance(stmt, ast.If):
                            # Check if this is an error condition
                            if self._is_error_condition(stmt):
                                # Convert error condition to canonical form
                                stmt = self._convert_error_to_canonical(stmt)
                            new_body.append(stmt)
                        else:
                            new_body.append(stmt)
                    
                    return new_body
                
                def _match_error_handling(self, body, canon_pattern):
                    """Match error handling to canonical pattern exactly"""
                    # This would implement adding error handling if canon has it
                    # For now, focus on removal case
                    return self._remove_error_handling(body)
                
                def _is_error_condition(self, if_node):
                    """Check if an if statement is an error condition"""
                    # Look for patterns like: if n < 0: raise ValueError(...)
                    if not if_node.body:
                        return False
                    
                    # Check if body contains raise statement
                    for stmt in if_node.body:
                        if isinstance(stmt, ast.Raise):
                            return True
                    
                    return False
                
                def _convert_error_to_canonical(self, if_node):
                    """Convert error condition to canonical boundary check"""
                    # Pattern: if n < 0: raise ValueError(...) → if n <= 0: return 0
                    
                    # Check if this matches the pattern: if n < 0
                    if (isinstance(if_node.test, ast.Compare) and
                        len(if_node.test.ops) == 1 and
                        isinstance(if_node.test.ops[0], ast.Lt) and
                        isinstance(if_node.test.left, ast.Name) and
                        if_node.test.left.id == 'n' and
                        isinstance(if_node.test.comparators[0], ast.Constant) and
                        if_node.test.comparators[0].value == 0):
                        
                        # Convert to: if n <= 0: return 0
                        new_test = ast.Compare(
                            left=ast.Name(id='n', ctx=ast.Load()),
                            ops=[ast.LtE()],
                            comparators=[ast.Constant(value=0)]
                        )
                        
                        new_body = [ast.Return(value=ast.Constant(value=0))]
                        
                        if_node.test = new_test
                        if_node.body = new_body
                        if_node.orelse = []  # Remove any else clause
                    
                    return if_node
            
            # Apply the transformation
            aligner = ErrorHandlingAligner(canon_error_patterns)
            transformed_tree = aligner.visit(current_tree)
            
            # Convert back to code
            import astor
            return astor.to_source(transformed_tree)
            
        except Exception as e:
            # If transformation fails, return original code
            return code
    
    def _extract_error_patterns(self, canon_tree):
        """Extract error handling patterns from canonical code"""
        patterns = {}
        
        for node in ast.walk(canon_tree):
            if isinstance(node, ast.FunctionDef):
                pattern = {
                    "has_error_handling": False,
                    "error_conditions": [],
                    "boundary_conditions": []
                }
                
                # Check if function has any raise statements
                for child in ast.walk(node):
                    if isinstance(child, ast.Raise):
                        pattern["has_error_handling"] = True
                        break
                
                # Extract boundary conditions (like if n <= 0: return 0)
                for stmt in node.body:
                    if isinstance(stmt, ast.If):
                        pattern["boundary_conditions"].append(ast.dump(stmt.test))
                
                patterns[node.name] = pattern
        
        return patterns
    
    def _normalize_variable_names(self, code: str, params: Dict[str, Any]) -> str:
        """Normalize variable names to canonical forms"""
        try:
            tree = ast.parse(code)
            
            class VariableNormalizer(ast.NodeTransformer):
                def __init__(self):
                    self.var_map = {}
                    self.counter = 0
                
                def visit_Name(self, node):
                    if isinstance(node.ctx, ast.Store):
                        if node.id not in self.var_map:
                            self.var_map[node.id] = f"var_{self.counter}"
                            self.counter += 1
                        node.id = self.var_map[node.id]
                    elif isinstance(node.ctx, ast.Load):
                        if node.id in self.var_map:
                            node.id = self.var_map[node.id]
                    
                    return node
            
            normalizer = VariableNormalizer()
            normalized_tree = normalizer.visit(tree)
            
            import astor
            return astor.to_source(normalized_tree)
            
        except:
            return code
    
    def _remove_print_statements(self, code: str, params: Dict[str, Any]) -> str:
        """Remove print statements that don't affect behavior"""
        try:
            tree = ast.parse(code)
            
            class PrintRemover(ast.NodeTransformer):
                def visit_Expr(self, node):
                    # Remove standalone print statements
                    if (isinstance(node.value, ast.Call) and
                        isinstance(node.value.func, ast.Name) and
                        node.value.func.id == 'print'):
                        return None  # Remove this node
                    return node
            
            remover = PrintRemover()
            modified_tree = remover.visit(tree)
            
            # Convert back to code
            import astor
            return astor.to_source(modified_tree)
            
        except Exception:
            return code
    
    def _normalize_control_flow(self, code: str, params: Dict[str, Any]) -> str:
        """Normalize control flow structures"""
        # This is a simplified version - could be much more sophisticated
        try:
            tree = ast.parse(code)
            
            class ControlFlowNormalizer(ast.NodeTransformer):
                def visit_If(self, node):
                    # Normalize if statements
                    self.generic_visit(node)
                    return node
                
                def visit_For(self, node):
                    # Normalize for loops
                    self.generic_visit(node)
                    return node
            
            normalizer = ControlFlowNormalizer()
            normalized_tree = normalizer.visit(tree)
            
            import astor
            return astor.to_source(normalized_tree)
            
        except:
            return code
    
    def _normalize_operators(self, code: str, params: Dict[str, Any]) -> str:
        """Normalize operator usage"""
        # Simple operator normalizations
        normalizations = [
            (r'\s*\+\s*', ' + '),
            (r'\s*-\s*', ' - '),
            (r'\s*\*\s*', ' * '),
            (r'\s*/\s*', ' / '),
            (r'\s*==\s*', ' == '),
            (r'\s*!=\s*', ' != '),
            (r'\s*<=\s*', ' <= '),
            (r'\s*>=\s*', ' >= '),
        ]
        
        normalized = code
        for pattern, replacement in normalizations:
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized
    
    def _normalize_statements(self, code: str, params: Dict[str, Any]) -> str:
        """Normalize statement ordering and structure"""
        try:
            tree = ast.parse(code)
            
            # Sort imports, function definitions, etc.
            class StatementNormalizer(ast.NodeTransformer):
                def visit_Module(self, node):
                    # Separate different types of statements
                    imports = []
                    functions = []
                    other = []
                    
                    for stmt in node.body:
                        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                            imports.append(stmt)
                        elif isinstance(stmt, ast.FunctionDef):
                            functions.append(stmt)
                        else:
                            other.append(stmt)
                    
                    # Reorder: imports, functions, other
                    node.body = imports + functions + other
                    
                    self.generic_visit(node)
                    return node
            
            normalizer = StatementNormalizer()
            normalized_tree = normalizer.visit(tree)
            
            import astor
            return astor.to_source(normalized_tree)
            
        except:
            return code
