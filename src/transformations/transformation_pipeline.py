"""
Transformation Pipeline - Orchestrates all transformations
Manages the order and application of different transformation modules
"""

from typing import List, Dict, Any, Optional
from .transformation_base import TransformationBase, TransformationResult
from .structural.error_handling_aligner import ErrorHandlingAligner
from .structural.redundant_clause_remover import RedundantClauseRemover
from .behavioral.algorithm_optimizer import AlgorithmOptimizer
from .behavioral.boundary_condition_aligner import BoundaryConditionAligner
from .behavioral.recursion_schema_aligner import RecursionSchemaAligner
from .behavioral.in_place_return_converter import InPlaceReturnConverter


class TransformationPipeline:
    """Orchestrates multiple transformations in sequence"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.transformations: List[TransformationBase] = []
        self.results_history: List[TransformationResult] = []
        
        # Initialize default transformations
        self._setup_default_transformations()
    
    def _setup_default_transformations(self):
        """Setup the default transformation pipeline"""
        
        # Order matters - structural transformations first, then behavioral
        transformations = [
            # Structural transformations (syntax-focused)
            ErrorHandlingAligner(),
            RedundantClauseRemover(),
            
            # Behavioral transformations (logic-focused)
            RecursionSchemaAligner(),      # NEW: For recursive algorithms
            InPlaceReturnConverter(),       # NEW: For sorting return semantics
            AlgorithmOptimizer(),
            BoundaryConditionAligner(),
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
    
    def transform_code(self, code: str, canon_code: str, max_iterations: int = 3) -> Dict[str, Any]:
        """
        Apply all applicable transformations to the code
        
        Args:
            code: Code to transform
            canon_code: Canonical reference code
            max_iterations: Maximum number of transformation passes
            
        Returns:
            Dictionary with transformation results and final code
        """
        
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
                    if self.debug_mode:
                        print(f"✅ {transformer.name} succeeded")
                    
                    current_code = result.transformed_code
                    successful_transformations.append(transformer.name)
                    code_changed = True
                    break  # Apply one transformation per iteration
                else:
                    if self.debug_mode:
                        print(f"❌ {transformer.name} failed: {result.error_message}")
            
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
