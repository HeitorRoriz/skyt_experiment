#!/usr/bin/env python3
"""
Agent Components for Enhanced SKYT Transformation
These components add agentic capabilities without breaking existing functionality
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

# SKYT imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.contract import Contract
from src.oracle_system import OracleSystem
from src.code_transformer import CodeTransformer
from src.canon_system import CanonSystem
from src.foundational_properties import FoundationalProperties


class TransformationStrategy(Enum):
    """Different approaches to code transformation"""
    TRADITIONAL = "traditional"
    GENETIC_ENGINEERING = "genetic_engineering"
    HYBRID = "hybrid"


@dataclass
class TransformationPlan:
    """Plan for how to transform code"""
    strategy: TransformationStrategy
    confidence: float
    reasoning: str
    expected_difficulty: str
    dna_preservation_required: bool


@dataclass
class CodeDNA:
    """DNA signature of code (placeholder for future implementation)"""
    algorithm_signature: str
    complexity_class: str
    structural_properties: Dict[str, Any]
    behavioral_properties: Dict[str, Any]
    extraction_confidence: float


class DnaSequencer:
    """Extracts DNA signature from code (placeholder for future implementation)"""
    
    def __init__(self):
        self.properties_extractor = FoundationalProperties()
    
    def extract_dna(self, code: str) -> CodeDNA:
        """
        Extract DNA signature from code
        For now, this is a simplified version that will be enhanced
        """
        try:
            properties = self.properties_extractor.extract_all_properties(code)
            
            return CodeDNA(
                algorithm_signature=self._extract_algorithm_signature(properties),
                complexity_class=properties.get("complexity_class", "unknown"),
                structural_properties=properties.get("normalized_ast_structure", {}),
                behavioral_properties=properties.get("control_flow_signature", {}),
                extraction_confidence=0.8  # Placeholder
            )
        except Exception as e:
            # Fallback DNA for error cases
            return CodeDNA(
                algorithm_signature="unknown",
                complexity_class="unknown",
                structural_properties={},
                behavioral_properties={},
                extraction_confidence=0.0
            )
    
    def _extract_algorithm_signature(self, properties: Dict[str, Any]) -> str:
        """Extract algorithm signature from properties"""
        # Simplified version - will be enhanced
        control_flow = properties.get("control_flow_signature", {})
        return f"flow_{control_flow.get('complexity', 'unknown')}"


class TransformationPlanner:
    """Plans transformation strategies using agent intelligence"""
    
    def __init__(self):
        self.decision_rules = self._initialize_decision_rules()
    
    def plan_strategy(self, code: str, code_dna: CodeDNA, contract: Optional[Contract] = None) -> TransformationPlan:
        """
        Decide on transformation strategy
        For now, uses rule-based approach that will be enhanced with LLM
        """
        
        # Analyze code complexity
        complexity_score = self._analyze_complexity(code, code_dna)
        
        # Check contract requirements
        strict_requirements = self._check_contract_strictness(contract) if contract else False
        
        # Make decision
        if complexity_score > 0.8 or strict_requirements:
            return TransformationPlan(
                strategy=TransformationStrategy.TRADITIONAL,
                confidence=0.9,
                reasoning="High complexity or strict requirements - use proven traditional approach",
                expected_difficulty="high",
                dna_preservation_required=False
            )
        elif complexity_score > 0.5:
            return TransformationPlan(
                strategy=TransformationStrategy.HYBRID,
                confidence=0.7,
                reasoning="Medium complexity - try agents with traditional fallback",
                expected_difficulty="medium",
                dna_preservation_required=True
            )
        else:
            return TransformationPlan(
                strategy=TransformationStrategy.GENETIC_ENGINEERING,
                confidence=0.6,
                reasoning="Low complexity - good candidate for genetic engineering",
                expected_difficulty="low",
                dna_preservation_required=True
            )
    
    def _analyze_complexity(self, code: str, code_dna: CodeDNA) -> float:
        """Analyze code complexity (0.0 = simple, 1.0 = complex)"""
        complexity_indicators = {
            "very_high": 1.0,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4,
            "very_low": 0.2
        }
        
        return complexity_indicators.get(code_dna.complexity_class, 0.5)
    
    def _check_contract_strictness(self, contract: Contract) -> bool:
        """Check if contract has strict requirements"""
        if not contract:
            return False
        
        constraints = contract.data.get("constraints", {})
        
        # Check for strict indicators
        strict_indicators = [
            constraints.get("single_exit", False),
            constraints.get("strict_naming", False),
            constraints.get("bounds_checking_required", False),
            constraints.get("naming_policy") == "strict"
        ]
        
        return any(strict_indicators)
    
    def _initialize_decision_rules(self) -> Dict[str, Any]:
        """Initialize decision-making rules (will be enhanced with learning)"""
        return {
            "complexity_threshold": 0.7,
            "strict_contract_threshold": 0.8,
            "confidence_threshold": 0.6
        }


class GeneticEngineer:
    """Performs DNA-preserving code transformations (placeholder for future implementation)"""
    
    def __init__(self):
        self.canon_system = CanonSystem()
        self.dna_sequencer = DnaSequencer()
    
    def transform_with_dna_preservation(self, code: str, contract_id: str, contract: Optional[Contract] = None) -> Dict[str, Any]:
        """
        Transform code while preserving DNA
        For now, this is a placeholder that will be enhanced
        """
        try:
            # Extract original DNA
            original_dna = self.dna_sequencer.extract_dna(code)
            
            # For now, use traditional transformation as placeholder
            # In future, this will use sophisticated genetic engineering
            traditional_transformer = CodeTransformer(self.canon_system)
            traditional_result = traditional_transformer.transform_to_canon(code, contract_id, contract)
            
            # Extract DNA of transformed code
            if traditional_result.get("success"):
                transformed_code = traditional_result.get("transformed_code", code)
                new_dna = self.dna_sequencer.extract_dna(transformed_code)
                
                # Simple DNA preservation check (will be enhanced)
                dna_preserved = self._simple_dna_check(original_dna, new_dna)
                
                return {
                    "success": traditional_result["success"],
                    "transformed_code": transformed_code,
                    "final_distance": traditional_result.get("final_distance", 0.0),
                    "strategy_used": "genetic_engineering",
                    "dna_preserved": dna_preserved,
                    "original_dna": original_dna,
                    "new_dna": new_dna,
                    "transformations_applied": traditional_result.get("transformations_applied", []),
                    "agent_decisions": [
                        "Used genetic engineering approach",
                        f"DNA preservation: {'PRESERVED' if dna_preserved else 'NOT PRESERVED'}"
                    ]
                }
            else:
                return {
                    "success": False,
                    "error": traditional_result.get("error", "Genetic engineering failed"),
                    "strategy_used": "genetic_engineering",
                    "dna_preserved": False,
                    "agent_decisions": ["Genetic engineering failed, DNA not preserved"]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Genetic engineering error: {str(e)}",
                "strategy_used": "genetic_engineering",
                "dna_preserved": False,
                "agent_decisions": [f"Error in genetic engineering: {str(e)}"]
            }
    
    def _simple_dna_check(self, original_dna: CodeDNA, new_dna: CodeDNA) -> bool:
        """Simple DNA preservation check (will be enhanced)"""
        # For now, check basic algorithm signature preservation
        return original_dna.algorithm_signature == new_dna.algorithm_signature


class AgentMetricsCollector:
    """Collects metrics about agent performance"""
    
    def __init__(self):
        self.agent_decisions = []
        self.strategy_performance = {}
    
    def record_decision(self, strategy: TransformationStrategy, success: bool, reasoning: str):
        """Record agent decision for learning"""
        decision = {
            "strategy": strategy.value,
            "success": success,
            "reasoning": reasoning,
            "timestamp": asyncio.get_event_loop().time() if asyncio.get_event_loop() else 0
        }
        self.agent_decisions.append(decision)
        
        # Update strategy performance
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = {"successes": 0, "attempts": 0}
        
        self.strategy_performance[strategy]["attempts"] += 1
        if success:
            self.strategy_performance[strategy]["successes"] += 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of agent performance"""
        summary = {}
        for strategy, perf in self.strategy_performance.items():
            success_rate = perf["successes"] / perf["attempts"] if perf["attempts"] > 0 else 0
            summary[strategy.value] = {
                "success_rate": success_rate,
                "total_attempts": perf["attempts"],
                "total_successes": perf["successes"]
            }
        return summary
