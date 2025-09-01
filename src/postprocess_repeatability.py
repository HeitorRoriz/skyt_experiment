# src/postprocess_repeatability.py
"""
Repeatability metrics and reports for SKYT pipeline
Computes R_raw, R_anchor, mean_distance, variance_distance, and outlier_rate from execution records
"""

import csv
import os
import numpy as np
from collections import Counter, defaultdict
from typing import Dict, Any, List
from .log import read_execution_records


def compute_repeatability_metrics(results_path: str = "outputs/results.csv") -> Dict[str, Any]:
    """
    Compute repeatability metrics from execution records
    
    Args:
        results_path: Path to results CSV file
    
    Returns:
        Dict with repeatability metrics per prompt_id
    """
    records = read_execution_records(results_path)
    
    if not records:
        return {}
    
    # Group records by prompt_id and temperature
    grouped = defaultdict(lambda: defaultdict(list))
    
    for record in records:
        prompt_id = record.get("prompt_id", "unknown")
        temperature = record.get("temperature", "0.0")
        grouped[prompt_id][temperature].append(record)
    
    metrics = {}
    
    for prompt_id, temp_groups in grouped.items():
        prompt_metrics = {}
        
        for temperature, temp_records in temp_groups.items():
            temp_metrics = _compute_temp_metrics(temp_records)
            prompt_metrics[f"T{temperature}"] = temp_metrics
        
        metrics[prompt_id] = prompt_metrics
    
    return metrics


def _compute_temp_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute metrics for a specific temperature group with anchor-based variance"""
    if not records:
        return {}
    
    # Extract hashes and signatures
    raw_hashes = [r.get("raw_hash", "") for r in records if r.get("raw_hash")]
    canon_signatures = [r.get("canon_signature", "") for r in records if r.get("canon_signature")]
    
    # Extract anchor-specific metrics
    anchor_hits = [str(r.get("anchor_hit", "false")).lower() == "true" for r in records]
    distances = [float(r.get("distance", 1.0)) for r in records if r.get("distance") is not None]
    
    # Compute R_raw (modal probability mass on raw_hash)
    raw_counter = Counter(raw_hashes)
    r_raw = max(raw_counter.values()) / len(raw_hashes) if raw_hashes else 0.0
    
    # Compute R_anchor (% of runs with distance == 0)
    r_anchor = sum(1 for hit in anchor_hits if hit) / len(anchor_hits) if anchor_hits else 0.0
    
    # Compute distance statistics
    if distances:
        mean_distance = np.mean(distances)
        variance_distance = np.var(distances)
        std_distance = np.std(distances)
        
        # Outlier rate (distance > mean + 2*std)
        outlier_threshold = mean_distance + 2 * std_distance if std_distance > 0 else mean_distance
        outlier_rate = sum(1 for d in distances if d > outlier_threshold) / len(distances)
    else:
        mean_distance = 0.0
        variance_distance = 0.0
        std_distance = 0.0
        outlier_rate = 0.0
    
    # Legacy R_canon for comparison
    canon_counter = Counter(canon_signatures)
    r_canon = max(canon_counter.values()) / len(canon_signatures) if canon_signatures else 0.0
    
    # Additional metrics
    contract_pass_count = sum(1 for r in records if str(r.get("contract_pass", "")).lower() == "true")
    contract_pass_rate = contract_pass_count / len(records) if records else 0.0
    
    oracle_pass_count = sum(1 for r in records if str(r.get("oracle_pass", "")).lower() == "true")
    oracle_pass_rate = oracle_pass_count / len(records) if records else 0.0
    
    # Monotonicity check: R_anchor <= R_canon always
    monotonicity_check = r_anchor <= r_canon
    
    return {
        "total_runs": len(records),
        "R_raw": round(r_raw, 4),
        "R_anchor": round(r_anchor, 4),
        "R_canon": round(r_canon, 4),
        "mean_distance": round(mean_distance, 4),
        "variance_distance": round(variance_distance, 4),
        "std_distance": round(std_distance, 4),
        "outlier_rate": round(outlier_rate, 4),
        "contract_pass_rate": round(contract_pass_rate, 4),
        "oracle_pass_rate": round(oracle_pass_rate, 4),
        "unique_raw_hashes": len(raw_counter),
        "unique_canon_signatures": len(canon_counter),
        "monotonicity_check": monotonicity_check
    }


def generate_repeatability_report(output_path: str = "outputs/repeatability_summary.csv"):
    """
    Generate repeatability summary report
    
    Args:
        output_path: Path for output summary CSV
    """
    metrics = compute_repeatability_metrics()
    
    if not metrics:
        print("No execution records found for repeatability analysis")
        return
    
    # Prepare summary rows
    summary_rows = []
    
    for prompt_id, prompt_metrics in metrics.items():
        for temp_key, temp_metrics in prompt_metrics.items():
            row = {
                "prompt_id": prompt_id,
                "temperature": temp_key,
                **temp_metrics
            }
            summary_rows.append(row)
    
    # Write summary CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if summary_rows:
        fieldnames = summary_rows[0].keys()
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summary_rows)
        
        print(f"Repeatability summary written to: {output_path}")
        
        # Print summary to console
        print("\nRepeatability Summary:")
        print("=" * 50)
        for row in summary_rows:
            print(f"{row['prompt_id']} {row['temperature']}: R_raw={row['R_raw']}, R_anchor={row['R_anchor']}, mean_dist={row['mean_distance']}, var_dist={row['variance_distance']}")


def generate_histogram_csvs(output_dir: str = "outputs"):
    """
    Generate per-prompt histogram CSVs for distance distributions around anchor
    
    Args:
        output_dir: Directory for histogram CSV files
    """
    records = read_execution_records()
    
    if not records:
        return
    
    # Group by prompt_id
    grouped = defaultdict(list)
    for record in records:
        prompt_id = record.get("prompt_id", "unknown")
        grouped[prompt_id].append(record)
    
    os.makedirs(output_dir, exist_ok=True)
    
    for prompt_id, prompt_records in grouped.items():
        # Distance distribution histogram (main focus)
        distances = [float(r.get("distance", 1.0)) for r in prompt_records if r.get("distance") is not None]
        
        if distances:
            # Create distance bins
            distance_bins = {}
            for distance in distances:
                bin_key = f"{distance:.2f}"
                distance_bins[bin_key] = distance_bins.get(bin_key, 0) + 1
            
            dist_hist_path = os.path.join(output_dir, f"hist_{prompt_id}_distances.csv")
            with open(dist_hist_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["distance", "count"])
                for distance, count in sorted(distance_bins.items(), key=lambda x: float(x[0])):
                    writer.writerow([distance, count])
        
        # Raw hash histogram (for ablation)
        raw_hashes = [r.get("raw_hash", "") for r in prompt_records if r.get("raw_hash")]
        raw_counter = Counter(raw_hashes)
        
        raw_hist_path = os.path.join(output_dir, f"hist_{prompt_id}_raw.csv")
        with open(raw_hist_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["hash", "count"])
            for hash_val, count in raw_counter.most_common():
                writer.writerow([hash_val, count])
    
    print(f"Histogram CSVs generated in: {output_dir}")


def generate_distance_analysis(output_dir: str = "outputs"):
    """
    Generate detailed distance analysis and outlier detection
    
    Args:
        output_dir: Directory for analysis files
    """
    records = read_execution_records()
    
    if not records:
        return
    
    # Group by prompt_id
    grouped = defaultdict(list)
    for record in records:
        prompt_id = record.get("prompt_id", "unknown")
        grouped[prompt_id].append(record)
    
    os.makedirs(output_dir, exist_ok=True)
    
    analysis_rows = []
    
    for prompt_id, prompt_records in grouped.items():
        distances = [float(r.get("distance", 1.0)) for r in prompt_records if r.get("distance") is not None]
        
        if distances:
            mean_dist = np.mean(distances)
            var_dist = np.var(distances)
            std_dist = np.std(distances)
            min_dist = np.min(distances)
            max_dist = np.max(distances)
            median_dist = np.median(distances)
            
            # Percentiles
            p25 = np.percentile(distances, 25)
            p75 = np.percentile(distances, 75)
            p95 = np.percentile(distances, 95)
            
            # Outlier analysis
            outlier_threshold = mean_dist + 2 * std_dist
            outliers = [d for d in distances if d > outlier_threshold]
            outlier_count = len(outliers)
            
            analysis_rows.append({
                "prompt_id": prompt_id,
                "total_runs": len(distances),
                "mean_distance": round(mean_dist, 4),
                "variance_distance": round(var_dist, 4),
                "std_distance": round(std_dist, 4),
                "min_distance": round(min_dist, 4),
                "max_distance": round(max_dist, 4),
                "median_distance": round(median_dist, 4),
                "p25_distance": round(p25, 4),
                "p75_distance": round(p75, 4),
                "p95_distance": round(p95, 4),
                "outlier_threshold": round(outlier_threshold, 4),
                "outlier_count": outlier_count,
                "outlier_rate": round(outlier_count / len(distances), 4)
            })
    
    # Write distance analysis
    if analysis_rows:
        analysis_path = os.path.join(output_dir, "distance_analysis.csv")
        with open(analysis_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=analysis_rows[0].keys())
            writer.writeheader()
            writer.writerows(analysis_rows)
        
        print(f"Distance analysis written to: {analysis_path}")


if __name__ == "__main__":
    generate_repeatability_report()
    generate_histogram_csvs()
    generate_distance_analysis()
