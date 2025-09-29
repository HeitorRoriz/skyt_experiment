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
        
        # Transformation rules ordered by safety (safest first)
        self.transformation_rules = [
            self._normalize_whitespace,
            self._normalize_function_names,
            self._remove_comments_and_docstrings,
            self._normalize_variable_names,
            self._normalize_control_flow,
            self._normalize_operators,
            self._normalize_statements
        ]
    
    def transform_to_canon(self, code: str, contract_id: str, 
                          max_iterations: int = 5) -> Dict[str, Any]:
        """
        Transform code to match canonical form
        
        Args:
            code: Code to transform
            contract_id: Contract identifier for canon lookup
            max_iterations: Maximum transformation iterations
            
        Returns:
            Transformation results with success status and transformed code
        """
        canon_data = self.canon_system.load_canon(contract_id)
        
        if not canon_data:
            return {
                "success": False,
                "error": "No canon found for contract",
                "original_code": code,
                "transformed_code": code,
                "transformations_applied": []
            }
        
        canon_properties = canon_data["foundational_properties"]
        current_code = code
        transformations_applied = []
        
        for iteration in range(max_iterations):
            # Extract current properties
            current_properties = self.properties_extractor.extract_all_properties(current_code)
            
            # Calculate distance to canon
            distance = self.properties_extractor.calculate_distance(
                canon_properties, current_properties
            )
            
            if distance == 0.0:
                # Perfect match achieved
                return {
                    "success": True,
                    "original_code": code,
                    "transformed_code": current_code,
                    "final_distance": distance,
                    "iterations": iteration + 1,
                    "transformations_applied": transformations_applied
                }
            
            # Find best transformation to apply
            best_transformation = self._find_best_transformation(
                current_code, current_properties, canon_properties
            )
            
            if not best_transformation:
                # No more transformations possible
                break
            
            # Apply transformation
            try:
                transformed_code = best_transformation["transform_func"](
                    current_code, best_transformation["params"]
                )
                
                # Verify transformation improved distance
                new_properties = self.properties_extractor.extract_all_properties(transformed_code)
                new_distance = self.properties_extractor.calculate_distance(
                    canon_properties, new_properties
                )
                
                if new_distance < distance:
                    current_code = transformed_code
                    transformations_applied.append({
                        "rule": best_transformation["rule_name"],
                        "iteration": iteration + 1,
                        "distance_before": distance,
                        "distance_after": new_distance,
                        "improvement": distance - new_distance
                    })
                else:
                    # Transformation didn't help, stop
                    break
                    
            except Exception as e:
                transformations_applied.append({
                    "rule": best_transformation["rule_name"],
                    "iteration": iteration + 1,
                    "error": str(e),
                    "failed": True
                })
                break
        
        # Final distance calculation
        final_properties = self.properties_extractor.extract_all_properties(current_code)
        final_distance = self.properties_extractor.calculate_distance(
            canon_properties, final_properties
        )
        
        return {
            "success": final_distance < 0.1,  # Consider success if very close
            "original_code": code,
            "transformed_code": current_code,
            "final_distance": final_distance,
            "iterations": len(transformations_applied),
            "transformations_applied": transformations_applied
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
    
    def _normalize_variable_names(self, code: str, params: Dict[str, Any]) -> str:
        """Normalize variable names to canonical forms"""
        try:
            tree = ast.parse(code)
            
            # Simple variable renaming (could be more sophisticated)
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
