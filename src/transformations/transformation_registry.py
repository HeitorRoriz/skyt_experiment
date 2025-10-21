"""
Transformation Registry
Central registry for all transformation rules
"""

from typing import List, Dict, Optional
from .transformation_rule import TransformationRule, create_rule
from . import ast_patterns


class TransformationRegistry:
    """
    Central registry for transformation rules
    Stores, queries, and manages all transformation rules
    """
    
    def __init__(self):
        self.rules: List[TransformationRule] = []
        self.rules_by_property: Dict[str, List[TransformationRule]] = {}
        self.rules_by_mismatch: Dict[str, List[TransformationRule]] = {}
        
        # Register built-in rules
        self._register_built_in_rules()
    
    def register_rule(self, rule: TransformationRule) -> bool:
        """
        Register a transformation rule
        
        Args:
            rule: TransformationRule to register
            
        Returns:
            True if registered successfully, False otherwise
        """
        # Check if rule already exists
        if any(r.rule_id == rule.rule_id for r in self.rules):
            return False
        
        # Add to main list
        self.rules.append(rule)
        
        # Index by property
        if rule.property_target not in self.rules_by_property:
            self.rules_by_property[rule.property_target] = []
        self.rules_by_property[rule.property_target].append(rule)
        
        # Index by mismatch pattern
        if rule.mismatch_pattern not in self.rules_by_mismatch:
            self.rules_by_mismatch[rule.mismatch_pattern] = []
        self.rules_by_mismatch[rule.mismatch_pattern].append(rule)
        
        return True
    
    def get_rules_for_property(self, property_name: str) -> List[TransformationRule]:
        """Get all rules that target a specific property"""
        return self.rules_by_property.get(property_name, [])
    
    def get_rules_for_mismatch(self, mismatch_type: str) -> List[TransformationRule]:
        """Get all rules that handle a specific mismatch type"""
        return self.rules_by_mismatch.get(mismatch_type, [])
    
    def get_all_rules(self) -> List[TransformationRule]:
        """Get all registered rules"""
        return self.rules.copy()
    
    def get_rule_by_id(self, rule_id: str) -> Optional[TransformationRule]:
        """Get a specific rule by ID"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None
    
    def get_rules_sorted_by_priority(self) -> List[TransformationRule]:
        """Get all rules sorted by priority (highest first)"""
        return sorted(self.rules, key=lambda r: r.priority, reverse=True)
    
    # ========================================================================
    # BUILT-IN RULE REGISTRATION
    # ========================================================================
    
    def _register_built_in_rules(self):
        """Register all built-in transformation rules"""
        self._register_logical_equivalence_rules()
        self._register_control_flow_rules()
        self._register_ast_structure_rules()
    
    def _register_logical_equivalence_rules(self):
        """Register rules for logical equivalence transformations"""
        
        # Rule: len(x) == 0 → not x
        rule = create_rule(
            rule_id="len_zero_to_not",
            property_target="logical_equivalence",
            mismatch_pattern="empty_check",
            pattern_type="len_zero_check",
            match_func=ast_patterns.match_len_zero_check,
            replace_func=ast_patterns.replace_len_check_with_bool,
            semantic_class="boolean_simplification",
            priority=2,
            description="Replace len(x) == 0 with 'not x'",
            examples=[
                {
                    'before': 'return len(stack) == 0',
                    'after': 'return not stack',
                    'description': 'Empty check simplification'
                }
            ]
        )
        self.register_rule(rule)
        
        # Rule: x == True/False → x or not x
        rule = create_rule(
            rule_id="boolean_redundancy_removal",
            property_target="logical_equivalence",
            mismatch_pattern="boolean_redundancy",
            pattern_type="boolean_redundancy",
            match_func=ast_patterns.match_boolean_redundancy,
            replace_func=ast_patterns.replace_boolean_redundancy,
            semantic_class="boolean_simplification",
            priority=2,
            description="Remove redundant boolean comparisons",
            examples=[
                {
                    'before': 'if x == True: return y',
                    'after': 'if x: return y',
                    'description': 'Boolean redundancy removal'
                }
            ]
        )
        self.register_rule(rule)
    
    def _register_control_flow_rules(self):
        """Register rules for control flow transformations"""
        
        # Rule: if-else with returns → ternary
        rule = create_rule(
            rule_id="if_else_to_ternary",
            property_target="control_flow_signature",
            mismatch_pattern="ternary_opportunity",
            pattern_type="ternary_opportunity",
            match_func=ast_patterns.match_ternary_opportunity,
            replace_func=ast_patterns.replace_if_else_with_ternary,
            semantic_class="control_flow_simplification",
            priority=1,
            description="Replace if-else with ternary expression",
            examples=[
                {
                    'before': 'if n > 0:\n    return 1\nelse:\n    return 0',
                    'after': 'return 1 if n > 0 else 0',
                    'description': 'Ternary conversion'
                }
            ]
        )
        self.register_rule(rule)
    
    def _register_ast_structure_rules(self):
        """Register rules for AST structure transformations"""
        
        # Rule: append loop → list comprehension
        rule = create_rule(
            rule_id="append_loop_to_comprehension",
            property_target="normalized_ast_structure",
            mismatch_pattern="loop_to_comprehension",
            pattern_type="append_in_loop",
            match_func=ast_patterns.match_append_in_loop,
            replace_func=ast_patterns.replace_append_loop_with_comprehension,
            semantic_class="comprehension_conversion",
            priority=3,
            description="Convert append loop to list comprehension",
            examples=[
                {
                    'before': 'result = []\nfor x in items:\n    result.append(x)',
                    'after': 'result = [x for x in items]',
                    'description': 'List comprehension conversion'
                }
            ]
        )
        self.register_rule(rule)
        
        # Rule: string concat loop → join
        rule = create_rule(
            rule_id="string_concat_to_join",
            property_target="normalized_ast_structure",
            mismatch_pattern="string_building",
            pattern_type="string_concat_in_loop",
            match_func=ast_patterns.match_string_concat_in_loop,
            replace_func=ast_patterns.replace_string_concat_with_join,
            semantic_class="string_building_idiom",
            priority=3,
            description="Convert string concatenation loop to join",
            examples=[
                {
                    'before': 'result = ""\nfor char in text:\n    result += char',
                    'after': 'result = "".join(text)',
                    'description': 'String join conversion'
                }
            ]
        )
        self.register_rule(rule)
        
        # Rule: separate assignment + return → inline return
        rule = create_rule(
            rule_id="separate_to_inline_return",
            property_target="statement_ordering",
            mismatch_pattern="return_statement_style",
            pattern_type="separate_assign_return",
            match_func=ast_patterns.match_separate_assign_return,
            replace_func=ast_patterns.replace_separate_with_inline_return,
            semantic_class="return_normalization",
            priority=2,
            description="Convert separate assignment+return to inline return",
            examples=[
                {
                    'before': 'text = text.strip("-")\nreturn text',
                    'after': 'return text.strip("-")',
                    'description': 'Inline return normalization'
                }
            ]
        )
        self.register_rule(rule)
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about registered rules"""
        return {
            'total_rules': len(self.rules),
            'properties_covered': len(self.rules_by_property),
            'mismatch_types_covered': len(self.rules_by_mismatch),
            'rules_by_priority': {
                priority: len([r for r in self.rules if r.priority == priority])
                for priority in sorted(set(r.priority for r in self.rules), reverse=True)
            }
        }
    
    def validate_all_rules(self) -> Dict[str, tuple]:
        """
        Validate all registered rules
        Returns dict of rule_id -> (is_valid, message)
        """
        from .transformation_rule import validate_rule
        
        results = {}
        for rule in self.rules:
            is_valid, message = validate_rule(rule)
            results[rule.rule_id] = (is_valid, message)
        
        return results
    
    def __repr__(self):
        stats = self.get_statistics()
        return f"TransformationRegistry({stats['total_rules']} rules, {stats['properties_covered']} properties)"
