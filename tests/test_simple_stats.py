# tests/test_simple_stats.py
"""
Tests for simple statistical analysis module
"""

import pytest
from src.simple_stats import (
    descriptive_statistics,
    wilcoxon_test,
    compare_metrics,
    format_comparison_report,
    format_paper_summary
)


def test_descriptive_statistics():
    """Test descriptive statistics calculation"""
    data = [0.4, 0.5, 0.6, 0.7, 0.8]
    
    stats = descriptive_statistics(data, "test_metric")
    
    assert stats["name"] == "test_metric"
    assert stats["n"] == 5
    assert stats["mean"] == 0.6
    assert stats["median"] == 0.6
    assert stats["min"] == 0.4
    assert stats["max"] == 0.8


def test_wilcoxon_improvement():
    """Test Wilcoxon test detects improvement"""
    before = [0.3, 0.4, 0.5, 0.4, 0.3]
    after = [0.8, 0.9, 0.85, 0.9, 0.95]
    
    result = wilcoxon_test(before, after)
    
    assert result["test"] == "wilcoxon_signed_rank"
    assert result["n"] == 5
    assert result["significant"] == True  # Should detect improvement
    assert result["p_value"] < 0.05
    assert result["median_improvement"] > 0


def test_wilcoxon_no_change():
    """Test Wilcoxon when no improvement"""
    before = [0.5, 0.6, 0.7, 0.5, 0.6]
    after = [0.5, 0.6, 0.7, 0.5, 0.6]  # Same values
    
    result = wilcoxon_test(before, after)
    
    assert result["significant"] == False
    assert result["median_improvement"] == 0.0


def test_compare_metrics():
    """Test full metric comparison"""
    r_raw = [0.3, 0.4, 0.5, 0.4, 0.3]
    r_structural = [0.8, 0.9, 0.85, 0.9, 0.95]
    
    comparison = compare_metrics(r_raw, r_structural)
    
    # Check structure
    assert "r_raw" in comparison
    assert "r_structural" in comparison
    assert "improvement" in comparison
    assert "wilcoxon_test" in comparison
    
    # Check improvement calculation
    assert comparison["improvement"]["absolute"] > 0
    assert comparison["improvement"]["relative_percent"] > 0
    
    # Check significance
    assert comparison["wilcoxon_test"]["significant"] == True


def test_format_comparison_report():
    """Test report formatting"""
    r_raw = [0.4, 0.5, 0.6]
    r_structural = [0.8, 0.9, 0.85]
    
    comparison = compare_metrics(r_raw, r_structural)
    report = format_comparison_report(comparison)
    
    # Check report contains key information
    assert "R_raw" in report
    assert "R_structural" in report
    assert "Wilcoxon" in report
    assert "Mean:" in report
    assert "p-value:" in report


def test_format_paper_summary():
    """Test paper summary formatting"""
    r_raw = [0.4, 0.5, 0.6]
    r_structural = [0.8, 0.9, 0.85]
    
    comparison = compare_metrics(r_raw, r_structural)
    summary = format_paper_summary(comparison)
    
    # Check summary is concise
    assert "R_raw=" in summary
    assert "R_structural=" in summary
    assert "p<" in summary or "p=" in summary
    assert len(summary) < 200  # Should be one line


if __name__ == "__main__":
    # Run a quick demo
    print("Demo: Comparing R_raw vs R_structural\n")
    
    # Example data
    r_raw = [0.45, 0.50, 0.42, 0.48, 0.43, 0.47, 0.44, 0.46, 0.49, 0.41]
    r_structural = [0.78, 0.82, 0.75, 0.80, 0.77, 0.81, 0.76, 0.79, 0.83, 0.74]
    
    # Compare
    comparison = compare_metrics(r_raw, r_structural)
    
    # Print full report
    print(format_comparison_report(comparison))
    
    # Print paper summary
    print("\nFor paper:")
    print(format_paper_summary(comparison))
