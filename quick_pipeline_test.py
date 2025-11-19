"""Quick pipeline test to verify Phase 1.5 fix works"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.comprehensive_experiment import ComprehensiveExperiment

print("Running quick pipeline test on fibonacci_basic (3 runs)...")
print("="*70)

experiment = ComprehensiveExperiment()
result = experiment.run_full_experiment(
    contract_template_path='contracts/templates.json',
    contract_id='fibonacci_basic',
    num_runs=3,
    temperature=0.7
)

metrics = result.get('metrics', {})

print("\n" + "="*70)
print("RESULTS:")
print("="*70)
print(f"R_raw: {metrics.get('R_raw', 0):.3f}")
print(f"R_anchor (post): {metrics.get('R_anchor_post', metrics.get('R_anchor', 0)):.3f}")
print(f"Δ_rescue: {metrics.get('Delta_rescue', 0):.3f}")
print(f"Rescue rate: {result.get('rescue_rate', 0):.1%}")

if metrics.get('R_anchor_post', 0) >= 0.9:
    print("\n✅ Transformations WORKING! Phase 1.5 fix successful!")
else:
    print("\n⚠️  Transformations still incomplete")
