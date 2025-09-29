# src/metrics.py
"""
Comprehensive repeatability metrics for SKYT experiments
Implements three-tier repeatability: raw, behavioral, and structural
"""

from typing import List, Dict, Any, Optional
from collections import Counter
import numpy as np
from .simple_canonicalizer import SimpleCanonicalizer
from .oracle_system import OracleSystem
from .foundational_properties import FoundationalProperties
from .canon_system import CanonSystem


class ComprehensiveMetrics:
    """Calculate comprehensive SKYT repeatability metrics"""
    
    def __init__(self, canon_system: Optional[CanonSystem] = None):
        self.canonicalizer = SimpleCanonicalizer()
        self.oracle_system = OracleSystem()
        self.properties_extractor = FoundationalProperties()
        self.canon_system = canon_system
    
    def calculate_three_tier_metrics(self, raw_outputs: List[str], 
                                   contract: Dict[str, Any],
                                   contract_id: str) -> Dict[str, Any]:
        """
        Calculate three-tier repeatability metrics
        
        Args:
            raw_outputs: List of raw LLM code outputs
            contract: Contract specification
            contract_id: Contract identifier for canon lookup
            
        Returns:
            Dictionary with all three repeatability metrics
        """
        if not raw_outputs:
            return self._empty_metrics()
        
        total_runs = len(raw_outputs)
        
        # Tier 1: Raw Repeatability (R_raw)
        r_raw, raw_stats = self._calculate_raw_repeatability(raw_outputs)
        
        # Tier 2: Behavioral Repeatability (R_behavioral)
        r_behavioral, behavioral_stats = self._calculate_behavioral_repeatability(
            raw_outputs, contract
        )
        
        # Tier 3: Structural Repeatability (R_structural)
        r_structural, structural_stats = self._calculate_structural_repeatability(
            raw_outputs, contract_id
        )
        
        # Distance variance calculations
        distances = self._calculate_distance_variance(raw_outputs, contract_id)
        
        return {
            # Core metrics
            "R_raw": r_raw,
            "R_behavioral": r_behavioral,
            "R_structural": r_structural,
            
            # Legacy compatibility
            "R_canon": r_structural,  # Structural is the new canonical
            
            # Detailed statistics
            "total_runs": total_runs,
            "raw_stats": raw_stats,
            "behavioral_stats": behavioral_stats,
            "structural_stats": structural_stats,
            
            # Distance analysis
            "distance_variance": distances,
            
            # Improvement metrics
            "behavioral_improvement": r_behavioral - r_raw,
            "structural_improvement": r_structural - r_raw,
            "total_improvement": r_structural - r_raw
        }
    
    def _calculate_raw_repeatability(self, raw_outputs: List[str]) -> tuple[float, Dict[str, Any]]:
        """Calculate raw string-based repeatability"""
        raw_counter = Counter(raw_outputs)
        most_common = raw_counter.most_common(1)[0]
        r_raw = most_common[1] / len(raw_outputs)
        
        stats = {
            "unique_outputs": len(raw_counter),
            "most_common_count": most_common[1],
            "distribution": dict(raw_counter),
            "entropy": self._calculate_entropy(list(raw_counter.values()))
        }
        
        return r_raw, stats
    
    def _calculate_behavioral_repeatability(self, raw_outputs: List[str], 
                                          contract: Dict[str, Any]) -> tuple[float, Dict[str, Any]]:
        """Calculate behavioral equivalence using oracle tests"""
        behavioral_groups = {}
        oracle_results = []
        
        for i, code in enumerate(raw_outputs):
            # Run oracle tests
            oracle_result = self.oracle_system.run_oracle_tests(code, contract)
            oracle_results.append(oracle_result)
            
            # Group by behavioral signature
            if oracle_result["passed"]:
                # Create behavioral signature from test results
                signature = self._create_behavioral_signature(oracle_result)
                if signature not in behavioral_groups:
                    behavioral_groups[signature] = []
                behavioral_groups[signature].append(i)
            else:
                # Failed tests get unique signatures
                behavioral_groups[f"failed_{i}"] = [i]
        
        # Calculate repeatability
        if behavioral_groups:
            largest_group = max(len(group) for group in behavioral_groups.values())
            r_behavioral = largest_group / len(raw_outputs)
        else:
            r_behavioral = 0.0
        
        stats = {
            "unique_behaviors": len(behavioral_groups),
            "oracle_results": oracle_results,
            "behavioral_groups": behavioral_groups,
            "pass_rate": sum(1 for r in oracle_results if r["passed"]) / len(oracle_results)
        }
        
        return r_behavioral, stats
    
    def _calculate_structural_repeatability(self, raw_outputs: List[str], 
                                          contract_id: str) -> tuple[float, Dict[str, Any]]:
        """Calculate structural equivalence using foundational properties"""
        structural_groups = {}
        property_results = []
        distances = []
        
        # Get canon if available
        canon_data = None
        if self.canon_system:
            canon_data = self.canon_system.load_canon(contract_id)
        
        for i, code in enumerate(raw_outputs):
            # Extract foundational properties
            properties = self.properties_extractor.extract_all_properties(code)
            property_results.append(properties)
            
            # Create structural signature
            signature = self._create_structural_signature(properties)
            if signature not in structural_groups:
                structural_groups[signature] = []
            structural_groups[signature].append(i)
            
            # Calculate distance to canon if available
            if canon_data:
                distance = self.properties_extractor.calculate_distance(
                    canon_data["foundational_properties"], properties
                )
                distances.append(distance)
        
        # Calculate repeatability
        if structural_groups:
            largest_group = max(len(group) for group in structural_groups.values())
            r_structural = largest_group / len(raw_outputs)
        else:
            r_structural = 0.0
        
        stats = {
            "unique_structures": len(structural_groups),
            "property_results": property_results,
            "structural_groups": structural_groups,
            "distances_to_canon": distances,
            "mean_distance": np.mean(distances) if distances else None,
            "std_distance": np.std(distances) if distances else None
        }
        
        return r_structural, stats
    
    def _calculate_distance_variance(self, raw_outputs: List[str], 
                                   contract_id: str) -> Dict[str, Any]:
        """Calculate distance variance for bell curve analysis"""
        if not self.canon_system:
            return {"error": "No canon system available"}
        
        canon_data = self.canon_system.load_canon(contract_id)
        if not canon_data:
            return {"error": "No canon found"}
        
        distances = []
        canon_properties = canon_data["foundational_properties"]
        
        for code in raw_outputs:
            properties = self.properties_extractor.extract_all_properties(code)
            distance = self.properties_extractor.calculate_distance(
                canon_properties, properties
            )
            distances.append(distance)
        
        if not distances:
            return {"error": "No distances calculated"}
        
        return {
            "distances": distances,
            "mean": np.mean(distances),
            "std": np.std(distances),
            "min": np.min(distances),
            "max": np.max(distances),
            "variance": np.var(distances),
            "histogram_bins": np.histogram(distances, bins=10)[0].tolist(),
            "histogram_edges": np.histogram(distances, bins=10)[1].tolist()
        }
    
    def _create_behavioral_signature(self, oracle_result: Dict[str, Any]) -> str:
        """Create signature from oracle test results"""
        if not oracle_result["passed"]:
            return "failed"
        
        # Create signature from test outcomes
        test_results = oracle_result.get("test_results", [])
        signature_parts = []
        
        for test in test_results:
            if test.get("passed", False):
                signature_parts.append("P")
            else:
                signature_parts.append("F")
        
        return "".join(signature_parts)
    
    def _create_structural_signature(self, properties: Dict[str, Any]) -> str:
        """Create signature from foundational properties"""
        # Create a hash-like signature from key structural properties
        signature_parts = []
        
        key_properties = [
            "control_flow_signature",
            "complexity_class", 
            "side_effect_profile",
            "normalized_ast_structure"
        ]
        
        for prop_name in key_properties:
            prop_value = properties.get(prop_name)
            if prop_value:
                if isinstance(prop_value, dict):
                    # Convert dict to hashable form, handling nested lists/dicts
                    try:
                        hashable_items = []
                        for k, v in prop_value.items():
                            if isinstance(v, (list, dict)):
                                hashable_items.append((k, str(v)))
                            else:
                                hashable_items.append((k, v))
                        signature_parts.append(str(hash(frozenset(hashable_items))))
                    except:
                        signature_parts.append(str(hash(str(prop_value))))
                else:
                    signature_parts.append(str(hash(str(prop_value))))
            else:
                signature_parts.append("None")
        
        return "_".join(signature_parts)
    
    def _calculate_entropy(self, counts: List[int]) -> float:
        """Calculate Shannon entropy of distribution"""
        if not counts:
            return 0.0
        
        total = sum(counts)
        probabilities = [count / total for count in counts]
        
        entropy = 0.0
        for p in probabilities:
            if p > 0:
                entropy -= p * np.log2(p)
        
        return entropy
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            "R_raw": 0.0,
            "R_behavioral": 0.0,
            "R_structural": 0.0,
            "R_canon": 0.0,
            "total_runs": 0,
            "error": "No outputs provided"
        }
    
    def calculate_aggregate_metrics(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate aggregate metrics across multiple experiments
        
        Args:
            all_results: List of individual experiment results
            
        Returns:
            Aggregate metrics summary
        """
        if not all_results:
            return {}
        
        # Extract metric values
        r_raw_values = [result.get("R_raw", 0.0) for result in all_results]
        r_behavioral_values = [result.get("R_behavioral", 0.0) for result in all_results]
        r_structural_values = [result.get("R_structural", 0.0) for result in all_results]
        
        return {
            # Mean values
            "mean_R_raw": np.mean(r_raw_values),
            "mean_R_behavioral": np.mean(r_behavioral_values),
            "mean_R_structural": np.mean(r_structural_values),
            
            # Standard deviations
            "std_R_raw": np.std(r_raw_values),
            "std_R_behavioral": np.std(r_behavioral_values),
            "std_R_structural": np.std(r_structural_values),
            
            # Min/Max
            "min_R_raw": np.min(r_raw_values),
            "max_R_raw": np.max(r_raw_values),
            "min_R_behavioral": np.min(r_behavioral_values),
            "max_R_behavioral": np.max(r_behavioral_values),
            "min_R_structural": np.min(r_structural_values),
            "max_R_structural": np.max(r_structural_values),
            
            # Improvements
            "mean_behavioral_improvement": np.mean(r_behavioral_values) - np.mean(r_raw_values),
            "mean_structural_improvement": np.mean(r_structural_values) - np.mean(r_raw_values),
            
            # Meta
            "total_experiments": len(all_results)
        }


# Legacy compatibility
class MetricsCalculator(ComprehensiveMetrics):
    """Legacy metrics calculator for backward compatibility"""
    
    def calculate_metrics(self, raw_outputs: List[str]) -> Dict[str, Any]:
        """Legacy method - returns simplified metrics"""
        if not raw_outputs:
            return {"R_raw": 0.0, "R_canon": 0.0, "total_runs": 0}
        
        # Use simple canonicalizer for R_canon
        total_runs = len(raw_outputs)
        
        # Calculate R_raw
        raw_counter = Counter(raw_outputs)
        most_common_raw = raw_counter.most_common(1)[0]
        r_raw = most_common_raw[1] / total_runs
        
        # Calculate R_canon using simple canonicalizer
        canonical_outputs = [self.canonicalizer.canonicalize(code) for code in raw_outputs]
        canon_counter = Counter(canonical_outputs)
        most_common_canon = canon_counter.most_common(1)[0]
        r_canon = most_common_canon[1] / total_runs
        
        return {
            "R_raw": r_raw,
            "R_canon": r_canon,
            "total_runs": total_runs,
            "unique_raw": len(raw_counter),
            "unique_canon": len(canon_counter),
            "most_common_raw_count": most_common_raw[1],
            "most_common_canon_count": most_common_canon[1],
            "raw_distribution": dict(raw_counter),
            "canon_distribution": dict(canon_counter)
        }
