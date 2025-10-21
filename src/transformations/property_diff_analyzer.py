"""
Property Diff Analyzer
Compares two sets of foundational properties and identifies specific mismatches
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import ast
from . import ast_patterns


@dataclass
class PropertyMismatch:
    """Represents a specific mismatch between code and canon properties"""
    property_name: str
    mismatch_type: str
    severity: float  # 0.0 to 1.0, contribution to distance
    details: Dict[str, Any]
    
    def __repr__(self):
        return f"PropertyMismatch({self.property_name}.{self.mismatch_type}, severity={self.severity:.3f})"


class PropertyDiffAnalyzer:
    """
    Analyzes differences between code and canonical properties
    Identifies specific, actionable mismatches for transformation
    """
    
    def __init__(self):
        self.analyzers = {
            "logical_equivalence": self._analyze_logical_equivalence,
            "control_flow_signature": self._analyze_control_flow,
            "data_dependency_graph": self._analyze_data_dependencies,
            "statement_ordering": self._analyze_statement_ordering,
            "normalized_ast_structure": self._analyze_ast_structure,
        }
    
    def analyze(self, code_props: Dict[str, Any], canon_props: Dict[str, Any], 
                code: str, canon_code: str) -> List[PropertyMismatch]:
        """
        Analyze property differences and return specific mismatches
        
        Args:
            code_props: Properties extracted from code
            canon_props: Properties extracted from canonical code
            code: Original code string (for AST pattern matching)
            canon_code: Canonical code string
            
        Returns:
            List of PropertyMismatch objects
        """
        mismatches = []
        
        for prop_name, analyzer_func in self.analyzers.items():
            if prop_name in code_props and prop_name in canon_props:
                prop_mismatches = analyzer_func(
                    code_props[prop_name],
                    canon_props[prop_name],
                    code,
                    canon_code
                )
                mismatches.extend(prop_mismatches)
        
        return mismatches
    
    def _analyze_logical_equivalence(self, code_prop, canon_prop, code, canon_code) -> List[PropertyMismatch]:
        """Analyze logical equivalence differences"""
        mismatches = []
        
        # Parse ASTs for pattern matching
        try:
            code_tree = ast.parse(code)
            canon_tree = ast.parse(canon_code)
        except SyntaxError:
            return mismatches
        
        # Check for len(x) == 0 vs not x pattern
        code_len_matches = ast_patterns.find_pattern_in_tree(code_tree, ast_patterns.match_len_zero_check)
        canon_not_checks = self._find_not_checks(canon_tree)
        
        if code_len_matches and canon_not_checks:
            for match in code_len_matches:
                mismatches.append(PropertyMismatch(
                    property_name="logical_equivalence",
                    mismatch_type="empty_check",
                    severity=0.15,
                    details={
                        "code_pattern": f"len({match['target']}) == 0",
                        "canon_pattern": f"not {match['target']}",
                        "semantic_class": "boolean_simplification",
                        "target_variable": match['target'],
                        "match": match
                    }
                ))
        
        # Check for x == True/False patterns
        code_bool_matches = ast_patterns.find_pattern_in_tree(code_tree, ast_patterns.match_boolean_redundancy)
        
        for match in code_bool_matches:
            mismatches.append(PropertyMismatch(
                property_name="logical_equivalence",
                mismatch_type="boolean_redundancy",
                severity=0.10,
                details={
                    "code_pattern": f"{match['target']} == {match['value']}",
                    "canon_pattern": match['target'] if match['value'] else f"not {match['target']}",
                    "semantic_class": "boolean_simplification",
                    "match": match
                }
            ))
        
        return mismatches
    
    def _analyze_control_flow(self, code_prop, canon_prop, code, canon_code) -> List[PropertyMismatch]:
        """Analyze control flow differences"""
        mismatches = []
        
        if not code_prop or not canon_prop:
            return mismatches
        
        # Check for differences in if statements
        code_ifs = code_prop.get("if_statements", 0)
        canon_ifs = canon_prop.get("if_statements", 0)
        
        if code_ifs > canon_ifs:
            # Check for ternary opportunities
            try:
                code_tree = ast.parse(code)
                ternary_matches = ast_patterns.find_pattern_in_tree(code_tree, ast_patterns.match_ternary_opportunity)
                
                if ternary_matches:
                    for match in ternary_matches:
                        mismatches.append(PropertyMismatch(
                            property_name="control_flow_signature",
                            mismatch_type="ternary_opportunity",
                            severity=0.15,
                            details={
                                "code_pattern": "if-else with returns",
                                "canon_pattern": "ternary expression",
                                "semantic_class": "control_flow_simplification",
                                "match": match
                            }
                        ))
            except SyntaxError:
                pass
        
        # Check for loop differences
        code_loops = code_prop.get("for_loops", 0) + code_prop.get("while_loops", 0)
        canon_loops = canon_prop.get("for_loops", 0) + canon_prop.get("while_loops", 0)
        
        if code_loops != canon_loops:
            mismatches.append(PropertyMismatch(
                property_name="control_flow_signature",
                mismatch_type="loop_count_mismatch",
                severity=0.25,
                details={
                    "code_loops": code_loops,
                    "canon_loops": canon_loops,
                    "semantic_class": "loop_transformation"
                }
            ))
        
        return mismatches
    
    def _analyze_data_dependencies(self, code_prop, canon_prop, code, canon_code) -> List[PropertyMismatch]:
        """Analyze data dependency differences"""
        mismatches = []
        
        if not code_prop or not canon_prop:
            return mismatches
        
        code_deps = code_prop.get("dependencies", {})
        canon_deps = canon_prop.get("dependencies", {})
        
        # Check for variable name differences with same dependency structure
        if len(code_deps) == len(canon_deps) and code_deps != canon_deps:
            mismatches.append(PropertyMismatch(
                property_name="data_dependency_graph",
                mismatch_type="variable_naming",
                severity=0.10,
                details={
                    "code_vars": list(code_deps.keys()),
                    "canon_vars": list(canon_deps.keys()),
                    "semantic_class": "variable_normalization"
                }
            ))
        
        return mismatches
    
    def _analyze_statement_ordering(self, code_prop, canon_prop, code, canon_code) -> List[PropertyMismatch]:
        """Analyze statement ordering differences"""
        mismatches = []
        
        try:
            code_tree = ast.parse(code)
            canon_tree = ast.parse(canon_code)
        except SyntaxError:
            return mismatches
        
        # Check for separate assignment + return vs inline return
        code_sep_match = ast_patterns.match_separate_assign_return(code_tree)
        canon_sep_match = ast_patterns.match_separate_assign_return(canon_tree)
        
        # If code has separate but canon doesn't, that's a mismatch
        if code_sep_match and not canon_sep_match:
            mismatches.append(PropertyMismatch(
                property_name="statement_ordering",
                mismatch_type="return_statement_style",
                severity=0.15,
                details={
                    "code_pattern": "separate assignment + return",
                    "canon_pattern": "inline return",
                    "semantic_class": "return_normalization",
                    "match": code_sep_match
                }
            ))
        
        return mismatches
    
    def _analyze_ast_structure(self, code_prop, canon_prop, code, canon_code) -> List[PropertyMismatch]:
        """Analyze AST structure differences"""
        mismatches = []
        
        try:
            code_tree = ast.parse(code)
            canon_tree = ast.parse(canon_code)
        except SyntaxError:
            return mismatches
        
        # Check for loop vs comprehension
        code_append_match = ast_patterns.match_append_in_loop(code_tree)
        canon_has_comprehension = self._has_list_comprehension(canon_tree)
        
        if code_append_match and canon_has_comprehension:
            mismatches.append(PropertyMismatch(
                property_name="normalized_ast_structure",
                mismatch_type="loop_to_comprehension",
                severity=0.30,
                details={
                    "code_pattern": "for x in y: list.append(x)",
                    "canon_pattern": "[x for x in y]",
                    "semantic_class": "comprehension_conversion",
                    "match": code_append_match
                }
            ))
        
        # Check for string concatenation in loop
        code_concat_match = ast_patterns.match_string_concat_in_loop(code_tree)
        canon_has_join = self._has_string_join(canon_tree)
        
        if code_concat_match and canon_has_join:
            mismatches.append(PropertyMismatch(
                property_name="normalized_ast_structure",
                mismatch_type="string_building",
                severity=0.25,
                details={
                    "code_pattern": "s += char in loop",
                    "canon_pattern": "''.join(...)",
                    "semantic_class": "string_building_idiom",
                    "match": code_concat_match
                }
            ))
        
        return mismatches
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _find_not_checks(self, tree: ast.AST) -> List[Dict]:
        """Find 'not x' patterns in return statements"""
        matches = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Return):
                if isinstance(node.value, ast.UnaryOp) and isinstance(node.value.op, ast.Not):
                    target = ast_patterns.extract_variable_name(node.value.operand)
                    if target:
                        matches.append({'target': target, 'node': node})
        return matches
    
    def _has_list_comprehension(self, tree: ast.AST) -> bool:
        """Check if tree contains list comprehension"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ListComp):
                return True
        return False
    
    def _has_string_join(self, tree: ast.AST) -> bool:
        """Check if tree contains ''.join(...) pattern"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and
                    node.func.attr == 'join' and
                    isinstance(node.func.value, ast.Constant) and
                    isinstance(node.func.value.value, str)):
                    return True
        return False
    
    def calculate_total_severity(self, mismatches: List[PropertyMismatch]) -> float:
        """Calculate total severity score from mismatches"""
        return sum(m.severity for m in mismatches)
    
    def group_by_property(self, mismatches: List[PropertyMismatch]) -> Dict[str, List[PropertyMismatch]]:
        """Group mismatches by property name"""
        grouped = {}
        for mismatch in mismatches:
            if mismatch.property_name not in grouped:
                grouped[mismatch.property_name] = []
            grouped[mismatch.property_name].append(mismatch)
        return grouped
    
    def filter_by_severity(self, mismatches: List[PropertyMismatch], 
                          min_severity: float = 0.0) -> List[PropertyMismatch]:
        """Filter mismatches by minimum severity"""
        return [m for m in mismatches if m.severity >= min_severity]
