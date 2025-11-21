"""
Test single contract with compliance checking
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.comprehensive_experiment import ComprehensiveExperiment


def test_lru_cache():
    """Test lru_cache with compliance checking"""
    
    print("="*70)
    print("TESTING LRU_CACHE WITH CONTRACT COMPLIANCE")
    print("="*70)
    
    experiment = ComprehensiveExperiment()
    
    result = experiment.run_full_experiment(
        contract_template_path='contracts/templates.json',
        contract_id='lru_cache',
        num_runs=5,  # Just 5 runs for testing
        temperature=0.7
    )
    
    if "error" in result:
        print(f"\n❌ Error: {result['error']}")
        return False
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    metrics = result.get('metrics', {})
    print(f"\nR_raw: {metrics.get('R_raw', 0):.3f}")
    print(f"R_anchor (post): {metrics.get('R_anchor_post', 0):.3f}")
    print(f"Delta_rescue: {metrics.get('Delta_rescue', 0):.3f}")
    print(f"Mean distance: {metrics.get('mean_distance_pre', 0):.3f} → {metrics.get('mean_distance_post', 0):.3f}")
    
    return True


if __name__ == "__main__":
    success = test_lru_cache()
    
    if success:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")
