# tests/test_enhanced_stats.py
"""
Tests for enhanced statistical analysis module
Demonstrates Professor Nasser's recommended statistical methods
"""

import pytest
from src.enhanced_stats import (
    wilson_confidence_interval,
    bootstrap_confidence_interval,
    descriptive_statistics_with_ci,
    fishers_exact_test,
    effect_size_proportions,
    holm_bonferroni_correction,
    compare_repeatability_rigorous,
    format_rigorous_report
)


def test_wilson_confidence_interval():
    """Test Wilson score confidence interval"""
    # 15 successes out of 20 trials
    lower, upper = wilson_confidence_interval(15, 20, confidence=0.95)
    
    assert 0.0 <= lower <= 1.0
    assert 0.0 <= upper <= 1.0
    assert lower < upper
    assert lower < 0.75  # Point estimate
    assert upper > 0.75


def test_bootstrap_confidence_interval():
    """Test bootstrap confidence interval"""
    data = [0.6, 0.7, 0.65, 0.68, 0.72, 0.63, 0.69, 0.71, 0.64, 0.67]
    
    lower, upper = bootstrap_confidence_interval(data, confidence=0.95, n_bootstrap=1000)
    
    assert lower < upper
    assert lower < sum(data)/len(data)  # Mean should be in interval
    assert upper > sum(data)/len(data)


def test_descriptive_statistics_with_ci():
    """Test descriptive statistics with confidence intervals"""
    data = [0.5, 0.6, 0.55, 0.58, 0.62, 0.53, 0.59, 0.61, 0.54, 0.57]
    
    stats = descriptive_statistics_with_ci(data, "test_metric", confidence=0.95)
    
    assert stats["name"] == "test_metric"
    assert stats["n"] == 10
    assert stats["mean"] > 0
    assert stats["mean_ci"][0] < stats["mean"]
    assert stats["mean_ci"][1] > stats["mean"]
    assert stats["median_ci"][0] < stats["median"]
    assert stats["median_ci"][1] > stats["median"]


def test_fishers_exact_test():
    """Test Fisher's exact test"""
    # Before: 10/20 successes, After: 18/20 successes
    result = fishers_exact_test(10, 20, 18, 20)
    
    assert result["test"] == "fisher_exact"
    assert 0.0 <= result["p_value"] <= 1.0
    assert result["proportion_before"] == 0.5
    assert result["proportion_after"] == 0.9
    assert result["odds_ratio"] > 1.0  # Should show improvement


def test_effect_size_proportions():
    """Test effect size calculation"""
    # Before: 10/20, After: 18/20
    effect = effect_size_proportions(10, 20, 18, 20)
    
    assert effect["absolute_difference"] == 0.4  # 0.9 - 0.5
    assert effect["relative_improvement_percent"] == 80.0  # 80% improvement
    assert effect["cohens_h"] > 0  # Positive effect
    assert effect["effect_size_interpretation"] in ["negligible", "small", "medium", "large"]


def test_holm_bonferroni_correction():
    """Test Holm-Bonferroni correction"""
    # Multiple p-values
    p_values = [0.001, 0.01, 0.03, 0.06, 0.10]
    
    result = holm_bonferroni_correction(p_values, alpha=0.05)
    
    assert result["method"] == "holm_bonferroni"
    assert result["n_tests"] == 5
    assert len(result["adjusted_p_values"]) == 5
    assert result["n_rejected"] >= 0
    assert result["n_rejected"] <= 5


def test_compare_repeatability_rigorous():
    """Test comprehensive rigorous comparison"""
    # Example data: 5 contracts
    r_raw = [0.45, 0.50, 0.42, 0.48, 0.43]
    r_structural = [0.78, 0.82, 0.75, 0.80, 0.77]
    contracts = ["fibonacci", "binary_search", "merge_sort", "quick_sort", "factorial"]
    
    analysis = compare_repeatability_rigorous(r_raw, r_structural, contracts, confidence=0.95)
    
    # Check structure
    assert "summary" in analysis
    assert "per_contract" in analysis
    assert "multiple_comparison_correction" in analysis
    assert "significant_contracts" in analysis
    
    # Check summary
    summary = analysis["summary"]
    assert summary["n_contracts"] == 5
    assert summary["r_raw"]["n"] == 5
    assert summary["r_structural"]["n"] == 5
    
    # Check per-contract results
    assert len(analysis["per_contract"]) == 5
    for result in analysis["per_contract"]:
        assert "contract" in result
        assert "fisher_test" in result
        assert "effect_size" in result


def test_format_rigorous_report():
    """Test report formatting"""
    r_raw = [0.45, 0.50, 0.42]
    r_structural = [0.78, 0.82, 0.75]
    contracts = ["test1", "test2", "test3"]
    
    analysis = compare_repeatability_rigorous(r_raw, r_structural, contracts)
    report = format_rigorous_report(analysis)
    
    # Check report contains key information
    assert "RIGOROUS STATISTICAL ANALYSIS" in report
    assert "R_raw" in report
    assert "R_structural" in report
    assert "Fisher's exact test" in report
    assert "Cohen's h" in report
    assert "Confidence Interval" in report
    assert "Holm-Bonferroni" in report or "holm_bonferroni" in report


if __name__ == "__main__":
    # Run a comprehensive demo
    print("=" * 80)
    print("DEMO: Enhanced Statistical Analysis for SKYT")
    print("=" * 80)
    print("\nImplementing Professor Nasser's recommendations:")
    print("1. Confidence intervals (Wilson score, bootstrap)")
    print("2. Fisher's exact test (for small samples)")
    print("3. Effect sizes (Cohen's h, odds ratios)")
    print("4. Holm-Bonferroni correction (multiple comparisons)")
    print("\n" + "=" * 80)
    
    # Example data: 12 contracts
    r_raw = [0.45, 0.50, 0.42, 0.48, 0.43, 0.47, 0.44, 0.46, 0.49, 0.41, 0.52, 0.40]
    r_structural = [0.78, 0.82, 0.75, 0.80, 0.77, 0.81, 0.76, 0.79, 0.83, 0.74, 0.85, 0.73]
    contracts = [
        "fibonacci", "binary_search", "merge_sort", "quick_sort", 
        "factorial", "is_palindrome", "is_prime", "gcd",
        "matrix_multiply", "slugify", "brackets_balanced", "longest_common_subsequence"
    ]
    
    # Run rigorous analysis
    analysis = compare_repeatability_rigorous(r_raw, r_structural, contracts, confidence=0.95)
    
    # Print formatted report
    print(format_rigorous_report(analysis))
    
    print("\n" + "=" * 80)
    print("Key Features:")
    print("- Wilson score CI: Accurate for small samples and extreme proportions")
    print("- Fisher's exact: No assumptions about sample size or distribution")
    print("- Cohen's h: Standardized effect size for proportions")
    print("- Holm-Bonferroni: Controls family-wise error rate (more powerful than Bonferroni)")
    print("=" * 80)
