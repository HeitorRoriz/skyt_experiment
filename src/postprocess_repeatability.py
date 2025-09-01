# src/postprocess_repeatability.py
"""
Repeatability metrics and reports for SKYT pipeline
Computes R_raw, R_canon, canon_coverage, and rescue_delta from execution records
"""

import csv
import os
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
    """Compute metrics for a specific temperature group"""
    if not records:
        return {}
    
    # Extract hashes and signatures
    raw_hashes = [r.get("raw_hash", "") for r in records if r.get("raw_hash")]
    canon_signatures = [r.get("canon_signature", "") for r in records if r.get("canon_signature")]
    
    # Compute R_raw (modal probability mass on raw_hash)
    raw_counter = Counter(raw_hashes)
    r_raw = max(raw_counter.values()) / len(raw_hashes) if raw_hashes else 0.0
    
    # Compute R_canon (modal probability mass on canon_signature)
    canon_counter = Counter(canon_signatures)
    r_canon = max(canon_counter.values()) / len(canon_signatures) if canon_signatures else 0.0
    
    # Compute canon_coverage (% with canonicalization_ok == True)
    canon_ok_count = sum(1 for r in records if str(r.get("canonicalization_ok", "")).lower() == "true")
    canon_coverage = canon_ok_count / len(records) if records else 0.0
    
    # Compute rescue_delta
    rescue_delta = r_canon - r_raw
    
    # Additional metrics
    contract_pass_count = sum(1 for r in records if str(r.get("contract_pass", "")).lower() == "true")
    contract_pass_rate = contract_pass_count / len(records) if records else 0.0
    
    oracle_pass_count = sum(1 for r in records if str(r.get("oracle_pass", "")).lower() == "true")
    oracle_pass_rate = oracle_pass_count / len(records) if records else 0.0
    
    return {
        "total_runs": len(records),
        "R_raw": round(r_raw, 4),
        "R_canon": round(r_canon, 4),
        "canon_coverage": round(canon_coverage, 4),
        "rescue_delta": round(rescue_delta, 4),
        "contract_pass_rate": round(contract_pass_rate, 4),
        "oracle_pass_rate": round(oracle_pass_rate, 4),
        "unique_raw_hashes": len(raw_counter),
        "unique_canon_signatures": len(canon_counter)
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
            print(f"{row['prompt_id']} {row['temperature']}: R_raw={row['R_raw']}, R_canon={row['R_canon']}, rescue_delta={row['rescue_delta']}")


def generate_histogram_csvs(output_dir: str = "outputs"):
    """
    Generate per-prompt histogram CSVs for raw and canonical distributions
    
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
        # Raw hash histogram
        raw_hashes = [r.get("raw_hash", "") for r in prompt_records if r.get("raw_hash")]
        raw_counter = Counter(raw_hashes)
        
        raw_hist_path = os.path.join(output_dir, f"hist_{prompt_id}_raw.csv")
        with open(raw_hist_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["hash", "count"])
            for hash_val, count in raw_counter.most_common():
                writer.writerow([hash_val, count])
        
        # Canon signature histogram
        canon_sigs = [r.get("canon_signature", "") for r in prompt_records if r.get("canon_signature")]
        canon_counter = Counter(canon_sigs)
        
        canon_hist_path = os.path.join(output_dir, f"hist_{prompt_id}_canon.csv")
        with open(canon_hist_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["signature", "count"])
            for sig_val, count in canon_counter.most_common():
                writer.writerow([sig_val, count])
    
    print(f"Histogram CSVs generated in: {output_dir}")


if __name__ == "__main__":
    generate_repeatability_report()
    generate_histogram_csvs()
