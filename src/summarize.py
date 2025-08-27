# src/summarize.py
"""
Prints per-prompt summary table with the four metrics
"""

import os
from typing import Dict, List
from collections import defaultdict

from .log import ExperimentLogger, RunLog
from .metrics import calculate_metrics, MetricsResult


def calculate_metrics_from_logs(logs: List[RunLog]) -> MetricsResult:
    """
    Calculate metrics from run logs
    
    Args:
        logs: List of run logs for a specific prompt
        
    Returns:
        MetricsResult with calculated metrics
    """
    raw_outputs = [log.raw_code for log in logs]
    canonical_outputs = [log.canonical_code for log in logs]
    contract_passes = [log.contract_passed for log in logs]
    
    return calculate_metrics(raw_outputs, canonical_outputs, contract_passes)


def print_summary_table(log_file: str):
    """
    Print summary table with metrics for each prompt
    
    Args:
        log_file: Path to experiment log CSV file
    """
    # Load logs
    logger = ExperimentLogger(log_file)
    all_logs = logger.read_logs()
    
    if not all_logs:
        print("No logs found in file")
        return
    
    # Group logs by prompt_id
    logs_by_prompt = defaultdict(list)
    for log in all_logs:
        logs_by_prompt[log.prompt_id].append(log)
    
    # Calculate metrics for each prompt
    results = {}
    for prompt_id, logs in logs_by_prompt.items():
        results[prompt_id] = calculate_metrics_from_logs(logs)
    
    # Print header
    print("\n" + "=" * 80)
    print("SKYT EXPERIMENT SUMMARY")
    print("=" * 80)
    print(f"Total Prompts: {len(results)}")
    print(f"Total Runs: {len(all_logs)}")
    print(f"Metrics Version: simplified_v1")
    print()
    
    # Print table header
    print(f"{'Prompt ID':<15} | {'Runs':<4} | {'R_raw':<6} | {'R_canon':<7} | {'Coverage':<8} | {'Delta':<7}")
    print("-" * 80)
    
    # Print metrics for each prompt
    total_runs = 0
    sum_r_raw = 0
    sum_r_canon = 0
    sum_coverage = 0
    sum_delta = 0
    
    for prompt_id, metrics in results.items():
        total_runs += metrics.total_runs
        sum_r_raw += metrics.r_raw
        sum_r_canon += metrics.r_canon
        sum_coverage += metrics.canon_coverage
        sum_delta += metrics.rescue_delta
        
        print(f"{prompt_id:<15} | {metrics.total_runs:<4} | "
              f"{metrics.r_raw:<6.3f} | {metrics.r_canon:<7.3f} | "
              f"{metrics.canon_coverage:<8.3f} | {metrics.rescue_delta:<7.3f}")
    
    # Print averages
    num_prompts = len(results)
    if num_prompts > 0:
        print("-" * 80)
        print(f"{'AVERAGE':<15} | {total_runs/num_prompts:<4.1f} | "
              f"{sum_r_raw/num_prompts:<6.3f} | {sum_r_canon/num_prompts:<7.3f} | "
              f"{sum_coverage/num_prompts:<8.3f} | {sum_delta/num_prompts:<7.3f}")
    
    print("=" * 80)
    
    # Print metric definitions
    print("\nMETRIC DEFINITIONS:")
    print("R_raw:     Raw repeatability (most frequent raw output / total runs)")
    print("R_canon:   Canonical repeatability (most frequent canonical form / total runs)")
    print("Coverage:  Canonicalization success rate (successful canonicalizations / total runs)")
    print("Delta:     Rescue delta (R_canon - R_raw)")
    print()


def print_detailed_summary(log_file: str):
    """
    Print detailed summary including per-run information
    
    Args:
        log_file: Path to experiment log CSV file
    """
    logger = ExperimentLogger(log_file)
    all_logs = logger.read_logs()
    
    if not all_logs:
        print("No logs found in file")
        return
    
    # Group by prompt
    logs_by_prompt = defaultdict(list)
    for log in all_logs:
        logs_by_prompt[log.prompt_id].append(log)
    
    print("\n" + "=" * 100)
    print("DETAILED EXPERIMENT SUMMARY")
    print("=" * 100)
    
    for prompt_id, logs in logs_by_prompt.items():
        print(f"\nPrompt: {prompt_id}")
        print("-" * 60)
        
        # Calculate metrics
        metrics = calculate_metrics_from_logs(logs)
        
        print(f"Runs: {metrics.total_runs}")
        print(f"R_raw: {metrics.r_raw:.3f}, R_canon: {metrics.r_canon:.3f}, "
              f"Coverage: {metrics.canon_coverage:.3f}, Delta: {metrics.rescue_delta:.3f}")
        
        # Show run details
        print("\nRun Details:")
        for log in logs:
            status_symbols = []
            if log.structural_ok:
                status_symbols.append("S")
            if log.canonicalization_ok:
                status_symbols.append("C")
            if log.oracle_passed:
                status_symbols.append("O")
            if log.contract_passed:
                status_symbols.append("[OK]")
            else:
                status_symbols.append("[FAIL]")
            
            status_str = "".join(status_symbols)
            error_str = f" ({log.error_message})" if log.error_message else ""
            
            print(f"  Run {log.run_id}: {status_str}{error_str}")
        
        print()


def export_summary_csv(log_file: str, output_file: str = None):
    """
    Export summary metrics to CSV file
    
    Args:
        log_file: Path to experiment log CSV file
        output_file: Path to output CSV file (default: summary.csv)
    """
    if output_file is None:
        output_file = os.path.join(os.path.dirname(log_file), "summary.csv")
    
    logger = ExperimentLogger(log_file)
    all_logs = logger.read_logs()
    
    if not all_logs:
        print("No logs found in file")
        return
    
    # Group by prompt and calculate metrics
    logs_by_prompt = defaultdict(list)
    for log in all_logs:
        logs_by_prompt[log.prompt_id].append(log)
    
    # Write summary CSV
    import csv
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['prompt_id', 'total_runs', 'r_raw', 'r_canon', 'canon_coverage', 'rescue_delta']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for prompt_id, logs in logs_by_prompt.items():
            metrics = calculate_metrics_from_logs(logs)
            writer.writerow({
                'prompt_id': prompt_id,
                'total_runs': metrics.total_runs,
                'r_raw': metrics.r_raw,
                'r_canon': metrics.r_canon,
                'canon_coverage': metrics.canon_coverage,
                'rescue_delta': metrics.rescue_delta
            })
    
    print(f"Summary exported to: {output_file}")


def main():
    """Main entry point for summary generation"""
    log_file = os.path.join("results", "experiment_log.csv")
    
    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        print("Run experiments first using run_experiment.py")
        return
    
    # Print summary table
    print_summary_table(log_file)
    
    # Export CSV summary
    export_summary_csv(log_file)


if __name__ == "__main__":
    main()
