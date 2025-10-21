"""
Transformation Rule
Defines the structure and behavior of transformation rules
"""

import ast
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field


@dataclass
class ASTPattern:
    """
    Defines an AST pattern for matching and replacement
    """
    pattern_type: str  # e.g., "len_zero_check", "boolean_redundancy"
    match_func: Callable[[ast.AST], Optional[Dict[str, Any]]]
    replace_func: Callable[[Dict[str, Any]], Optional[str]]
    description: str = ""
    
    def match(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Try to match pattern in code
        Returns match dictionary if found, None otherwise
        """
        try:
            tree = ast.parse(code)
            
            # Try matching on whole tree first
            match = self.match_func(tree)
            if match:
                return match
            
            # Try matching on individual nodes
            for node in ast.walk(tree):
                match = self.match_func(node)
                if match:
                    return match
            
            return None
            
        except SyntaxError:
            return None
    
    def replace(self, match: Dict[str, Any]) -> Optional[str]:
        """
        Generate replacement code from match
        """
        try:
            return self.replace_func(match)
        except Exception:
            return None


@dataclass
class TransformationRule:
    """
    Defines a transformation rule that maps property mismatches to code changes
    """
    rule_id: str
    property_target: str  # Which property this rule addresses
    mismatch_pattern: str  # Specific mismatch type (e.g., "empty_check")
    ast_pattern: ASTPattern
    semantic_class: str  # e.g., "boolean_simplification"
    priority: int = 1  # Higher = applied first
    preserves_semantics: bool = True
    description: str = ""
    examples: list = field(default_factory=list)
    
    def matches(self, mismatch_type: str, code: str) -> Optional[Dict[str, Any]]:
        """
        Check if this rule matches the given mismatch and code
        
        Args:
            mismatch_type: Type of property mismatch
            code: Code to check
            
        Returns:
            Match dictionary if applicable, None otherwise
        """
        # Check if mismatch type matches
        if mismatch_type != self.mismatch_pattern:
            return None
        
        # Check if AST pattern matches
        return self.ast_pattern.match(code)
    
    def apply(self, code: str, match: Dict[str, Any]) -> Optional[str]:
        """
        Apply transformation to code
        
        Args:
            code: Original code
            match: Match dictionary from pattern matching
            
        Returns:
            Transformed code or None if transformation failed
        """
        try:
            # Get replacement string from pattern
            replacement_str = self.ast_pattern.replace(match)
            if not replacement_str:
                return None
            
            # Parse original code
            tree = ast.parse(code)
            original_node = match.get('original_node')
            
            if not original_node:
                return None
            
            # Handle special case: replacing two statements with one
            if 'original_nodes' in match and isinstance(match['original_nodes'], tuple):
                # This is a multi-node replacement (e.g., assign + return → inline return)
                try:
                    replacement_tree = ast.parse(replacement_str)
                    replacement_node = replacement_tree.body[0]
                    new_tree = self._replace_two_statements(tree, match['original_nodes'], replacement_node)
                except:
                    return None
            else:
                # Parse replacement string as an expression
                # The replacement is always an expression (e.g., "not stack")
                try:
                    # Parse as expression
                    replacement_node = ast.parse(replacement_str, mode='eval').body
                except SyntaxError:
                    # Fallback: try parsing as statement and extract value
                    try:
                        replacement_tree = ast.parse(replacement_str)
                        replacement_node = replacement_tree.body[0]
                        if isinstance(replacement_node, ast.Expr):
                            replacement_node = replacement_node.value
                    except:
                        return None
                
                # Replace node in tree using identity-based replacement
                new_tree = self._replace_node(tree, original_node, replacement_node)
            
            # Convert back to code
            return ast.unparse(new_tree)
            
        except Exception as e:
            # Log error if needed
            return None
    
    def _replace_node(self, tree: ast.AST, old_node: ast.AST, new_node: ast.AST) -> ast.AST:
        """
        Replace a node in the AST tree
        Since we re-parse the code, we can't use identity comparison.
        Instead, we find nodes that match the pattern structurally.
        """
        class NodeReplacer(ast.NodeTransformer):
            def __init__(self):
                self.replaced = False
                
            def visit_Compare(self, node):
                # Check if this Compare node matches our pattern
                if (not self.replaced and
                    isinstance(old_node, ast.Compare) and
                    self._nodes_match(node, old_node)):
                    self.replaced = True
                    return new_node
                return self.generic_visit(node)
            
            def _nodes_match(self, node1, node2):
                """Check if two nodes are structurally equivalent"""
                if type(node1) != type(node2):
                    return False
                
                # For Compare nodes, check structure
                if isinstance(node1, ast.Compare):
                    # Check if both have len() call on left
                    if (isinstance(node1.left, ast.Call) and 
                        isinstance(node2.left, ast.Call) and
                        isinstance(node1.left.func, ast.Name) and
                        isinstance(node2.left.func, ast.Name) and
                        node1.left.func.id == node2.left.func.id == 'len'):
                        # Check operators match
                        if (len(node1.ops) == len(node2.ops) and
                            type(node1.ops[0]) == type(node2.ops[0])):
                            # Check comparators match
                            if (len(node1.comparators) == len(node2.comparators) and
                                isinstance(node1.comparators[0], ast.Constant) and
                                isinstance(node2.comparators[0], ast.Constant) and
                                node1.comparators[0].value == node2.comparators[0].value):
                                return True
                return False
        
        replacer = NodeReplacer()
        return replacer.visit(tree)
    
    def _replace_two_statements(self, tree: ast.AST, old_nodes: tuple, new_node: ast.AST) -> ast.AST:
        """
        Replace two consecutive statements with one
        Used for patterns like: var = var.method(); return var → return var.method()
        """
        class TwoStatementReplacer(ast.NodeTransformer):
            def __init__(self):
                self.replaced = False
                
            def visit_FunctionDef(self, node):
                if self.replaced or len(node.body) < 2:
                    return self.generic_visit(node)
                
                # Check if last two statements match the pattern structurally
                if len(node.body) >= 2:
                    second_last = node.body[-2]
                    last = node.body[-1]
                    
                    # Check if these match our pattern (assign + return)
                    if (isinstance(second_last, ast.Assign) and isinstance(last, ast.Return) and
                        len(second_last.targets) == 1 and isinstance(second_last.targets[0], ast.Name) and
                        isinstance(second_last.value, ast.Call) and
                        isinstance(last.value, ast.Name)):
                        
                        # Replace last two statements with new statement
                        node.body = node.body[:-2] + [new_node]
                        self.replaced = True
                
                return self.generic_visit(node)
        
        replacer = TwoStatementReplacer()
        return replacer.visit(tree)
    
    def __repr__(self):
        return f"TransformationRule({self.rule_id}, {self.property_target}.{self.mismatch_pattern})"


# ============================================================================
# RULE BUILDER HELPERS
# ============================================================================

def create_rule(rule_id: str,
                property_target: str,
                mismatch_pattern: str,
                pattern_type: str,
                match_func: Callable,
                replace_func: Callable,
                semantic_class: str,
                priority: int = 1,
                description: str = "",
                examples: list = None) -> TransformationRule:
    """
    Helper function to create a transformation rule
    
    Args:
        rule_id: Unique identifier for the rule
        property_target: Property this rule addresses
        mismatch_pattern: Specific mismatch type
        pattern_type: AST pattern type
        match_func: Function to match pattern
        replace_func: Function to generate replacement
        semantic_class: Semantic classification
        priority: Priority (higher = applied first)
        description: Human-readable description
        examples: List of example transformations
        
    Returns:
        TransformationRule instance
    """
    ast_pattern = ASTPattern(
        pattern_type=pattern_type,
        match_func=match_func,
        replace_func=replace_func,
        description=description
    )
    
    return TransformationRule(
        rule_id=rule_id,
        property_target=property_target,
        mismatch_pattern=mismatch_pattern,
        ast_pattern=ast_pattern,
        semantic_class=semantic_class,
        priority=priority,
        preserves_semantics=True,
        description=description,
        examples=examples or []
    )


def validate_rule(rule: TransformationRule) -> tuple[bool, str]:
    """
    Validate a transformation rule
    
    Returns:
        (is_valid, error_message)
    """
    if not rule.rule_id:
        return False, "Rule must have an ID"
    
    if not rule.property_target:
        return False, "Rule must target a property"
    
    if not rule.mismatch_pattern:
        return False, "Rule must specify a mismatch pattern"
    
    if not rule.ast_pattern:
        return False, "Rule must have an AST pattern"
    
    if not rule.semantic_class:
        return False, "Rule must have a semantic class"
    
    # Test the rule on examples if provided
    if rule.examples:
        for example in rule.examples:
            if 'before' not in example or 'after' not in example:
                return False, f"Example missing 'before' or 'after': {example}"
            
            # Try to match and apply
            match = rule.ast_pattern.match(example['before'])
            if not match:
                return False, f"Rule doesn't match its own example: {example['before']}"
            
            result = rule.apply(example['before'], match)
            if not result:
                return False, f"Rule failed to apply to example: {example['before']}"
    
    return True, "Rule is valid"
