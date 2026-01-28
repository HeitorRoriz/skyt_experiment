#!/usr/bin/env python3
"""Comprehensive data verification for SKYT experiment results"""

import pandas as pd
import json
import sys
sys.path.insert(0, 'src')

# Load data
df = pd.read_csv('outputs/metrics_summary.csv')

print('='*80)
print('DATA INTEGRITY CHECK')
print('='*80)

errors = []

# 1. Row count
print('\n1. ROW COUNT')
expected_rows = 180
actual_rows = len(df)
print(f'   Expected: {expected_rows}')
print(f'   Actual: {actual_rows}')
if actual_rows == expected_rows:
    print('   Status: OK')
else:
    print('   Status: MISMATCH')
    errors.append(f'Row count mismatch: {actual_rows} vs {expected_rows}')

# 2. Model distribution
print('\n2. MODEL DISTRIBUTION')
model_counts = df.groupby('model').size()
for model, count in model_counts.items():
    expected = 60
    if count == expected:
        print(f'   {model}: {count} - OK')
    else:
        print(f'   {model}: {count} (expected {expected}) - MISMATCH')
        errors.append(f'Model {model} count mismatch')

# 3. Contract distribution
print('\n3. CONTRACT DISTRIBUTION')
contract_counts = df.groupby('contract_id').size()
for contract, count in sorted(contract_counts.items()):
    expected = 15
    if count == expected:
        print(f'   {contract}: {count} - OK')
    else:
        print(f'   {contract}: {count} (expected {expected}) - MISMATCH')
        errors.append(f'Contract {contract} count mismatch')

# 4. Temperature distribution
print('\n4. TEMPERATURE DISTRIBUTION')
temp_counts = df.groupby('decoding_temperature').size()
for temp, count in sorted(temp_counts.items()):
    expected = 36
    if count == expected:
        print(f'   Temp {temp}: {count} - OK')
    else:
        print(f'   Temp {temp}: {count} (expected {expected}) - MISMATCH')
        errors.append(f'Temperature {temp} count mismatch')

# 5. Missing values
print('\n5. MISSING VALUES CHECK')
critical_cols = ['R_raw', 'R_behavioral', 'R_structural', 'Delta_rescue', 'model', 'contract_id']
for col in critical_cols:
    if col in df.columns:
        missing = df[col].isna().sum()
        if missing == 0:
            print(f'   {col}: OK (no missing)')
        else:
            print(f'   {col}: MISSING {missing} values')
            errors.append(f'{col} has {missing} missing values')
    else:
        print(f'   {col}: COLUMN NOT FOUND')
        errors.append(f'{col} column not found')

# 6. Value ranges
print('\n6. VALUE RANGE CHECK')
for col in ['R_raw', 'R_behavioral', 'R_structural']:
    min_val = df[col].min()
    max_val = df[col].max()
    in_range = 0 <= min_val and max_val <= 1
    if in_range:
        print(f'   {col}: [{min_val:.3f}, {max_val:.3f}] - OK')
    else:
        print(f'   {col}: [{min_val:.3f}, {max_val:.3f}] - OUT OF RANGE')
        errors.append(f'{col} out of range')

# 7. Unique models
print('\n7. UNIQUE MODELS')
expected_models = ['gpt-4o-mini', 'gpt-4o', 'claude-sonnet-4-5-20250929']
actual_models = list(df['model'].unique())
for m in actual_models:
    print(f'   - {m}')
if set(actual_models) == set(expected_models):
    print('   All expected models present: OK')
else:
    print(f'   Expected: {expected_models}')
    errors.append('Model set mismatch')

# 8. Unique contracts
print('\n8. UNIQUE CONTRACTS')
expected_contracts = [
    'fibonacci_basic', 'fibonacci_recursive', 'slugify', 'balanced_brackets',
    'gcd', 'binary_search', 'lru_cache', 'merge_sort', 'quick_sort',
    'factorial', 'is_palindrome', 'is_prime'
]
actual_contracts = sorted(df['contract_id'].unique())
for c in actual_contracts:
    print(f'   - {c}')
if set(actual_contracts) == set(expected_contracts):
    print('   All expected contracts present: OK')
else:
    missing = set(expected_contracts) - set(actual_contracts)
    extra = set(actual_contracts) - set(expected_contracts)
    if missing:
        print(f'   Missing: {missing}')
        errors.append(f'Missing contracts: {missing}')
    if extra:
        print(f'   Extra: {extra}')

# 9. Cross-check: Each model-contract-temp combination
print('\n9. CONFIGURATION COMPLETENESS')
expected_configs = len(expected_models) * len(expected_contracts) * 5  # 5 temps
combos = df.groupby(['model', 'contract_id', 'decoding_temperature']).size()
actual_configs = len(combos)
if actual_configs == expected_configs:
    print(f'   All {expected_configs} configurations present: OK')
else:
    print(f'   Expected {expected_configs}, found {actual_configs} - MISMATCH')
    errors.append('Configuration completeness mismatch')

# Summary
print('\n' + '='*80)
print('VERIFICATION SUMMARY')
print('='*80)
if errors:
    print(f'\nFOUND {len(errors)} ERRORS:')
    for e in errors:
        print(f'   - {e}')
else:
    print('\nALL CHECKS PASSED - DATA IS VALID')
print('='*80)
