# tests/test_statistical_analysis.py
"""
Tests for statistical analysis module
"""

import pytest
import numpy as np
from src.statistical_analysis import StatisticalAnalyzer, format_statistical_report


class TestStatisticalAnalyzer:
    """Test suite for StatisticalAnalyzer"""
    
    def test_wilcoxon_improvement(self):
        """Test Wilcoxon test detects improvement"""
        analyzer = StatisticalAnalyzer(alpha=0.05)
        
        # Simulated data: SKYT improves repeatability
        r_raw = [0.3, 0.4, 0.3, 0.4, 0.3, 0.4, 0.3, 0.4, 0.3, 0.4, 
                 0.3, 0.4, 0.3, 0.4, 0.3, 0.4, 0.3, 0.4, 0.3, 0.4]
        r_structural = [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9,
                       0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]
        
        result = analyzer.wilcoxon_test(r_raw, r_structural, alternative="less")
        
        assert result["test"] == "wilcoxon_signed_rank"
        # Just check that the test runs and detects improvement direction
        assert result["effect_direction"] == "improvement"
        assert result["median_difference"] > 0
        assert "p_value" in result
        assert "significant" in result
    
    def test_wilcoxon_no_change(self):
        """Test Wilcoxon test when no change occurs"""
        analyzer = StatisticalAnalyzer(alpha=0.05)
        
        # No change
        r_raw = [0.5, 0.6, 0.4, 0.5, 0.6]
        r_structural = [0.5, 0.6, 0.4, 0.5, 0.6]
        
        result = analyzer.wilcoxon_test(r_raw, r_structural)
        
        assert result["median_difference"] == 0.0
        assert result["effect_direction"] == "none"
    
    def test_cliffs_delta_large_effect(self):
        """Test Cliff's delta detects large effect"""
        analyzer = StatisticalAnalyzer()
        
        # Large difference between groups
        group1 = [0.3, 0.4, 0.3, 0.4, 0.3]
        group2 = [0.8, 0.9, 0.9, 0.8, 0.9]
        
        result = analyzer.cliffs_delta(group1, group2)
        
        assert result["effect_size"] == "cliffs_delta"
        assert result["magnitude"] == "large"
        assert result["delta"] > 0.474
        assert result["direction"] == "group2 > group1"
    
    def test_cliffs_delta_negligible(self):
        """Test Cliff's delta detects negligible effect"""
        analyzer = StatisticalAnalyzer()
        
        # Minimal difference
        group1 = [0.5, 0.51, 0.49, 0.5, 0.51]
        group2 = [0.5, 0.52, 0.48, 0.5, 0.52]
        
        result = analyzer.cliffs_delta(group1, group2)
        
        assert result["magnitude"] == "negligible"
        assert abs(result["delta"]) < 0.147
    
    def test_bootstrap_ci(self):
        """Test bootstrap confidence interval"""
        analyzer = StatisticalAnalyzer()
        
        data = [0.5, 0.6, 0.4, 0.5, 0.6, 0.5, 0.4, 0.6, 0.5, 0.6]
        
        result = analyzer.bootstrap_ci(data, n_bootstrap=1000, ci_level=0.95)
        
        assert result["statistic"] == "mean"
        assert "point_estimate" in result
        assert "ci_lower" in result
        assert "ci_upper" in result
        assert result["ci_lower"] < result["point_estimate"] < result["ci_upper"]
        assert result["ci_level"] == 0.95
    
    def test_compare_metrics(self):
        """Test comprehensive metric comparison"""
        analyzer = StatisticalAnalyzer(alpha=0.05)
        
        # Simulated SKYT experiment results
        r_raw = [0.3, 0.4, 0.3, 0.4, 0.3, 0.4, 0.3, 0.4, 0.3, 0.4, 
                 0.3, 0.4, 0.3, 0.4, 0.3, 0.4, 0.3, 0.4, 0.3, 0.4]
        r_structural = [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9,
                       0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]
        
        result = analyzer.compare_metrics(r_raw, r_structural, metric_name="repeatability")
        
        # Check all components present
        assert "wilcoxon_test" in result
        assert "cliffs_delta" in result
        assert "confidence_intervals" in result
        assert "descriptive_statistics" in result
        assert "conclusion" in result
        
        # Check improvement detected in descriptive stats and effect size
        assert result["cliffs_delta"]["magnitude"] in ["medium", "large"]
        assert result["descriptive_statistics"]["improvement"]["mean_delta"] > 0
        assert result["cliffs_delta"]["delta"] > 0  # Positive effect
    
    def test_bonferroni_correction(self):
        """Test Bonferroni correction for multiple comparisons"""
        analyzer = StatisticalAnalyzer(alpha=0.05)
        
        # 5 tests with various p-values
        p_values = [0.001, 0.02, 0.03, 0.04, 0.06]
        
        result = analyzer.bonferroni_correction(p_values)
        
        assert result["correction"] == "bonferroni"
        assert result["n_tests"] == 5
        assert result["adjusted_alpha"] == 0.05 / 5  # 0.01
        assert len(result["significant"]) == 5
        # Only p=0.001 should be significant after correction
        assert result["n_significant"] == 1
    
    def test_temperature_sweep_analysis(self):
        """Test analysis across temperature sweep"""
        analyzer = StatisticalAnalyzer(alpha=0.05)
        
        # Simulated results at different temperatures
        results_by_temp = {
            0.0: {
                "r_raw": [0.6, 0.7, 0.6, 0.7, 0.6],
                "r_structural": [0.9, 0.9, 0.9, 0.9, 0.9]
            },
            0.5: {
                "r_raw": [0.4, 0.5, 0.4, 0.5, 0.4],
                "r_structural": [0.8, 0.9, 0.8, 0.9, 0.8]
            },
            1.0: {
                "r_raw": [0.3, 0.4, 0.3, 0.4, 0.3],
                "r_structural": [0.7, 0.8, 0.7, 0.8, 0.7]
            }
        }
        
        result = analyzer.analyze_temperature_sweep(results_by_temp)
        
        assert "temperatures" in result
        assert "comparisons_by_temperature" in result
        assert "bonferroni_correction" in result
        assert "kruskal_wallis" in result
        
        # Check all temperatures analyzed
        assert len(result["comparisons_by_temperature"]) == 3
        assert 0.0 in result["comparisons_by_temperature"]
        assert 0.5 in result["comparisons_by_temperature"]
        assert 1.0 in result["comparisons_by_temperature"]


class TestStatisticalReporting:
    """Test statistical report formatting"""
    
    def test_format_report(self):
        """Test report formatting"""
        analyzer = StatisticalAnalyzer(alpha=0.05)
        
        r_raw = [0.4, 0.5, 0.3, 0.6, 0.4]
        r_structural = [0.8, 0.9, 0.7, 0.9, 0.8]
        
        analysis = analyzer.compare_metrics(r_raw, r_structural, metric_name="test_metric")
        report = format_statistical_report(analysis)
        
        # Check report contains key sections
        assert "Statistical Analysis" in report
        assert "Descriptive Statistics" in report
        assert "Wilcoxon Signed-Rank Test" in report
        assert "Effect Size (Cliff's Delta)" in report
        assert "95% Confidence Intervals" in report
        assert "Conclusion" in report
        
        # Check specific values present
        assert "R_raw" in report
        assert "R_structural" in report
        assert "p=" in report
        assert "δ=" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
