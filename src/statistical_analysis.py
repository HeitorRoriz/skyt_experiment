# src/statistical_analysis.py
"""
Statistical analysis module for SKYT experiments
Provides rigorous statistical tests for camera-ready revision
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Any, Optional
import warnings


class StatisticalAnalyzer:
    """
    Comprehensive statistical analysis for SKYT repeatability metrics
    
    Implements:
    - Wilcoxon signed-rank test (paired non-parametric test)
    - Cliff's delta (effect size for non-parametric data)
    - Bootstrap confidence intervals
    - Multiple comparison corrections (Bonferroni)
    """
    
    def __init__(self, alpha: float = 0.05):
        """
        Initialize statistical analyzer
        
        Args:
            alpha: Significance level (default: 0.05)
        """
        self.alpha = alpha
    
    def wilcoxon_test(self, before: List[float], after: List[float], 
                      alternative: str = "two-sided") -> Dict[str, Any]:
        """
        Wilcoxon signed-rank test for paired samples
        
        Tests if SKYT transformation significantly improves repeatability.
        H0: median(after - before) = 0
        H1: median(after - before) != 0 (or > 0 for one-sided)
        
        Args:
            before: Repeatability scores before transformation (R_raw or R_anchor_pre)
            after: Repeatability scores after transformation (R_structural or R_anchor_post)
            alternative: "two-sided", "greater", or "less"
            
        Returns:
            Dictionary with test results
        """
        if len(before) != len(after):
            raise ValueError(f"Sample sizes must match: {len(before)} vs {len(after)}")
        
        if len(before) < 3:
            warnings.warn("Sample size < 3, Wilcoxon test may be unreliable")
        
        # Calculate differences
        differences = np.array(after) - np.array(before)
        
        # Perform Wilcoxon signed-rank test
        try:
            statistic, p_value = stats.wilcoxon(
                differences, 
                alternative=alternative,
                zero_method='wilcox',  # Wilcox method for zeros
                correction=True  # Continuity correction
            )
        except ValueError as e:
            # Handle case where all differences are zero
            return {
                "test": "wilcoxon_signed_rank",
                "statistic": 0.0,
                "p_value": 1.0,
                "significant": False,
                "effect_direction": "none",
                "n_pairs": len(before),
                "median_difference": 0.0,
                "error": str(e)
            }
        
        # Determine significance
        significant = p_value < self.alpha
        
        # Effect direction
        median_diff = np.median(differences)
        if median_diff > 0:
            effect_direction = "improvement"
        elif median_diff < 0:
            effect_direction = "degradation"
        else:
            effect_direction = "none"
        
        return {
            "test": "wilcoxon_signed_rank",
            "statistic": float(statistic),
            "p_value": float(p_value),
            "significant": significant,
            "alpha": self.alpha,
            "alternative": alternative,
            "effect_direction": effect_direction,
            "n_pairs": len(before),
            "median_difference": float(median_diff),
            "mean_difference": float(np.mean(differences)),
            "std_difference": float(np.std(differences))
        }
    
    def cliffs_delta(self, group1: List[float], group2: List[float]) -> Dict[str, Any]:
        """
        Cliff's delta effect size for non-parametric data
        
        Measures the probability that a random value from group2 
        is greater than a random value from group1.
        
        Interpretation:
        - |delta| < 0.147: negligible
        - 0.147 <= |delta| < 0.33: small
        - 0.33 <= |delta| < 0.474: medium
        - |delta| >= 0.474: large
        
        Args:
            group1: First group (e.g., R_raw scores)
            group2: Second group (e.g., R_structural scores)
            
        Returns:
            Dictionary with effect size results
        """
        n1 = len(group1)
        n2 = len(group2)
        
        if n1 == 0 or n2 == 0:
            raise ValueError("Groups cannot be empty")
        
        # Calculate Cliff's delta
        # delta = (# pairs where group2 > group1 - # pairs where group2 < group1) / (n1 * n2)
        greater = 0
        less = 0
        
        for x in group1:
            for y in group2:
                if y > x:
                    greater += 1
                elif y < x:
                    less += 1
        
        delta = (greater - less) / (n1 * n2)
        
        # Interpret magnitude
        abs_delta = abs(delta)
        if abs_delta < 0.147:
            magnitude = "negligible"
        elif abs_delta < 0.33:
            magnitude = "small"
        elif abs_delta < 0.474:
            magnitude = "medium"
        else:
            magnitude = "large"
        
        # Interpret direction
        if delta > 0:
            direction = "group2 > group1"
        elif delta < 0:
            direction = "group2 < group1"
        else:
            direction = "no difference"
        
        return {
            "effect_size": "cliffs_delta",
            "delta": float(delta),
            "magnitude": magnitude,
            "direction": direction,
            "n_group1": n1,
            "n_group2": n2,
            "interpretation": f"{magnitude} effect, {direction}"
        }
    
    def bootstrap_ci(self, data: List[float], n_bootstrap: int = 10000,
                     ci_level: float = 0.95, statistic: str = "mean") -> Dict[str, Any]:
        """
        Bootstrap confidence interval for a statistic
        
        Args:
            data: Sample data
            n_bootstrap: Number of bootstrap samples
            ci_level: Confidence level (default: 0.95 for 95% CI)
            statistic: "mean" or "median"
            
        Returns:
            Dictionary with confidence interval
        """
        if len(data) == 0:
            raise ValueError("Data cannot be empty")
        
        data = np.array(data)
        
        # Choose statistic function
        if statistic == "mean":
            stat_func = np.mean
        elif statistic == "median":
            stat_func = np.median
        else:
            raise ValueError(f"Unsupported statistic: {statistic}")
        
        # Bootstrap resampling
        bootstrap_stats = []
        for _ in range(n_bootstrap):
            sample = np.random.choice(data, size=len(data), replace=True)
            bootstrap_stats.append(stat_func(sample))
        
        bootstrap_stats = np.array(bootstrap_stats)
        
        # Calculate percentile confidence interval
        alpha = 1 - ci_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        ci_lower = np.percentile(bootstrap_stats, lower_percentile)
        ci_upper = np.percentile(bootstrap_stats, upper_percentile)
        
        # Point estimate
        point_estimate = stat_func(data)
        
        return {
            "statistic": statistic,
            "point_estimate": float(point_estimate),
            "ci_level": ci_level,
            "ci_lower": float(ci_lower),
            "ci_upper": float(ci_upper),
            "ci_width": float(ci_upper - ci_lower),
            "n_bootstrap": n_bootstrap,
            "n_samples": len(data)
        }
    
    def compare_metrics(self, r_raw: List[float], r_structural: List[float],
                       metric_name: str = "repeatability") -> Dict[str, Any]:
        """
        Comprehensive comparison of two metrics (e.g., R_raw vs R_structural)
        
        Performs:
        1. Wilcoxon signed-rank test
        2. Cliff's delta effect size
        3. Bootstrap confidence intervals for both metrics
        
        Args:
            r_raw: Raw repeatability scores
            r_structural: Structural repeatability scores (post-transformation)
            metric_name: Name of the metric being compared
            
        Returns:
            Dictionary with comprehensive comparison results
        """
        # Wilcoxon test (paired)
        wilcoxon_result = self.wilcoxon_test(r_raw, r_structural, alternative="less")
        
        # Cliff's delta (unpaired effect size)
        cliffs_result = self.cliffs_delta(r_raw, r_structural)
        
        # Bootstrap CIs
        ci_raw = self.bootstrap_ci(r_raw, statistic="mean")
        ci_structural = self.bootstrap_ci(r_structural, statistic="mean")
        
        # Descriptive statistics
        descriptive = {
            "r_raw": {
                "mean": float(np.mean(r_raw)),
                "median": float(np.median(r_raw)),
                "std": float(np.std(r_raw)),
                "min": float(np.min(r_raw)),
                "max": float(np.max(r_raw)),
                "n": len(r_raw)
            },
            "r_structural": {
                "mean": float(np.mean(r_structural)),
                "median": float(np.median(r_structural)),
                "std": float(np.std(r_structural)),
                "min": float(np.min(r_structural)),
                "max": float(np.max(r_structural)),
                "n": len(r_structural)
            },
            "improvement": {
                "mean_delta": float(np.mean(r_structural) - np.mean(r_raw)),
                "median_delta": float(np.median(r_structural) - np.median(r_raw))
            }
        }
        
        return {
            "metric_name": metric_name,
            "wilcoxon_test": wilcoxon_result,
            "cliffs_delta": cliffs_result,
            "confidence_intervals": {
                "r_raw": ci_raw,
                "r_structural": ci_structural
            },
            "descriptive_statistics": descriptive,
            "conclusion": self._generate_conclusion(wilcoxon_result, cliffs_result, descriptive)
        }
    
    def _generate_conclusion(self, wilcoxon: Dict, cliffs: Dict, 
                            descriptive: Dict) -> str:
        """Generate human-readable conclusion from statistical tests"""
        
        # Check significance
        if wilcoxon["significant"]:
            sig_text = f"statistically significant (p={wilcoxon['p_value']:.4f} < {self.alpha})"
        else:
            sig_text = f"not statistically significant (p={wilcoxon['p_value']:.4f} >= {self.alpha})"
        
        # Effect size
        effect_text = f"{cliffs['magnitude']} effect size (δ={cliffs['delta']:.3f})"
        
        # Improvement
        mean_improvement = descriptive["improvement"]["mean_delta"]
        improvement_text = f"mean improvement of {mean_improvement:.3f}"
        
        conclusion = (
            f"SKYT transformation shows {sig_text} with {effect_text}. "
            f"R_structural (M={descriptive['r_structural']['mean']:.3f}) "
            f"vs R_raw (M={descriptive['r_raw']['mean']:.3f}), "
            f"{improvement_text}."
        )
        
        return conclusion
    
    def bonferroni_correction(self, p_values: List[float]) -> Dict[str, Any]:
        """
        Bonferroni correction for multiple comparisons
        
        Adjusts significance threshold to control family-wise error rate.
        
        Args:
            p_values: List of p-values from multiple tests
            
        Returns:
            Dictionary with corrected results
        """
        n_tests = len(p_values)
        adjusted_alpha = self.alpha / n_tests
        
        significant = [p < adjusted_alpha for p in p_values]
        
        return {
            "correction": "bonferroni",
            "n_tests": n_tests,
            "original_alpha": self.alpha,
            "adjusted_alpha": adjusted_alpha,
            "p_values": p_values,
            "significant": significant,
            "n_significant": sum(significant)
        }
    
    def analyze_temperature_sweep(self, results_by_temp: Dict[float, Dict[str, List[float]]]) -> Dict[str, Any]:
        """
        Analyze results across temperature sweep
        
        Tests if SKYT effectiveness varies with temperature.
        
        Args:
            results_by_temp: {temperature: {"r_raw": [...], "r_structural": [...]}}
            
        Returns:
            Dictionary with temperature sweep analysis
        """
        temperatures = sorted(results_by_temp.keys())
        
        # Compare each temperature
        comparisons = {}
        p_values = []
        
        for temp in temperatures:
            r_raw = results_by_temp[temp]["r_raw"]
            r_structural = results_by_temp[temp]["r_structural"]
            
            comparison = self.compare_metrics(r_raw, r_structural, 
                                             metric_name=f"temp_{temp}")
            comparisons[temp] = comparison
            p_values.append(comparison["wilcoxon_test"]["p_value"])
        
        # Bonferroni correction for multiple temperatures
        bonferroni = self.bonferroni_correction(p_values)
        
        # Test if improvement varies with temperature (Kruskal-Wallis)
        improvements_by_temp = []
        for temp in temperatures:
            r_raw = results_by_temp[temp]["r_raw"]
            r_structural = results_by_temp[temp]["r_structural"]
            improvements = np.array(r_structural) - np.array(r_raw)
            improvements_by_temp.append(improvements)
        
        if len(temperatures) > 2:
            kruskal_stat, kruskal_p = stats.kruskal(*improvements_by_temp)
            kruskal_result = {
                "test": "kruskal_wallis",
                "statistic": float(kruskal_stat),
                "p_value": float(kruskal_p),
                "significant": kruskal_p < self.alpha,
                "interpretation": "Improvement varies significantly across temperatures" if kruskal_p < self.alpha else "Improvement consistent across temperatures"
            }
        else:
            kruskal_result = None
        
        return {
            "temperatures": temperatures,
            "comparisons_by_temperature": comparisons,
            "bonferroni_correction": bonferroni,
            "kruskal_wallis": kruskal_result
        }


def format_statistical_report(analysis: Dict[str, Any]) -> str:
    """
    Format statistical analysis results as publication-ready text
    
    Args:
        analysis: Output from StatisticalAnalyzer.compare_metrics()
        
    Returns:
        Formatted text report
    """
    report = []
    report.append(f"Statistical Analysis: {analysis['metric_name']}")
    report.append("=" * 60)
    
    # Descriptive statistics
    report.append("\nDescriptive Statistics:")
    r_raw = analysis['descriptive_statistics']['r_raw']
    r_struct = analysis['descriptive_statistics']['r_structural']
    
    report.append(f"  R_raw:        M={r_raw['mean']:.3f}, SD={r_raw['std']:.3f}, "
                 f"Mdn={r_raw['median']:.3f}, n={r_raw['n']}")
    report.append(f"  R_structural: M={r_struct['mean']:.3f}, SD={r_struct['std']:.3f}, "
                 f"Mdn={r_struct['median']:.3f}, n={r_struct['n']}")
    
    # Wilcoxon test
    report.append("\nWilcoxon Signed-Rank Test:")
    wilcoxon = analysis['wilcoxon_test']
    report.append(f"  W={wilcoxon['statistic']:.2f}, p={wilcoxon['p_value']:.4f}")
    report.append(f"  Result: {'Significant' if wilcoxon['significant'] else 'Not significant'} "
                 f"at α={wilcoxon['alpha']}")
    report.append(f"  Effect: {wilcoxon['effect_direction']} "
                 f"(Mdn Δ={wilcoxon['median_difference']:.3f})")
    
    # Cliff's delta
    report.append("\nEffect Size (Cliff's Delta):")
    cliffs = analysis['cliffs_delta']
    report.append(f"  δ={cliffs['delta']:.3f} ({cliffs['magnitude']})")
    report.append(f"  Interpretation: {cliffs['interpretation']}")
    
    # Confidence intervals
    report.append("\n95% Confidence Intervals (Bootstrap):")
    ci_raw = analysis['confidence_intervals']['r_raw']
    ci_struct = analysis['confidence_intervals']['r_structural']
    report.append(f"  R_raw:        [{ci_raw['ci_lower']:.3f}, {ci_raw['ci_upper']:.3f}]")
    report.append(f"  R_structural: [{ci_struct['ci_lower']:.3f}, {ci_struct['ci_upper']:.3f}]")
    
    # Conclusion
    report.append("\nConclusion:")
    report.append(f"  {analysis['conclusion']}")
    
    return "\n".join(report)
