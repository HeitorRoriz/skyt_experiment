"""
Quick test of Phase 1 validation (3 runs on fibonacci_basic)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from validate_phase1_enhancements import Phase1Validator

if __name__ == "__main__":
    print("\n🧪 Quick Validation Test (3 runs on fibonacci_basic)")
    print("Testing that enhanced properties work correctly...\n")
    
    validator = Phase1Validator()
    
    # Test with just fibonacci_basic, 3 runs
    validator.contracts = {"fibonacci_basic": validator.contracts["fibonacci_basic"]}
    results = validator.run_validation(num_runs=3)
    
    print("\n✅ Quick test complete!")
    print("\nIf this looks good, run the full validation with:")
    print("  python validate_phase1_enhancements.py")
