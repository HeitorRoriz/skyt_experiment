# src/runners/run_single.py
"""
[TODO run_single.py]
Goal: run N samples for a single prompt, compute metrics, produce figs. No code.

1. CLI args: --prompt-id, --n, --mode(contract|simple), --tau(0.10 default).
2. Loop N times:
   - Produce output via existing LLM call path wrapped with middleware.pipeline.
3. After loop:
   - metrics.compute(...) then viz.* to write figures.
4. Print a compact summary table to stdout.
5. Acceptance: all four CSV logs have new rows and figures exist.
"""

import argparse
import sys
import os
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.middleware.pipeline import wrap_contract_run, wrap_simple_run, create_pipeline_context
from src.middleware.metrics import compute_metrics, write_metrics_summary, print_metrics_summary
from src.middleware.viz import generate_all_visualizations
from src.middleware.schema import DEFAULT_TAU
from src.contract import load_contract_from_template, create_prompt_contract
from src.llm import query_llm
from src.prompt_builder import build_llm_prompt_for_code

def main():
    """Main entry point for single prompt runner"""
    parser = argparse.ArgumentParser(description='Run SKYT middleware for single prompt')
    parser.add_argument('--prompt-id', required=True, help='Prompt identifier')
    parser.add_argument('--n', type=int, default=5, help='Number of samples to run')
    parser.add_argument('--mode', choices=['contract', 'simple'], default='contract', 
                       help='Execution mode')
    parser.add_argument('--tau', type=float, default=DEFAULT_TAU, 
                       help='Threshold for P_tau computation')
    parser.add_argument('--model', default='gpt-4o-mini', help='LLM model to use')
    parser.add_argument('--temperature', type=float, default=0.0, help='Temperature parameter')
    
    args = parser.parse_args()
    
    print(f"SKYT Middleware Single Runner")
    print(f"Prompt: {args.prompt_id}, Mode: {args.mode}, N: {args.n}")
    print("=" * 50)
    
    # Load contract
    contract = _load_contract(args.prompt_id, args.mode)
    if not contract:
        print(f"ERROR: Could not load contract for prompt {args.prompt_id}")
        return 1
    
    # Create pipeline context
    context = create_pipeline_context(
        args.prompt_id, contract, args.model, args.temperature
    )
    
    # Run N samples
    success_count = 0
    for i in range(args.n):
        print(f"Running sample {i+1}/{args.n}...", end=" ")
        
        try:
            # Create LLM callable
            def llm_callable():
                messages = build_llm_prompt_for_code(contract)
                return query_llm(messages, args.model, args.temperature)
            
            if args.mode == "contract":
                result = wrap_contract_run(llm_callable, context)
            else:
                result = wrap_simple_run(llm_callable, context)
            
            print("OK")  # Success
            success_count += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
    
    print(f"\nCompleted {success_count}/{args.n} samples")
    # Compute metrics
    print("Computing metrics...")
    metrics = compute_metrics(args.prompt_id, args.tau)
    
    if metrics:
        # Write metrics summary
        write_metrics_summary(metrics)
        
        # Print compact summary
        print_metrics_summary(metrics)
        
        # Generate visualizations
        print("Generating visualizations...")
        try:
            generate_all_visualizations()
            print("Visualizations saved to outputs/figs/")
        except Exception as e:
            print(f"Visualization error: {e}")
    else:
        print("No metrics computed - check logs for errors")
    
    return 0

def _load_contract(prompt_id: str, mode: str) -> Dict[str, Any]:
    """
    Load contract for prompt
    
    Args:
        prompt_id: Prompt identifier
        mode: Execution mode
    
    Returns:
        Contract dict or None if not found
    """
    if mode == "contract":
        # Try to load from templates
        try:
            return load_contract_from_template("contracts/templates.json", prompt_id)
        except:
            pass
    
    # Fallback: create simple contract
    return create_prompt_contract(
        prompt_id=prompt_id,
        prompt=f"Generate Python code for {prompt_id}",
        function_name=None,
        oracle=None
    )

if __name__ == "__main__":
    sys.exit(main())
