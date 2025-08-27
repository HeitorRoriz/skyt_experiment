# src/analyze.py
"""
Produces histograms of raw vs. canonical outputs
"""

import matplotlib.pyplot as plt
import os
from typing import List, Dict, Optional
from collections import Counter

from .log import ExperimentLogger, RunLog
from .metrics import hash_output


def create_output_histograms(logs: List[RunLog], 
                           output_dir: str = "analysis",
                           prompt_id: Optional[str] = None):
    """
    Create histograms comparing raw vs canonical output distributions
    
    Args:
        logs: List of run logs to analyze
        output_dir: Directory to save histogram plots
        prompt_id: Optional prompt ID for filtering and naming
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Filter logs if prompt_id specified
    if prompt_id:
        logs = [log for log in logs if log.prompt_id == prompt_id]
    
    if not logs:
        print("No logs found for analysis")
        return
    
    # Extract raw and canonical outputs
    raw_outputs = [log.raw_code for log in logs if log.raw_code]
    canonical_outputs = [log.canonical_code for log in logs if log.canonical_code]
    
    # Generate hashes for comparison
    raw_hashes = [hash_output(output)[:8] for output in raw_outputs]  # Short hash for display
    canonical_hashes = [hash_output(output)[:8] for output in canonical_outputs]
    
    # Count occurrences
    raw_counts = Counter(raw_hashes)
    canonical_counts = Counter(canonical_hashes)
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Raw outputs histogram
    if raw_counts:
        ax1.bar(range(len(raw_counts)), list(raw_counts.values()))
        ax1.set_title(f'Raw Output Distribution\n({len(raw_outputs)} outputs, {len(raw_counts)} unique)')
        ax1.set_xlabel('Output Hash (shortened)')
        ax1.set_ylabel('Frequency')
        ax1.set_xticks(range(len(raw_counts)))
        ax1.set_xticklabels(list(raw_counts.keys()), rotation=45, ha='right')
        
        # Add frequency labels on bars
        for i, count in enumerate(raw_counts.values()):
            ax1.text(i, count + 0.1, str(count), ha='center', va='bottom')
    
    # Canonical outputs histogram
    if canonical_counts:
        ax2.bar(range(len(canonical_counts)), list(canonical_counts.values()), color='orange')
        ax2.set_title(f'Canonical Output Distribution\n({len(canonical_outputs)} outputs, {len(canonical_counts)} unique)')
        ax2.set_xlabel('Output Hash (shortened)')
        ax2.set_ylabel('Frequency')
        ax2.set_xticks(range(len(canonical_counts)))
        ax2.set_xticklabels(list(canonical_counts.keys()), rotation=45, ha='right')
        
        # Add frequency labels on bars
        for i, count in enumerate(canonical_counts.values()):
            ax2.text(i, count + 0.1, str(count), ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Save plot
    filename = f"output_histogram_{prompt_id}.png" if prompt_id else "output_histogram_all.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Histogram saved: {filepath}")
    
    # Print summary statistics
    print(f"\nAnalysis Summary:")
    print(f"Raw outputs: {len(raw_outputs)} total, {len(raw_counts)} unique")
    print(f"Canonical outputs: {len(canonical_outputs)} total, {len(canonical_counts)} unique")
    
    if raw_counts:
        max_raw_freq = max(raw_counts.values())
        raw_repeatability = max_raw_freq / len(raw_outputs)
        print(f"Raw repeatability: {raw_repeatability:.3f} ({max_raw_freq}/{len(raw_outputs)})")
    
    if canonical_counts:
        max_canon_freq = max(canonical_counts.values())
        canon_repeatability = max_canon_freq / len(logs)  # Use total logs as denominator
        print(f"Canonical repeatability: {canon_repeatability:.3f} ({max_canon_freq}/{len(logs)})")


def create_metrics_comparison_plot(results: Dict[str, Dict[str, float]], 
                                 output_dir: str = "analysis"):
    """
    Create comparison plot of metrics across different prompts
    
    Args:
        results: Dictionary mapping prompt_id to metrics dict
        output_dir: Directory to save plots
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if not results:
        print("No results to plot")
        return
    
    # Extract data
    prompt_ids = list(results.keys())
    r_raw_values = [results[pid]['r_raw'] for pid in prompt_ids]
    r_canon_values = [results[pid]['r_canon'] for pid in prompt_ids]
    coverage_values = [results[pid]['canon_coverage'] for pid in prompt_ids]
    delta_values = [results[pid]['rescue_delta'] for pid in prompt_ids]
    
    # Create subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # R_raw
    ax1.bar(prompt_ids, r_raw_values, color='skyblue')
    ax1.set_title('Raw Repeatability (R_raw)')
    ax1.set_ylabel('Repeatability')
    ax1.set_ylim(0, 1)
    ax1.tick_params(axis='x', rotation=45)
    
    # R_canon
    ax2.bar(prompt_ids, r_canon_values, color='orange')
    ax2.set_title('Canonical Repeatability (R_canon)')
    ax2.set_ylabel('Repeatability')
    ax2.set_ylim(0, 1)
    ax2.tick_params(axis='x', rotation=45)
    
    # Coverage
    ax3.bar(prompt_ids, coverage_values, color='lightgreen')
    ax3.set_title('Canonicalization Coverage')
    ax3.set_ylabel('Coverage')
    ax3.set_ylim(0, 1)
    ax3.tick_params(axis='x', rotation=45)
    
    # Delta
    ax4.bar(prompt_ids, delta_values, color='lightcoral')
    ax4.set_title('Rescue Delta (R_canon - R_raw)')
    ax4.set_ylabel('Delta')
    ax4.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # Save plot
    filepath = os.path.join(output_dir, "metrics_comparison.png")
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Metrics comparison plot saved: {filepath}")


def analyze_experiment_results(log_file: str, output_dir: str = "analysis"):
    """
    Main analysis function - creates all histograms and plots
    
    Args:
        log_file: Path to experiment log CSV file
        output_dir: Directory to save analysis outputs
    """
    print("Analyzing experiment results...")
    
    # Load logs
    logger = ExperimentLogger(log_file)
    all_logs = logger.read_logs()
    
    if not all_logs:
        print("No logs found in file")
        return
    
    # Get unique prompt IDs
    prompt_ids = list(set(log.prompt_id for log in all_logs))
    
    print(f"Found {len(all_logs)} total runs across {len(prompt_ids)} prompts")
    
    # Create histograms for each prompt
    for prompt_id in prompt_ids:
        print(f"\nAnalyzing prompt: {prompt_id}")
        create_output_histograms(all_logs, output_dir, prompt_id)
    
    # Create overall histogram
    print(f"\nAnalyzing all prompts combined")
    create_output_histograms(all_logs, output_dir, None)
    
    print(f"\nAnalysis complete. Results saved to: {output_dir}")


if __name__ == "__main__":
    # Default analysis
    log_file = os.path.join("results", "experiment_log.csv")
    analyze_experiment_results(log_file)
