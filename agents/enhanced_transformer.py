#!/usr/bin/env python3
"""
Enhanced Code Transformer with Agent Capabilities
Preserves all existing functionality while adding agentic enhancements
"""

import sys
import os
from typing import Dict, Any, Optional

# SKYT imports
_REPO = os.path.join(os.path.dirname(__file__), '..')
if _REPO not in sys.path:
    sys.path.append(_REPO)
from src.code_transformer import CodeTransformer
from src.canon_system import CanonSystem
try:
    from agents.agent_components import (
        DnaSequencer, TransformationPlanner, GeneticEngineer,
        TransformationStrategy, AgentMetricsCollector
    )
except ImportError:
    DnaSequencer = None
    TransformationPlanner = None
    GeneticEngineer = None
    TransformationStrategy = None
    AgentMetricsCollector = None


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
        
        # Agent components (only initialized if enabled). Replay uses
        # enable_agents=False and must not require the planner stack.
        self.enable_agents = bool(enable_agents) and DnaSequencer is not None
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
            result = self._agent_enhanced_transform(
                code, contract_id, contract, oracle_system
            )
        else:
            # FALLBACK: Use traditional transformation exactly as before
            result = self._traditional_transform(
                code, contract_id, contract, oracle_system
            )

        return self._validate_final_output(
            result, code, contract, oracle_system, contract_id
        )
    
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
            result = self.traditional_transformer.transform_to_canon(
                code,
                contract_id,
                contract=contract,
                oracle_system=oracle_system,
            )
            
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
                result = self._traditional_transform(
                    code, contract_id, contract, oracle_system
                )
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

    def _validate_final_output(
        self,
        result: Dict[str, Any],
        original_code: str,
        contract: Optional[Dict[str, Any]],
        oracle_system: Optional[Any],
        contract_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Oracle-check the actual persisted output and roll back on regression."""
        if not isinstance(result, dict):
            result = {
                "success": False,
                "error": "Transformer returned a non-dictionary result",
                "transformed_code": original_code,
                "transformations_applied": [],
                "final_distance": 1.0,
            }

        candidate = result.get("transformed_code", original_code)
        result.setdefault("success", False)
        result.setdefault("transformed_code", candidate)
        result.setdefault("transformations_applied", [])
        result.setdefault("final_distance", 1.0)
        result["oracle_validation_performed"] = False
        if oracle_system is None or contract is None:
            return result

        candidate_oracle = oracle_system.run_oracle_tests(candidate, contract)
        result["oracle_validation_performed"] = True
        result["attempted_post_oracle_result"] = candidate_oracle

        if candidate_oracle.get("passed", False):
            result["post_oracle_result"] = candidate_oracle
            result["rolled_back"] = False
            return result

        if candidate == original_code:
            result["post_oracle_result"] = candidate_oracle
            result["rolled_back"] = False
            return result

        # Never persist a behavior-breaking transformation. Revalidate the
        # original because it may itself have failed before transformation.
        original_oracle = oracle_system.run_oracle_tests(original_code, contract)
        result["attempted_transformed_code"] = candidate
        result["attempted_final_distance"] = result.get("final_distance")
        result["transformed_code"] = original_code
        if contract_id and getattr(self, "canon_system", None):
            try:
                comparison = self.canon_system.compare_to_canon(
                    contract_id, original_code
                )
                result["final_distance"] = comparison.get("distance", 1.0)
            except Exception:
                result["final_distance"] = 1.0
        else:
            result["final_distance"] = 1.0
        result["post_oracle_result"] = original_oracle
        result["rolled_back"] = True
        result["success"] = False
        result["error"] = "Transformation rolled back after oracle failure"
        return result
    
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
