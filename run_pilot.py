#!/usr/bin/env python3
"""
Phase 1 Pilot Run - SKYT Experiment
1 contract × 3 models × 2 temps × 5 runs = 30 generations
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.comprehensive_experiment import ComprehensiveExperiment

def main():
    """Run Phase 1 pilot experiment"""
    
    # Configuration
    models = [
        "gpt-4o-mini",
        "gpt-4o",
        "claude-3-5-sonnet-20241022"
    ]
    
    contract = "fibonacci"
    temperatures = [0.0, 0.7]
    runs = 5
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = Path("outputs") / f"pilot_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("SKYT PHASE 1 PILOT EXPERIMENT")
    print("=" * 80)
    print(f"Contract: {contract}")
    print(f"Models: {', '.join(models)}")
    print(f"Temperatures: {temperatures}")
    print(f"Runs per config: {runs}")
    print(f"Total generations: {len(models) * len(temperatures) * runs}")
    print(f"Output directory: {output_dir}")
    print("=" * 80)
    print()
    
    # Run for each model
    for model in models:
        print(f"\n{'='*80}")
        print(f"MODEL: {model}")
        print(f"{'='*80}\n")
        
        for temp in temperatures:
            print(f"\nTemperature: {temp}")
            print("-" * 40)
            
            # Create experiment instance
            exp = ComprehensiveExperiment(
                output_dir=str(output_dir / model / f"temp_{temp}"),
                model=model
            )
            
            # Run experiment
            try:
                results = exp.run_full_experiment(
                    contract_template_path="contracts/templates.json",
                    contract_id=contract,
                    num_runs=runs,
                    temperature=temp
                )
                
                print(f"✓ Completed {runs} runs at temp={temp}")
                print(f"  Oracle pass rate: {results.get('oracle_pass_rate', 0):.2%}")
                
            except Exception as e:
                print(f"✗ FAILED at temp={temp}: {e}")
                print(f"  Stopping experiment (stop-on-error mode)")
                sys.exit(1)
    
    print("\n" + "=" * 80)
    print("PHASE 1 PILOT COMPLETE")
    print("=" * 80)
    print(f"Results saved to: {output_dir}")
    print("\nPlease review the outputs and logs before proceeding to Phase 2.")
    print("=" * 80)

if __name__ == "__main__":
    main()
