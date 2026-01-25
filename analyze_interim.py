#!/usr/bin/env python3
"""Interim statistical analysis of experiment results"""

import pandas as pd
import sys
sys.path.insert(0, 'src')
from enhanced_stats import compare_repeatability_rigorous, format_rigorous_report

df = pd.read_csv('outputs/metrics_summary.csv')

print('='*80)
print('PRELIMINARY STATISTICAL ANALYSIS')
print(f'Data: {len(df)}/180 configs complete ({100*len(df)/180:.1f}%)')
print('='*80)

# Per-model analysis
print('\n## MODEL COMPARISON ##\n')
for model in df['model'].unique():
    model_df = df[df['model'] == model]
    r_raw_mean = model_df['R_raw'].mean()
    r_raw_std = model_df['R_raw'].std()
    r_struct_mean = model_df['R_structural'].mean()
    r_struct_std = model_df['R_structural'].std()
    delta_mean = model_df['Delta_rescue'].mean()
    delta_std = model_df['Delta_rescue'].std()
    
    print(f'{model}:')
    print(f'  N experiments: {len(model_df)}')
    print(f'  R_raw:        {r_raw_mean:.3f} +/- {r_raw_std:.3f}')
    print(f'  R_structural: {r_struct_mean:.3f} +/- {r_struct_std:.3f}')
    print(f'  Delta_rescue: {delta_mean:.3f} +/- {delta_std:.3f}')
    print(f'  Improvement:  {(r_struct_mean - r_raw_mean):.3f} ({100*(r_struct_mean - r_raw_mean)/r_raw_mean:.1f}%)')
    print()

# Per-contract analysis
print('\n## CONTRACT COMPARISON ##\n')
for contract in df['contract_id'].unique():
    contract_df = df[df['contract_id'] == contract]
    print(f'{contract}: N={len(contract_df)}, R_raw={contract_df["R_raw"].mean():.3f}, R_structural={contract_df["R_structural"].mean():.3f}')

# Run rigorous analysis
print('\n' + '='*80)
print('RIGOROUS STATISTICAL ANALYSIS (Prof. Nasser methods)')
print('='*80)

r_raw = df['R_raw'].tolist()
r_structural = df['R_structural'].tolist()
contracts = df['contract_id'].tolist()

analysis = compare_repeatability_rigorous(r_raw, r_structural, contracts, confidence=0.95)
print(format_rigorous_report(analysis))

# Temperature effect
print('\n## TEMPERATURE EFFECT ##\n')
for temp in sorted(df['decoding_temperature'].unique()):
    temp_df = df[df['decoding_temperature'] == temp]
    print(f'Temp {temp}: R_raw={temp_df["R_raw"].mean():.3f}, R_structural={temp_df["R_structural"].mean():.3f}')
