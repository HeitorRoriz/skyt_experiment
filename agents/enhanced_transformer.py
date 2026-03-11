#!/usr/bin/env python3
"""
Enhanced Code Transformer with Agent Capabilities
Preserves all existing functionality while adding agentic enhancements
"""

import sys
import os
from typing import Dict, Any, Optional

# SKYT imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.code_transformer import CodeTransformer
from src.canon_system import CanonSystem
from agents.agent_components import (
    DnaSequencer, TransformationPlanner, GeneticEngineer, 
    TransformationStrategy, AgentMetricsCollector
)


class EnhancedCodeTransformer:
    """
    Enhanced code transformer that adds agent capabilities 
    while preserving all existing functionality as fallback
    """
    
    def __init__(self, canon_system: CanonSystem, enable_agents: bool = True):
        """
        Initialize enhanced transformer
        
        Args:
            canon_system: Existing canonical system
            enable_agents: Whether to use agent enhancements (default: True)
        """
        # Preserve existing transformer as fallback
        self.traditional_transformer = CodeTransformer(canon_system)
        self.canon_system = canon_system
        
        # Agent components (only initialized if enabled)
        self.enable_agents = enable_agents
        if self.enable_agents:
            self.dna_sequencer = DnaSequencer()
            self.transformation_planner = TransformationPlanner()
            self.genetic_engineer = GeneticEngineer()
            self.metrics_collector = AgentMetricsCollector()
        else:
            self.dna_sequencer = None
            self.transformation_planner = None
            self.genetic_engineer = None
            self.metrics_collector = None
    
    def transform_to_canon(self, code: str, contract_id: str, contract: Optional[Dict[str, Any]] = None, oracle_system: Optional[Any] = None) -> Dict[str, Any]:
        """
        Transform code to canonical form with agent enhancement
        
        This method maintains the exact same interface as the original
        but adds agent capabilities when enabled
        """
        
        # BIG IF: Use agents if enabled and available
        if self.enable_agents and self._agents_available():
            return self._agent_enhanced_transform(code, contract_id, contract)
        else:
            # FALLBACK: Use traditional transformation exactly as before
            return self._traditional_transform(code, contract_id, contract)
    
    def _agents_available(self) -> bool:
        """Check if all agent components are properly initialized"""
        return (self.dna_sequencer is not None and 
                self.transformation_planner is not None and 
                self.genetic_engineer is not None)
    
    def _traditional_transform(self, code: str, contract_id: str, contract: Optional[Dict[str, Any]] = None, oracle_system: Optional[Any] = None) -> Dict[str, Any]:
        """
        Traditional transformation (exact same as original)
        This is the fallback that ensures no functionality is lost
        """
        try:
            # Use the existing transformer without any changes
            result = self.traditional_transformer.transform_to_canon(code, contract_id, contract, oracle_system)
            
            # Add strategy information for consistency
            if isinstance(result, dict):
                result["strategy_used"] = "traditional"
                result["agent_decisions"] = ["Used traditional transformation (fallback)"]
                result["dna_preserved"] = None  # Not applicable for traditional
            
            return result
            
        except Exception as e:
            # Ensure error handling is preserved
            return {
                "success": False,
                "error": str(e),
                "strategy_used": "traditional",
                "agent_decisions": [f"Traditional transformation error: {str(e)}"],
                "dna_preserved": None
            }
    
    def _agent_enhanced_transform(self, code: str, contract_id: str, contract: Optional[Dict[str, Any]] = None, oracle_system: Optional[Any] = None) -> Dict[str, Any]:
        """
        Agent-enhanced transformation with fallback to traditional
        """
        try:
            # Step 1: Extract DNA (non-critical, won't fail if this fails)
            code_dna = None
            try:
                code_dna = self.dna_sequencer.extract_dna(code)
            except Exception as dna_error:
                # DNA extraction failure shouldn't break the transformation
                print(f"Warning: DNA extraction failed: {dna_error}")
                code_dna = None
            
            # Step 2: Plan transformation strategy
            try:
                plan = self.transformation_planner.plan_strategy(code, code_dna, contract)
            except Exception as planning_error:
                # Planning failure - fall back to traditional
                print(f"Warning: Agent planning failed: {planning_error}")
                return self._traditional_transform(code, contract_id, contract, oracle_system)
            
            # Step 3: Execute based on strategy
            if plan.strategy == TransformationStrategy.TRADITIONAL:
                result = self._traditional_transform(code, contract_id, contract)
                result["planning_reasoning"] = plan.reasoning
                result["planning_confidence"] = plan.confidence
                
            elif plan.strategy == TransformationStrategy.GENETIC_ENGINEERING:
                result = self.genetic_engineer.transform_with_dna_preservation(code, contract_id, contract)
                result["planning_reasoning"] = plan.reasoning
                result["planning_confidence"] = plan.confidence
                
                # If genetic engineering fails, fall back to traditional
                if not result.get("success", False):
                    print(f"Genetic engineering failed, falling back to traditional: {result.get('error', 'Unknown error')}")
                    result = self._traditional_transform(code, contract_id, contract, oracle_system)
                    result["fallback_reason"] = "Genetic engineering failed"
            
            elif plan.strategy == TransformationStrategy.HYBRID:
                # Try genetic engineering first, fall back to traditional
                genetic_result = self.genetic_engineer.transform_with_dna_preservation(code, contract_id, contract)
                
                if genetic_result.get("success", False) and genetic_result.get("dna_preserved", False):
                    result = genetic_result
                else:
                    print(f"Hybrid approach: Genetic engineering not successful, using traditional")
                    result = self._traditional_transform(code, contract_id, contract, oracle_system)
                    result["fallback_reason"] = "Hybrid: Genetic engineering unsuccessful"
                
                result["planning_reasoning"] = plan.reasoning
                result["planning_confidence"] = plan.confidence
            
            else:
                # Unknown strategy - fall back to traditional
                result = self._traditional_transform(code, contract_id, contract, oracle_system)
                result["fallback_reason"] = f"Unknown strategy: {plan.strategy}"
            
            # Step 4: Record decision for learning (non-critical)
            try:
                if self.metrics_collector:
                    self.metrics_collector.record_decision(
                        plan.strategy, 
                        result.get("success", False), 
                        plan.reasoning
                    )
            except Exception as metrics_error:
                print(f"Warning: Metrics recording failed: {metrics_error}")
            
            # Add DNA information if available
            if code_dna:
                result["original_dna"] = code_dna
            
            return result
            
        except Exception as e:
            # Any failure in agent enhancement - fall back to traditional
            print(f"Agent enhancement failed: {e}, falling back to traditional")
            return self._traditional_transform(code, contract_id, contract, oracle_system)
    
    def get_agent_performance(self) -> Optional[Dict[str, Any]]:
        """Get agent performance metrics"""
        if self.metrics_collector:
            return self.metrics_collector.get_performance_summary()
        return None
    
    def disable_agents(self):
        """Disable agent enhancements and use only traditional transformation"""
        self.enable_agents = False
        print("Agent enhancements disabled - using traditional transformation only")
    
    def enable_agents_mode(self):
        """Enable agent enhancements"""
        self.enable_agents = True
        print("Agent enhancements enabled")
    
    def get_transformation_stats(self) -> Dict[str, Any]:
        """Get statistics about transformation approaches"""
        stats = {
            "agents_enabled": self.enable_agents,
            "agents_available": self._agents_available()
        }
        
        if self.metrics_collector:
            stats["agent_performance"] = self.metrics_collector.get_performance_summary()
        
        return stats


# Backward compatibility function
def create_enhanced_transformer(canon_system: CanonSystem, enable_agents: bool = True) -> EnhancedCodeTransformer:
    """
    Create enhanced transformer with same interface as traditional
    
    This function provides easy migration from traditional to enhanced
    """
    return EnhancedCodeTransformer(canon_system, enable_agents)
