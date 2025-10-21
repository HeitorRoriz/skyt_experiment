"""
Transformation Strategies
Property-specific transformation logic derived from property explanations.
Each strategy knows how to fix ONE type of property difference.
"""

import ast
from abc import ABC, abstractmethod
from typing import Optional, Dict
from .property_explainers import PropertyDifference


class TransformationStrategy(ABC):
    """
    Abstract base for transformation strategies
    Each strategy fixes a specific type of property difference
    """
    
    def __init__(self, property_name: str):
        self.property_name = property_name
    
    @abstractmethod
    def can_handle(self, difference: PropertyDifference) -> bool:
        """
        Can this strategy handle this property difference?
        
        Args:
            difference: PropertyDifference from explainer
            
        Returns:
            True if this strategy can fix this difference
        """
        pass
    
    @abstractmethod
    def generate_transformation(self, difference: PropertyDifference, code: str) -> Optional[str]:
        """
        Generate transformed code based on property difference explanation
        
        Args:
            difference: PropertyDifference with transformation hints
            code: Original code
            
        Returns:
            Transformed code or None if transformation failed
        """
        pass
    
    def _parse_safely(self, code: str) -> Optional[ast.AST]:
        """Safely parse code"""
        try:
            return ast.parse(code)
        except SyntaxError:
            return None


class StatementConsolidationStrategy(TransformationStrategy):
    """
    Consolidates consecutive statements when they can be merged
    Example: var = expr; return var → return expr
    """
    
    def __init__(self):
        super().__init__("statement_ordering")
    
    def can_handle(self, difference: PropertyDifference) -> bool:
        return (difference.property_name == "statement_ordering" and
                difference.difference_type in {
                    "consecutive_statements_consolidatable",
                    "chained_statements_consolidatable"
                })
    
    def generate_transformation(self, difference: PropertyDifference, code: str) -> Optional[str]:
        """Generate transformation to consolidate statements"""
        hints = difference.transformation_hints
        
        tree = self._parse_safely(code)
        if not tree:
            return None
        
        pattern = hints.get('pattern')
        variable = hints.get('variable')
        chain_length = hints.get('chain_length', 2)
        
        # Find function and consolidate statements based on pattern
        result_code = self._consolidate_statements(tree, pattern, variable, chain_length, code)
        return result_code
    
    def _consolidate_statements(self, tree: ast.AST, pattern: Optional[str], variable: Optional[str], chain_length: int, code: str) -> Optional[str]:
        """Consolidate assign + return to inline return"""
        class Consolidator(ast.NodeTransformer):
            def __init__(self, pattern: Optional[str], variable: Optional[str], chain_length: int):
                self.pattern = pattern
                self.variable = variable
                self.chain_length = chain_length
                self.transformed = False
            
            def visit_FunctionDef(self, node):
                if self.transformed or len(node.body) < 2:
                    return self.generic_visit(node)
                
                last = node.body[-1]
                if not isinstance(last, ast.Return) or last.value is None:
                    return self.generic_visit(node)
                
                if self.pattern == 'separate_to_inline':
                    if len(node.body) < 2:
                        return self.generic_visit(node)
                    second_last = node.body[-2]
                    if (isinstance(second_last, ast.Assign) and
                        len(second_last.targets) == 1 and
                        isinstance(second_last.targets[0], ast.Name) and
                        isinstance(last.value, ast.Name) and
                        second_last.targets[0].id == last.value.id):
                        new_return = ast.Return(value=second_last.value)
                        ast.copy_location(new_return, last)
                        node.body = node.body[:-2] + [new_return]
                        self.transformed = True
                        return self.generic_visit(node)
                elif self.pattern == 'chain_to_inline':
                    # Expect chain_length assignments to same variable before return
                    if self.variable is None or len(node.body) < (self.chain_length + 1):
                        return self.generic_visit(node)
                    # last is Return, gather preceding assignments
                    preceding = node.body[-(self.chain_length+1):-1]
                    # Ensure all preceding are assigns to same variable
                    if not all(isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and
                               isinstance(stmt.targets[0], ast.Name) and stmt.targets[0].id == self.variable
                               for stmt in preceding):
                        return self.generic_visit(node)
                    # Ensure return uses that variable
                    if not isinstance(last.value, ast.Name) or last.value.id != self.variable:
                        return self.generic_visit(node)
                    # Use last assignment expression as return value
                    final_assign = preceding[-1]
                    new_return = ast.Return(value=final_assign.value)
                    ast.copy_location(new_return, last)
                    # Replace body: drop final assignment, keep earlier ones
                    new_body = node.body[:-(self.chain_length+1)]
                    new_body.extend(preceding[:-1])
                    new_body.append(new_return)
                    node.body = new_body
                    self.transformed = True
                    return self.generic_visit(node)
                
                return self.generic_visit(node)
        
        consolidator = Consolidator(pattern, variable, chain_length)
        new_tree = consolidator.visit(tree)
        
        if not consolidator.transformed:
            return None
        
        # Unparse and preserve raw string literals
        unparsed = ast.unparse(new_tree)
        # Add r prefix to regex-like strings that had it in original
        if 're.sub(' in code and 're.sub(r' in code:
            # Preserve raw string prefix for regex patterns
            unparsed = unparsed.replace("re.sub('", "re.sub(r'")
            unparsed = unparsed.replace('re.sub("', 're.sub(r"')
        
        return unparsed


class BooleanSimplificationStrategy(TransformationStrategy):
    """
    Simplifies boolean expressions to canonical form
    Example: len(x) == 0 → not x, x == True → x
    """
    
    def __init__(self):
        super().__init__("logical_equivalence")
    
    def can_handle(self, difference: PropertyDifference) -> bool:
        return (difference.property_name == "logical_equivalence" and
                difference.difference_type in ["empty_check_form", "boolean_redundancy"])
    
    def generate_transformation(self, difference: PropertyDifference, code: str) -> Optional[str]:
        """Generate boolean simplification transformation"""
        hints = difference.transformation_hints
        pattern = hints.get('pattern')
        
        if pattern == 'len_to_not':
            return self._transform_len_to_not(code, hints)
        elif pattern == 'boolean_redundancy':
            return self._transform_boolean_redundancy(code, hints)
        
        return None
    
    def _transform_len_to_not(self, code: str, hints: dict) -> Optional[str]:
        """Transform len(x) == 0 to not x"""
        tree = self._parse_safely(code)
        if not tree:
            return None
        
        target = hints.get('target')
        operator = hints.get('operator')
        
        class LenToNotTransformer(ast.NodeTransformer):
            def __init__(self, target_var, op):
                self.target_var = target_var
                self.op = op
                self.transformed = False
            
            def visit_Compare(self, node):
                # Match len(target) == 0
                if (isinstance(node.left, ast.Call) and
                    isinstance(node.left.func, ast.Name) and
                    node.left.func.id == 'len' and
                    len(node.left.args) == 1 and
                    isinstance(node.left.args[0], ast.Name) and
                    node.left.args[0].id == self.target_var and
                    len(node.ops) == 1 and
                    isinstance(node.ops[0], ast.Eq) and
                    len(node.comparators) == 1 and
                    isinstance(node.comparators[0], ast.Constant) and
                    node.comparators[0].value == 0):
                    
                    self.transformed = True
                    # Replace with not target
                    return ast.UnaryOp(op=ast.Not(), operand=ast.Name(id=self.target_var, ctx=ast.Load()))
                
                return self.generic_visit(node)
        
        transformer = LenToNotTransformer(target, operator)
        new_tree = transformer.visit(tree)
        
        return ast.unparse(new_tree) if transformer.transformed else None
    
    def _transform_boolean_redundancy(self, code: str, hints: dict) -> Optional[str]:
        """Transform x == True to x, x == False to not x"""
        tree = self._parse_safely(code)
        if not tree:
            return None
        
        target = hints.get('target')
        value = hints.get('value')
        operator = hints.get('operator')
        
        class BoolRedundancyTransformer(ast.NodeTransformer):
            def __init__(self, target_var, bool_val, op):
                self.target_var = target_var
                self.bool_val = bool_val
                self.op = op
                self.transformed = False
            
            def visit_Compare(self, node):
                if (isinstance(node.left, ast.Name) and
                    node.left.id == self.target_var and
                    len(node.ops) == 1 and
                    len(node.comparators) == 1 and
                    isinstance(node.comparators[0], ast.Constant) and
                    isinstance(node.comparators[0].value, bool)):
                    
                    self.transformed = True
                    if self.op == 'Eq':
                        if self.bool_val:
                            return ast.Name(id=self.target_var, ctx=ast.Load())
                        else:
                            return ast.UnaryOp(op=ast.Not(), operand=ast.Name(id=self.target_var, ctx=ast.Load()))
                    elif self.op == 'NotEq':
                        if self.bool_val:
                            return ast.UnaryOp(op=ast.Not(), operand=ast.Name(id=self.target_var, ctx=ast.Load()))
                        else:
                            return ast.Name(id=self.target_var, ctx=ast.Load())
                
                return self.generic_visit(node)
        
        transformer = BoolRedundancyTransformer(target, value, operator)
        new_tree = transformer.visit(tree)
        
        return ast.unparse(new_tree) if transformer.transformed else None


class LoopTransformationStrategy(TransformationStrategy):
    """
    Transforms between loop and comprehension idioms
    Example: for x in y: list.append(x) → list = [x for x in y]
    """
    
    def __init__(self):
        super().__init__("normalized_ast_structure")
    
    def can_handle(self, difference: PropertyDifference) -> bool:
        return (difference.property_name == "normalized_ast_structure" and
                difference.difference_type == "loop_vs_comprehension")
    
    def generate_transformation(self, difference: PropertyDifference, code: str) -> Optional[str]:
        """Generate loop to comprehension transformation"""
        # This is complex and depends on specific loop structure
        # For now, return None - can be expanded later
        return None


class ControlFlowNormalizationStrategy(TransformationStrategy):
    """
    Normalizes control flow structures
    Example: if-else with returns → ternary expression
    """
    
    def __init__(self):
        super().__init__("control_flow_signature")
    
    def can_handle(self, difference: PropertyDifference) -> bool:
        return (difference.property_name == "control_flow_signature" and
                difference.difference_type == "if_else_vs_ternary")
    
    def generate_transformation(self, difference: PropertyDifference, code: str) -> Optional[str]:
        """Generate if-else to ternary transformation"""
        tree = self._parse_safely(code)
        if not tree:
            return None
        
        new_tree = self._transform_to_ternary(tree)
        if new_tree:
            return ast.unparse(new_tree)
        
        return None
    
    def _transform_to_ternary(self, tree: ast.AST) -> Optional[ast.AST]:
        """Transform if-else with returns to ternary"""
        class TernaryTransformer(ast.NodeTransformer):
            def __init__(self):
                self.transformed = False
            
            def visit_If(self, node):
                # Check for if-else with single returns
                if (len(node.body) == 1 and isinstance(node.body[0], ast.Return) and
                    len(node.orelse) == 1 and isinstance(node.orelse[0], ast.Return)):
                    
                    self.transformed = True
                    # Create ternary: return x if cond else y
                    ternary = ast.IfExp(
                        test=node.test,
                        body=node.body[0].value,
                        orelse=node.orelse[0].value
                    )
                    return ast.Return(value=ternary)
                
                return self.generic_visit(node)
        
        transformer = TernaryTransformer()
        new_tree = transformer.visit(tree)
        
        return new_tree if transformer.transformed else None


class StringNormalizationStrategy(TransformationStrategy):
    """
    Normalizes string literals (especially regex patterns)
    Example: r'[\s-]+' → r'[\s]+'
    """
    
    def __init__(self):
        super().__init__("string_literals")
    
    def can_handle(self, difference: PropertyDifference) -> bool:
        return (difference.property_name == "string_literals" and
                difference.difference_type in {
                    "regex_pattern_variation",
                    "regex_character_class_difference"
                })
    
    def generate_transformation(self, difference: PropertyDifference, code: str) -> Optional[str]:
        """Generate string normalization transformation"""
        hints = difference.transformation_hints
        differences = hints.get('differences', [])
        
        if not differences:
            return None
        
        # Use source-level replacement to preserve exact formatting
        # But only replace FIRST occurrence to avoid oscillation
        transformed = code
        changed = False
        
        for diff in differences:
            old_pattern = diff['code_pattern']
            new_pattern = diff['canon_pattern']
            # Replace in source with proper escaping (first occurrence only)
            old_repr = repr(old_pattern)
            new_repr = repr(new_pattern)
            if old_repr in transformed:
                # Replace only first occurrence to avoid oscillation
                transformed = transformed.replace(old_repr, new_repr, 1)
                changed = True
                break  # Only fix one pattern per iteration
        
        return transformed if changed else None
    
    def _normalize_strings(self, tree: ast.AST, differences: list) -> Optional[ast.AST]:
        """Normalize string literals according to differences"""
        class StringNormalizer(ast.NodeTransformer):
            def __init__(self, diffs):
                self.diffs = diffs
                self.transformed = False
            
            def visit_Constant(self, node):
                if isinstance(node.value, str):
                    # Check if this string should be normalized
                    for diff in self.diffs:
                        if node.value == diff['code_pattern']:
                            # Replace with canon pattern
                            node.value = diff['canon_pattern']
                            self.transformed = True
                            break
                return node
        
        normalizer = StringNormalizer(differences)
        new_tree = normalizer.visit(tree)
        
        return new_tree if normalizer.transformed else None


class VariableRenamingStrategy(TransformationStrategy):
    """
    Renames variables to align with canonical naming while honoring contract rules
    """
    
    def __init__(self):
        super().__init__("data_dependency_graph")
        self.contract: Dict = None
    
    def can_handle(self, difference: PropertyDifference) -> bool:
        return (difference.property_name == "data_dependency_graph" and
                difference.difference_type == "variable_naming_difference")
    
    def generate_transformation(self, difference: PropertyDifference, code: str) -> Optional[str]:
        hints = difference.transformation_hints or {}
        renames = hints.get("renames", [])
        if not renames:
            return None
        
        if not self._renaming_allowed(renames):
            return None
        
        mapping = {item["code_variable"]: item["canon_variable"] for item in renames}
        tree = self._parse_safely(code)
        if not tree:
            return None
        
        class VariableRenamer(ast.NodeTransformer):
            def __init__(self, mapping: Dict[str, str]):
                self.mapping = mapping
                self.transformed = False
            
            def visit_Name(self, node):
                if node.id in self.mapping:
                    self.transformed = True
                    return ast.copy_location(ast.Name(id=self.mapping[node.id], ctx=node.ctx), node)
                return self.generic_visit(node)
            
            def visit_arg(self, node):
                if node.arg in self.mapping:
                    self.transformed = True
                    node.arg = self.mapping[node.arg]
                return node
        
        renamer = VariableRenamer(mapping)
        new_tree = renamer.visit(tree)
        if not renamer.transformed:
            return None
        return ast.unparse(new_tree)
    
    def _renaming_allowed(self, renames: list) -> bool:
        """Verify renames comply with contract variable naming rules"""
        if not self.contract:
            return True
        variable_rules = (self.contract.get("constraints", {})
                          .get("variable_naming", {}))
        policy = variable_rules.get("naming_policy", "flexible")
        if policy == "strict":
            return False
        fixed = set(variable_rules.get("fixed_variables", []))
        flexible = set(variable_rules.get("flexible_variables", []))
        for item in renames:
            source = item["code_variable"]
            target = item["canon_variable"]
            # Never rename away from fixed variables
            if source in fixed:
                return False
            # If flexible list provided, ensure target is allowed or fixed
            if flexible and target not in fixed and target not in flexible:
                return False
        return True
