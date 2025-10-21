"""
Transformation Selector
Selects applicable transformations based on property mismatches
"""

import ast
from typing import List, Optional
from dataclasses import dataclass
from .transformation_rule import TransformationRule
from .transformation_registry import TransformationRegistry
from .property_diff_analyzer import PropertyMismatch


@dataclass
class SelectedTransformation:
    """Represents a selected transformation ready to be applied"""
    rule: TransformationRule
    mismatch: PropertyMismatch
    confidence: float  # 0.0 to 1.0
    match_details: dict
    
    def __repr__(self):
        return f"SelectedTransformation({self.rule.rule_id}, confidence={self.confidence:.2f})"


class TransformationSelector:
    """
    Selects applicable transformations based on property mismatches
    """
    
    def __init__(self, registry: TransformationRegistry):
        self.registry = registry
    
    def select(self, mismatches: List[PropertyMismatch], code: str) -> List[SelectedTransformation]:
        """
        Select applicable transformations for given mismatches
        
        Args:
            mismatches: List of property mismatches
            code: Code to transform
            
        Returns:
            List of selected transformations, sorted by priority and confidence
        """
        selections = []
        
        for mismatch in mismatches:
            # Get rules that handle this mismatch type
            rules = self.registry.get_rules_for_mismatch(mismatch.mismatch_type)
            
            for rule in rules:
                # Check if rule is applicable
                confidence, match_details = self._check_applicability(rule, mismatch, code)
                
                if confidence > 0.0 and match_details:
                    selections.append(SelectedTransformation(
                        rule=rule,
                        mismatch=mismatch,
                        confidence=confidence,
                        match_details=match_details
                    ))
        
        # Remove conflicts
        selections = self._detect_conflicts(selections)
        
        # Sort by priority and confidence
        selections = self._sort_by_priority(selections)
        
        return selections
    
    def _check_applicability(self, rule: TransformationRule, 
                           mismatch: PropertyMismatch, 
                           code: str) -> tuple[float, Optional[dict]]:
        """
        Check if a rule is applicable to the code
        
        Returns:
            (confidence, match_details) tuple
            confidence is 0.0 if not applicable
        """
        try:
            # Try to match the rule's pattern in the code
            match = rule.matches(mismatch.mismatch_type, code)
            
            if not match:
                return 0.0, None
            
            # Calculate confidence based on:
            # 1. Rule priority (higher = more confident)
            # 2. Mismatch severity (higher = more important)
            # 3. Pattern match quality
            
            base_confidence = 0.5
            priority_boost = rule.priority * 0.1
            severity_boost = mismatch.severity * 0.3
            
            confidence = min(1.0, base_confidence + priority_boost + severity_boost)
            
            # Merge match details with mismatch details
            match_details = {**match, **mismatch.details}
            
            return confidence, match_details
            
        except Exception:
            return 0.0, None
    
    def _detect_conflicts(self, selections: List[SelectedTransformation]) -> List[SelectedTransformation]:
        """
        Detect and resolve conflicts between transformations
        
        Conflicts occur when:
        - Two transformations target the same AST node
        - Transformations have incompatible effects
        
        Resolution: Keep higher priority/confidence transformation
        """
        if len(selections) <= 1:
            return selections
        
        # Group by target node (if available)
        node_groups = {}
        no_node = []
        
        for selection in selections:
            node = selection.match_details.get('original_node')
            if node:
                node_id = id(node)
                if node_id not in node_groups:
                    node_groups[node_id] = []
                node_groups[node_id].append(selection)
            else:
                no_node.append(selection)
        
        # Resolve conflicts within each group
        resolved = []
        
        for group in node_groups.values():
            if len(group) == 1:
                resolved.extend(group)
            else:
                # Keep the one with highest priority * confidence
                best = max(group, key=lambda s: s.rule.priority * s.confidence)
                resolved.append(best)
        
        # Add selections without node conflicts
        resolved.extend(no_node)
        
        return resolved
    
    def _sort_by_priority(self, selections: List[SelectedTransformation]) -> List[SelectedTransformation]:
        """
        Sort selections by priority and confidence
        Higher priority and confidence come first
        """
        return sorted(selections, 
                     key=lambda s: (s.rule.priority, s.confidence, s.mismatch.severity),
                     reverse=True)
    
    def filter_by_confidence(self, selections: List[SelectedTransformation],
                           min_confidence: float = 0.5) -> List[SelectedTransformation]:
        """Filter selections by minimum confidence threshold"""
        return [s for s in selections if s.confidence >= min_confidence]
    
    def filter_by_semantic_class(self, selections: List[SelectedTransformation],
                                semantic_class: str) -> List[SelectedTransformation]:
        """Filter selections by semantic class"""
        return [s for s in selections if s.rule.semantic_class == semantic_class]
    
    def get_top_n(self, selections: List[SelectedTransformation], n: int) -> List[SelectedTransformation]:
        """Get top N selections by priority and confidence"""
        return selections[:n]
    
    def explain_selection(self, selection: SelectedTransformation) -> str:
        """
        Generate human-readable explanation of why this transformation was selected
        """
        explanation = []
        explanation.append(f"Rule: {selection.rule.rule_id}")
        explanation.append(f"Description: {selection.rule.description}")
        explanation.append(f"Property: {selection.mismatch.property_name}")
        explanation.append(f"Mismatch: {selection.mismatch.mismatch_type}")
        explanation.append(f"Severity: {selection.mismatch.severity:.2f}")
        explanation.append(f"Confidence: {selection.confidence:.2f}")
        explanation.append(f"Priority: {selection.rule.priority}")
        
        if 'code_pattern' in selection.mismatch.details:
            explanation.append(f"Pattern: {selection.mismatch.details['code_pattern']} → {selection.mismatch.details['canon_pattern']}")
        
        return "\n".join(explanation)
    
    def get_statistics(self, selections: List[SelectedTransformation]) -> dict:
        """Get statistics about selections"""
        if not selections:
            return {
                'total': 0,
                'avg_confidence': 0.0,
                'properties': [],
                'semantic_classes': []
            }
        
        return {
            'total': len(selections),
            'avg_confidence': sum(s.confidence for s in selections) / len(selections),
            'avg_priority': sum(s.rule.priority for s in selections) / len(selections),
            'properties': list(set(s.mismatch.property_name for s in selections)),
            'semantic_classes': list(set(s.rule.semantic_class for s in selections)),
            'mismatch_types': list(set(s.mismatch.mismatch_type for s in selections))
        }
