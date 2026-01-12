# src/simple_stats.py
"""
Simple statistical analysis for SKYT experiments
Provides descriptive statistics and Wilcoxon signed-rank test
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Any


def descriptive_statistics(data: List[float], name: str = "metric") -> Dict[str, Any]:
    """
    Calculate descriptive statistics for a metric
    
    Args:
        data: List of metric values
        name: Name of the metric
        
    Returns:
        Dictionary with mean, median, std, min, max, n
    """
    if len(data) == 0:
        return {
            "name": name,
            "n": 0,
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "max": None
        }
    
    return {
        "name": name,
        "n": len(data),
        "mean": float(np.mean(data)),
        "median": float(np.median(data)),
        "std": float(np.std(data)),
        "min": float(np.min(data)),
        "max": float(np.max(data))
    }


def wilcoxon_test(before: List[float], after: List[float]) -> Dict[str, Any]:
    """
    Wilcoxon signed-rank test for paired samples
    
    Tests if transformation significantly improves repeatability.
    H0: No difference between before and after
    H1: After > Before (one-sided test)
    
    Args:
        before: Repeatability scores before transformation (R_raw)
        after: Repeatability scores after transformation (R_structural)
        
    Returns:
        Dictionary with test results
    """
    if len(before) != len(after):
        raise ValueError(f"Sample sizes must match: {len(before)} vs {len(after)}")
    
    if len(before) < 3:
        return {
            "test": "wilcoxon_signed_rank",
            "n": len(before),
            "statistic": None,
            "p_value": None,
            "significant": False,
            "note": "Sample size too small (n < 3)"
        }
    
    # Calculate differences
    differences = np.array(after) - np.array(before)
    
    # Check if all differences are zero
    if np.all(differences == 0):
        return {
            "test": "wilcoxon_signed_rank",
            "n": len(before),
            "statistic": 0.0,
            "p_value": 1.0,
            "significant": False,
            "median_improvement": 0.0,
            "note": "All differences are zero"
        }
    
    # Perform Wilcoxon signed-rank test (one-sided: after > before)
    try:
        statistic, p_value = stats.wilcoxon(
            differences,
            alternative='greater',
            zero_method='wilcox',
            correction=True
        )
    except ValueError as e:
        return {
            "test": "wilcoxon_signed_rank",
            "n": len(before),
            "statistic": None,
            "p_value": None,
            "significant": False,
            "note": f"Test failed: {str(e)}"
        }
    
    # Determine significance (α = 0.05)
    significant = p_value < 0.05
    
    return {
        "test": "wilcoxon_signed_rank",
        "n": len(before),
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": significant,
        "median_improvement": float(np.median(differences)),
        "mean_improvement": float(np.mean(differences))
    }


def compare_metrics(r_raw: List[float], r_structural: List[float]) -> Dict[str, Any]:
    """
    Compare R_raw vs R_structural with descriptive stats and significance test
    
    Args:
        r_raw: Raw repeatability scores
        r_structural: Structural repeatability scores (post-transformation)
        
    Returns:
        Dictionary with comparison results
    """
    # Descriptive statistics
    stats_raw = descriptive_statistics(r_raw, "R_raw")
    stats_structural = descriptive_statistics(r_structural, "R_structural")
    
    # Wilcoxon test
    wilcoxon_result = wilcoxon_test(r_raw, r_structural)
    
    # Calculate improvement
    if stats_raw["mean"] is not None and stats_structural["mean"] is not None:
        absolute_improvement = stats_structural["mean"] - stats_raw["mean"]
        if stats_raw["mean"] > 0:
            relative_improvement = (absolute_improvement / stats_raw["mean"]) * 100
        else:
            relative_improvement = None
    else:
        absolute_improvement = None
        relative_improvement = None
    
    return {
        "r_raw": stats_raw,
        "r_structural": stats_structural,
        "improvement": {
            "absolute": absolute_improvement,
            "relative_percent": relative_improvement
        },
        "wilcoxon_test": wilcoxon_result
    }


def format_comparison_report(comparison: Dict[str, Any]) -> str:
    """
    Format comparison results as readable text
    
    Args:
        comparison: Output from compare_metrics()
        
    Returns:
        Formatted text report
    """
    lines = []
    lines.append("=" * 60)
    lines.append("SKYT Repeatability Comparison")
    lines.append("=" * 60)
    
    # R_raw statistics
    r_raw = comparison["r_raw"]
    lines.append(f"\nR_raw (before transformation):")
    lines.append(f"  Mean: {r_raw['mean']:.3f}")
    lines.append(f"  Median: {r_raw['median']:.3f}")
    lines.append(f"  Std Dev: {r_raw['std']:.3f}")
    lines.append(f"  Range: [{r_raw['min']:.3f}, {r_raw['max']:.3f}]")
    lines.append(f"  N: {r_raw['n']}")
    
    # R_structural statistics
    r_struct = comparison["r_structural"]
    lines.append(f"\nR_structural (after transformation):")
    lines.append(f"  Mean: {r_struct['mean']:.3f}")
    lines.append(f"  Median: {r_struct['median']:.3f}")
    lines.append(f"  Std Dev: {r_struct['std']:.3f}")
    lines.append(f"  Range: [{r_struct['min']:.3f}, {r_struct['max']:.3f}]")
    lines.append(f"  N: {r_struct['n']}")
    
    # Improvement
    improvement = comparison["improvement"]
    if improvement["absolute"] is not None:
        lines.append(f"\nImprovement:")
        lines.append(f"  Absolute: +{improvement['absolute']:.3f}")
        if improvement["relative_percent"] is not None:
            lines.append(f"  Relative: +{improvement['relative_percent']:.1f}%")
    
    # Wilcoxon test
    wilcoxon = comparison["wilcoxon_test"]
    lines.append(f"\nStatistical Significance (Wilcoxon signed-rank test):")
    if wilcoxon["p_value"] is not None:
        lines.append(f"  Test statistic: {wilcoxon['statistic']:.2f}")
        lines.append(f"  p-value: {wilcoxon['p_value']:.4f}")
        lines.append(f"  Result: {'SIGNIFICANT' if wilcoxon['significant'] else 'NOT SIGNIFICANT'} (α=0.05)")
        lines.append(f"  Median improvement: {wilcoxon['median_improvement']:.3f}")
    else:
        lines.append(f"  {wilcoxon.get('note', 'Test not performed')}")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)


def format_paper_summary(comparison: Dict[str, Any]) -> str:
    """
    Format results for paper (one-line summary)
    
    Args:
        comparison: Output from compare_metrics()
        
    Returns:
        One-line summary suitable for paper
    """
    r_raw = comparison["r_raw"]
    r_struct = comparison["r_structural"]
    wilcoxon = comparison["wilcoxon_test"]
    improvement = comparison["improvement"]
    
    # Build summary
    summary = (
        f"SKYT improved repeatability from R_raw={r_raw['mean']:.2f}±{r_raw['std']:.2f} "
        f"to R_structural={r_struct['mean']:.2f}±{r_struct['std']:.2f} "
        f"(+{improvement['relative_percent']:.0f}%"
    )
    
    if wilcoxon["significant"]:
        summary += f", p<{wilcoxon['p_value']:.3f})"
    else:
        summary += f", p={wilcoxon['p_value']:.3f})"
    
    return summary
