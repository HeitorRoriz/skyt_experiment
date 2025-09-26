# src/runners/run_suite.py
"""
[TODO run_suite.py]
Goal: iterate a matrix of prompts, compute metrics per prompt. No code.

1. CLI args: --matrix <file>, --tau(0.10 default).
2. For each prompt in matrix, run run_single with its N.
3. Aggregate metrics_summary.csv across prompts.
4. Acceptance: metrics_summary.csv contains one row per prompt.
"""

import argparse
import json
import sys
import os
import subprocess
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.middleware.metrics import compute_metrics, write_metrics_summary, print_metrics_summary
from src.middleware.viz import generate_all_visualizations, create_summary_dashboard
from src.middleware.schema import DEFAULT_TAU
from src.middleware.logger import read_csv_records

def main():
    """Main entry point for experiment suite runner"""
    parser = argparse.ArgumentParser(description='Run SKYT middleware experiment suite')
    parser.add_argument('--matrix', default='contracts/templates.json', 
                       help='Path to experiment matrix file')
    parser.add_argument('--tau', type=float, default=DEFAULT_TAU,
                       help='Threshold for P_tau computation')
    parser.add_argument('--n', type=int, default=5,
                       help='Number of samples per prompt')
    parser.add_argument('--mode', choices=['contract', 'simple'], default='contract',
                       help='Execution mode')
    parser.add_argument('--model', default='gpt-4o-mini', help='LLM model to use')
    parser.add_argument('--temperature', type=float, default=0.0, help='Temperature parameter')
    
    args = parser.parse_args()
    
    print("SKYT Middleware Suite Runner")
    print(f"Matrix: {args.matrix}, Mode: {args.mode}, N: {args.n}")
    print("=" * 50)
    
    # Load experiment matrix
    matrix = _load_matrix(args.matrix)
    if not matrix:
        print(f"ERROR: Could not load matrix from {args.matrix}")
        return 1
    
    print(f"Loaded {len(matrix)} prompts from matrix")
    
    # Run experiments for each prompt
    completed_prompts = []
    
    for i, prompt_spec in enumerate(matrix):
        prompt_id = prompt_spec.get("id", f"prompt_{i}")
        print(f"\n[{i+1}/{len(matrix)}] Running prompt: {prompt_id}")
        
        try:
            # Run single prompt experiment
            result = _run_single_prompt(
                prompt_id, args.n, args.mode, args.tau,
                args.model, args.temperature
            )
            
            if result == 0:
                completed_prompts.append(prompt_id)
                print(f"✓ Completed {prompt_id}")
            else:
                print(f"✗ Failed {prompt_id}")
        
        except Exception as e:
            print(f"✗ Error running {prompt_id}: {e}")
    
    print(f"\nCompleted {len(completed_prompts)}/{len(matrix)} prompts")
    
    # Aggregate metrics across all prompts
    print("\nAggregating metrics...")
    all_metrics = compute_metrics(tau=args.tau)
    
    if all_metrics:
        # Write aggregated metrics
        write_metrics_summary(all_metrics)
        
        # Print summary
        print_metrics_summary(all_metrics)
        
        # Generate comprehensive visualizations
        print("Generating suite visualizations...")
        try:
            generate_all_visualizations()
            
            # Create summary dashboard
            metrics_records = read_csv_records("outputs/logs/metrics_summary.csv")
            create_summary_dashboard(metrics_records)
            
            print("All visualizations saved to outputs/figs/")
        except Exception as e:
            print(f"Visualization error: {e}")
        
        # Print final summary
        _print_suite_summary(all_metrics)
    else:
        print("No metrics computed - check individual prompt logs")
    
    return 0

def _load_matrix(matrix_path: str) -> List[Dict[str, Any]]:
    """
    Load experiment matrix from file
    
    Args:
        matrix_path: Path to matrix JSON file
    
    Returns:
        List of prompt specifications
    """
    try:
        with open(matrix_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading matrix: {e}")
        return []

def _run_single_prompt(prompt_id: str, n: int, mode: str, tau: float,
                      model: str, temperature: float) -> int:
    """
    Run single prompt experiment by calling run_single.py
    
    Args:
        prompt_id: Prompt identifier
        n: Number of samples
        mode: Execution mode
        tau: P_tau threshold
        model: LLM model
        temperature: Temperature parameter
    
    Returns:
        Exit code (0 for success)
    """
    # Build command
    cmd = [
        sys.executable, "-m", "src.runners.run_single",
        "--prompt-id", prompt_id,
        "--n", str(n),
        "--mode", mode,
        "--tau", str(tau),
        "--model", model,
        "--temperature", str(temperature)
    ]
    
    # Execute subprocess
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"STDERR: {result.stderr}")
        
        return result.returncode
    
    except subprocess.TimeoutExpired:
        print(f"Timeout running {prompt_id}")
        return 1
    except Exception as e:
        print(f"Subprocess error: {e}")
        return 1

def _print_suite_summary(metrics: Dict[str, Any]) -> None:
    """
    Print comprehensive suite summary
    
    Args:
        metrics: Dict of prompt_id -> MetricsRecord
    """
    if not metrics:
        return
    
    print("\n" + "=" * 60)
    print("SUITE SUMMARY")
    print("=" * 60)
    
    # Overall statistics
    total_prompts = len(metrics)
    total_samples = sum(m.N for m in metrics.values())
    
    avg_R_raw = sum(m.R_raw for m in metrics.values()) / total_prompts
    avg_R_anchor = sum(m.R_anchor for m in metrics.values()) / total_prompts
    avg_rescue_rate = sum(m.rescue_rate for m in metrics.values()) / total_prompts
    
    avg_delta_R = sum(m.delta_R_anchor for m in metrics.values()) / total_prompts
    avg_delta_mu = sum(m.delta_mu for m in metrics.values()) / total_prompts
    
    print(f"Total Prompts: {total_prompts}")
    print(f"Total Samples: {total_samples}")
    print(f"Average R_raw: {avg_R_raw:.3f}")
    print(f"Average R_anchor: {avg_R_anchor:.3f}")
    print(f"Average Rescue Rate: {avg_rescue_rate:.1%}")
    print(f"Average ΔR_anchor: {avg_delta_R:.3f}")
    print(f"Average Δμ: {avg_delta_mu:.3f}")
    
    # Best and worst performing prompts
    best_R_anchor = max(metrics.items(), key=lambda x: x[1].R_anchor)
    worst_R_anchor = min(metrics.items(), key=lambda x: x[1].R_anchor)
    
    print(f"\nBest R_anchor: {best_R_anchor[0]} ({best_R_anchor[1].R_anchor:.3f})")
    print(f"Worst R_anchor: {worst_R_anchor[0]} ({worst_R_anchor[1].R_anchor:.3f})")
    
    # Rescue effectiveness
    high_rescue = [pid for pid, m in metrics.items() if m.rescue_rate > 0.5]
    if high_rescue:
        print(f"\nHigh rescue rate prompts: {', '.join(high_rescue)}")
    
    print("\nFiles generated:")
    print("- outputs/logs/metrics_summary.csv")
    print("- outputs/figs/*.png")

if __name__ == "__main__":
    sys.exit(main())
