"""
Enhanced Repeatability Calculation with Correctness Validation
Measures true repeatability by combining structural similarity with functional correctness
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict, Counter
import statistics

# Import for proper type hints
try:
    from acceptance_test_runner import AcceptanceTestReport
except ImportError:
    AcceptanceTestReport = Any

@dataclass
class EnhancedResult:
    """Single test run result with all metrics"""
    run_id: int
    canonical_hash: str
    behavior_hash: str
    acceptance_report: Optional[AcceptanceTestReport]  # AcceptanceTestReport object or None
    correctness_score: float
    is_valid: bool  # Passes quality gates

@dataclass
class RepeatabilityMetrics:
    """Comprehensive repeatability analysis"""
    # Traditional metrics
    total_runs: int
    raw_repeatability: float          # Traditional: identical outputs / total
    canonical_repeatability: float    # Canonical hashes match / total
    behavioral_repeatability: float   # Behavior hashes match / total
    
    # Enhanced metrics with correctness validation
    valid_runs: int                   # Runs passing quality gates
    valid_repeatability: float       # Valid identical outputs / valid runs
    correctness_weighted_repeatability: float  # Weighted by correctness scores
    
    # Quality analysis
    average_correctness: float
    correctness_std: float
    quality_gate_pass_rate: float
    
    # Detailed breakdowns
    hash_distribution: Dict[str, int]
    correctness_distribution: List[float]
    failure_analysis: Dict[str, int]

class EnhancedRepeatabilityCalculator:
    """Calculate repeatability with correctness validation"""
    
    def __init__(self, quality_threshold: float = 0.8, min_pass_rate: float = 0.9):
        self.quality_threshold = quality_threshold
        self.min_pass_rate = min_pass_rate
    
    def calculate_repeatability(self, test_results: List[Dict[str, Any]]) -> RepeatabilityMetrics:
        """Calculate comprehensive repeatability metrics"""
        
        # Convert to enhanced results
        enhanced_results = self._convert_to_enhanced_results(test_results)
        
        if not enhanced_results:
            return self._empty_metrics()
        
        total_runs = len(enhanced_results)
        
        # Traditional repeatability calculations
        raw_repeatability = self._calculate_raw_repeatability(test_results)
        canonical_repeatability = self._calculate_canonical_repeatability(enhanced_results)
        behavioral_repeatability = self._calculate_behavioral_repeatability(enhanced_results)
        
        # Enhanced repeatability with correctness validation
        valid_results = [r for r in enhanced_results if r.is_valid]
        valid_runs = len(valid_results)
        
        valid_repeatability = self._calculate_valid_repeatability(valid_results)
        correctness_weighted = self._calculate_correctness_weighted_repeatability(enhanced_results)
        
        # Quality analysis
        correctness_scores = [r.correctness_score for r in enhanced_results]
        average_correctness = statistics.mean(correctness_scores)
        correctness_std = statistics.stdev(correctness_scores) if len(correctness_scores) > 1 else 0.0
        quality_gate_pass_rate = valid_runs / total_runs
        
        # Detailed analysis
        hash_distribution = self._analyze_hash_distribution(enhanced_results)
        failure_analysis = self._analyze_failures(enhanced_results)
        
        return RepeatabilityMetrics(
            total_runs=total_runs,
            raw_repeatability=raw_repeatability,
            canonical_repeatability=canonical_repeatability,
            behavioral_repeatability=behavioral_repeatability,
            valid_runs=valid_runs,
            valid_repeatability=valid_repeatability,
            correctness_weighted_repeatability=correctness_weighted,
            average_correctness=average_correctness,
            correctness_std=correctness_std,
            quality_gate_pass_rate=quality_gate_pass_rate,
            hash_distribution=hash_distribution,
            correctness_distribution=correctness_scores,
            failure_analysis=failure_analysis
        )
    
    def _convert_to_enhanced_results(self, test_results: List[Dict[str, Any]]) -> List[EnhancedResult]:
        """Convert raw test results to enhanced result objects"""
        enhanced_results = []
        
        for i, result in enumerate(test_results):
            # Extract acceptance report
            acceptance_report = result.get("acceptance_report", None)
            if acceptance_report and hasattr(acceptance_report, 'correctness_score'):
                correctness_score = acceptance_report.correctness_score
                pass_rate = acceptance_report.pass_rate
            else:
                correctness_score = 0.0
                pass_rate = 0.0
            
            # Apply quality gates
            is_valid = (
                correctness_score >= self.quality_threshold and
                pass_rate >= self.min_pass_rate and
                self._all_property_tests_pass(acceptance_report)
            )
            
            enhanced_results.append(EnhancedResult(
                run_id=result.get("run_id", i),
                canonical_hash=result.get("canonical_hash", ""),
                behavior_hash=result.get("behavior_hash", ""),
                acceptance_report=acceptance_report,
                correctness_score=correctness_score,
                is_valid=is_valid
            ))
        
        return enhanced_results
    
    def _calculate_raw_repeatability(self, test_results: List[Dict[str, Any]]) -> float:
        """Traditional repeatability: identical raw outputs"""
        if len(test_results) <= 1:
            return 1.0
        
        raw_outputs = [result.get("final_output", "") for result in test_results]
        output_counts = Counter(raw_outputs)
        max_identical = max(output_counts.values())
        
        return max_identical / len(test_results)
    
    def _calculate_canonical_repeatability(self, enhanced_results: List[EnhancedResult]) -> float:
        """Repeatability based on canonical hash matching"""
        if len(enhanced_results) <= 1:
            return 1.0
        
        hash_counts = Counter(r.canonical_hash for r in enhanced_results)
        max_identical = max(hash_counts.values())
        
        return max_identical / len(enhanced_results)
    
    def _calculate_behavioral_repeatability(self, enhanced_results: List[EnhancedResult]) -> float:
        """Repeatability based on behavioral hash matching"""
        if len(enhanced_results) <= 1:
            return 1.0
        
        behavior_counts = Counter(r.behavior_hash for r in enhanced_results)
        max_identical = max(behavior_counts.values())
        
        return max_identical / len(enhanced_results)
    
    def _calculate_valid_repeatability(self, valid_results: List[EnhancedResult]) -> float:
        """Repeatability among only valid (correct) results"""
        if len(valid_results) <= 1:
            return 1.0 if valid_results else 0.0
        
        hash_counts = Counter(r.canonical_hash for r in valid_results)
        max_identical = max(hash_counts.values())
        
        return max_identical / len(valid_results)
    
    def _calculate_correctness_weighted_repeatability(self, enhanced_results: List[EnhancedResult]) -> float:
        """Repeatability weighted by correctness scores"""
        if len(enhanced_results) <= 1:
            return enhanced_results[0].correctness_score if enhanced_results else 0.0
        
        # Group by canonical hash and weight by correctness
        hash_groups = defaultdict(list)
        for result in enhanced_results:
            hash_groups[result.canonical_hash].append(result.correctness_score)
        
        # Find the group with highest weighted count
        max_weighted_score = 0.0
        total_weight = sum(r.correctness_score for r in enhanced_results)
        
        for hash_val, scores in hash_groups.items():
            group_weight = sum(scores)
            if group_weight > max_weighted_score:
                max_weighted_score = group_weight
        
        return max_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _all_property_tests_pass(self, acceptance_report) -> bool:
        """Check if all property tests passed (critical for correctness)"""
        if not acceptance_report:
            return True  # If no acceptance tests, consider as passing
        
        if not hasattr(acceptance_report, 'test_results'):
            return True
        
        for test_result in acceptance_report.test_results:
            if hasattr(test_result, 'name') and hasattr(test_result, 'passed'):
                if "property" in test_result.name.lower() and not test_result.passed:
                    return False
        
        return True
    
    def _analyze_hash_distribution(self, enhanced_results: List[EnhancedResult]) -> Dict[str, int]:
        """Analyze distribution of canonical hashes"""
        return dict(Counter(r.canonical_hash for r in enhanced_results))
    
    def _analyze_failures(self, enhanced_results: List[EnhancedResult]) -> Dict[str, int]:
        """Analyze common failure patterns"""
        failure_types = defaultdict(int)
        
        for result in enhanced_results:
            if not result.is_valid:
                if result.correctness_score < self.quality_threshold:
                    failure_types["low_correctness"] += 1
                
                acceptance_report = result.acceptance_report
                pass_rate = acceptance_report.pass_rate if hasattr(acceptance_report, 'pass_rate') else 0.0
                if pass_rate < self.min_pass_rate:
                    failure_types["low_pass_rate"] += 1
                
                if not self._all_property_tests_pass(acceptance_report):
                    failure_types["property_test_failure"] += 1
        
        return dict(failure_types)
    
    def _empty_metrics(self) -> RepeatabilityMetrics:
        """Return empty metrics for edge cases"""
        return RepeatabilityMetrics(
            total_runs=0,
            raw_repeatability=0.0,
            canonical_repeatability=0.0,
            behavioral_repeatability=0.0,
            valid_runs=0,
            valid_repeatability=0.0,
            correctness_weighted_repeatability=0.0,
            average_correctness=0.0,
            correctness_std=0.0,
            quality_gate_pass_rate=0.0,
            hash_distribution={},
            correctness_distribution=[],
            failure_analysis={}
        )

def calculate_enhanced_repeatability(test_results: List[Dict[str, Any]], 
                                   quality_threshold: float = 0.8,
                                   min_pass_rate: float = 0.9) -> RepeatabilityMetrics:
    """Factory function for enhanced repeatability calculation"""
    calculator = EnhancedRepeatabilityCalculator(quality_threshold, min_pass_rate)
    return calculator.calculate_repeatability(test_results)

def print_repeatability_report(metrics: RepeatabilityMetrics):
    """Print comprehensive repeatability report"""
    print("=" * 60)
    print("ENHANCED REPEATABILITY ANALYSIS")
    print("=" * 60)
    
    print(f"\n📊 TRADITIONAL METRICS:")
    print(f"  Raw Repeatability:        {metrics.raw_repeatability:.1%}")
    print(f"  Canonical Repeatability:  {metrics.canonical_repeatability:.1%}")
    print(f"  Behavioral Repeatability: {metrics.behavioral_repeatability:.1%}")
    
    print(f"\n🎯 ENHANCED METRICS (Correctness-Validated):")
    print(f"  Valid Runs:               {metrics.valid_runs}/{metrics.total_runs} ({metrics.quality_gate_pass_rate:.1%})")
    print(f"  Valid Repeatability:      {metrics.valid_repeatability:.1%}")
    print(f"  Correctness-Weighted:     {metrics.correctness_weighted_repeatability:.1%}")
    
    print(f"\n📈 QUALITY ANALYSIS:")
    print(f"  Average Correctness:      {metrics.average_correctness:.3f} ± {metrics.correctness_std:.3f}")
    print(f"  Quality Gate Pass Rate:   {metrics.quality_gate_pass_rate:.1%}")
    
    if metrics.failure_analysis:
        print(f"\n❌ FAILURE ANALYSIS:")
        for failure_type, count in metrics.failure_analysis.items():
            print(f"  {failure_type.replace('_', ' ').title()}: {count}")
    
    print(f"\n🔍 HASH DISTRIBUTION:")
    for hash_val, count in metrics.hash_distribution.items():
        print(f"  {hash_val[:8]}...: {count} runs")
