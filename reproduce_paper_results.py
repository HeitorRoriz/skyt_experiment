#!/usr/bin/env python3
"""
Single-command script to reproduce all paper results
Generates the exact data reported in MSR 2026 paper tables

Usage:
    python reproduce_paper_results.py [--verify-only]

Options:
    --verify-only    Skip LLM calls, only verify existing data matches paper
"""

import sys
import os
import csv
import argparse
from pathlib import Path

# Paper-reported configurations
PAPER_TASKS = ["binary_search", "balanced_brackets", "slugify"]
ALL_TASKS = [
    "fibonacci_basic", "fibonacci_recursive", "factorial", "gcd", "is_prime",
    "binary_search", "merge_sort", "quick_sort",
    "slugify", "is_palindrome", "balanced_brackets", "lru_cache"
]
MODELS = ["gpt-4o-mini", "gpt-4o", "claude-sonnet-4-5-20250929"]
TEMPERATURES = [0.0, 0.3, 0.5, 0.7, 1.0]
RUNS_PER_CONFIG = 20

# Expected totals
EXPECTED_TOTAL = len(ALL_TASKS) * len(MODELS) * len(TEMPERATURES)  # 180 configs
EXPECTED_GENERATIONS = EXPECTED_TOTAL * RUNS_PER_CONFIG  # 3,600 generations


def verify_existing_results():
    """Verify that existing results match paper-reported values"""
    print("\n" + "="*80)
    print("VERIFYING EXISTING RESULTS AGAINST PAPER")
    print("="*80)
    
    csv_path = Path("outputs/metrics_summary.csv")
    if not csv_path.exists():
        print(f"❌ Missing: {csv_path}")
        return False
    
    # Read CSV
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"\n✓ Found {len(rows)} experiment configurations")
    
    # Paper Table 1: Binary-Search + GPT-4o-mini + T=0.5
    # Expected: R_raw=0.30, R_anchor_pre=0.45, R_anchor_post=1.00, Delta_rescue=0.55
    print("\n" + "-"*80)
    print("Verifying Table 1 (Representative Tasks - GPT-4o-mini)")
    print("-"*80)
    
    test_cases = [
        ("binary_search", "gpt-4o-mini", 0.5, 0.30, 0.45, 1.00, 0.55),
        ("balanced_brackets", "gpt-4o-mini", 0.3, 0.20, 0.35, 1.00, 0.65),
        ("slugify", "gpt-4o-mini", 0.5, 0.40, 0.40, 0.80, 0.40),
    ]
    
    all_match = True
    for contract, model, temp, exp_raw, exp_pre, exp_post, exp_delta in test_cases:
        # Find matching row
        matching = [r for r in rows 
                   if r['contract_id'] == contract 
                   and r['model'] == model 
                   and float(r['decoding_temperature']) == temp]
        
        if not matching:
            print(f"❌ Missing: {contract} + {model} + T={temp}")
            all_match = False
            continue
        
        row = matching[0]
        actual_raw = float(row['R_raw'])
        actual_pre = float(row['R_anchor_pre'])
        actual_post = float(row['R_anchor_post'])
        actual_delta = float(row['Delta_rescue'])
        
        # Check with tolerance for floating point
        tolerance = 0.01
        matches = (
            abs(actual_raw - exp_raw) < tolerance and
            abs(actual_pre - exp_pre) < tolerance and
            abs(actual_post - exp_post) < tolerance and
            abs(actual_delta - exp_delta) < tolerance
        )
        
        if matches:
            print(f"✓ {contract:20} T={temp}: R_raw={actual_raw:.2f}, Δ_rescue={actual_delta:.2f}")
        else:
            print(f"❌ {contract:20} T={temp}: MISMATCH")
            print(f"   Expected: R_raw={exp_raw:.2f}, R_pre={exp_pre:.2f}, R_post={exp_post:.2f}, Δ={exp_delta:.2f}")
            print(f"   Actual:   R_raw={actual_raw:.2f}, R_pre={actual_pre:.2f}, R_post={actual_post:.2f}, Δ={actual_delta:.2f}")
            all_match = False
    
    print("\n" + "="*80)
    if all_match:
        print("✅ ALL PAPER VALUES VERIFIED")
        print("="*80)
        return True
    else:
        print("⚠️  SOME VALUES DO NOT MATCH - May need to re-run experiments")
        print("="*80)
        return False


def run_full_experiments():
    """Run all 3,600 experiments to reproduce paper results"""
    print("\n" + "="*80)
    print("REPRODUCING FULL PAPER RESULTS")
    print("="*80)
    print(f"\nThis will run:")
    print(f"  • {len(ALL_TASKS)} contracts")
    print(f"  • {len(MODELS)} models")
    print(f"  • {len(TEMPERATURES)} temperatures")
    print(f"  • {RUNS_PER_CONFIG} runs per configuration")
    print(f"  • Total: {EXPECTED_GENERATIONS} LLM generations")
    print(f"\n⚠️  This requires API keys and will take several hours")
    print(f"⚠️  Estimated cost: ~$50-100 depending on API rates")
    
    response = input("\nProceed? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return False
    
    # Check for API keys
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ Missing API keys. Please set OPENAI_API_KEY and/or ANTHROPIC_API_KEY")
        return False
    
    print("\n" + "-"*80)
    print("Starting experiments...")
    print("-"*80)
    
    # Import here to avoid dependency issues if just verifying
    try:
        from src.comprehensive_experiment import ComprehensiveExperiment
        from src.llm_client import LLMClient
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure dependencies are installed: pip install -r requirements.txt")
        return False
    
    completed = 0
    failed = 0
    
    for contract in ALL_TASKS:
        for model in MODELS:
            print(f"\n{'='*60}")
            print(f"Contract: {contract} | Model: {model}")
            print(f"{'='*60}")
            
            try:
                llm_client = LLMClient(model=model)
                exp = ComprehensiveExperiment(llm_client=llm_client)
                
                # Run temperature sweep
                result = exp.run_temperature_sweep(
                    contract_template_path="contracts/templates.json",
                    contract_id=contract,
                    temperatures=TEMPERATURES,
                    num_runs=RUNS_PER_CONFIG
                )
                
                completed += len(TEMPERATURES)
                print(f"✓ Completed {contract} + {model}")
                
            except Exception as e:
                print(f"❌ Failed {contract} + {model}: {e}")
                failed += len(TEMPERATURES)
    
    print("\n" + "="*80)
    print("EXPERIMENT COMPLETE")
    print("="*80)
    print(f"✓ Completed: {completed}/{EXPECTED_TOTAL} configurations")
    if failed > 0:
        print(f"❌ Failed: {failed}/{EXPECTED_TOTAL} configurations")
    print(f"\nResults saved to: outputs/metrics_summary.csv")
    print("="*80)
    
    return failed == 0


def main():
    parser = argparse.ArgumentParser(
        description="Reproduce MSR 2026 paper results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify existing results match paper
  python reproduce_paper_results.py --verify-only
  
  # Run full reproduction (3,600 LLM calls)
  python reproduce_paper_results.py
        """
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing data, don't run new experiments"
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("MSR 2026 PAPER REPRODUCTION SCRIPT")
    print("SKYT: Prompt Contracts for Software Repeatability")
    print("="*80)
    
    if args.verify_only:
        success = verify_existing_results()
        return 0 if success else 1
    else:
        # First verify if data already exists
        csv_path = Path("outputs/metrics_summary.csv")
        if csv_path.exists():
            print("\n⚠️  Existing results found. Verifying first...")
            if verify_existing_results():
                print("\n✓ Existing results match paper. No need to re-run.")
                print("  Use --verify-only flag to skip this check in the future.")
                return 0
            else:
                print("\n⚠️  Existing results don't match. Will re-run experiments.")
        
        # Run full experiments
        success = run_full_experiments()
        
        # Verify results
        if success:
            print("\n" + "="*80)
            print("Verifying reproduced results...")
            print("="*80)
            verify_existing_results()
        
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
