# src/middleware/viz.py
"""
[TODO viz.py]
Goal: plot pre vs post distributions and bar pairs. No code.

1. Generate:
   - pre_vs_post_overlay.png: overlay histograms of d with shared bins.
   - violin_pre.png and violin_post.png by prompt when multiple prompts exist.
   - Bar pairs for R_anchor and P_tau with numeric labels and deltas.
2. Inputs: metrics_summary.csv and distances CSVs.
3. Acceptance: files created under outputs/figs with stable filenames.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from typing import Dict, List
from .schema import DISTANCES_PRE_CSV_PATH, DISTANCES_POST_CSV_PATH, METRICS_CSV_PATH
from .logger import read_csv_records

def generate_all_visualizations() -> None:
    """
    Generate all visualization outputs
    
    Creates:
    - pre_vs_post_overlay.png
    - violin_pre.png  
    - violin_post.png
    - bar_pairs_R_anchor.png
    - bar_pairs_P_tau.png
    """
    # Load data
    pre_distances = read_csv_records(DISTANCES_PRE_CSV_PATH)
    post_distances = read_csv_records(DISTANCES_POST_CSV_PATH)
    metrics = read_csv_records(METRICS_CSV_PATH)
    
    if not pre_distances and not post_distances:
        print("No distance data available for visualization")
        return
    
    # Generate visualizations
    generate_overlay_histogram(pre_distances, post_distances)
    generate_violin_plots(pre_distances, post_distances)
    generate_bar_pairs(metrics)
    
    print("All visualizations generated in outputs/figs/")

def generate_overlay_histogram(pre_distances: List[Dict], post_distances: List[Dict]) -> None:
    """
    Generate overlay histogram of pre vs post distances
    
    Args:
        pre_distances: Pre-repair distance records
        post_distances: Post-repair distance records
    """
    import os
    
    # Extract distance values
    pre_d = [float(r["d"]) for r in pre_distances if "d" in r]
    post_d = [float(r["d"]) for r in post_distances if "d" in r]
    
    if not pre_d and not post_d:
        return
    
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Shared bins for overlay
    all_distances = pre_d + post_d
    bins = np.linspace(0, 1, 21)  # 20 bins from 0 to 1
    
    # Plot histograms
    if pre_d:
        plt.hist(pre_d, bins=bins, alpha=0.7, label=f'Pre-repair (n={len(pre_d)})', 
                color='red', density=True)
    
    if post_d:
        plt.hist(post_d, bins=bins, alpha=0.7, label=f'Post-repair (n={len(post_d)})', 
                color='blue', density=True)
    
    # Formatting
    plt.xlabel('Distance to Canon')
    plt.ylabel('Density')
    plt.title('Pre vs Post-Repair Distance Distribution')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 1)
    
    # Save
    output_path = "outputs/figs/pre_vs_post_overlay.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def generate_violin_plots(pre_distances: List[Dict], post_distances: List[Dict]) -> None:
    """
    Generate violin plots by prompt for pre and post distances
    
    Args:
        pre_distances: Pre-repair distance records
        post_distances: Post-repair distance records
    """
    import os
    
    # Group by prompt_id
    pre_by_prompt = {}
    for r in pre_distances:
        prompt_id = r.get("prompt_id", "unknown")
        if prompt_id not in pre_by_prompt:
            pre_by_prompt[prompt_id] = []
        pre_by_prompt[prompt_id].append(float(r["d"]))
    
    post_by_prompt = {}
    for r in post_distances:
        prompt_id = r.get("prompt_id", "unknown")
        if prompt_id not in post_by_prompt:
            post_by_prompt[prompt_id] = []
        post_by_prompt[prompt_id].append(float(r["d"]))
    
    # Generate pre violin plot
    if pre_by_prompt:
        _create_violin_plot(pre_by_prompt, "Pre-Repair Distance by Prompt", 
                           "outputs/figs/violin_pre.png")
    
    # Generate post violin plot
    if post_by_prompt:
        _create_violin_plot(post_by_prompt, "Post-Repair Distance by Prompt", 
                           "outputs/figs/violin_post.png")

def _create_violin_plot(data_by_prompt: Dict[str, List[float]], title: str, output_path: str) -> None:
    """
    Create violin plot for distance data grouped by prompt
    
    Args:
        data_by_prompt: Dict mapping prompt_id to list of distances
        title: Plot title
        output_path: Output file path
    """
    import os
    
    if len(data_by_prompt) < 2:
        # Skip violin plot if only one prompt
        return
    
    # Prepare data for seaborn
    plot_data = []
    for prompt_id, distances in data_by_prompt.items():
        for d in distances:
            plot_data.append({"prompt_id": prompt_id, "distance": d})
    
    if not plot_data:
        return
    
    df = pd.DataFrame(plot_data)
    
    # Create violin plot
    plt.figure(figsize=(12, 6))
    sns.violinplot(data=df, x="prompt_id", y="distance")
    plt.title(title)
    plt.xlabel("Prompt ID")
    plt.ylabel("Distance to Canon")
    plt.xticks(rotation=45)
    plt.ylim(0, 1)
    plt.grid(True, alpha=0.3)
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def generate_bar_pairs(metrics: List[Dict]) -> None:
    """
    Generate bar pair plots for R_anchor and P_tau with deltas
    
    Args:
        metrics: Metrics summary records
    """
    if not metrics:
        return
    
    # Generate R_anchor bar pairs
    _create_bar_pairs(
        metrics, "R_anchor", "delta_R_anchor",
        "R_anchor: Raw vs Canon Repeatability",
        "outputs/figs/bar_pairs_R_anchor.png"
    )
    
    # Generate P_tau bar pairs
    _create_bar_pairs(
        metrics, "P_tau_post", "delta_P_tau", 
        "P_tau: Pre vs Post Repair Success Rate",
        "outputs/figs/bar_pairs_P_tau.png"
    )

def _create_bar_pairs(metrics: List[Dict], metric_key: str, delta_key: str, 
                     title: str, output_path: str) -> None:
    """
    Create bar pair plot with delta annotations
    
    Args:
        metrics: Metrics records
        metric_key: Key for main metric value
        delta_key: Key for delta value
        title: Plot title
        output_path: Output file path
    """
    import os
    
    # Extract data
    prompt_ids = []
    values = []
    deltas = []
    
    for record in metrics:
        prompt_ids.append(record.get("prompt_id", "unknown"))
        values.append(float(record.get(metric_key, 0)))
        deltas.append(float(record.get(delta_key, 0)))
    
    if not prompt_ids:
        return
    
    # Create bar plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x_pos = np.arange(len(prompt_ids))
    bars = ax.bar(x_pos, values, alpha=0.7, color='steelblue')
    
    # Add delta annotations
    for i, (bar, delta) in enumerate(zip(bars, deltas)):
        height = bar.get_height()
        ax.annotate(f'Δ={delta:.3f}',
                   xy=(bar.get_x() + bar.get_width() / 2, height),
                   xytext=(0, 3),  # 3 points vertical offset
                   textcoords="offset points",
                   ha='center', va='bottom',
                   fontsize=9)
    
    # Formatting
    ax.set_xlabel('Prompt ID')
    ax.set_ylabel(metric_key.replace('_', ' ').title())
    ax.set_title(title)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(prompt_ids, rotation=45)
    ax.set_ylim(0, 1.1)
    ax.grid(True, alpha=0.3)
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def create_summary_dashboard(metrics: List[Dict]) -> None:
    """
    Create comprehensive dashboard with all key metrics
    
    Args:
        metrics: Metrics summary records
    """
    import os
    
    if not metrics:
        return
    
    # Create 2x2 subplot layout
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    prompt_ids = [r.get("prompt_id", "unknown") for r in metrics]
    x_pos = np.arange(len(prompt_ids))
    
    # Plot 1: R_raw vs R_anchor
    r_raw = [float(r.get("R_raw", 0)) for r in metrics]
    r_anchor = [float(r.get("R_anchor", 0)) for r in metrics]
    
    width = 0.35
    ax1.bar(x_pos - width/2, r_raw, width, label='R_raw', alpha=0.7)
    ax1.bar(x_pos + width/2, r_anchor, width, label='R_anchor', alpha=0.7)
    ax1.set_title('Raw vs Anchor Repeatability')
    ax1.set_ylabel('Repeatability')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(prompt_ids, rotation=45)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Mean distances
    mu_pre = [float(r.get("mu_pre", 0)) for r in metrics]
    mu_post = [float(r.get("mu_post", 0)) for r in metrics]
    
    ax2.bar(x_pos - width/2, mu_pre, width, label='μ_pre', alpha=0.7)
    ax2.bar(x_pos + width/2, mu_post, width, label='μ_post', alpha=0.7)
    ax2.set_title('Mean Distance Pre vs Post')
    ax2.set_ylabel('Mean Distance')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(prompt_ids, rotation=45)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: P_tau comparison
    p_tau_pre = [float(r.get("P_tau_pre", 0)) for r in metrics]
    p_tau_post = [float(r.get("P_tau_post", 0)) for r in metrics]
    
    ax3.bar(x_pos - width/2, p_tau_pre, width, label='P_τ_pre', alpha=0.7)
    ax3.bar(x_pos + width/2, p_tau_post, width, label='P_τ_post', alpha=0.7)
    ax3.set_title('P_tau Pre vs Post Repair')
    ax3.set_ylabel('P_tau')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(prompt_ids, rotation=45)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Rescue rate
    rescue_rates = [float(r.get("rescue_rate", 0)) for r in metrics]
    
    bars = ax4.bar(x_pos, rescue_rates, alpha=0.7, color='green')
    ax4.set_title('Rescue Rate by Prompt')
    ax4.set_ylabel('Rescue Rate')
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(prompt_ids, rotation=45)
    ax4.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, rate in zip(bars, rescue_rates):
        height = bar.get_height()
        ax4.annotate(f'{rate:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Save
    output_path = "outputs/figs/summary_dashboard.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
