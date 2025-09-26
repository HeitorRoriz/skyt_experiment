# src/middleware/metrics.py
"""
[TODO metrics.py]
Goal: compute R_raw, R_anchor, mu, P_tau, deltas, rescue_rate. No code.

1. Inputs: outputs/logs/*.csv.
2. Definitions:
   - R_raw: modal mass of pre signatures within a prompt set.
   - R_anchor: fraction of post with d=0 relative to the canon.
   - Rescue rate: count(pre d>0 and post d==0) / count(pre all).
   - mu_pre and mu_post: mean d in pre and post.
   - P_tau: fraction with d ≤ tau. Default tau=0.10; allow CLI override.
   - Deltas: post minus pre for anchor, mu, P_tau.
3. Emit metrics_summary.csv with schema from schema.py.
4. Acceptance: deterministic results given same inputs.
"""

import csv
from collections import Counter, defaultdict
from typing import Dict, List, Optional
from .schema import (
    MetricsRecord, METRICS_CSV_PATH, DISTANCES_PRE_CSV_PATH, 
    DISTANCES_POST_CSV_PATH, REPAIRS_CSV_PATH, DEFAULT_TAU, METRICS_CSV_HEADERS
)
from .logger import read_csv_records

def compute_metrics(prompt_id: Optional[str] = None, tau: float = DEFAULT_TAU) -> Dict[str, MetricsRecord]:
    """
    Compute repeatability metrics from logged data
    
    Args:
        prompt_id: Specific prompt to compute metrics for (None for all)
        tau: Threshold for P_tau computation
    
    Returns:
        Dict mapping prompt_id to MetricsRecord
    """
    # Load data from CSV files
    pre_distances = read_csv_records(DISTANCES_PRE_CSV_PATH)
    post_distances = read_csv_records(DISTANCES_POST_CSV_PATH)
    repairs = read_csv_records(REPAIRS_CSV_PATH)
    
    # Group by prompt_id
    pre_by_prompt = _group_by_prompt(pre_distances)
    post_by_prompt = _group_by_prompt(post_distances)
    repairs_by_prompt = _group_by_prompt(repairs)
    
    # Filter to specific prompt if requested
    if prompt_id:
        prompts = [prompt_id] if prompt_id in pre_by_prompt else []
    else:
        prompts = set(pre_by_prompt.keys()) | set(post_by_prompt.keys())
    
    metrics = {}
    
    for pid in prompts:
        pre_records = pre_by_prompt.get(pid, [])
        post_records = post_by_prompt.get(pid, [])
        repair_records = repairs_by_prompt.get(pid, [])
        
        if not pre_records:
            continue  # Skip prompts with no pre-distance data
        
        # Compute metrics for this prompt
        metrics[pid] = _compute_prompt_metrics(
            pid, pre_records, post_records, repair_records, tau
        )
    
    return metrics

def write_metrics_summary(metrics: Dict[str, MetricsRecord]) -> None:
    """
    Write metrics summary to CSV file
    
    Args:
        metrics: Dict of prompt_id -> MetricsRecord
    """
    import os
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(METRICS_CSV_PATH), exist_ok=True)
    
    with open(METRICS_CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=METRICS_CSV_HEADERS)
        writer.writeheader()
        
        for prompt_id, record in metrics.items():
            row = {
                "prompt_id": record.prompt_id,
                "N": record.N,
                "R_raw": record.R_raw,
                "R_anchor": record.R_anchor,
                "mu_pre": record.mu_pre,
                "mu_post": record.mu_post,
                "delta_R_anchor": record.delta_R_anchor,
                "delta_mu": record.delta_mu,
                "P_tau_pre": record.P_tau_pre,
                "P_tau_post": record.P_tau_post,
                "delta_P_tau": record.delta_P_tau,
                "rescue_rate": record.rescue_rate,
                "tau": record.tau
            }
            writer.writerow(row)

def _group_by_prompt(records: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group records by prompt_id
    
    Args:
        records: List of record dicts
    
    Returns:
        Dict mapping prompt_id to list of records
    """
    grouped = defaultdict(list)
    for record in records:
        prompt_id = record.get("prompt_id")
        if prompt_id:
            grouped[prompt_id].append(record)
    return dict(grouped)

def _compute_prompt_metrics(prompt_id: str, pre_records: List[Dict], 
                           post_records: List[Dict], repair_records: List[Dict],
                           tau: float) -> MetricsRecord:
    """
    Compute metrics for a single prompt
    
    Args:
        prompt_id: Prompt identifier
        pre_records: Pre-repair distance records
        post_records: Post-repair distance records
        repair_records: Repair operation records
        tau: Threshold for P_tau
    
    Returns:
        MetricsRecord with computed metrics
    """
    N = len(pre_records)
    
    # Extract signatures and distances
    pre_signatures = [r["signature"] for r in pre_records]
    pre_distances = [float(r["d"]) for r in pre_records]
    
    post_signatures = [r["signature"] for r in post_records if r["prompt_id"] == prompt_id]
    post_distances = [float(r["d"]) for r in post_records if r["prompt_id"] == prompt_id]
    
    # R_raw: modal mass of pre signatures (byte-identical)
    if pre_signatures:
        signature_counts = Counter(pre_signatures)
        most_common_count = signature_counts.most_common(1)[0][1]
        R_raw = most_common_count / len(pre_signatures)
    else:
        R_raw = 0.0
    
    # R_anchor: fraction of post with d=0 (exact canon match)
    if post_distances:
        exact_matches = sum(1 for d in post_distances if d == 0.0)
        R_anchor = exact_matches / len(post_distances)
    else:
        R_anchor = 0.0
    
    # Mean distances
    mu_pre = sum(pre_distances) / len(pre_distances) if pre_distances else 0.0
    mu_post = sum(post_distances) / len(post_distances) if post_distances else 0.0
    
    # P_tau: fraction with d ≤ tau
    P_tau_pre = sum(1 for d in pre_distances if d <= tau) / len(pre_distances) if pre_distances else 0.0
    P_tau_post = sum(1 for d in post_distances if d <= tau) / len(post_distances) if post_distances else 0.0
    
    # Rescue rate: count(pre d>0 and post d==0) / count(pre all)
    rescue_rate = _compute_rescue_rate(pre_records, post_records, repair_records)
    
    # Delta metrics
    # Note: R_anchor_pre is 0 by definition (no canon exists pre-repair)
    delta_R_anchor = R_anchor - 0.0
    delta_mu = mu_post - mu_pre
    delta_P_tau = P_tau_post - P_tau_pre
    
    return MetricsRecord(
        prompt_id=prompt_id,
        N=N,
        R_raw=R_raw,
        R_anchor=R_anchor,
        mu_pre=mu_pre,
        mu_post=mu_post,
        delta_R_anchor=delta_R_anchor,
        delta_mu=delta_mu,
        P_tau_pre=P_tau_pre,
        P_tau_post=P_tau_post,
        delta_P_tau=delta_P_tau,
        rescue_rate=rescue_rate,
        tau=tau
    )

def _compute_rescue_rate(pre_records: List[Dict], post_records: List[Dict], 
                        repair_records: List[Dict]) -> float:
    """
    Compute rescue rate: fraction of samples that went from d>0 to d=0
    
    Args:
        pre_records: Pre-repair distance records
        post_records: Post-repair distance records
        repair_records: Repair operation records
    
    Returns:
        Rescue rate [0,1]
    """
    if not pre_records:
        return 0.0
    
    # Match pre and post records by run_id and sample_id
    pre_lookup = {(r["run_id"], r["sample_id"]): float(r["d"]) for r in pre_records}
    post_lookup = {(r["run_id"], r["sample_id"]): float(r["d"]) for r in post_records}
    
    rescued_count = 0
    total_count = len(pre_records)
    
    for (run_id, sample_id), pre_d in pre_lookup.items():
        post_d = post_lookup.get((run_id, sample_id))
        
        if post_d is not None and pre_d > 0.0 and post_d == 0.0:
            rescued_count += 1
    
    return rescued_count / total_count if total_count > 0 else 0.0

def print_metrics_summary(metrics: Dict[str, MetricsRecord]) -> None:
    """
    Print compact metrics summary to stdout
    
    Args:
        metrics: Dict of prompt_id -> MetricsRecord
    """
    if not metrics:
        print("No metrics to display")
        return
    
    print("\nSKYT Middleware Metrics Summary")
    print("=" * 50)
    
    # Header
    print(f"{'Prompt':<15} {'N':<3} {'R_raw':<6} {'R_anchor':<8} {'μ_pre':<6} {'μ_post':<6} {'Rescue%':<7}")
    print("-" * 50)
    
    # Metrics rows
    for prompt_id, record in sorted(metrics.items()):
        print(f"{prompt_id:<15} {record.N:<3} {record.R_raw:<6.3f} {record.R_anchor:<8.3f} "
              f"{record.mu_pre:<6.3f} {record.mu_post:<6.3f} {record.rescue_rate*100:<7.1f}")
    
    # Summary statistics
    if len(metrics) > 1:
        avg_R_raw = sum(m.R_raw for m in metrics.values()) / len(metrics)
        avg_R_anchor = sum(m.R_anchor for m in metrics.values()) / len(metrics)
        avg_rescue = sum(m.rescue_rate for m in metrics.values()) / len(metrics)
        
        print("-" * 50)
        print(f"{'AVERAGE':<15} {'':<3} {avg_R_raw:<6.3f} {avg_R_anchor:<8.3f} "
              f"{'':<6} {'':<6} {avg_rescue*100:<7.1f}")
    
    print()
