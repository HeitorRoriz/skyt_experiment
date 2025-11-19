"""
Phase 1.7 Full Experiment

Tests the impact of Phase 1.7 (Oracle-Guided Template Transformation) on all contracts.
This includes both Phase 1.6 (syntactic) and Phase 1.7 (algorithmic) transformations.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.comprehensive_experiment import ComprehensiveExperiment


def run_experiment(contract_id: str, num_runs: int = 10):
    """
    Run experiment on a single contract with Phase 1.7 integrated.
    """
    print("\n" + "="*70)
    print(f"CONTRACT: {contract_id}")
    print("="*70)
    
    experiment = ComprehensiveExperiment()
    result = experiment.run_full_experiment(
        contract_template_path='contracts/templates.json',
        contract_id=contract_id,
        num_runs=num_runs,
        temperature=0.7
    )
    
    return result


def main():
    """Run Phase 1.7 validation experiment"""
    
    print("="*70)
    print("PHASE 1.7 FULL EXPERIMENT")
    print("Testing Oracle-Guided Template Transformation")
    print("Includes Phase 1.6 (syntactic) + Phase 1.7 (algorithmic)")
    print("="*70)
    print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    contracts = [
        'fibonacci_basic',
        'fibonacci_recursive',
        'slugify',
        'balanced_brackets',
        'gcd',
        'binary_search',
        'lru_cache',
    ]
    
    num_runs = 10
    results = {}
    
    print(f"\nTesting {len(contracts)} contracts with {num_runs} runs each")
    print(f"Total: {len(contracts) * num_runs} LLM outputs\n")
    
    for i, contract_id in enumerate(contracts, 1):
        print(f"\n[{i}/{len(contracts)}] Testing {contract_id}...")
        
        try:
            result = run_experiment(contract_id, num_runs)
            
            metrics = result.get('metrics', {})
            
            results[contract_id] = {
                'num_runs': num_runs,
                'R_raw': metrics.get('R_raw', 0),
                'R_anchor_pre': metrics.get('R_anchor_pre', 0),
                'R_anchor_post': metrics.get('R_anchor_post', metrics.get('R_anchor', 0)),
                'delta_rescue': metrics.get('Delta_rescue', 0),
                'rescue_rate': result.get('rescue_rate', 0),
                'mean_distance_pre': metrics.get('mean_distance_pre', 0),
                'mean_distance_post': metrics.get('mean_distance_post', 0),
                'transformation_success_rate': result.get('transformation_success_rate', 0)
            }
            
            print(f"\n  Results for {contract_id}:")
            print(f"    R_raw: {results[contract_id]['R_raw']:.3f}")
            print(f"    R_anchor (post): {results[contract_id]['R_anchor_post']:.3f}")
            print(f"    Δ_rescue: {results[contract_id]['delta_rescue']:.3f}")
            print(f"    Mean distance: {results[contract_id]['mean_distance_pre']:.3f} → {results[contract_id]['mean_distance_post']:.3f}")
            
        except Exception as e:
            print(f"\n  ❌ Error testing {contract_id}: {e}")
            import traceback
            traceback.print_exc()
            results[contract_id] = {'error': str(e)}
    
    # Save results
    output_file = Path('phase17_experiment_results.json')
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'phase': '1.7 (Oracle-Guided Template Transformation)',
            'num_runs_per_contract': num_runs,
            'total_outputs': len(contracts) * num_runs,
            'contracts': results
        }, f, indent=2)
    
    print("\n" + "="*70)
    print("EXPERIMENT COMPLETE")
    print("="*70)
    
    # Summary
    successful_contracts = [c for c, r in results.items() if 'error' not in r]
    
    if successful_contracts:
        avg_r_raw = sum(results[c]['R_raw'] for c in successful_contracts) / len(successful_contracts)
        avg_r_anchor = sum(results[c]['R_anchor_post'] for c in successful_contracts) / len(successful_contracts)
        avg_delta_rescue = sum(results[c]['delta_rescue'] for c in successful_contracts) / len(successful_contracts)
        
        perfect_transforms = sum(1 for c in successful_contracts if results[c]['R_anchor_post'] >= 0.95)
        
        print(f"\n📊 SUMMARY STATISTICS:")
        print("-" * 70)
        print(f"\nContracts tested: {len(contracts)}")
        print(f"Successful: {len(successful_contracts)}")
        print(f"\nAverage R_raw: {avg_r_raw:.3f}")
        print(f"Average R_anchor (post): {avg_r_anchor:.3f}")
        print(f"Average Δ_rescue: {avg_delta_rescue:.3f}")
        print(f"\nPerfect transformations (R_anchor ≥ 0.95): {perfect_transforms}/{len(successful_contracts)}")
        
        print("\n📋 CONTRACT BREAKDOWN:")
        print("-" * 70)
        print(f"{'Contract':<20} {'R_raw':>8} {'R_anchor':>10} {'Δ_rescue':>10}")
        print("-" * 70)
        
        for contract_id in contracts:
            if contract_id in successful_contracts:
                r = results[contract_id]
                print(f"{contract_id:<20} {r['R_raw']:>8.3f} {r['R_anchor_post']:>10.3f} {r['delta_rescue']:>10.3f}")
        
        # Compare to Phase 1.6 if available
        phase16_file = Path('PHASE16_EXPERIMENT_RESULTS.md')
        if phase16_file.exists():
            print("\n📈 COMPARISON TO PHASE 1.6:")
            print("-" * 70)
            print("Phase 1.6 avg R_anchor: 0.629")
            print(f"Phase 1.7 avg R_anchor: {avg_r_anchor:.3f}")
            improvement = avg_r_anchor - 0.629
            print(f"Improvement: {improvement:+.3f} ({improvement/0.629*100:+.1f}%)")
    
    print("\n" + "="*70)
    print(f"Results saved to: {output_file}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)


if __name__ == "__main__":
    main()
