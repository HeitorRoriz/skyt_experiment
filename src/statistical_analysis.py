"""
Statistical analysis functions for repeatability testing
Implements Wilson confidence intervals, two-proportion tests, and effect size calculations
"""

import math
import scipy.stats as stats
import numpy as np
from typing import Tuple, Dict, List, Any
from dataclasses import dataclass

@dataclass
class ProportionResult:
    """Result of proportion analysis"""
    proportion: float
    lower_ci: float
    upper_ci: float
    n: int
    
@dataclass
class ComparisonResult:
    """Result of two-proportion comparison"""
    prop1: float
    prop2: float
    effect_size: float  # Difference in percentage points
    p_value: float
    significant: bool
    ci_lower: float
    ci_upper: float

def wilson_confidence_interval(successes: int, n: int, confidence: float = 0.95) -> Tuple[float, float, float]:
    """
    Calculate Wilson score confidence interval for proportions
    
    Args:
        successes: Number of successes
        n: Total number of trials
        confidence: Confidence level (default 0.95 for 95% CI)
        
    Returns:
        (proportion, lower_bound, upper_bound)
    """
    if n == 0:
        return 0.0, 0.0, 0.0
    
    p = successes / n
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    
    denominator = 1 + z**2 / n
    centre_adjusted_probability = (p + z**2 / (2 * n)) / denominator
    adjusted_standard_deviation = math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator
    
    lower_bound = centre_adjusted_probability - z * adjusted_standard_deviation
    upper_bound = centre_adjusted_probability + z * adjusted_standard_deviation
    
    return p, max(0, lower_bound), min(1, upper_bound)

def two_proportion_test(successes1: int, n1: int, successes2: int, n2: int, 
                       confidence: float = 0.95) -> ComparisonResult:
    """
    Two-proportion z-test with effect size and confidence interval
    
    Args:
        successes1, n1: First group successes and total
        successes2, n2: Second group successes and total
        confidence: Confidence level
        
    Returns:
        ComparisonResult with test statistics and effect size
    """
    if n1 == 0 or n2 == 0:
        return ComparisonResult(0, 0, 0, 1.0, False, 0, 0)
    
    p1 = successes1 / n1
    p2 = successes2 / n2
    
    # Pooled proportion for test statistic
    p_pool = (successes1 + successes2) / (n1 + n2)
    
    # Standard error
    se_pool = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    
    if se_pool == 0:
        z_stat = 0
        p_value = 1.0
    else:
        z_stat = (p1 - p2) / se_pool
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    # Effect size (difference in percentage points)
    effect_size = (p1 - p2) * 100
    
    # Confidence interval for difference
    se_diff = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    z_crit = stats.norm.ppf(1 - (1 - confidence) / 2)
    
    ci_lower = (p1 - p2 - z_crit * se_diff) * 100
    ci_upper = (p1 - p2 + z_crit * se_diff) * 100
    
    significant = p_value < (1 - confidence)
    
    return ComparisonResult(
        prop1=p1,
        prop2=p2,
        effect_size=effect_size,
        p_value=p_value,
        significant=significant,
        ci_lower=ci_lower,
        ci_upper=ci_upper
    )

def analyze_repeatability_by_config(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze repeatability metrics by configuration (A/B/C)
    
    Args:
        results: List of test results with audit trails
        
    Returns:
        Statistical analysis by configuration
    """
    # Group results by configuration
    config_groups = {}
    for result in results:
        config = result.get('audit_trail', {}).get('config_mode', 'unknown')
        if config not in config_groups:
            config_groups[config] = []
        config_groups[config].append(result)
    
    analysis = {}
    
    for config, group_results in config_groups.items():
        if not group_results:
            continue
            
        # Calculate success rates
        total_runs = len(group_results)
        successful_runs = sum(1 for r in group_results if r.get('success', False))
        
        # Wilson CI for success rate
        success_prop, success_lower, success_upper = wilson_confidence_interval(successful_runs, total_runs)
        
        # Calculate other metrics if available
        deterministic_runs = sum(1 for r in group_results 
                               if not r.get('audit_trail', {}).get('determinism_violations', []))
        determ_prop, determ_lower, determ_upper = wilson_confidence_interval(deterministic_runs, total_runs)
        
        # Cache rescue rate (Config C only)
        cache_hits = sum(1 for r in group_results 
                        if r.get('audit_trail', {}).get('cache_hit', False))
        cache_prop, cache_lower, cache_upper = wilson_confidence_interval(cache_hits, total_runs)
        
        analysis[config] = {
            'total_runs': total_runs,
            'success_rate': ProportionResult(success_prop, success_lower, success_upper, total_runs),
            'determinism_compliance_rate': ProportionResult(determ_prop, determ_lower, determ_upper, total_runs),
            'cache_rescue_rate': ProportionResult(cache_prop, cache_lower, cache_upper, total_runs),
            'mean_execution_time': np.mean([r.get('execution_time', 0) for r in group_results]),
            'median_execution_time': np.median([r.get('execution_time', 0) for r in group_results])
        }
    
    return analysis

def compare_configurations(config_a_results: List[Dict], config_b_results: List[Dict]) -> Dict[str, ComparisonResult]:
    """
    Compare two configurations statistically
    
    Args:
        config_a_results: Results from first configuration
        config_b_results: Results from second configuration
        
    Returns:
        Dictionary of comparison results for different metrics
    """
    comparisons = {}
    
    # Success rate comparison
    a_successes = sum(1 for r in config_a_results if r.get('success', False))
    b_successes = sum(1 for r in config_b_results if r.get('success', False))
    
    comparisons['success_rate'] = two_proportion_test(
        a_successes, len(config_a_results),
        b_successes, len(config_b_results)
    )
    
    # Determinism compliance comparison
    a_deterministic = sum(1 for r in config_a_results 
                         if not r.get('audit_trail', {}).get('determinism_violations', []))
    b_deterministic = sum(1 for r in config_b_results 
                         if not r.get('audit_trail', {}).get('determinism_violations', []))
    
    comparisons['determinism_compliance'] = two_proportion_test(
        a_deterministic, len(config_a_results),
        b_deterministic, len(config_b_results)
    )
    
    return comparisons

def calculate_intrinsic_repeatability(audit_trails: List[Dict[str, Any]]) -> ProportionResult:
    """
    Calculate R_intrinsic (raw LLM repeatability) with confidence intervals
    
    Args:
        audit_trails: List of audit trail dictionaries
        
    Returns:
        ProportionResult with repeatability and confidence intervals
    """
    if not audit_trails:
        return ProportionResult(0.0, 0.0, 0.0, 0)
    
    # Extract raw codes and normalize for comparison
    raw_codes = []
    for trail in audit_trails:
        raw_code = trail.get('raw_code', '')
        if raw_code:
            # Basic normalization for comparison
            normalized = '\n'.join(line.strip() for line in raw_code.split('\n') 
                                 if line.strip() and not line.strip().startswith('#'))
            raw_codes.append(normalized)
    
    if not raw_codes:
        return ProportionResult(0.0, 0.0, 0.0, 0)
    
    # Find most common output
    from collections import Counter
    code_counts = Counter(raw_codes)
    most_common_count = code_counts.most_common(1)[0][1]
    
    # Calculate repeatability with Wilson CI
    prop, lower, upper = wilson_confidence_interval(most_common_count, len(raw_codes))
    
    return ProportionResult(prop, lower, upper, len(raw_codes))

def mann_whitney_u_test(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """
    Mann-Whitney U test for comparing medians
    
    Args:
        group1, group2: Lists of numeric values
        
    Returns:
        (u_statistic, p_value)
    """
    if len(group1) == 0 or len(group2) == 0:
        return 0.0, 1.0
    
    try:
        u_stat, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')
        return float(u_stat), float(p_value)
    except:
        return 0.0, 1.0
