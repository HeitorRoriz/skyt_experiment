# src/enhanced_stats.py
"""
Enhanced statistical analysis for SKYT experiments
Implements Professor Nasser's recommendations for methodological rigor:
- Confidence intervals (Wilson score, bootstrap)
- Fisher's exact test for small samples
- Effect sizes (difference in proportions, odds ratios)
- Holm-Bonferroni correction for multiple comparisons
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Any, Tuple
import math


def wilson_confidence_interval(successes: int, trials: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Wilson score confidence interval for proportions (recommended for small samples)
    
    More accurate than normal approximation for small n or extreme proportions.
    
    Args:
        successes: Number of successes
        trials: Total number of trials
        confidence: Confidence level (default 0.95 for 95% CI)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if trials == 0:
        return (0.0, 0.0)
    
    p = successes / trials
    z = stats.norm.ppf((1 + confidence) / 2)
    
    denominator = 1 + z**2 / trials
    center = (p + z**2 / (2 * trials)) / denominator
    margin = z * math.sqrt((p * (1 - p) / trials + z**2 / (4 * trials**2))) / denominator
    
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    
    return (lower, upper)


def bootstrap_confidence_interval(data: List[float], statistic_fn=np.mean, 
                                  confidence: float = 0.95, n_bootstrap: int = 10000) -> Tuple[float, float]:
    """
    Bootstrap confidence interval for any statistic
    
    Args:
        data: Sample data
        statistic_fn: Function to compute statistic (default: mean)
        confidence: Confidence level (default 0.95)
        n_bootstrap: Number of bootstrap samples
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if len(data) == 0:
        return (0.0, 0.0)
    
    bootstrap_stats = []
    data_array = np.array(data)
    
    for _ in range(n_bootstrap):
        sample = np.random.choice(data_array, size=len(data_array), replace=True)
        bootstrap_stats.append(statistic_fn(sample))
    
    alpha = 1 - confidence
    lower = np.percentile(bootstrap_stats, 100 * alpha / 2)
    upper = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))
    
    return (float(lower), float(upper))


def descriptive_statistics_with_ci(data: List[float], name: str = "metric", 
                                   confidence: float = 0.95) -> Dict[str, Any]:
    """
    Calculate descriptive statistics with confidence intervals
    
    Args:
        data: List of metric values
        name: Name of the metric
        confidence: Confidence level for intervals
        
    Returns:
        Dictionary with mean, median, std, min, max, n, and confidence intervals
    """
    if len(data) == 0:
        return {
            "name": name,
            "n": 0,
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "max": None,
            "mean_ci": (None, None),
            "median_ci": (None, None)
        }
    
    mean_ci = bootstrap_confidence_interval(data, np.mean, confidence)
    median_ci = bootstrap_confidence_interval(data, np.median, confidence)
    
    return {
        "name": name,
        "n": len(data),
        "mean": float(np.mean(data)),
        "median": float(np.median(data)),
        "std": float(np.std(data)),
        "min": float(np.min(data)),
        "max": float(np.max(data)),
        "mean_ci": mean_ci,
        "median_ci": median_ci,
        "confidence_level": confidence
    }


def fishers_exact_test(before_successes: int, before_trials: int,
                       after_successes: int, after_trials: int) -> Dict[str, Any]:
    """
    Fisher's exact test for comparing two proportions (recommended for small samples)
    
    Tests if transformation significantly improves success rate.
    H0: No difference in success rates
    H1: Success rates are different (two-sided)
    
    Args:
        before_successes: Number of successes before transformation
        before_trials: Total trials before transformation
        after_successes: Number of successes after transformation
        after_trials: Total trials after transformation
        
    Returns:
        Dictionary with test results
    """
    # Create contingency table
    # [[successes_after, failures_after],
    #  [successes_before, failures_before]]
    # Note: First row is "exposed" (after), second row is "control" (before)
    # This gives odds_ratio > 1 when after > before (improvement)
    table = [
        [after_successes, after_trials - after_successes],
        [before_successes, before_trials - before_successes]
    ]
    
    # Fisher's exact test
    odds_ratio, p_value = stats.fisher_exact(table, alternative='two-sided')
    
    # Calculate proportions
    p_before = before_successes / before_trials if before_trials > 0 else 0
    p_after = after_successes / after_trials if after_trials > 0 else 0
    
    return {
        "test": "fisher_exact",
        "p_value": float(p_value),
        "odds_ratio": float(odds_ratio),
        "significant": p_value < 0.05,
        "proportion_before": p_before,
        "proportion_after": p_after,
        "contingency_table": table
    }


def effect_size_proportions(before_successes: int, before_trials: int,
                            after_successes: int, after_trials: int) -> Dict[str, Any]:
    """
    Calculate effect sizes for difference in proportions
    
    Args:
        before_successes: Number of successes before transformation
        before_trials: Total trials before transformation
        after_successes: Number of successes after transformation
        after_trials: Total trials after transformation
        
    Returns:
        Dictionary with effect size measures
    """
    p_before = before_successes / before_trials if before_trials > 0 else 0
    p_after = after_successes / after_trials if after_trials > 0 else 0
    
    # Absolute difference
    absolute_diff = p_after - p_before
    
    # Relative improvement (percentage)
    if p_before > 0:
        relative_improvement = (absolute_diff / p_before) * 100
    else:
        relative_improvement = float('inf') if p_after > 0 else 0
    
    # Odds ratio
    if before_successes > 0 and after_successes > 0:
        odds_before = before_successes / (before_trials - before_successes) if before_trials > before_successes else float('inf')
        odds_after = after_successes / (after_trials - after_successes) if after_trials > after_successes else float('inf')
        odds_ratio = odds_after / odds_before if odds_before > 0 and odds_before != float('inf') else float('inf')
    else:
        odds_ratio = None
    
    # Cohen's h (effect size for proportions)
    phi_before = 2 * math.asin(math.sqrt(p_before))
    phi_after = 2 * math.asin(math.sqrt(p_after))
    cohens_h = phi_after - phi_before
    
    # Interpret Cohen's h
    if abs(cohens_h) < 0.2:
        effect_interpretation = "negligible"
    elif abs(cohens_h) < 0.5:
        effect_interpretation = "small"
    elif abs(cohens_h) < 0.8:
        effect_interpretation = "medium"
    else:
        effect_interpretation = "large"
    
    return {
        "absolute_difference": absolute_diff,
        "relative_improvement_percent": relative_improvement if relative_improvement != float('inf') else None,
        "odds_ratio": odds_ratio,
        "cohens_h": cohens_h,
        "effect_size_interpretation": effect_interpretation
    }


def holm_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Holm-Bonferroni correction for multiple comparisons
    
    More powerful than Bonferroni while controlling family-wise error rate.
    
    Args:
        p_values: List of p-values from multiple tests
        alpha: Family-wise error rate (default 0.05)
        
    Returns:
        Dictionary with corrected results
    """
    n = len(p_values)
    if n == 0:
        return {
            "method": "holm_bonferroni",
            "alpha": alpha,
            "n_tests": 0,
            "rejected": [],
            "adjusted_p_values": []
        }
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    # Apply Holm-Bonferroni correction
    rejected = []
    adjusted_p_values = [None] * n
    
    for i, p in enumerate(sorted_p_values):
        # Adjusted alpha for this test
        adjusted_alpha = alpha / (n - i)
        
        # Adjusted p-value (for reporting)
        adjusted_p = min(1.0, p * (n - i))
        
        # Store adjusted p-value in original order
        original_idx = sorted_indices[i]
        adjusted_p_values[original_idx] = adjusted_p
        
        # Check if we reject this hypothesis
        if p <= adjusted_alpha:
            rejected.append(original_idx)
        else:
            # Once we fail to reject, stop (Holm's sequential procedure)
            break
    
    return {
        "method": "holm_bonferroni",
        "alpha": alpha,
        "n_tests": n,
        "n_rejected": len(rejected),
        "rejected_indices": rejected,
        "adjusted_p_values": adjusted_p_values,
        "original_p_values": p_values
    }


def compare_repeatability_rigorous(r_raw_list: List[float], r_structural_list: List[float],
                                   contract_names: List[str] = None,
                                   confidence: float = 0.95) -> Dict[str, Any]:
    """
    Rigorous statistical comparison of R_raw vs R_structural
    
    Implements all of Professor Nasser's recommendations:
    - Confidence intervals
    - Fisher's exact test (for small samples)
    - Effect sizes
    - Holm-Bonferroni correction
    
    Args:
        r_raw_list: List of R_raw values (one per contract)
        r_structural_list: List of R_structural values (one per contract)
        contract_names: Optional list of contract names
        confidence: Confidence level for intervals
        
    Returns:
        Dictionary with comprehensive statistical analysis
    """
    n_contracts = len(r_raw_list)
    
    if contract_names is None:
        contract_names = [f"contract_{i+1}" for i in range(n_contracts)]
    
    # Descriptive statistics with confidence intervals
    raw_stats = descriptive_statistics_with_ci(r_raw_list, "R_raw", confidence)
    structural_stats = descriptive_statistics_with_ci(r_structural_list, "R_structural", confidence)
    
    # Per-contract comparisons
    contract_results = []
    p_values = []
    
    for i in range(n_contracts):
        # Treat repeatability as proportion (0-1 scale)
        # For Fisher's exact test, we need counts
        # Assume each repeatability score represents proportion of n=20 runs
        n_runs = 20
        raw_successes = int(round(r_raw_list[i] * n_runs))
        structural_successes = int(round(r_structural_list[i] * n_runs))
        
        # Fisher's exact test
        fisher_result = fishers_exact_test(raw_successes, n_runs, structural_successes, n_runs)
        
        # Effect size
        effect = effect_size_proportions(raw_successes, n_runs, structural_successes, n_runs)
        
        contract_results.append({
            "contract": contract_names[i],
            "r_raw": r_raw_list[i],
            "r_structural": r_structural_list[i],
            "fisher_test": fisher_result,
            "effect_size": effect
        })
        
        p_values.append(fisher_result["p_value"])
    
    # Multiple comparison correction
    correction = holm_bonferroni_correction(p_values, alpha=0.05)
    
    # Overall improvement
    improvements = [r_structural_list[i] - r_raw_list[i] for i in range(n_contracts)]
    improvement_stats = descriptive_statistics_with_ci(improvements, "improvement", confidence)
    
    return {
        "summary": {
            "n_contracts": n_contracts,
            "confidence_level": confidence,
            "r_raw": raw_stats,
            "r_structural": structural_stats,
            "improvement": improvement_stats
        },
        "per_contract": contract_results,
        "multiple_comparison_correction": correction,
        "significant_contracts": [
            contract_names[i] for i in correction["rejected_indices"]
        ]
    }


def format_rigorous_report(analysis: Dict[str, Any]) -> str:
    """
    Format rigorous statistical analysis as readable report
    
    Args:
        analysis: Output from compare_repeatability_rigorous()
        
    Returns:
        Formatted text report
    """
    lines = []
    lines.append("=" * 80)
    lines.append("RIGOROUS STATISTICAL ANALYSIS - SKYT Repeatability")
    lines.append("=" * 80)
    
    summary = analysis["summary"]
    conf = summary["confidence_level"]
    
    # R_raw statistics
    raw = summary["r_raw"]
    lines.append(f"\nR_raw (before transformation):")
    lines.append(f"  Mean: {raw['mean']:.3f} [{raw['mean_ci'][0]:.3f}, {raw['mean_ci'][1]:.3f}] ({conf*100:.0f}% CI)")
    lines.append(f"  Median: {raw['median']:.3f} [{raw['median_ci'][0]:.3f}, {raw['median_ci'][1]:.3f}] ({conf*100:.0f}% CI)")
    lines.append(f"  Std Dev: {raw['std']:.3f}")
    lines.append(f"  Range: [{raw['min']:.3f}, {raw['max']:.3f}]")
    lines.append(f"  N: {raw['n']}")
    
    # R_structural statistics
    struct = summary["r_structural"]
    lines.append(f"\nR_structural (after transformation):")
    lines.append(f"  Mean: {struct['mean']:.3f} [{struct['mean_ci'][0]:.3f}, {struct['mean_ci'][1]:.3f}] ({conf*100:.0f}% CI)")
    lines.append(f"  Median: {struct['median']:.3f} [{struct['median_ci'][0]:.3f}, {struct['median_ci'][1]:.3f}] ({conf*100:.0f}% CI)")
    lines.append(f"  Std Dev: {struct['std']:.3f}")
    lines.append(f"  Range: [{struct['min']:.3f}, {struct['max']:.3f}]")
    lines.append(f"  N: {struct['n']}")
    
    # Improvement
    imp = summary["improvement"]
    lines.append(f"\nImprovement (R_structural - R_raw):")
    lines.append(f"  Mean: {imp['mean']:.3f} [{imp['mean_ci'][0]:.3f}, {imp['mean_ci'][1]:.3f}] ({conf*100:.0f}% CI)")
    lines.append(f"  Median: {imp['median']:.3f}")
    
    # Multiple comparison correction
    correction = analysis["multiple_comparison_correction"]
    lines.append(f"\nMultiple Comparison Correction ({correction['method']}):")
    lines.append(f"  Total tests: {correction['n_tests']}")
    lines.append(f"  Significant (α={correction['alpha']}): {correction['n_rejected']}")
    lines.append(f"  Significant contracts: {', '.join(analysis['significant_contracts']) if analysis['significant_contracts'] else 'None'}")
    
    # Per-contract details
    lines.append(f"\nPer-Contract Analysis:")
    lines.append("-" * 80)
    
    for result in analysis["per_contract"]:
        lines.append(f"\n{result['contract']}:")
        lines.append(f"  R_raw: {result['r_raw']:.3f} → R_structural: {result['r_structural']:.3f}")
        
        fisher = result["fisher_test"]
        lines.append(f"  Fisher's exact test: p={fisher['p_value']:.4f} {'*' if fisher['significant'] else ''}")
        lines.append(f"  Odds ratio: {fisher['odds_ratio']:.2f}")
        
        effect = result["effect_size"]
        lines.append(f"  Effect size (Cohen's h): {effect['cohens_h']:.3f} ({effect['effect_size_interpretation']})")
        lines.append(f"  Absolute improvement: {effect['absolute_difference']:.3f}")
        if effect['relative_improvement_percent'] is not None:
            lines.append(f"  Relative improvement: {effect['relative_improvement_percent']:.1f}%")
    
    lines.append("\n" + "=" * 80)
    lines.append("Note: * indicates significance at α=0.05 level")
    lines.append("CI = Confidence Interval (bootstrap method)")
    lines.append("=" * 80)
    
    return "\n".join(lines)
