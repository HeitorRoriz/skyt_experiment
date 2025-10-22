# src/metrics.py
"""
Comprehensive repeatability metrics for SKYT experiments
Implements all metrics required for the paper:
- Core: R_raw, R_anchor (pre/post), Δ_rescue, R_repair@k
- Distributional: Distance distributions, Δμ, ΔPτ
- Complementary: Canon coverage, rescue rate, structural/behavioral breakdown
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import numpy as np
from .oracle_system import OracleSystem
from .foundational_properties import FoundationalProperties
from .canon_system import CanonSystem


class ComprehensiveMetrics:
    """Calculate comprehensive SKYT repeatability metrics for paper"""
    
    def __init__(self, canon_system: Optional[CanonSystem] = None):
        self.oracle_system = OracleSystem()
        self.properties_extractor = FoundationalProperties()
        self.canon_system = canon_system
        
        # Default thresholds for R_repair@k
        self.repair_thresholds = [0.05, 0.1, 0.15, 0.2]
    
    def calculate_comprehensive_metrics(self, raw_outputs: List[str],
                                        repaired_outputs: List[str],
                                        contract: Dict[str, Any],
                                        contract_id: str) -> Dict[str, Any]:
        """
        Calculate ALL metrics required for the paper
        
        Args:
            raw_outputs: List of raw LLM code outputs (pre-repair)
            repaired_outputs: List of repaired/canonicalized outputs (post-repair)
            contract: Contract specification
            contract_id: Contract identifier for canon lookup
            
        Returns:
            Dictionary with all required metrics
        """
        if not raw_outputs:
            return self._empty_metrics()
        
        total_runs = len(raw_outputs)
        
        # === CORE REPEATABILITY METRICS ===
        
        # R_raw: Raw repeatability (byte-identical outputs)
        r_raw, raw_stats = self._calculate_raw_repeatability(raw_outputs)
        
        # R_anchor: Pre and post repair anchor repeatability
        r_anchor_pre, anchor_pre_stats = self._calculate_anchor_repeatability(
            raw_outputs, contract_id
        )
        r_anchor_post, anchor_post_stats = self._calculate_anchor_repeatability(
            repaired_outputs, contract_id
        )
        
        # Δ_rescue: Improvement in exact canon matches after repair
        delta_rescue = r_anchor_post - r_anchor_pre
        
        # R_repair@k: Tolerance-based repeatability at different thresholds
        r_repair_at_k_pre = self._calculate_repair_at_k(
            raw_outputs, contract_id, self.repair_thresholds
        )
        r_repair_at_k_post = self._calculate_repair_at_k(
            repaired_outputs, contract_id, self.repair_thresholds
        )
        
        # === DISTRIBUTIONAL / STATISTICAL METRICS ===
        
        # Distance distributions (pre vs post)
        distances_pre = self._get_distances_to_canon(raw_outputs, contract_id)
        distances_post = self._get_distances_to_canon(repaired_outputs, contract_id)
        
        # Δμ: Mean distance delta
        mean_distance_pre = np.mean(distances_pre) if distances_pre else 0.0
        mean_distance_post = np.mean(distances_post) if distances_post else 0.0
        delta_mu = mean_distance_pre - mean_distance_post
        
        # ΔPτ: Partial repeatability delta at thresholds
        delta_p_tau = self._calculate_delta_p_tau(
            distances_pre, distances_post, self.repair_thresholds
        )
        
        # === COMPLEMENTARY METRICS ===
        
        # Canon coverage: Fraction passing oracle tests
        canon_coverage = self._calculate_canon_coverage(raw_outputs, contract)
        
        # Rescue rate: Fraction of non-canonical outputs successfully repaired
        rescue_rate = self._calculate_rescue_rate(
            raw_outputs, repaired_outputs, contract_id
        )
        
        # Structural & Behavioral breakdown
        r_behavioral, behavioral_stats = self._calculate_behavioral_repeatability(
            raw_outputs, contract
        )
        r_structural, structural_stats = self._calculate_structural_repeatability(
            repaired_outputs, contract_id  # Use repaired outputs for structural repeatability
        )
        
        # === LEGACY COMPATIBILITY ===
        r_canon = r_anchor_post  # Canonical repeatability = post-repair anchor
        
        return {
            # === CORE REPEATABILITY METRICS ===
            "R_raw": r_raw,
            "R_anchor_pre": r_anchor_pre,
            "R_anchor_post": r_anchor_post,
            "Delta_rescue": delta_rescue,
            "R_repair_at_k_pre": r_repair_at_k_pre,
            "R_repair_at_k_post": r_repair_at_k_post,
            
            # === DISTRIBUTIONAL METRICS ===
            "distances_pre": distances_pre,
            "distances_post": distances_post,
            "mean_distance_pre": mean_distance_pre,
            "mean_distance_post": mean_distance_post,
            "std_distance_pre": np.std(distances_pre) if distances_pre else 0.0,
            "std_distance_post": np.std(distances_post) if distances_post else 0.0,
            "Delta_mu": delta_mu,
            "Delta_P_tau": delta_p_tau,
            
            # === COMPLEMENTARY METRICS ===
            "canon_coverage": canon_coverage,
            "rescue_rate": rescue_rate,
            "R_behavioral": r_behavioral,
            "R_structural": r_structural,
            
            # === LEGACY COMPATIBILITY ===
            "R_canon": r_canon,
            "behavioral_improvement": r_behavioral - r_raw,
            "structural_improvement": r_structural - r_raw,
            
            # === METADATA ===
            "total_runs": total_runs,
            "raw_stats": raw_stats,
            "anchor_pre_stats": anchor_pre_stats,
            "anchor_post_stats": anchor_post_stats,
            "behavioral_stats": behavioral_stats,
            "structural_stats": structural_stats
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
    
    def _calculate_anchor_repeatability(self, outputs: List[str], 
                                        contract_id: str) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate R_anchor: Probability mass of outputs with distance d=0 to canon
        
        Args:
            outputs: List of code outputs
            contract_id: Contract identifier for canon lookup
            
        Returns:
            Tuple of (R_anchor, statistics)
        """
        if not self.canon_system:
            return 0.0, {"error": "No canon system available"}
        
        canon_data = self.canon_system.load_canon(contract_id)
        if not canon_data:
            return 0.0, {"error": "No canon found"}
        
        exact_matches = 0
        distances = []
        
        for code in outputs:
            comparison = self.canon_system.compare_to_canon(contract_id, code)
            distance = comparison.get("distance", float('inf'))
            distances.append(distance)
            
            if distance == 0.0 or comparison.get("is_identical", False):
                exact_matches += 1
        
        r_anchor = exact_matches / len(outputs) if outputs else 0.0
        
        stats = {
            "exact_matches": exact_matches,
            "total_outputs": len(outputs),
            "distances": distances,
            "mean_distance": np.mean(distances) if distances else 0.0,
            "min_distance": np.min(distances) if distances else 0.0
        }
        
        return r_anchor, stats
    
    def _calculate_repair_at_k(self, outputs: List[str], contract_id: str,
                              thresholds: List[float]) -> Dict[str, float]:
        """
        Calculate R_repair@k: Probability mass within distance ≤ k
        
        Args:
            outputs: List of code outputs
            contract_id: Contract identifier
            thresholds: List of distance thresholds
            
        Returns:
            Dictionary mapping threshold to repeatability score
        """
        if not self.canon_system:
            return {f"k={k}": 0.0 for k in thresholds}
        
        distances = self._get_distances_to_canon(outputs, contract_id)
        if not distances:
            return {f"k={k}": 0.0 for k in thresholds}
        
        results = {}
        for k in thresholds:
            within_threshold = sum(1 for d in distances if d <= k)
            results[f"k={k}"] = within_threshold / len(distances)
        
        return results
    
    def _get_distances_to_canon(self, outputs: List[str], 
                               contract_id: str) -> List[float]:
        """
        Get list of distances from each output to canon
        
        Args:
            outputs: List of code outputs
            contract_id: Contract identifier
            
        Returns:
            List of distance values
        """
        if not self.canon_system:
            return []
        
        canon_data = self.canon_system.load_canon(contract_id)
        if not canon_data:
            return []
        
        distances = []
        for code in outputs:
            comparison = self.canon_system.compare_to_canon(contract_id, code)
            distances.append(comparison.get("distance", float('inf')))
        
        return distances
    
    def _calculate_delta_p_tau(self, distances_pre: List[float],
                               distances_post: List[float],
                               thresholds: List[float]) -> Dict[str, float]:
        """
        Calculate ΔPτ: Difference in probability mass within threshold τ
        
        Args:
            distances_pre: Pre-repair distances
            distances_post: Post-repair distances
            thresholds: Distance thresholds
            
        Returns:
            Dictionary mapping threshold to delta value
        """
        if not distances_pre or not distances_post:
            return {f"tau={tau}": 0.0 for tau in thresholds}
        
        results = {}
        for tau in thresholds:
            p_pre = sum(1 for d in distances_pre if d <= tau) / len(distances_pre)
            p_post = sum(1 for d in distances_post if d <= tau) / len(distances_post)
            results[f"tau={tau}"] = p_post - p_pre
        
        return results
    
    def _calculate_canon_coverage(self, outputs: List[str], 
                                 contract: Dict[str, Any]) -> float:
        """
        Calculate canon coverage: Fraction of outputs passing oracle tests
        
        Args:
            outputs: List of code outputs
            contract: Contract specification
            
        Returns:
            Coverage fraction (0.0 to 1.0)
        """
        if not outputs:
            return 0.0
        
        passing = 0
        for code in outputs:
            oracle_result = self.oracle_system.run_oracle_tests(code, contract)
            if oracle_result.get("passed", False):
                passing += 1
        
        return passing / len(outputs)
    
    def _calculate_rescue_rate(self, raw_outputs: List[str],
                              repaired_outputs: List[str],
                              contract_id: str) -> float:
        """
        Calculate rescue rate: Fraction of non-canonical outputs successfully repaired
        
        Args:
            raw_outputs: Pre-repair outputs
            repaired_outputs: Post-repair outputs
            contract_id: Contract identifier
            
        Returns:
            Rescue rate (0.0 to 1.0)
        """
        if not self.canon_system or len(raw_outputs) != len(repaired_outputs):
            return 0.0
        
        non_canonical_count = 0
        rescued_count = 0
        
        for i, result in enumerate(zip(raw_outputs, repaired_outputs)):
            raw, repaired = result
            raw_comparison = self.canon_system.compare_to_canon(contract_id, raw)
            
            # Check if originally non-canonical
            if not raw_comparison.get("is_identical", False):
                non_canonical_count += 1
                
                # Check if repair made it canonical
                repaired_comparison = self.canon_system.compare_to_canon(contract_id, repaired)
                if repaired_comparison.get("is_identical", False):
                    rescued_count += 1
                # Check if distance reduced significantly (e.g., by more than 20%)
                elif raw_comparison.get("final_distance", float('inf')) > 0 and repaired_comparison.get("final_distance", float('inf')) < raw_comparison.get("final_distance", float('inf')) * 0.8:
                    rescued_count += 0.5  # Partial credit for significant reduction
        
        return rescued_count / non_canonical_count if non_canonical_count > 0 else 0.0
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            "R_raw": 0.0,
            "R_anchor_pre": 0.0,
            "R_anchor_post": 0.0,
            "Delta_rescue": 0.0,
            "R_behavioral": 0.0,
            "R_structural": 0.0,
            "R_canon": 0.0,
            "canon_coverage": 0.0,
            "rescue_rate": 0.0,
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
