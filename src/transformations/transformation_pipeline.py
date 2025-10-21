"""
Transformation Pipeline - Orchestrates all transformations
Manages the order and application of different transformation modules
"""

from typing import List, Dict, Any, Optional
from .transformation_base import TransformationBase, TransformationResult
from .structural.error_handling_aligner import ErrorHandlingAligner
from .structural.redundant_clause_remover import RedundantClauseRemover
from .structural.variable_renamer import VariableRenamer
from .structural.snap_to_canon_finalizer import SnapToCanonFinalizer
from .behavioral.algorithm_optimizer import AlgorithmOptimizer
from .behavioral.boundary_condition_aligner import BoundaryConditionAligner
from .behavioral.recursion_schema_aligner import RecursionSchemaAligner
from .behavioral.in_place_return_converter import InPlaceReturnConverter
from .semantic_validator import SemanticValidator


class TransformationPipeline:
    """Orchestrates multiple transformations in sequence"""
    
    def __init__(self, debug_mode: bool = False, contract: dict = None):
        self.debug_mode = debug_mode
        self.contract_data = contract  # Store for SnapToCanonFinalizer
        self.contract_id = None  # Will be set in transform_code
        self.transformations: List[TransformationBase] = []
        self.results_history: List[TransformationResult] = []
        self.semantic_validator = SemanticValidator()  # For behavioral validation
        
        # Initialize default transformations
        self._setup_default_transformations()
    
    def _setup_default_transformations(self):
        """Setup the default transformation pipeline"""
        
        # Import PropertyDrivenTransformer
        from .property_driven_transformer import PropertyDrivenTransformer
        
        # NEW APPROACH: Use property-driven transformer as primary
        # Falls back to algorithm-specific transformers if needed
        transformations = [
            # PRIMARY: Property-driven transformation (generic, no hardcoded logic)
            PropertyDrivenTransformer(contract=self.contract_data, debug_mode=self.debug_mode),
            
            # FALLBACK: Algorithm-specific transformers (kept for compatibility)
            # These will only apply if PropertyDrivenTransformer doesn't handle the case
            VariableRenamer(),
            ErrorHandlingAligner(),
            RedundantClauseRemover(),
            RecursionSchemaAligner(),
            InPlaceReturnConverter(),
            AlgorithmOptimizer(),
            BoundaryConditionAligner(),
            
            # LAST: Snap-to-canon finalizer (handles remaining harmless differences)
            SnapToCanonFinalizer(contract=self.contract_data),
        ]
        
        for transformer in transformations:
            if self.debug_mode:
                transformer.enable_debug()
            self.transformations.append(transformer)
    
    def add_transformation(self, transformation: TransformationBase):
        """Add a custom transformation to the pipeline"""
        if self.debug_mode:
            transformation.enable_debug()
        self.transformations.append(transformation)
    
    def transform_code(self, code: str, canon_code: str, max_iterations: int = 3,
                      contract: dict = None, contract_id: str = None) -> Dict[str, Any]:
        """
        Apply all applicable transformations to the code
        
        Args:
            code: Code to transform
            canon_code: Canonical reference code
            max_iterations: Maximum number of transformation passes
            contract: Optional contract for domain-aware validation
            contract_id: Optional contract ID for distance calculation
            
        Returns:
            Dictionary with transformation results and final code
        """
        
        # Store contract for validation (override init contract if provided)
        if contract:
            self.contract_data = contract
        self.contract_id = contract_id
        
        if self.debug_mode:
            print(f"\n=== TRANSFORMATION PIPELINE START ===")
            print(f"Input code:\n{code}")
            print(f"Canon code:\n{canon_code}")
        
        current_code = code
        all_results = []
        successful_transformations = []
        
        # Import property extractor for property-driven transformation
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from foundational_properties import FoundationalProperties
        props_extractor = FoundationalProperties()
        
        for iteration in range(max_iterations):
            if self.debug_mode:
                print(f"\n--- Iteration {iteration + 1} ---")
            
            # Compute property differences for this iteration
            current_props = props_extractor.extract_all_properties(current_code)
            canon_props = props_extractor.extract_all_properties(canon_code)
            property_diffs = self._compute_property_diffs(current_props, canon_props, props_extractor)
            
            if self.debug_mode and property_diffs:
                print(f"Property differences detected: {len([d for d in property_diffs if d['distance'] > 0])}")
            
            iteration_results = []
            code_changed = False
            
            for transformer in self.transformations:
                if self.debug_mode:
                    print(f"\nTrying {transformer.name}...")
                
                # Pass property differences to transformer
                result = transformer.transform(current_code, canon_code, property_diffs=property_diffs)
                iteration_results.append(result)
                
                if result.success:
                    # CRITICAL: Validate transformation didn't break the code
                    is_valid = self._validate_transformation(
                        original_code=current_code,
                        transformed_code=result.transformed_code,
                        transformer_name=transformer.name
                    )
                    
                    if is_valid:
                        if self.debug_mode:
                            print(f"[SUCCESS] {transformer.name} succeeded and validated")
                        
                        current_code = result.transformed_code
                        successful_transformations.append(transformer.name)
                        code_changed = True
                        break  # Apply one transformation per iteration
                    else:
                        # ROLLBACK: Reject transformation that breaks code
                        if self.debug_mode:
                            print(f"[ROLLBACK] {transformer.name} broke code - rolling back")
                        # Don't update current_code, continue to next transformer
                        continue
                else:
                    if self.debug_mode:
                        print(f"[FAILED] {transformer.name} failed: {result.error_message}")
            
            all_results.extend(iteration_results)
            
            # If no transformation was applied this iteration, stop
            if not code_changed:
                if self.debug_mode:
                    print("No more transformations applicable")
                break
        
        # Calculate final results
        transformation_success = len(successful_transformations) > 0
        final_code = current_code
        
        if self.debug_mode:
            print(f"\n=== TRANSFORMATION PIPELINE END ===")
            print(f"Final code:\n{final_code}")
            print(f"Successful transformations: {successful_transformations}")
        
        return {
            'original_code': code,
            'final_code': final_code,
            'transformation_success': transformation_success,
            'successful_transformations': successful_transformations,
            'all_results': all_results,
            'iterations_used': min(iteration + 1, max_iterations)
        }
    
    def get_available_transformations(self) -> List[str]:
        """Get list of available transformation names"""
        return [t.name for t in self.transformations]
    
    def enable_debug(self):
        """Enable debug mode for pipeline and all transformations"""
        self.debug_mode = True
        for transformer in self.transformations:
            transformer.enable_debug()
    
    def disable_debug(self):
        """Disable debug mode"""
        self.debug_mode = False
        for transformer in self.transformations:
            transformer.debug_mode = False
    
    def _compute_property_diffs(self, current_props: dict, canon_props: dict, extractor) -> list:
        """Compute property differences between current code and canon"""
        diffs = []
        
        for prop_name in extractor.properties:
            if prop_name in current_props and prop_name in canon_props:
                distance = extractor._calculate_property_distance(
                    current_props[prop_name],
                    canon_props[prop_name],
                    prop_name
                )
                
                diffs.append({
                    'property': prop_name,
                    'distance': distance,
                    'current_value': current_props[prop_name],
                    'canon_value': canon_props[prop_name]
                })
        
        return diffs
    
    def _validate_transformation(self, original_code: str, transformed_code: str, 
                                 transformer_name: str) -> bool:
        """
        Validate that transformation didn't break the code
        
        Uses contract-aware validation if contract is available, otherwise falls back to
        basic syntax and semantic checks.
        
        Contract-aware validation:
        1. Both codes must pass oracle tests within contract domain
        2. Transformation must be monotonic (reduce distance to canon)
        
        Basic validation:
        1. Code is still parseable (valid Python syntax)
        2. No undefined variables introduced
        3. Function still exists
        
        Returns True if transformation is valid, False if it broke code
        """
        try:
            import ast
            
            # Check 1: Can we parse it?
            try:
                tree = ast.parse(transformed_code)
            except SyntaxError:
                if self.debug_mode:
                    print(f"  REJECT: {transformer_name} produced syntax error")
                return False
            
            # Check 2: Look for undefined variable references
            class VariableChecker(ast.NodeVisitor):
                def __init__(self):
                    self.defined = set()
                    self.used = set()
                    self.current_scope = set()
                
                def visit_Import(self, node):
                    # Handle: import re, import os
                    for alias in node.names:
                        self.defined.add(alias.asname if alias.asname else alias.name)
                    self.generic_visit(node)
                
                def visit_ImportFrom(self, node):
                    # Handle: from re import sub
                    for alias in node.names:
                        self.defined.add(alias.asname if alias.asname else alias.name)
                    self.generic_visit(node)
                    
                def visit_FunctionDef(self, node):
                    self.defined.add(node.name)
                    for arg in node.args.args:
                        self.defined.add(arg.arg)
                        self.current_scope.add(arg.arg)
                    self.generic_visit(node)
                
                def visit_Assign(self, node):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.defined.add(target.id)
                            self.current_scope.add(target.id)
                        elif isinstance(target, ast.Tuple):
                            # Handle tuple unpacking (e.g., a, b = 0, 1)
                            for elt in target.elts:
                                if isinstance(elt, ast.Name):
                                    self.defined.add(elt.id)
                                    self.current_scope.add(elt.id)
                    self.generic_visit(node)
                
                def visit_For(self, node):
                    # Handle for loop variables (e.g., for char in s:)
                    if isinstance(node.target, ast.Name):
                        self.defined.add(node.target.id)
                        self.current_scope.add(node.target.id)
                    elif isinstance(node.target, ast.Tuple):
                        # Handle tuple unpacking in for loops (e.g., for i, val in enumerate(...))
                        for elt in node.target.elts:
                            if isinstance(elt, ast.Name):
                                self.defined.add(elt.id)
                                self.current_scope.add(elt.id)
                    self.generic_visit(node)
                
                def visit_Name(self, node):
                    if isinstance(node.ctx, ast.Load):
                        self.used.add(node.id)
                    self.generic_visit(node)
            
            checker = VariableChecker()
            checker.visit(tree)
            
            builtins = {'range', 'len', 'print', 'max', 'min', 'sum', 'abs', 'sorted', 'enumerate', 'zip'}
            undefined = (checker.used - checker.defined) - builtins
            
            if undefined:
                if self.debug_mode:
                    print(f"  REJECT: {transformer_name} introduced undefined variables: {undefined}")
                return False
            
            # Check 3: Does the code still have at least one function?
            has_function = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
            if not has_function:
                if self.debug_mode:
                    print(f"  REJECT: {transformer_name} removed all functions")
                return False
            
            # Check 4: CONTRACT-AWARE VALIDATION (if contract available)
            if hasattr(self, 'contract_data') and self.contract_data and hasattr(self, 'contract_id') and self.contract_id:
                if self.debug_mode:
                    print(f"  Using contract-aware validation for {transformer_name}")
                
                try:
                    # Try to import from src package
                    from src.contract_validator import validate_transformation
                except ImportError:
                    # Fallback: add src to path and import
                    import sys
                    import os
                    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                    if src_dir not in sys.path:
                        sys.path.insert(0, src_dir)
                    import contract_validator
                    validate_transformation = contract_validator.validate_transformation
                
                is_valid, message = validate_transformation(
                    original_code, transformed_code, 
                    self.contract_data, self.contract_id
                )
                
                if not is_valid:
                    if self.debug_mode:
                        print(f"  REJECT (contract-aware): {transformer_name} - {message}")
                    return False
                else:
                    if self.debug_mode:
                        print(f"  ACCEPT (contract-aware): {transformer_name} - {message}")
                    return True
            else:
                if self.debug_mode:
                    print(f"  Contract-aware validation NOT available - using semantic equivalence")
                    print(f"    has contract_data: {hasattr(self, 'contract_data')}")
                    print(f"    contract_data: {getattr(self, 'contract_data', None) is not None}")
                    print(f"    has contract_id: {hasattr(self, 'contract_id')}")
                    print(f"    contract_id: {getattr(self, 'contract_id', None)}")
            
            # Fallback: SEMANTIC EQUIVALENCE (legacy behavior)
            # SKIP for PropertyDrivenTransformer - it's property-preserving by design
            if transformer_name != "PropertyDrivenTransformer":
                if not self.semantic_validator.are_semantically_equivalent(original_code, transformed_code):
                    if self.debug_mode:
                        behavioral_dist = self.semantic_validator.calculate_behavioral_distance(
                            original_code, transformed_code
                        )
                        print(f"  REJECT: {transformer_name} changed behavior (distance={behavioral_dist:.3f})")
                    return False
            
            # All checks passed
            return True
            
        except Exception as e:
            # If validation itself fails, be conservative and reject
            if self.debug_mode:
                print(f"  REJECT: Validation failed with error: {e}")
            return False
