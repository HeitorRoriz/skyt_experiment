# src/bell_curve_analysis.py
"""
Bell curve analysis and plotting for SKYT distance variance
Visualizes the distribution of code distances from canonical anchor
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from typing import List, Dict, Any, Optional
from scipy import stats
import os


class BellCurveAnalyzer:
    """
    Analyzes and plots bell curve distributions of code distances from canon
    """
    
    def __init__(self, output_dir: str = "outputs/analysis"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set plotting style
        plt.style.use('default')
        sns.set_palette("husl")
    
    def plot_distance_distribution(self, distances: List[float], 
                                 experiment_id: str,
                                 title: Optional[str] = None) -> Dict[str, Any]:
        """
        Plot bell curve distribution of distances from canon
        
        Args:
            distances: List of distance values
            experiment_id: Experiment identifier for filename
            title: Optional plot title
            
        Returns:
            Analysis results with statistics and plot path
        """
        if not distances:
            return {"error": "No distances provided"}
        
        # Calculate statistics
        mean_dist = np.mean(distances)
        std_dist = np.std(distances)
        median_dist = np.median(distances)
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Histogram with fitted normal curve
        ax1.hist(distances, bins=20, density=True, alpha=0.7, 
                color='skyblue', edgecolor='black', label='Observed')
        
        # Fit and plot normal distribution
        x_range = np.linspace(min(distances), max(distances), 100)
        normal_fit = stats.norm.pdf(x_range, mean_dist, std_dist)
        ax1.plot(x_range, normal_fit, 'r-', linewidth=2, 
                label=f'Normal fit (μ={mean_dist:.3f}, σ={std_dist:.3f})')
        
        ax1.axvline(mean_dist, color='red', linestyle='--', alpha=0.8, label=f'Mean: {mean_dist:.3f}')
        ax1.axvline(median_dist, color='orange', linestyle='--', alpha=0.8, label=f'Median: {median_dist:.3f}')
        
        ax1.set_xlabel('Distance from Canon')
        ax1.set_ylabel('Density')
        ax1.set_title(title or f'Distance Distribution - {experiment_id}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Box plot and violin plot
        ax2.boxplot(distances, vert=True, patch_artist=True,
                   boxprops=dict(facecolor='lightblue', alpha=0.7))
        ax2.set_ylabel('Distance from Canon')
        ax2.set_title('Distance Distribution Summary')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        plot_path = os.path.join(self.output_dir, f'bell_curve_{experiment_id}.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Statistical tests
        normality_test = stats.shapiro(distances)
        
        # Calculate percentiles
        percentiles = {
            '25th': np.percentile(distances, 25),
            '50th': np.percentile(distances, 50),
            '75th': np.percentile(distances, 75),
            '90th': np.percentile(distances, 90),
            '95th': np.percentile(distances, 95)
        }
        
        return {
            "plot_path": plot_path,
            "statistics": {
                "mean": mean_dist,
                "std": std_dist,
                "median": median_dist,
                "min": np.min(distances),
                "max": np.max(distances),
                "variance": np.var(distances),
                "skewness": stats.skew(distances),
                "kurtosis": stats.kurtosis(distances),
                "percentiles": percentiles
            },
            "normality_test": {
                "statistic": normality_test.statistic,
                "p_value": normality_test.pvalue,
                "is_normal": normality_test.pvalue > 0.05
            },
            "sample_size": len(distances)
        }
    
    def compare_distributions(self, distance_sets: Dict[str, List[float]], 
                            comparison_title: str = "Distribution Comparison") -> Dict[str, Any]:
        """
        Compare multiple distance distributions
        
        Args:
            distance_sets: Dictionary mapping labels to distance lists
            comparison_title: Title for the comparison plot
            
        Returns:
            Comparison analysis results
        """
        if not distance_sets:
            return {"error": "No distance sets provided"}
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Overlaid histograms
        ax1 = axes[0, 0]
        colors = plt.cm.Set3(np.linspace(0, 1, len(distance_sets)))
        
        for i, (label, distances) in enumerate(distance_sets.items()):
            if distances:
                ax1.hist(distances, bins=15, alpha=0.6, label=label, 
                        color=colors[i], density=True)
        
        ax1.set_xlabel('Distance from Canon')
        ax1.set_ylabel('Density')
        ax1.set_title('Overlaid Distributions')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Box plots
        ax2 = axes[0, 1]
        box_data = [distances for distances in distance_sets.values() if distances]
        box_labels = [label for label, distances in distance_sets.items() if distances]
        
        if box_data:
            ax2.boxplot(box_data, labels=box_labels, patch_artist=True)
            ax2.set_ylabel('Distance from Canon')
            ax2.set_title('Distribution Comparison')
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(True, alpha=0.3)
        
        # Plot 3: Violin plots
        ax3 = axes[1, 0]
        if box_data:
            parts = ax3.violinplot(box_data, positions=range(1, len(box_data) + 1))
            ax3.set_xticks(range(1, len(box_data) + 1))
            ax3.set_xticklabels(box_labels, rotation=45)
            ax3.set_ylabel('Distance from Canon')
            ax3.set_title('Violin Plot Comparison')
            ax3.grid(True, alpha=0.3)
        
        # Plot 4: Statistical summary
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        # Create statistical summary table
        summary_text = "Statistical Summary:\n\n"
        for label, distances in distance_sets.items():
            if distances:
                mean_val = np.mean(distances)
                std_val = np.std(distances)
                summary_text += f"{label}:\n"
                summary_text += f"  Mean: {mean_val:.3f}\n"
                summary_text += f"  Std:  {std_val:.3f}\n"
                summary_text += f"  N:    {len(distances)}\n\n"
        
        ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace')
        
        plt.tight_layout()
        
        # Save comparison plot
        comparison_path = os.path.join(self.output_dir, 'distribution_comparison.png')
        plt.savefig(comparison_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Statistical comparisons
        comparisons = {}
        labels = list(distance_sets.keys())
        
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                label1, label2 = labels[i], labels[j]
                dist1, dist2 = distance_sets[label1], distance_sets[label2]
                
                if dist1 and dist2:
                    # Mann-Whitney U test (non-parametric)
                    u_stat, u_p = stats.mannwhitneyu(dist1, dist2, alternative='two-sided')
                    
                    # Kolmogorov-Smirnov test
                    ks_stat, ks_p = stats.ks_2samp(dist1, dist2)
                    
                    comparisons[f"{label1}_vs_{label2}"] = {
                        "mann_whitney": {"statistic": u_stat, "p_value": u_p},
                        "kolmogorov_smirnov": {"statistic": ks_stat, "p_value": ks_p},
                        "significantly_different": min(u_p, ks_p) < 0.05
                    }
        
        return {
            "comparison_plot_path": comparison_path,
            "statistical_comparisons": comparisons,
            "summary_statistics": {
                label: {
                    "mean": np.mean(distances),
                    "std": np.std(distances),
                    "median": np.median(distances),
                    "n": len(distances)
                } for label, distances in distance_sets.items() if distances
            }
        }
    
    def analyze_variance_trends(self, experiment_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze trends in distance variance across experiments
        
        Args:
            experiment_results: List of experiment results with distance data
            
        Returns:
            Trend analysis results
        """
        if not experiment_results:
            return {"error": "No experiment results provided"}
        
        # Extract variance data
        variances = []
        means = []
        experiment_ids = []
        
        for result in experiment_results:
            distance_data = result.get("distance_variance", {})
            if "variance" in distance_data and "mean" in distance_data:
                variances.append(distance_data["variance"])
                means.append(distance_data["mean"])
                experiment_ids.append(result.get("experiment_id", "unknown"))
        
        if not variances:
            return {"error": "No variance data found"}
        
        # Create trend plots
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
        
        # Plot 1: Variance over experiments
        ax1.plot(range(len(variances)), variances, 'o-', linewidth=2, markersize=6)
        ax1.set_xlabel('Experiment Index')
        ax1.set_ylabel('Distance Variance')
        ax1.set_title('Variance Trend Across Experiments')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Mean distance over experiments
        ax2.plot(range(len(means)), means, 's-', linewidth=2, markersize=6, color='orange')
        ax2.set_xlabel('Experiment Index')
        ax2.set_ylabel('Mean Distance')
        ax2.set_title('Mean Distance Trend')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Variance vs Mean scatter
        ax3.scatter(means, variances, alpha=0.7, s=60)
        ax3.set_xlabel('Mean Distance')
        ax3.set_ylabel('Distance Variance')
        ax3.set_title('Variance vs Mean Relationship')
        ax3.grid(True, alpha=0.3)
        
        # Add trend line
        if len(means) > 1:
            z = np.polyfit(means, variances, 1)
            p = np.poly1d(z)
            ax3.plot(means, p(means), "r--", alpha=0.8)
        
        plt.tight_layout()
        
        # Save trend plot
        trend_path = os.path.join(self.output_dir, 'variance_trends.png')
        plt.savefig(trend_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Calculate trend statistics
        variance_trend = np.polyfit(range(len(variances)), variances, 1)[0] if len(variances) > 1 else 0
        mean_trend = np.polyfit(range(len(means)), means, 1)[0] if len(means) > 1 else 0
        
        # Correlation between mean and variance
        correlation = np.corrcoef(means, variances)[0, 1] if len(means) > 1 else 0
        
        return {
            "trend_plot_path": trend_path,
            "variance_trend_slope": variance_trend,
            "mean_trend_slope": mean_trend,
            "mean_variance_correlation": correlation,
            "overall_statistics": {
                "mean_variance": np.mean(variances),
                "std_variance": np.std(variances),
                "mean_distance": np.mean(means),
                "std_distance": np.std(means)
            },
            "experiment_count": len(experiment_results)
        }
    
    def create_research_summary_plot(self, comprehensive_results: Dict[str, Any]) -> str:
        """
        Create comprehensive summary plot for research hypothesis
        
        Args:
            comprehensive_results: Complete experimental results
            
        Returns:
            Path to summary plot
        """
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('SKYT Repeatability Research Summary\n"Can prompt contracts and SKYT improve LLM-generated code repeatability?"', 
                    fontsize=16, fontweight='bold')
        
        # Extract data for plotting
        r_raw_values = comprehensive_results.get("R_raw_values", [])
        r_behavioral_values = comprehensive_results.get("R_behavioral_values", [])
        r_structural_values = comprehensive_results.get("R_structural_values", [])
        distances = comprehensive_results.get("all_distances", [])
        
        # Plot 1: Three-tier repeatability comparison
        ax1 = axes[0, 0]
        metrics = ['R_raw', 'R_behavioral', 'R_structural']
        values = [
            np.mean(r_raw_values) if r_raw_values else 0,
            np.mean(r_behavioral_values) if r_behavioral_values else 0,
            np.mean(r_structural_values) if r_structural_values else 0
        ]
        
        bars = ax1.bar(metrics, values, color=['lightcoral', 'lightblue', 'lightgreen'])
        ax1.set_ylabel('Repeatability Score')
        ax1.set_title('Three-Tier Repeatability Comparison')
        ax1.set_ylim(0, 1)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.3f}', ha='center', va='bottom')
        
        # Plot 2: Distance distribution (bell curve)
        ax2 = axes[0, 1]
        if distances:
            ax2.hist(distances, bins=20, density=True, alpha=0.7, color='skyblue')
            mean_dist = np.mean(distances)
            std_dist = np.std(distances)
            x_range = np.linspace(min(distances), max(distances), 100)
            normal_fit = stats.norm.pdf(x_range, mean_dist, std_dist)
            ax2.plot(x_range, normal_fit, 'r-', linewidth=2)
            ax2.axvline(mean_dist, color='red', linestyle='--', alpha=0.8)
        
        ax2.set_xlabel('Distance from Canon')
        ax2.set_ylabel('Density')
        ax2.set_title('Distance Variance (Bell Curve)')
        
        # Plot 3: Improvement metrics
        ax3 = axes[0, 2]
        if r_raw_values and r_behavioral_values and r_structural_values:
            improvements = [
                np.mean(r_behavioral_values) - np.mean(r_raw_values),
                np.mean(r_structural_values) - np.mean(r_raw_values)
            ]
            improvement_labels = ['Behavioral\nImprovement', 'Structural\nImprovement']
            
            bars = ax3.bar(improvement_labels, improvements, 
                          color=['orange', 'green'], alpha=0.7)
            ax3.set_ylabel('Improvement over R_raw')
            ax3.set_title('SKYT Effectiveness')
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            # Add value labels
            for bar, value in zip(bars, improvements):
                ax3.text(bar.get_x() + bar.get_width()/2, 
                        bar.get_height() + (0.01 if value >= 0 else -0.03),
                        f'{value:.3f}', ha='center', 
                        va='bottom' if value >= 0 else 'top')
        
        # Plot 4: Repeatability over time/experiments
        ax4 = axes[1, 0]
        if r_raw_values:
            x_range = range(len(r_raw_values))
            ax4.plot(x_range, r_raw_values, 'o-', label='R_raw', alpha=0.7)
            if r_behavioral_values:
                ax4.plot(x_range, r_behavioral_values, 's-', label='R_behavioral', alpha=0.7)
            if r_structural_values:
                ax4.plot(x_range, r_structural_values, '^-', label='R_structural', alpha=0.7)
            
            ax4.set_xlabel('Experiment Index')
            ax4.set_ylabel('Repeatability Score')
            ax4.set_title('Repeatability Trends')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
        
        # Plot 5: Statistical summary
        ax5 = axes[1, 1]
        ax5.axis('off')
        
        summary_text = "Research Findings:\n\n"
        if values:
            summary_text += f"Raw Repeatability:        {values[0]:.3f}\n"
            summary_text += f"Behavioral Repeatability: {values[1]:.3f}\n"
            summary_text += f"Structural Repeatability: {values[2]:.3f}\n\n"
            
            if values[2] > values[0]:
                summary_text += f"✓ SKYT improves repeatability by {values[2] - values[0]:.3f}\n"
            else:
                summary_text += f"✗ No significant improvement detected\n"
        
        if distances:
            summary_text += f"\nDistance Statistics:\n"
            summary_text += f"Mean distance: {np.mean(distances):.3f}\n"
            summary_text += f"Std deviation: {np.std(distances):.3f}\n"
            summary_text += f"Variance: {np.var(distances):.3f}\n"
        
        ax5.text(0.1, 0.9, summary_text, transform=ax5.transAxes,
                fontsize=11, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))
        
        # Plot 6: Hypothesis conclusion
        ax6 = axes[1, 2]
        ax6.axis('off')
        
        # Determine conclusion based on results
        if values and values[2] > values[0] + 0.1:  # Significant improvement threshold
            conclusion = "HYPOTHESIS SUPPORTED"
            conclusion_color = "green"
            details = "SKYT demonstrates significant\nimprovement in code repeatability\nthrough contract-driven\ncanonicalization."
        elif values and values[2] > values[0]:
            conclusion = "PARTIAL SUPPORT"
            conclusion_color = "orange"
            details = "SKYT shows modest improvement\nin repeatability. Further\noptimization may be needed."
        else:
            conclusion = "HYPOTHESIS NOT SUPPORTED"
            conclusion_color = "red"
            details = "No significant improvement\ndetected. Current approach\nmay need revision."
        
        ax6.text(0.5, 0.7, conclusion, transform=ax6.transAxes,
                fontsize=14, fontweight='bold', ha='center',
                color=conclusion_color,
                bbox=dict(boxstyle="round,pad=0.5", facecolor=conclusion_color, alpha=0.2))
        
        ax6.text(0.5, 0.3, details, transform=ax6.transAxes,
                fontsize=10, ha='center', va='center')
        
        plt.tight_layout()
        
        # Save research summary
        summary_path = os.path.join(self.output_dir, 'research_summary.png')
        plt.savefig(summary_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return summary_path
