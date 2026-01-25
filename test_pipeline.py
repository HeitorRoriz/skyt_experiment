#!/usr/bin/env python3
"""
Comprehensive Pipeline Test - Verify all components before full experiment
Tests model attribution, metrics calculation, file I/O, and data integrity
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

def test_model_attribution():
    """Test that model names are correctly tracked"""
    print("\n" + "="*80)
    print("TEST 1: Model Attribution")
    print("="*80)
    
    models = ["gpt-4o-mini", "gpt-4o", "claude-sonnet-4-5-20250929"]
    test_contract = "fibonacci_basic"
    test_temp = 0.0
    test_runs = 3
    
    test_results = []
    
    for model in models:
        print(f"\nTesting model: {model}")
        
        # Run single experiment
        cmd = f'python main.py --contract {test_contract} --runs {test_runs} --temperature {test_temp} --model {model}'
        print(f"  Command: {cmd}")
        
        result = os.system(cmd)
        
        if result != 0:
            print(f"  ❌ FAILED: Command returned exit code {result}")
            return False
        
        print(f"  ✓ Experiment completed")
        
        # Check if model was saved correctly in JSON
        json_files = sorted(Path("outputs").glob(f"{test_contract}_temp{test_temp}_*.json"))
        if not json_files:
            print(f"  ❌ FAILED: No JSON output found")
            return False
        
        latest_json = json_files[-1]
        with open(latest_json) as f:
            data = json.load(f)
        
        saved_model = data.get("model", "NOT_FOUND")
        print(f"  Model in JSON: {saved_model}")
        
        if saved_model != model:
            print(f"  ❌ FAILED: Expected '{model}', got '{saved_model}'")
            return False
        
        test_results.append({
            "model": model,
            "json_model": saved_model,
            "json_file": str(latest_json)
        })
        
        print(f"  ✓ Model correctly saved in JSON")
    
    # Check CSV
    print("\nChecking metrics_summary.csv...")
    csv_path = "outputs/metrics_summary.csv"
    
    if not os.path.exists(csv_path):
        print(f"  ❌ FAILED: CSV not found at {csv_path}")
        return False
    
    df = pd.read_csv(csv_path)
    
    # Get last 3 rows (our test experiments)
    recent = df.tail(3)
    
    print(f"  Last 3 CSV entries:")
    for idx, row in recent.iterrows():
        print(f"    - {row['contract_id']}, temp={row['decoding_temperature']}, model={row['model']}")
    
    # Verify models match
    csv_models = recent['model'].tolist()
    
    if set(csv_models) != set(models):
        print(f"  ❌ FAILED: CSV models {csv_models} don't match expected {models}")
        return False
    
    print(f"  ✓ All models correctly saved in CSV")
    
    print("\n✅ TEST 1 PASSED: Model attribution working correctly")
    return True


def test_metrics_calculation():
    """Test that all metrics are calculated and saved"""
    print("\n" + "="*80)
    print("TEST 2: Metrics Calculation")
    print("="*80)
    
    csv_path = "outputs/metrics_summary.csv"
    df = pd.read_csv(csv_path)
    
    required_columns = [
        'R_raw', 'R_anchor_pre', 'R_anchor_post', 'Delta_rescue',
        'R_behavioral', 'R_structural',
        'mean_distance_pre', 'mean_distance_post',
        'canon_coverage', 'rescue_rate'
    ]
    
    print(f"\nChecking for required columns...")
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        print(f"  ❌ FAILED: Missing columns: {missing}")
        return False
    
    print(f"  ✓ All required columns present")
    
    # Check for NaN values in critical columns
    print(f"\nChecking for missing values...")
    last_row = df.iloc[-1]
    
    for col in required_columns:
        value = last_row[col]
        if pd.isna(value):
            print(f"  ❌ FAILED: Column '{col}' has NaN value")
            return False
    
    print(f"  ✓ No missing values in critical columns")
    
    # Verify metric ranges
    print(f"\nVerifying metric ranges...")
    issues = []
    
    if not (0 <= last_row['R_raw'] <= 1):
        issues.append(f"R_raw={last_row['R_raw']} out of range [0,1]")
    if not (0 <= last_row['R_behavioral'] <= 1):
        issues.append(f"R_behavioral={last_row['R_behavioral']} out of range [0,1]")
    if not (0 <= last_row['R_structural'] <= 1):
        issues.append(f"R_structural={last_row['R_structural']} out of range [0,1]")
    
    if issues:
        for issue in issues:
            print(f"  ❌ {issue}")
        return False
    
    print(f"  ✓ All metrics in valid ranges")
    
    print("\n✅ TEST 2 PASSED: Metrics calculation working correctly")
    return True


def test_file_structure():
    """Test that output files are created with correct structure"""
    print("\n" + "="*80)
    print("TEST 3: File Structure")
    print("="*80)
    
    required_dirs = [
        "outputs",
        "outputs/analysis",
        "outputs/canon"
    ]
    
    print(f"\nChecking directory structure...")
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"  ❌ FAILED: Directory missing: {dir_path}")
            return False
        print(f"  ✓ {dir_path}")
    
    print(f"\nChecking required files...")
    required_files = [
        "outputs/metrics_summary.csv"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"  ❌ FAILED: File missing: {file_path}")
            return False
        print(f"  ✓ {file_path}")
    
    print("\n✅ TEST 3 PASSED: File structure correct")
    return True


def main():
    """Run all tests"""
    print("="*80)
    print("SKYT PIPELINE COMPREHENSIVE TEST")
    print("="*80)
    print("\nThis will run 3 small experiments to verify:")
    print("  1. Model attribution is tracked correctly")
    print("  2. All metrics are calculated and saved")
    print("  3. File structure is correct")
    print("\nEstimated time: 2-3 minutes")
    print("Estimated cost: ~$0.10")
    
    input("\nPress Enter to start tests...")
    
    # Run tests
    tests = [
        ("Model Attribution", test_model_attribution),
        ("Metrics Calculation", test_metrics_calculation),
        ("File Structure", test_file_structure)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED - System ready for full experiment!")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - Fix issues before running full experiment")
        return 1


if __name__ == "__main__":
    sys.exit(main())
