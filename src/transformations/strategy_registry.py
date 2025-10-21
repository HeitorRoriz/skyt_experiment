"""
Strategy Registry
Maps properties to transformation strategies
"""

from typing import List, Dict
from .transformation_strategies import (
    TransformationStrategy,
    StatementConsolidationStrategy,
    BooleanSimplificationStrategy,
    LoopTransformationStrategy,
    ControlFlowNormalizationStrategy,
    StringNormalizationStrategy,
    VariableRenamingStrategy
)
from .property_explainers import PropertyDifference


class StrategyRegistry:
    """
    Central registry mapping properties to transformation strategies
    """
    
    def __init__(self):
        self.strategies: Dict[str, List[TransformationStrategy]] = {}
        self._register_all_strategies()
    
    def _register_all_strategies(self):
        """Register all built-in transformation strategies"""
        strategies = [
            StatementConsolidationStrategy(),
            BooleanSimplificationStrategy(),
            LoopTransformationStrategy(),
            ControlFlowNormalizationStrategy(),
            StringNormalizationStrategy(),
            VariableRenamingStrategy()
        ]
        
        for strategy in strategies:
            self.register(strategy)
    
    def register(self, strategy: TransformationStrategy):
        """Register a transformation strategy"""
        if strategy.property_name not in self.strategies:
            self.strategies[strategy.property_name] = []
        self.strategies[strategy.property_name].append(strategy)
    
    def get_strategies_for_property(self, property_name: str) -> List[TransformationStrategy]:
        """Get all strategies that handle a specific property"""
        return self.strategies.get(property_name, [])
    
    def get_applicable_strategies(self, difference: PropertyDifference) -> List[TransformationStrategy]:
        """
        Get strategies that can handle this specific property difference
        
        Args:
            difference: PropertyDifference from explainer
            
        Returns:
            List of applicable strategies
        """
        property_strategies = self.get_strategies_for_property(difference.property_name)
        
        # Filter to only strategies that can handle this difference
        applicable = []
        for strategy in property_strategies:
            if strategy.can_handle(difference):
                applicable.append(strategy)
        
        return applicable
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about registered strategies"""
        return {
            'total_strategies': sum(len(strategies) for strategies in self.strategies.values()),
            'properties_covered': len(self.strategies),
            'strategies_per_property': {
                prop: len(strategies) for prop, strategies in self.strategies.items()
            }
        }
