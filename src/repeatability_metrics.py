"""
Enhanced repeatability metrics system that measures true LLM consistency
Replaces the flawed template replay system with proper intrinsic repeatability measurement
"""

import json
import os
import hashlib
from typing import Dict, List, Tuple, Optional, Any, Set
from collections import Counter, defaultdict
from dataclasses import dataclass
import ast

@dataclass
class RepeatabilityMetrics:
    """Comprehensive repeatability metrics"""
    # Core metrics
    r_intrinsic: float  # Raw LLM repeatability before any processing
    r_canonical: float  # Repeatability after canonicalization
    r_behavioral: float  # Behavioral equivalence repeatability
    
    # Process metrics
    cache_rescue_rate: float  # Fraction of runs rescued by cache
    canonicalization_convergence: float  # How often canonicalization produces same result
    repair_success_rate: float  # Fraction of runs successfully repaired
    
    # Diversity metrics
    unique_raw_outputs: int  # Number of distinct raw outputs
    unique_canonical_forms: int  # Number of distinct canonical forms
    unique_behaviors: int  # Number of distinct behaviors
    
    # Detailed breakdown
    status_distribution: Dict[str, int]  # Count of each final status
    repair_step_frequency: Dict[str, int]  # Frequency of each repair operation
    determinism_violation_frequency: Dict[str, int]  # Frequency of each violation type
    
    # Quality indicators
    mean_repair_complexity: float  # Average number of repair steps needed
    determinism_compliance_rate: float  # Fraction passing determinism lint
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "core_metrics": {
                "r_intrinsic": self.r_intrinsic,
                "r_canonical": self.r_canonical,
                "r_behavioral": self.r_behavioral
            },
            "process_metrics": {
                "cache_rescue_rate": self.cache_rescue_rate,
                "canonicalization_convergence": self.canonicalization_convergence,
                "repair_success_rate": self.repair_success_rate
            },
            "diversity_metrics": {
                "unique_raw_outputs": self.unique_raw_outputs,
                "unique_canonical_forms": self.unique_canonical_forms,
                "unique_behaviors": self.unique_behaviors
            },
            "detailed_breakdown": {
                "status_distribution": self.status_distribution,
                "repair_step_frequency": self.repair_step_frequency,
                "determinism_violation_frequency": self.determinism_violation_frequency
            },
            "quality_indicators": {
                "mean_repair_complexity": self.mean_repair_complexity,
                "determinism_compliance_rate": self.determinism_compliance_rate
            }
        }

class RepeatabilityAnalyzer:
    """Analyzes repeatability across multiple runs with comprehensive metrics"""
    
    def __init__(self):
        pass
    
    def analyze_runs(self, audit_trails: List[Dict[str, Any]]) -> RepeatabilityMetrics:
        """
        Compute comprehensive repeatability metrics from audit trails
        
        Args:
            audit_trails: List of audit trail dictionaries from each run
            
        Returns:
            RepeatabilityMetrics object with all computed metrics
        """
        if not audit_trails:
            return self._empty_metrics()
        
        total_runs = len(audit_trails)
        
        # Extract data for analysis
        raw_codes = [trail.get("raw_code", "") for trail in audit_trails]
        canonical_hashes = [trail.get("canonical_hash") for trail in audit_trails if trail.get("canonical_hash")]
        behavior_hashes = [trail.get("behavior_hash") for trail in audit_trails if trail.get("behavior_hash")]
        statuses = [trail.get("final_status", "unknown") for trail in audit_trails]
        repair_steps_lists = [trail.get("repair_steps", []) for trail in audit_trails]
        determinism_violations_lists = [trail.get("determinism_violations", []) for trail in audit_trails]
        cache_hits = [trail.get("cache_hit", False) for trail in audit_trails]
        
        # Core repeatability metrics
        r_intrinsic = self._calculate_intrinsic_repeatability(raw_codes)
        r_canonical = self._calculate_canonical_repeatability(canonical_hashes)
        r_behavioral = self._calculate_behavioral_repeatability(behavior_hashes)
        
        # Process metrics
        cache_rescue_rate = sum(cache_hits) / total_runs if total_runs > 0 else 0.0
        canonicalization_convergence = self._calculate_canonicalization_convergence(canonical_hashes)
        repair_success_rate = sum(1 for status in statuses if status in ['raw', 'normalized', 'repaired']) / total_runs
        
        # Diversity metrics
        unique_raw_outputs = len(set(self._normalize_code_for_comparison(code) for code in raw_codes if code))
        unique_canonical_forms = len(set(canonical_hashes))
        unique_behaviors = len(set(behavior_hashes))
        
        # Detailed breakdown
        status_distribution = dict(Counter(statuses))
        repair_step_frequency = self._count_repair_steps(repair_steps_lists)
        determinism_violation_frequency = self._count_determinism_violations(determinism_violations_lists)
        
        # Quality indicators
        mean_repair_complexity = sum(len(steps) for steps in repair_steps_lists) / total_runs
        determinism_compliance_rate = sum(1 for violations in determinism_violations_lists if not violations) / total_runs
        
        return RepeatabilityMetrics(
            r_intrinsic=r_intrinsic,
            r_canonical=r_canonical,
            r_behavioral=r_behavioral,
            cache_rescue_rate=cache_rescue_rate,
            canonicalization_convergence=canonicalization_convergence,
            repair_success_rate=repair_success_rate,
            unique_raw_outputs=unique_raw_outputs,
            unique_canonical_forms=unique_canonical_forms,
            unique_behaviors=unique_behaviors,
            status_distribution=status_distribution,
            repair_step_frequency=repair_step_frequency,
            determinism_violation_frequency=determinism_violation_frequency,
            mean_repair_complexity=mean_repair_complexity,
            determinism_compliance_rate=determinism_compliance_rate
        )
    
    def _calculate_intrinsic_repeatability(self, raw_codes: List[str]) -> float:
        """Calculate raw LLM repeatability before any processing"""
        if len(raw_codes) <= 1:
            return 1.0
        
        # Normalize codes for comparison (remove whitespace, comments)
        normalized_codes = [self._normalize_code_for_comparison(code) for code in raw_codes if code]
        
        if not normalized_codes:
            return 0.0
        
        # Find most common output
        code_counts = Counter(normalized_codes)
        most_common_count = code_counts.most_common(1)[0][1]
        
        return most_common_count / len(normalized_codes)
    
    def _calculate_canonical_repeatability(self, canonical_hashes: List[str]) -> float:
        """Calculate repeatability after canonicalization"""
        if len(canonical_hashes) <= 1:
            return 1.0 if canonical_hashes else 0.0
        
        hash_counts = Counter(canonical_hashes)
        most_common_count = hash_counts.most_common(1)[0][1]
        
        return most_common_count / len(canonical_hashes)
    
    def _calculate_behavioral_repeatability(self, behavior_hashes: List[str]) -> float:
        """Calculate behavioral equivalence repeatability"""
        if len(behavior_hashes) <= 1:
            return 1.0 if behavior_hashes else 0.0
        
        hash_counts = Counter(behavior_hashes)
        most_common_count = hash_counts.most_common(1)[0][1]
        
        return most_common_count / len(behavior_hashes)
    
    def _calculate_canonicalization_convergence(self, canonical_hashes: List[str]) -> float:
        """Calculate how often canonicalization produces the same result"""
        if len(canonical_hashes) <= 1:
            return 1.0 if canonical_hashes else 0.0
        
        unique_hashes = len(set(canonical_hashes))
        return 1.0 - (unique_hashes - 1) / (len(canonical_hashes) - 1)
    
    def _normalize_code_for_comparison(self, code: str) -> str:
        """Normalize code for comparison by removing whitespace and comments"""
        if not code:
            return ""
        
        try:
            # Parse and unparse to normalize formatting
            tree = ast.parse(code)
            normalized = ast.unparse(tree)
            
            # Remove comments and extra whitespace
            lines = []
            for line in normalized.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    lines.append(line)
            
            return '\n'.join(lines)
        except:
            # Fallback: basic text normalization
            lines = []
            for line in code.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    lines.append(line)
            return '\n'.join(lines)
    
    def _count_repair_steps(self, repair_steps_lists: List[List[str]]) -> Dict[str, int]:
        """Count frequency of each repair step across all runs"""
        all_steps = []
        for steps in repair_steps_lists:
            all_steps.extend(steps)
        return dict(Counter(all_steps))
    
    def _count_determinism_violations(self, violations_lists: List[List]) -> Dict[str, int]:
        """Count frequency of each determinism violation type"""
        all_violations = []
        for violations in violations_lists:
            for violation in violations:
                if isinstance(violation, dict):
                    rule = violation.get("rule", "unknown")
                elif hasattr(violation, "rule"):
                    rule = violation.rule
                else:
                    rule = str(violation)
                all_violations.append(rule)
        return dict(Counter(all_violations))
    
    def _empty_metrics(self) -> RepeatabilityMetrics:
        """Return empty metrics for edge cases"""
        return RepeatabilityMetrics(
            r_intrinsic=0.0,
            r_canonical=0.0,
            r_behavioral=0.0,
            cache_rescue_rate=0.0,
            canonicalization_convergence=0.0,
            repair_success_rate=0.0,
            unique_raw_outputs=0,
            unique_canonical_forms=0,
            unique_behaviors=0,
            status_distribution={},
            repair_step_frequency={},
            determinism_violation_frequency={},
            mean_repair_complexity=0.0,
            determinism_compliance_rate=0.0
        )

def load_audit_trails_from_directory(results_dir: str, contract_name: str) -> List[Dict[str, Any]]:
    """
    Load all audit trails for a contract from the results directory
    
    Args:
        results_dir: Path to results directory
        contract_name: Name of the contract
        
    Returns:
        List of audit trail dictionaries
    """
    contract_dir = os.path.join(results_dir, contract_name)
    if not os.path.exists(contract_dir):
        return []
    
    audit_trails = []
    
    # Look for audit trail files
    for filename in os.listdir(contract_dir):
        if filename.startswith("audit_trail_run") and filename.endswith(".json"):
            filepath = os.path.join(contract_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    audit_trail = json.load(f)
                    audit_trails.append(audit_trail)
            except Exception as e:
                print(f"Warning: Could not load {filepath}: {e}")
    
    # Sort by run number
    audit_trails.sort(key=lambda x: x.get("run_number", 0))
    
    return audit_trails

def analyze_contract_repeatability(results_dir: str, contract_name: str) -> RepeatabilityMetrics:
    """
    Analyze repeatability for a specific contract
    
    Args:
        results_dir: Path to results directory
        contract_name: Name of the contract to analyze
        
    Returns:
        RepeatabilityMetrics object
    """
    audit_trails = load_audit_trails_from_directory(results_dir, contract_name)
    analyzer = RepeatabilityAnalyzer()
    return analyzer.analyze_runs(audit_trails)

def generate_repeatability_report(results_dir: str, contract_names: List[str] = None) -> Dict[str, Any]:
    """
    Generate comprehensive repeatability report for all contracts
    
    Args:
        results_dir: Path to results directory
        contract_names: Optional list of specific contracts to analyze
        
    Returns:
        Dictionary containing the full repeatability report
    """
    if contract_names is None:
        # Auto-discover contracts
        contract_names = []
        if os.path.exists(results_dir):
            for item in os.listdir(results_dir):
                item_path = os.path.join(results_dir, item)
                if os.path.isdir(item_path):
                    contract_names.append(item)
    
    report = {
        "timestamp": "2024-01-01T00:00:00",  # Will be updated by caller
        "total_contracts": len(contract_names),
        "contracts": {},
        "aggregate_metrics": {}
    }
    
    all_metrics = []
    
    for contract_name in contract_names:
        try:
            metrics = analyze_contract_repeatability(results_dir, contract_name)
            report["contracts"][contract_name] = metrics.to_dict()
            all_metrics.append(metrics)
        except Exception as e:
            print(f"Warning: Could not analyze {contract_name}: {e}")
            report["contracts"][contract_name] = {"error": str(e)}
    
    # Calculate aggregate metrics
    if all_metrics:
        report["aggregate_metrics"] = {
            "mean_r_intrinsic": sum(m.r_intrinsic for m in all_metrics) / len(all_metrics),
            "mean_r_canonical": sum(m.r_canonical for m in all_metrics) / len(all_metrics),
            "mean_r_behavioral": sum(m.r_behavioral for m in all_metrics) / len(all_metrics),
            "mean_cache_rescue_rate": sum(m.cache_rescue_rate for m in all_metrics) / len(all_metrics),
            "mean_repair_success_rate": sum(m.repair_success_rate for m in all_metrics) / len(all_metrics),
            "mean_determinism_compliance_rate": sum(m.determinism_compliance_rate for m in all_metrics) / len(all_metrics)
        }
    
    return report
