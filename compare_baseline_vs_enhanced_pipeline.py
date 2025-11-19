"""
Baseline vs Enhanced Pipeline Comparison

Runs the full SKYT pipeline twice:
1. With enhanced properties DISABLED (baseline)
2. With enhanced properties ENABLED (enhanced)

Measures impact on transformation success and repeatability metrics.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

from src.comprehensive_experiment import ComprehensiveExperiment
from src.foundational_properties import FoundationalProperties


def disable_enhanced_properties():
    """
    Temporarily disable enhanced properties by monkey-patching.
    
    This allows us to run baseline experiments for comparison.
    """
    original_complexity_analyzer = FoundationalProperties.complexity_analyzer
    original_type_checker = FoundationalProperties.type_checker
    original_security_analyzer = FoundationalProperties.security_analyzer
    
    # Replace with properties that always return None
    FoundationalProperties.complexity_analyzer = property(lambda self: None)
    FoundationalProperties.type_checker = property(lambda self: None)
    FoundationalProperties.security_analyzer = property(lambda self: None)
    
    return (original_complexity_analyzer, original_type_checker, original_security_analyzer)


def enable_enhanced_properties(originals):
    """Restore enhanced properties"""
    original_complexity_analyzer, original_type_checker, original_security_analyzer = originals
    
    FoundationalProperties.complexity_analyzer = original_complexity_analyzer
    FoundationalProperties.type_checker = original_type_checker
    FoundationalProperties.security_analyzer = original_security_analyzer


def run_comparison_experiment(contract_id: str, num_runs: int = 10):
    """
    Run both baseline and enhanced experiments for comparison.
    """
    print("\n" + "="*70)
    print(f"COMPARISON EXPERIMENT: {contract_id}")
    print(f"Runs: {num_runs} | Temperature: 0.7")
    print("="*70)
    
    # ==== BASELINE EXPERIMENT ====
    print("\n🔹 STEP 1: Running BASELINE experiment (AST-only)...")
    print("   Temporarily disabling enhanced properties...")
    
    originals = disable_enhanced_properties()
    
    try:
        experiment_baseline = ComprehensiveExperiment()
        baseline_result = experiment_baseline.run_full_experiment(
            contract_template_path='contracts/templates.json',
            contract_id=contract_id,
            num_runs=num_runs,
            temperature=0.7
        )
        print("   ✅ Baseline experiment complete")
    finally:
        enable_enhanced_properties(originals)
    
    # ==== ENHANCED EXPERIMENT ====
    print("\n🔸 STEP 2: Running ENHANCED experiment (radon+mypy+bandit)...")
    print("   Enhanced properties enabled...")
    
    experiment_enhanced = ComprehensiveExperiment()
    enhanced_result = experiment_enhanced.run_full_experiment(
        contract_template_path='contracts/templates.json',
        contract_id=contract_id,
        num_runs=num_runs,
        temperature=0.7
    )
    print("   ✅ Enhanced experiment complete")
    
    # ==== COMPARISON ====
    comparison = compare_results(contract_id, baseline_result, enhanced_result)
    
    # Save results
    output_file = Path(f"comparison_{contract_id}_baseline_vs_enhanced.json")
    with open(output_file, 'w') as f:
        json.dump({
            'contract_id': contract_id,
            'num_runs': num_runs,
            'temperature': 0.7,
            'baseline': {
                'metrics': baseline_result.get('metrics', {}),
                'transformation_success_rate': baseline_result.get('transformation_success_rate', 0)
            },
            'enhanced': {
                'metrics': enhanced_result.get('metrics', {}),
                'transformation_success_rate': enhanced_result.get('transformation_success_rate', 0)
            },
            'improvements': comparison['improvements']
        }, f, indent=2)
    
    print(f"\n💾 Comparison saved to: {output_file}")
    
    return comparison


def compare_results(contract_id: str, baseline_result: dict, enhanced_result: dict) -> dict:
    """Compare baseline vs enhanced results"""
    
    print("\n" + "="*70)
    print(f"📊 RESULTS COMPARISON: {contract_id}")
    print("="*70)
    
    # Extract metrics
    baseline_metrics = baseline_result.get('metrics', {})
    enhanced_metrics = enhanced_result.get('metrics', {})
    
    # Core repeatability metrics
    print("\n📈 Repeatability Metrics:")
    
    b_raw = baseline_metrics.get('R_raw', 0)
    e_raw = enhanced_metrics.get('R_raw', 0)
    print(f"  R_raw (byte-identical):")
    print(f"    Baseline:  {b_raw:.3f}")
    print(f"    Enhanced:  {e_raw:.3f}")
    print(f"    Δ:         {e_raw - b_raw:+.3f}")
    
    b_anchor = baseline_metrics.get('R_anchor_post', baseline_metrics.get('R_anchor', 0))
    e_anchor = enhanced_metrics.get('R_anchor_post', enhanced_metrics.get('R_anchor', 0))
    print(f"\n  R_anchor (post-transformation):")
    print(f"    Baseline:  {b_anchor:.3f}")
    print(f"    Enhanced:  {e_anchor:.3f}")
    print(f"    Δ:         {e_anchor - b_anchor:+.3f}")
    
    b_struct = baseline_metrics.get('R_structural', 0)
    e_struct = enhanced_metrics.get('R_structural', 0)
    print(f"\n  R_structural:")
    print(f"    Baseline:  {b_struct:.3f}")
    print(f"    Enhanced:  {e_struct:.3f}")
    print(f"    Δ:         {e_struct - b_struct:+.3f}")
    
    # Transformation effectiveness
    b_rescue = b_anchor - b_raw
    e_rescue = e_anchor - e_raw
    print(f"\n🔧 Transformation Effectiveness:")
    print(f"  Δ_rescue:")
    print(f"    Baseline:  {b_rescue:.3f}")
    print(f"    Enhanced:  {e_rescue:.3f}")
    print(f"    Δ:         {e_rescue - b_rescue:+.3f}")
    
    b_success = baseline_result.get('transformation_success_rate', 0)
    e_success = enhanced_result.get('transformation_success_rate', 0)
    print(f"\n  Success rate:")
    print(f"    Baseline:  {b_success:.1%}")
    print(f"    Enhanced:  {e_success:.1%}")
    print(f"    Δ:         {(e_success - b_success)*100:+.1f}pp")
    
    # Overall assessment
    print(f"\n" + "─"*70)
    print("💡 Key Findings:")
    
    improvements = []
    regressions = []
    
    if e_rescue > b_rescue + 0.05:  # Significant improvement threshold
        improvements.append(f"  ✅ Δ_rescue improved by {e_rescue - b_rescue:.3f}")
    elif e_rescue < b_rescue - 0.05:
        regressions.append(f"  ⚠️  Δ_rescue decreased by {b_rescue - e_rescue:.3f}")
    
    if e_success > b_success + 0.1:
        improvements.append(f"  ✅ Transformation success increased by {(e_success - b_success)*100:.1f}pp")
    elif e_success < b_success - 0.1:
        regressions.append(f"  ⚠️  Transformation success decreased by {(b_success - e_success)*100:.1f}pp")
    
    if e_anchor > b_anchor + 0.05:
        improvements.append(f"  ✅ R_anchor improved by {e_anchor - b_anchor:.3f}")
    elif e_anchor < b_anchor - 0.05:
        regressions.append(f"  ⚠️  R_anchor decreased by {b_anchor - e_anchor:.3f}")
    
    if improvements:
        print("\n  Improvements:")
        for imp in improvements:
            print(imp)
    
    if regressions:
        print("\n  Regressions:")
        for reg in regressions:
            print(reg)
    
    if not improvements and not regressions:
        print("  ➖ No significant changes detected")
        print("  ℹ️  Enhanced properties may not affect this contract type")
    
    return {
        'contract_id': contract_id,
        'baseline': baseline_metrics,
        'enhanced': enhanced_metrics,
        'improvements': {
            'R_raw': e_raw - b_raw,
            'R_anchor': e_anchor - b_anchor,
            'R_structural': e_struct - b_struct,
            'delta_rescue': e_rescue - b_rescue,
            'transformation_success': e_success - b_success
        }
    }


def main():
    """Run baseline vs enhanced comparison"""
    
    print("\n" + "="*70)
    print("BASELINE vs ENHANCED PIPELINE COMPARISON")
    print("="*70)
    print("\nThis experiment runs the FULL SKYT pipeline twice:")
    print("  1. BASELINE: AST-only properties (enhanced disabled)")
    print("  2. ENHANCED: radon + mypy + bandit enabled")
    print("\nMeasures impact on:")
    print("  • Transformation success rate")
    print("  • Δ_rescue (transformation improvement)")
    print("  • Overall repeatability (R_raw, R_anchor, R_structural)")
    
    # Test on select contracts
    contracts = [
        'fibonacci_basic',   # Simple, should show little difference
        'lru_cache',         # Complex, should show type error impact
    ]
    
    num_runs = 10
    
    results = []
    
    for contract_id in contracts:
        comparison = run_comparison_experiment(contract_id, num_runs)
        results.append(comparison)
    
    # Overall summary
    print("\n" + "="*70)
    print("OVERALL SUMMARY")
    print("="*70)
    
    for result in results:
        contract = result['contract_id']
        improvements = result['improvements']
        
        print(f"\n{contract}:")
        print(f"  Δ_rescue change: {improvements['delta_rescue']:+.3f}")
        print(f"  Transformation success change: {improvements['transformation_success']:+.1%}")
        
        if improvements['delta_rescue'] > 0.05:
            print(f"  ✅ Enhanced properties improved transformation effectiveness")
        elif improvements['delta_rescue'] < -0.05:
            print(f"  ⚠️  Enhanced properties reduced transformation effectiveness")
        else:
            print(f"  ➖ No significant change in transformation effectiveness")
    
    print("\n" + "="*70)
    print("Detailed results saved to:")
    for contract_id in contracts:
        print(f"  • comparison_{contract_id}_baseline_vs_enhanced.json")
    print("="*70)


if __name__ == "__main__":
    main()
