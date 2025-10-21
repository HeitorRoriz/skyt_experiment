"""
Property Explainers
Explain HOW and WHY foundational properties differ between code and canon.
This enables true property-driven transformations rather than pattern matching.
"""

import ast
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field


@dataclass
class PropertyDifference:
    """
    Structured explanation of how a property differs
    Provides actionable information for transformation strategies
    """
    property_name: str
    difference_type: str  # Specific type of difference (e.g., "statement_count_mismatch")
    severity: float  # 0.0 to 1.0
    explanation: str  # Human-readable explanation
    transformation_hints: Dict[str, Any] = field(default_factory=dict)  # Hints for strategy
    code_details: Dict[str, Any] = field(default_factory=dict)  # What code has
    canon_details: Dict[str, Any] = field(default_factory=dict)  # What canon has
    
    def __repr__(self):
        return f"PropertyDifference({self.property_name}.{self.difference_type}, severity={self.severity:.3f})"


class PropertyExplainer(ABC):
    """
    Abstract base for property explainers
    Each explainer understands ONE foundational property deeply
    """
    
    def __init__(self, property_name: str):
        self.property_name = property_name
    
    @abstractmethod
    def explain_difference(self, 
                          code_prop: Dict[str, Any], 
                          canon_prop: Dict[str, Any],
                          code: str, 
                          canon_code: str) -> Optional[PropertyDifference]:
        """
        Analyze property values and explain the difference
        
        Args:
            code_prop: Property value from code
            canon_prop: Property value from canon
            code: Original code string
            canon_code: Canonical code string
            
        Returns:
            PropertyDifference if difference found and explainable, None otherwise
        """
        pass
    
    def _parse_safely(self, code: str) -> Optional[ast.AST]:
        """Safely parse code, return None on error"""
        try:
            return ast.parse(code)
        except SyntaxError:
            return None


class StatementOrderingExplainer(PropertyExplainer):
    """
    Explains differences in statement ordering and structure
    Detects: consecutive statements that can be consolidated, reordered, etc.
    """
    
    def __init__(self):
        super().__init__("statement_ordering")
    
    def explain_difference(self, code_prop, canon_prop, code, canon_code) -> Optional[PropertyDifference]:
        """Explain statement ordering differences"""
        if not code_prop or not canon_prop:
            return None
        
        code_tree = self._parse_safely(code)
        canon_tree = self._parse_safely(canon_code)
        
        if not code_tree or not canon_tree:
            return None
        
        # Check for consecutive assign + return pattern
        code_pattern = self._analyze_statement_pattern(code_tree)
        canon_pattern = self._analyze_statement_pattern(canon_tree)
        
        if code_pattern and canon_pattern:
            if code_pattern['type'] == 'separate_assign_return' and canon_pattern['type'] == 'inline_return':
                return PropertyDifference(
                    property_name="statement_ordering",
                    difference_type="consecutive_statements_consolidatable",
                    severity=0.15,
                    explanation=f"Code has separate assignment + return that can be consolidated to inline return",
                    transformation_hints={
                        'pattern': 'separate_to_inline',
                        'variable': code_pattern.get('variable'),
                        'method_call': code_pattern.get('method_call')
                    },
                    code_details=code_pattern,
                    canon_details=canon_pattern
                )
            elif code_pattern['type'] == 'chained_assignments' and canon_pattern['type'] == 'inline_return':
                return PropertyDifference(
                    property_name="statement_ordering",
                    difference_type="chained_statements_consolidatable",
                    severity=0.25,
                    explanation="Code has chained assignments that can be collapsed into a single inline return",
                    transformation_hints={
                        'pattern': 'chain_to_inline',
                        'variable': code_pattern.get('variable'),
                        'chain_length': code_pattern.get('chain_length', 2)
                    },
                    code_details=code_pattern,
                    canon_details=canon_pattern
                )
        
        return None
    
    def _analyze_statement_pattern(self, tree: ast.AST) -> Optional[Dict[str, Any]]:
        """Analyze statement pattern in function body"""
        func_def = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_def = node
                break
        
        if not func_def or len(func_def.body) < 1:
            return None
        
        # Check last statement
        last = func_def.body[-1]

        if isinstance(last, ast.Return) and last.value:
            # Check if it's an inline method call (return var.method())
            if isinstance(last.value, ast.Call) and isinstance(last.value.func, ast.Attribute):
                return {
                    'type': 'inline_return',
                    'method': last.value.func.attr,
                    'has_call': True
                }
            # Check if it's returning a variable
            elif isinstance(last.value, ast.Name):
                # Look for preceding assignment to same variable
                if len(func_def.body) >= 2:
                    second_last = func_def.body[-2]
                    if isinstance(second_last, ast.Assign):
                        if (len(second_last.targets) == 1 and 
                            isinstance(second_last.targets[0], ast.Name) and
                            second_last.targets[0].id == last.value.id):
                            # ANY assignment to this variable counts
                            return {
                                'type': 'separate_assign_return',
                                'variable': last.value.id,
                                'has_method_call': isinstance(second_last.value, ast.Call) and 
                                                  isinstance(second_last.value.func, ast.Attribute)
                            }
                    # Check for chained assignments to same variable before return
                    if len(func_def.body) >= 3:
                        second_last = func_def.body[-2]
                        third_last = func_def.body[-3]
                        if (isinstance(second_last, ast.Assign) and isinstance(third_last, ast.Assign)):
                            if (len(second_last.targets) == 1 and len(third_last.targets) == 1 and
                                isinstance(second_last.targets[0], ast.Name) and
                                isinstance(third_last.targets[0], ast.Name) and
                                second_last.targets[0].id == last.value.id == third_last.targets[0].id):
                                if (isinstance(second_last.value, ast.Call) and
                                    isinstance(second_last.value.func, ast.Attribute) and
                                    isinstance(second_last.value.func.value, ast.Name) and
                                    second_last.value.func.value.id == last.value.id):
                                    return {
                                        'type': 'chained_assignments',
                                        'variable': last.value.id,
                                        'chain_length': 2
                                    }
        
        return None


class LogicalEquivalenceExplainer(PropertyExplainer):
    """
    Explains differences in logical expressions
    Detects: boolean simplifications, redundant comparisons, etc.
    """
    
    def __init__(self):
        super().__init__("logical_equivalence")
    
    def explain_difference(self, code_prop, canon_prop, code, canon_code) -> Optional[PropertyDifference]:
        """Explain logical equivalence differences"""
        code_tree = self._parse_safely(code)
        canon_tree = self._parse_safely(canon_code)
        
        if not code_tree or not canon_tree:
            return None
        
        # Check for len(x) == 0 vs not x pattern
        code_len_check = self._find_len_zero_check(code_tree)
        canon_not_check = self._find_not_check(canon_tree)
        
        if code_len_check and canon_not_check:
            return PropertyDifference(
                property_name="logical_equivalence",
                difference_type="empty_check_form",
                severity=0.15,
                explanation=f"Code uses 'len({code_len_check['target']}) == 0' vs canon uses 'not {code_len_check['target']}'",
                transformation_hints={
                    'pattern': 'len_to_not',
                    'target': code_len_check['target'],
                    'operator': code_len_check['operator']
                },
                code_details={'form': 'len_comparison', 'target': code_len_check['target']},
                canon_details={'form': 'not_expression', 'target': code_len_check['target']}
            )
        
        # Check for boolean redundancy (x == True/False)
        bool_redundancy = self._find_boolean_redundancy(code_tree)
        if bool_redundancy:
            return PropertyDifference(
                property_name="logical_equivalence",
                difference_type="boolean_redundancy",
                severity=0.10,
                explanation=f"Code has redundant boolean comparison: {bool_redundancy['pattern']}",
                transformation_hints={
                    'pattern': 'boolean_redundancy',
                    'target': bool_redundancy['target'],
                    'value': bool_redundancy['value'],
                    'operator': bool_redundancy['operator']
                },
                code_details=bool_redundancy,
                canon_details={'form': 'direct_boolean'}
            )
        
        return None
    
    def _find_len_zero_check(self, tree: ast.AST) -> Optional[Dict[str, Any]]:
        """Find len(x) == 0 or len(x) != 0 pattern"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                if (isinstance(node.left, ast.Call) and
                    isinstance(node.left.func, ast.Name) and
                    node.left.func.id == 'len' and
                    len(node.left.args) == 1 and
                    len(node.ops) == 1 and
                    len(node.comparators) == 1 and
                    isinstance(node.comparators[0], ast.Constant) and
                    node.comparators[0].value == 0):
                    
                    target_arg = node.left.args[0]
                    if isinstance(target_arg, ast.Name):
                        return {
                            'target': target_arg.id,
                            'operator': type(node.ops[0]).__name__
                        }
        return None
    
    def _find_not_check(self, tree: ast.AST) -> bool:
        """Find 'not x' pattern in return"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Return) and node.value:
                if isinstance(node.value, ast.UnaryOp) and isinstance(node.value.op, ast.Not):
                    return True
        return False
    
    def _find_boolean_redundancy(self, tree: ast.AST) -> Optional[Dict[str, Any]]:
        """Find x == True/False patterns"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                if (len(node.ops) == 1 and
                    len(node.comparators) == 1 and
                    isinstance(node.comparators[0], ast.Constant) and
                    isinstance(node.comparators[0].value, bool)):
                    
                    if isinstance(node.left, ast.Name):
                        return {
                            'target': node.left.id,
                            'operator': type(node.ops[0]).__name__,
                            'value': node.comparators[0].value,
                            'pattern': f"{node.left.id} {self._op_to_str(node.ops[0])} {node.comparators[0].value}"
                        }
        return None
    
    def _op_to_str(self, op):
        """Convert operator to string"""
        if isinstance(op, ast.Eq):
            return "=="
        elif isinstance(op, ast.NotEq):
            return "!="
        return str(type(op).__name__)


class NormalizedASTStructureExplainer(PropertyExplainer):
    """
    Explains differences in AST structure
    Detects: loop vs comprehension, different idioms for same operation, etc.
    """
    
    def __init__(self):
        super().__init__("normalized_ast_structure")
    
    def explain_difference(self, code_prop, canon_prop, code, canon_code) -> Optional[PropertyDifference]:
        """Explain AST structure differences"""
        code_tree = self._parse_safely(code)
        canon_tree = self._parse_safely(canon_code)
        
        if not code_tree or not canon_tree:
            return None
        
        # Check for loop with append vs list comprehension
        code_has_append_loop = self._find_append_loop(code_tree)
        canon_has_comprehension = self._find_list_comprehension(canon_tree)
        
        if code_has_append_loop and canon_has_comprehension:
            return PropertyDifference(
                property_name="normalized_ast_structure",
                difference_type="loop_vs_comprehension",
                severity=0.30,
                explanation="Code uses loop with append, canon uses list comprehension",
                transformation_hints={
                    'pattern': 'loop_to_comprehension',
                    'loop_details': code_has_append_loop
                },
                code_details={'idiom': 'loop_append'},
                canon_details={'idiom': 'list_comprehension'}
            )
        
        # Check for string concatenation in loop vs join
        code_has_string_concat = self._find_string_concat_loop(code_tree)
        canon_has_join = self._find_join_pattern(canon_tree)
        
        if code_has_string_concat and canon_has_join:
            return PropertyDifference(
                property_name="normalized_ast_structure",
                difference_type="string_building_idiom",
                severity=0.25,
                explanation="Code uses += in loop, canon uses str.join()",
                transformation_hints={
                    'pattern': 'concat_to_join',
                    'loop_details': code_has_string_concat
                },
                code_details={'idiom': 'loop_concat'},
                canon_details={'idiom': 'string_join'}
            )
        
        return None
    
    def _find_append_loop(self, tree: ast.AST) -> Optional[Dict[str, Any]]:
        """Find loop with list.append() pattern"""
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                for stmt in node.body:
                    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                        if (isinstance(stmt.value.func, ast.Attribute) and
                            stmt.value.func.attr == 'append'):
                            return {'found': True}
        return None
    
    def _find_list_comprehension(self, tree: ast.AST) -> bool:
        """Check if tree has list comprehension"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ListComp):
                return True
        return False
    
    def _find_string_concat_loop(self, tree: ast.AST) -> Optional[Dict[str, Any]]:
        """Find loop with += string concatenation"""
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                for stmt in node.body:
                    if isinstance(stmt, ast.AugAssign) and isinstance(stmt.op, ast.Add):
                        return {'found': True}
        return None
    
    def _find_join_pattern(self, tree: ast.AST) -> bool:
        """Check if tree uses str.join()"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and
                    node.func.attr == 'join'):
                    return True
        return False


class ControlFlowSignatureExplainer(PropertyExplainer):
    """
    Explains differences in control flow
    Detects: if-else vs ternary, different loop structures, etc.
    """
    
    def __init__(self):
        super().__init__("control_flow_signature")
    
    def explain_difference(self, code_prop, canon_prop, code, canon_code) -> Optional[PropertyDifference]:
        """Explain control flow differences"""
        if not code_prop or not canon_prop:
            return None
        
        # Check if statement counts differ
        code_ifs = code_prop.get('if_statements', 0)
        canon_ifs = canon_prop.get('if_statements', 0)
        
        if code_ifs > canon_ifs:
            code_tree = self._parse_safely(code)
            if code_tree and self._has_ternary_opportunity(code_tree):
                return PropertyDifference(
                    property_name="control_flow_signature",
                    difference_type="if_else_vs_ternary",
                    severity=0.15,
                    explanation="Code has if-else that can be ternary expression",
                    transformation_hints={
                        'pattern': 'if_to_ternary'
                    },
                    code_details={'structure': 'if_else_return'},
                    canon_details={'structure': 'ternary_return'}
                )
        
        return None
    
    def _has_ternary_opportunity(self, tree: ast.AST) -> bool:
        """Check if code has if-else that could be ternary"""
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if (len(node.body) == 1 and isinstance(node.body[0], ast.Return) and
                    len(node.orelse) == 1 and isinstance(node.orelse[0], ast.Return)):
                    return True
        return False


class StringLiteralExplainer(PropertyExplainer):
    """
    Explains differences in string literals
    Detects: regex pattern variations, string normalization opportunities
    """
    
    def __init__(self):
        super().__init__("string_literals")
    
    def explain_difference(self, code_prop, canon_prop, code, canon_code) -> Optional[PropertyDifference]:
        """Explain string literal differences"""
        code_tree = self._parse_safely(code)
        canon_tree = self._parse_safely(canon_code)
        
        if not code_tree or not canon_tree:
            return None
        
        # Extract all string literals from both
        code_strings = self._extract_string_literals(code_tree)
        canon_strings = self._extract_string_literals(canon_tree)
        
        # Check for regex pattern differences
        regex_diffs = self._find_regex_differences(code_strings, canon_strings)
        
        if regex_diffs:
            return PropertyDifference(
                property_name="string_literals",
                difference_type=regex_diffs['difference_type'],
                severity=regex_diffs['severity'],
                explanation=f"Code has regex pattern variations: {regex_diffs['summary']}",
                transformation_hints={
                    'pattern': 'regex_normalization',
                    'differences': regex_diffs['differences']
                },
                code_details={'patterns': code_strings},
                canon_details={'patterns': canon_strings}
            )
        
        return None
    
    def _extract_string_literals(self, tree: ast.AST) -> List[str]:
        """Extract all string literals from tree"""
        strings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                strings.append(node.value)
        return strings
    
    def _find_regex_differences(self, code_strings: List[str], canon_strings: List[str]) -> Optional[Dict]:
        """Find differences in regex patterns"""
        differences = []
        difference_type = None
        max_severity = 0.0
        
        for code_str in code_strings:
            if not self._looks_like_regex(code_str):
                continue
            match = self._find_best_regex_match(code_str, canon_strings)
            if not match or match == code_str:
                continue
            diff_info = self._compare_regex_patterns(code_str, match)
            differences.append(diff_info)
            # Track most severe difference type encountered
            if diff_info['difference_type'] == 'regex_character_class_difference':
                difference_type = 'regex_character_class_difference'
                max_severity = max(max_severity, 0.30)
            else:
                if difference_type is None:
                    difference_type = 'regex_pattern_variation'
                max_severity = max(max_severity, 0.10)
        
        if differences:
            if difference_type is None:
                difference_type = 'regex_pattern_variation'
            severity = max_severity if max_severity > 0 else 0.10
            summary_parts = []
            for diff in differences:
                summary_parts.append(diff['summary'])
            summary = "; ".join(summary_parts)
            return {
                'differences': [{'code_pattern': d['code_pattern'],
                                  'canon_pattern': d['canon_pattern']}
                                 for d in differences],
                'summary': summary or f"{len(differences)} regex pattern(s) differ",
                'difference_type': difference_type,
                'severity': severity
            }
        
        return None

    def _find_best_regex_match(self, code_pattern: str, canon_strings: List[str]) -> Optional[str]:
        """Find the best matching canonical regex pattern for the given code pattern"""
        best_match = None
        best_score = 0.0
        
        for canon_pattern in canon_strings:
            if not self._looks_like_regex(canon_pattern):
                continue
            if code_pattern == canon_pattern:
                continue  # Already identical
            
            score = self._regex_similarity_score(code_pattern, canon_pattern)
            if score > best_score and score >= 0.7:  # High threshold for similarity
                best_score = score
                best_match = canon_pattern
        
        return best_match

    def _compare_regex_patterns(self, code_pattern: str, canon_pattern: str) -> Dict[str, Any]:
        """Compare two regex patterns and classify the difference"""
        code_classes = self._extract_character_classes(code_pattern)
        canon_classes = self._extract_character_classes(canon_pattern)
        difference_type = 'regex_pattern_variation'
        summary = f"{code_pattern} to {canon_pattern}"
        
        if code_classes and canon_classes:
            if code_classes != canon_classes:
                difference_type = 'regex_character_class_difference'
                summary = (f"character classes differ: code {sorted(code_classes)} vs canon {sorted(canon_classes)}"
                           f" ({code_pattern} to {canon_pattern})")
        
        return {
            'code_pattern': code_pattern,
            'canon_pattern': canon_pattern,
            'difference_type': difference_type,
            'summary': summary
        }
    
    def _looks_like_regex(self, s: str) -> bool:
        """Check if string looks like a regex pattern"""
        # Simple heuristic: contains regex special chars
        regex_chars = ['[', ']', '\\', '+', '*', '.', '^', '$', '|', '?', '{', '}']
        return any(char in s for char in regex_chars)
    
    def _regex_similarity_score(self, pattern1: str, pattern2: str) -> float:
        """Calculate similarity score between two regex patterns (0.0 to 1.0)"""
        if pattern1 == pattern2:
            return 1.0
        
        # CRITICAL: Never match negated with non-negated character classes
        p1_negated = '[^' in pattern1
        p2_negated = '[^' in pattern2
        if p1_negated != p2_negated:
            return 0.0  # Incompatible patterns
        
        # Check escape sequence similarity
        import re
        p1_escapes = set(re.findall(r'\\[a-zA-Z]', pattern1))
        p2_escapes = set(re.findall(r'\\[a-zA-Z]', pattern2))
        
        if not p1_escapes or not p2_escapes:
            return 0.0
        
        # Strong match only if they have the same escape sequences
        shared_escapes = p1_escapes & p2_escapes
        if shared_escapes:
            # Both must have EXACTLY the same escapes for high score
            if p1_escapes == p2_escapes:
                # Same escapes - check structural similarity
                length_similarity = 1.0 - min(abs(len(pattern1) - len(pattern2)) / max(len(pattern1), len(pattern2)), 1.0)
                return 0.9 + (length_similarity * 0.1)
            else:
                # Partial overlap - lower score
                overlap_ratio = len(shared_escapes) / max(len(p1_escapes), len(p2_escapes))
                return overlap_ratio * 0.5
        
        return 0.0

    def _extract_character_classes(self, pattern: str) -> Set[str]:
        """Extract character-class tokens from a regex pattern"""
        import re
        classes: Set[str] = set()
        for match in re.finditer(r'\[([^\]]+)\]', pattern):
            content = match.group(1)
            tokens = self._parse_char_class_content(content)
            classes.update(tokens)
        return classes

    def _parse_char_class_content(self, content: str) -> Set[str]:
        tokens: Set[str] = set()
        i = 0
        while i < len(content):
            char = content[i]
            if char == '^':
                i += 1
                continue
            if char == '\\' and i + 1 < len(content):
                tokens.add('\\' + content[i + 1])
                i += 2
                continue
            if i + 2 < len(content) and content[i + 1] == '-':
                tokens.add(f"{content[i]}-{content[i + 2]}")
                i += 3
                continue
            tokens.add(char)
            i += 1
        return tokens


class VariableNamingExplainer(PropertyExplainer):
    """
    Explains differences in variable names between code and canon
    Honors contract naming policies when provided
    """
    
    def __init__(self):
        super().__init__("data_dependency_graph")
    
    def explain_difference(self, code_prop, canon_prop, code, canon_code) -> Optional[PropertyDifference]:
        """Explain variable naming differences"""
        # Check for function parameter renames first
        code_tree = self._parse_safely(code)
        canon_tree = self._parse_safely(canon_code)
        
        candidate_pairs = []
        
        if code_tree and canon_tree:
            # Extract function parameters
            code_params = self._extract_function_params(code_tree)
            canon_params = self._extract_function_params(canon_tree)
            
            if code_params and canon_params and code_params != canon_params:
                # Simple case: same number of params, different names
                if len(code_params) == len(canon_params):
                    for code_param, canon_param in zip(code_params, canon_params):
                        if code_param != canon_param:
                            candidate_pairs.append((code_param, canon_param))
        
        # Also check assignment-level variables
        if not candidate_pairs and code_prop and canon_prop:
            code_assignments = code_prop.get("assignments", {})
            canon_assignments = canon_prop.get("assignments", {})
            if code_assignments and canon_assignments:
                code_vars = set(code_assignments.keys())
                canon_vars = set(canon_assignments.keys())
                if code_vars and canon_vars:
                    for code_var in code_vars:
                        if code_var in canon_vars:
                            continue
                        best_match = self._find_best_variable_match(code_var, canon_vars, canon_assignments)
                        if best_match:
                            candidate_pairs.append((code_var, best_match))
        
        if not candidate_pairs:
            return None
        
        # Produce PropertyDifference for rename
        differences = []
        for code_var, canon_var in candidate_pairs:
            differences.append({
                "code_variable": code_var,
                "canon_variable": canon_var
            })
        explanation = ", ".join(
            f"{diff['code_variable']} → {diff['canon_variable']}" for diff in differences
        )
        
        return PropertyDifference(
            property_name="data_dependency_graph",
            difference_type="variable_naming_difference",
            severity=0.20,
            explanation=f"Variable names differ: {explanation}",
            transformation_hints={
                "pattern": "variable_rename",
                "renames": differences
            },
            code_details={"renames": differences},
            canon_details={"variables": list(canon_vars)}
        )
    
    def _find_best_variable_match(self, code_var: str, canon_vars: Set[str], canon_assignments: Dict[str, Any]) -> Optional[str]:
        """Find best canonical variable match based on assignment structure"""
        code_normalized = code_var.lower()
        best_match = None
        best_score = 0.0
        for canon_var in canon_vars:
            score = self._variable_similarity(code_normalized, canon_var.lower())
            if score > best_score:
                best_match = canon_var
                best_score = score
        return best_match if best_score >= 0.5 else None
    
    def _variable_similarity(self, var1: str, var2: str) -> float:
        """Simple similarity score between variable names"""
        if var1 == var2:
            return 1.0
        if abs(len(var1) - len(var2)) > 3:
            return 0.0
        overlap = len(set(var1) & set(var2))
        total = max(len(set(var1)), len(set(var2)))
        return overlap / total if total else 0.0
    
    def _extract_function_params(self, tree: ast.AST) -> List[str]:
        """Extract function parameter names from AST"""
        params = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                params = [arg.arg for arg in node.args.args]
                break
        return params
