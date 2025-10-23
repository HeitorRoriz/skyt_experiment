"""
Transformation Pipeline - Orchestrates all transformations
Manages the order and application of different transformation modules
"""

from typing import List, Dict, Any, Optional
from .transformation_base import TransformationBase, TransformationResult
from .structural.error_handling_aligner import ErrorHandlingAligner
from .structural.redundant_clause_remover import RedundantClauseRemover
from .structural.variable_renamer import VariableRenamer
from .structural.arithmetic_expression_normalizer import ArithmeticExpressionNormalizer
from .structural.class_method_reorderer import ClassMethodReorderer
from .structural.import_normalizer import ImportNormalizer
from .structural.snap_to_canon_finalizer import SnapToCanonFinalizer
from .behavioral.algorithm_optimizer import AlgorithmOptimizer
from .behavioral.boundary_condition_aligner import BoundaryConditionAligner
from .behavioral.recursion_schema_aligner import RecursionSchemaAligner
from .behavioral.in_place_return_converter import InPlaceReturnConverter
from .semantic_validator import SemanticValidator
from .dictionary_normalizer import DictionaryNormalizer  # Import the new transformer
from .regex_pattern_normalizer import RegexPatternNormalizer  # Import regex normalizer
from .statement_chain_normalizer import StatementChainNormalizer  # Import statement chain normalizer


class TransformationPipeline:
    """Orchestrates multiple transformations in sequence"""
    
    def __init__(self, debug_mode: bool = False, contract: dict = None):
        self.debug_mode = debug_mode
        self.contract_data = contract  # Store for SnapToCanonFinalizer and others
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
            ImportNormalizer(),  # NEW: Add missing imports (should be first)
            VariableRenamer(contract=self.contract_data),  # Pass contract to respect fixed_variables
            ArithmeticExpressionNormalizer(),  # NEW: Handle algebraic equivalences
            ErrorHandlingAligner(contract=self.contract_data),
            RedundantClauseRemover(),
            RecursionSchemaAligner(),
            InPlaceReturnConverter(),
            AlgorithmOptimizer(),
            BoundaryConditionAligner(),
            
            # Add generic normalizers to handle common structural differences
            DictionaryNormalizer(),  # Dictionary key ordering
            RegexPatternNormalizer(),  # Regex pattern normalization
            StatementChainNormalizer(),  # Chained vs separate statements
            ClassMethodReorderer(),  # NEW: Class method ordering
            
            # LAST: Snap-to-canon finalizer (handles remaining harmless differences)
            SnapToCanonFinalizer(contract=self.contract_data),
        ]
        
        for transformer in transformations:
            if self.debug_mode:
                transformer.enable_debug()
            self.transformations.append(transformer)
    
    def transform_code(self, code: str, canon_code: str, max_iterations: int = 5, 
                      contract: dict = None, contract_id: str = None) -> dict:
        """
        Apply transformations to code to align with canon.
        
        Args:
            code: The code to transform
            canon_code: The canonical code to align with
            max_iterations: Maximum number of transformation iterations
            contract: Contract data (optional)
            contract_id: Contract identifier (optional)
        
        Returns:
            Dictionary with transformation results
        """
        self.contract_id = contract_id
        if contract:
            self.contract_data = contract
        
        current_code = code
        successful_transformations = []
        
        for iteration in range(max_iterations):
            transformed_this_iteration = False
            
            for transformer in self.transformations:
                if transformer.can_transform(current_code, canon_code):
                    result = transformer.transform(current_code, canon_code)
                    
                    if result.success:
                        current_code = result.transformed_code
                        successful_transformations.append(result.transformation_name)
                        transformed_this_iteration = True
                        
                        if self.debug_mode:
                            print(f"Applied {result.transformation_name}")
            
            # If no transformations were applied this iteration, stop
            if not transformed_this_iteration:
                break
        
        return {
            'final_code': current_code,
            'successful_transformations': successful_transformations,
            'iterations': len(successful_transformations)
        }
