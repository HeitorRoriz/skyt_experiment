"""
Property-Driven Transformer
Main transformer that uses property-driven approach to transform code
"""

import ast
from typing import Dict, Any, Optional, List
from ..transformations.transformation_base import TransformationBase, TransformationResult
from ..foundational_properties import FoundationalProperties
from .property_diff_analyzer import PropertyDiffAnalyzer, PropertyMismatch
from .transformation_registry import TransformationRegistry
from .transformation_selector import TransformationSelector, SelectedTransformation


class PropertyDrivenTransformer(TransformationBase):
    """
    Property-driven code transformer
    
    Uses foundational properties to identify differences and select
    appropriate transformations to align code with canonical form.
    """
    
    def __init__(self, contract: dict = None, debug_mode: bool = False):
        super().__init__(
            name="PropertyDrivenTransformer",
            description="Property-driven transformation using foundational properties"
        )
        self.contract = contract
        self.debug_mode = debug_mode
        
        # Initialize components
        self.props_extractor = FoundationalProperties()
        
        # NEW: Property explainers and transformation strategies
        from .property_explainers import (
            StatementOrderingExplainer,
            LogicalEquivalenceExplainer,
            NormalizedASTStructureExplainer,
            ControlFlowSignatureExplainer,
            StringLiteralExplainer,
            VariableNamingExplainer
        )
        from .strategy_registry import StrategyRegistry
        
        self.explainers = {
            "statement_ordering": StatementOrderingExplainer(),
            "logical_equivalence": LogicalEquivalenceExplainer(),
            "normalized_ast_structure": NormalizedASTStructureExplainer(),
            "control_flow_signature": ControlFlowSignatureExplainer(),
            "string_literals": StringLiteralExplainer(),
            "data_dependency_graph": VariableNamingExplainer()
        }
        
        self.strategy_registry = StrategyRegistry()
        # Pass contract to strategies that require it (e.g., variable naming)
        for strategy in self.strategy_registry.get_strategies_for_property("data_dependency_graph"):
            if hasattr(strategy, "contract"):
                strategy.contract = contract
        
        # Track transformation history
        self.transformation_history: List[Dict[str, Any]] = []
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """
        Check if property-driven transformation can be applied
        Always returns True since we analyze properties dynamically
        """
        return canon_code is not None
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """
        Apply property-driven transformation (internal method)
        Called by base class transform() method
        """
        result = self.transform(code, canon_code)
        return result.transformed_code
    
    def transform(self, code: str, canon_code: str = None, property_diffs: list = None) -> TransformationResult:
        """
        Transform code using property-driven approach
        
        Args:
            code: Code to transform
            canon_code: Canonical code to align with (optional)
            
        Returns:
            TransformationResult
        """
        if not canon_code:
            return TransformationResult(
                transformed_code=code,
                success=False,
                original_code=code,
                transformation_name=self.name,
                distance_improvement=0.0,
                error_message="No canonical code provided"
            )
        
        self.transformation_history = []
        current_code = code
        max_iterations = 5
        
        for iteration in range(max_iterations):
            if self.debug_mode:
                print(f"\n[PropertyDrivenTransformer] Iteration {iteration + 1}")
            
            # Step 1: Extract properties
            code_props = self._extract_properties(current_code)
            canon_props = self._extract_properties(canon_code)
            
            if not code_props or not canon_props:
                break
            
            # Step 2: Explain differences (NEW - not just measure)
            differences = self._explain_differences(code_props, canon_props, current_code, canon_code)
            
            if not differences:
                if self.debug_mode:
                    print("[PropertyDrivenTransformer] No explainable differences found")
                break
            
            if self.debug_mode:
                print(f"[PropertyDrivenTransformer] Found {len(differences)} explainable differences")
                for d in differences:
                    print(f"  - {d}")
                    print(f"    Explanation: {d.explanation}")
            
            # Step 3: Select strategies based on property explanations
            strategies = self._select_strategies(differences)
            
            if not strategies:
                if self.debug_mode:
                    print("[PropertyDrivenTransformer] No applicable strategies")
                break
            
            if self.debug_mode:
                print(f"[PropertyDrivenTransformer] Selected {len(strategies)} strategies")
            
            # Step 4: Apply ALL applicable strategies in this iteration
            # This allows compound transformations (e.g., normalize strings + consolidate statements)
            transformation_applied = False
            iteration_code = current_code
            
            for strategy, difference in strategies:
                if self.debug_mode:
                    print(f"[PropertyDrivenTransformer] Trying {strategy.__class__.__name__}")
                
                transformed = strategy.generate_transformation(difference, iteration_code)
                
                if transformed and transformed != iteration_code:
                    # Validate transformation
                    if self._validate_transformation(iteration_code, transformed):
                        if self.debug_mode:
                            print(f"[PropertyDrivenTransformer] [OK] Applied {strategy.__class__.__name__}")
                        
                        # Record history
                        self.transformation_history.append({
                            'iteration': iteration + 1,
                            'strategy': strategy.__class__.__name__,
                            'property': difference.property_name,
                            'difference_type': difference.difference_type,
                            'before': iteration_code,
                            'after': transformed
                        })
                        
                        iteration_code = transformed
                        transformation_applied = True
                        # Continue to next strategy (don't break!)
                    else:
                        if self.debug_mode:
                            print(f"[PropertyDrivenTransformer] [FAIL] Validation failed for {strategy.__class__.__name__}")
            
            # Update current code with all changes from this iteration
            if transformation_applied:
                current_code = iteration_code
            
            if not transformation_applied:
                if self.debug_mode:
                    print("[PropertyDrivenTransformer] No transformations could be applied")
                break
        
        # Generate result
        success = current_code != code
        explanation = self._generate_explanation()
        
        return TransformationResult(
            transformed_code=current_code,
            success=success,
            original_code=code,
            transformation_name=self.name,
            distance_improvement=0.0,  # Could calculate this
            error_message=None if success else explanation
        )
    
    def _extract_properties(self, code: str) -> Optional[Dict[str, Any]]:
        """Extract foundational properties from code"""
        try:
            return self.props_extractor.extract_all_properties(code)
        except Exception as e:
            if self.debug_mode:
                print(f"[PropertyDrivenTransformer] Property extraction failed: {e}")
            return None
    
    def _explain_differences(self, code_props: Dict, canon_props: Dict, 
                            code: str, canon: str) -> List:
        """
        Use property explainers to understand HOW properties differ
        Returns list of PropertyDifference objects with explanations
        """
        try:
            differences = []
            
            for prop_name, explainer in self.explainers.items():
                code_prop = code_props.get(prop_name)
                canon_prop = canon_props.get(prop_name)
                
                # Some explainers (like StringLiteralExplainer) don't rely on properties
                # They analyze code directly, so we pass None for props
                if code_prop is not None and canon_prop is not None:
                    diff = explainer.explain_difference(code_prop, canon_prop, code, canon)
                elif prop_name == "string_literals":
                    # StringLiteralExplainer doesn't use foundational properties
                    diff = explainer.explain_difference(None, None, code, canon)
                else:
                    continue
                
                if diff:
                    differences.append(diff)
            
            return differences
            
        except Exception as e:
            if self.debug_mode:
                print(f"[PropertyDrivenTransformer] Explain differences failed: {e}")
            return []
    
    def _select_strategies(self, differences: List) -> List:
        """
        Select transformation strategies based on property differences
        Returns list of (strategy, difference) tuples
        """
        try:
            strategy_pairs = []
            
            for difference in differences:
                # Get strategies that can handle this difference
                applicable_strategies = self.strategy_registry.get_applicable_strategies(difference)
                
                for strategy in applicable_strategies:
                    strategy_pairs.append((strategy, difference))
            
            # Sort by severity (most severe first)
            strategy_pairs.sort(key=lambda x: x[1].severity, reverse=True)
            
            return strategy_pairs
            
        except Exception as e:
            if self.debug_mode:
                print(f"[PropertyDrivenTransformer] Strategy selection failed: {e}")
            return []
    
    def _validate_transformation(self, original: str, transformed: str) -> bool:
        """
        Validate that transformation preserves semantics
        
        Basic validation:
        1. Code is syntactically valid
        2. Code is different from original
        3. Has same function structure
        """
        if original == transformed:
            return False
        
        try:
            # Check syntax
            ast.parse(transformed)
            
            # Check that function structure is preserved
            orig_tree = ast.parse(original)
            trans_tree = ast.parse(transformed)
            
            orig_funcs = [n.name for n in ast.walk(orig_tree) if isinstance(n, ast.FunctionDef)]
            trans_funcs = [n.name for n in ast.walk(trans_tree) if isinstance(n, ast.FunctionDef)]
            
            if orig_funcs != trans_funcs:
                return False
            
            return True
            
        except SyntaxError:
            return False
    
    def _generate_explanation(self) -> str:
        """Generate explanation of transformations applied"""
        if not self.transformation_history:
            return "No transformations applied"
        
        lines = [f"Applied {len(self.transformation_history)} transformation(s):"]
        
        for entry in self.transformation_history:
            lines.append(f"  {entry['iteration']}. {entry['strategy']} fixing {entry['property']}.{entry['difference_type']}")
        
        return "\n".join(lines)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about transformations"""
        return {
            'total_transformations': len(self.transformation_history),
            'strategies_used': list(set(e['strategy'] for e in self.transformation_history)),
            'properties_addressed': list(set(e['property'] for e in self.transformation_history)),
            'difference_types': list(set(e['difference_type'] for e in self.transformation_history)),
            'iterations': len(set(e['iteration'] for e in self.transformation_history))
        }
    
    def reset_history(self):
        """Reset transformation history"""
        self.transformation_history = []
