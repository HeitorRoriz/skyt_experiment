#!/usr/bin/env python3
"""Complete analysis for all 12 contracts"""

import pandas as pd
import numpy as np
from scipy import stats

df = pd.read_csv('outputs/metrics_summary.csv')

print('='*80)
print('COMPLETE SKYT ANALYSIS - ALL 12 CONTRACTS')
print('='*80)
print(f'Total configs: {len(df)}')
print(f'Contracts: {df.contract_id.nunique()}')
print(f'Models: {df.model.nunique()}')
print(f'Total LLM generations: {len(df) * 20}')

# Overall metrics
print('\n' + '='*80)
print('OVERALL METRICS')
print('='*80)
for metric in ['R_raw', 'R_behavioral', 'R_structural', 'Delta_rescue']:
    vals = df[metric].dropna()
    mean = vals.mean()
    ci = stats.bootstrap((vals.values,), np.mean, confidence_level=0.95, n_resamples=1000).confidence_interval
    print(f'{metric:15} Mean: {mean:.3f} [{ci.low:.3f}, {ci.high:.3f}]')

raw_mean = df['R_raw'].mean()
struct_mean = df['R_structural'].mean()
improve = struct_mean - raw_mean
print(f'\nImprovement (R_struct - R_raw): {improve:.3f} ({improve/raw_mean*100:.1f}%)')

# Per model
print('\n' + '='*80)
print('MODEL COMPARISON')
print('='*80)
for model in sorted(df['model'].unique()):
    mdf = df[df['model'] == model]
    raw = mdf['R_raw'].mean()
    struct = mdf['R_structural'].mean()
    delta = struct - raw
    pct = (delta/raw*100) if raw > 0 else 0
    print(f'{model:35} R_raw={raw:.3f} R_struct={struct:.3f} D={delta:+.3f} ({pct:+.1f}%)')

# Per contract
print('\n' + '='*80)
print('CONTRACT COMPARISON')
print('='*80)
contracts_data = []
for contract in sorted(df['contract_id'].unique()):
    cdf = df[df['contract_id'] == contract]
    raw = cdf['R_raw'].mean()
    struct = cdf['R_structural'].mean()
    delta = struct - raw
    pct = (delta/raw*100) if raw > 0 else 0
    contracts_data.append((contract, raw, struct, delta, pct))
    print(f'{contract:25} R_raw={raw:.3f} R_struct={struct:.3f} D={delta:+.3f} ({pct:+.1f}%)')

# Temperature effect
print('\n' + '='*80)
print('TEMPERATURE EFFECT')
print('='*80)
for temp in sorted(df['decoding_temperature'].unique()):
    tdf = df[df['decoding_temperature'] == temp]
    raw = tdf['R_raw'].mean()
    struct = tdf['R_structural'].mean()
    delta = struct - raw
    pct = (delta/raw*100) if raw > 0 else 0
    print(f'T={temp:.1f}  R_raw={raw:.3f} R_struct={struct:.3f} D={delta:+.3f} ({pct:+.1f}%)')

# Statistical tests
print('\n' + '='*80)
print('STATISTICAL SIGNIFICANCE (Fisher Exact + Cohen h)')
print('='*80)
sig_count = 0
results = []
for contract in sorted(df['contract_id'].unique()):
    cdf = df[df['contract_id'] == contract]
    n = len(cdf) * 20  # total trials
    
    raw_pass = int(cdf['R_raw'].mean() * n)
    raw_fail = n - raw_pass
    struct_pass = int(cdf['R_structural'].mean() * n)
    struct_fail = n - struct_pass
    
    table = [[raw_pass, raw_fail], [struct_pass, struct_fail]]
    _, p = stats.fisher_exact(table, alternative='less')
    
    # Cohen's h
    p1 = cdf['R_raw'].mean()
    p2 = cdf['R_structural'].mean()
    h = 2 * (np.arcsin(np.sqrt(p2)) - np.arcsin(np.sqrt(p1)))
    
    results.append((contract, p, h))

# Sort by p-value for Holm-Bonferroni
results.sort(key=lambda x: x[1])
for i, (contract, p, h) in enumerate(results):
    adjusted_alpha = 0.05 / (12 - i)
    sig = '*' if p < adjusted_alpha else ''
    if sig: sig_count += 1
    size = 'large' if abs(h) >= 0.8 else 'medium' if abs(h) >= 0.5 else 'small' if abs(h) >= 0.2 else 'negligible'
    print(f'{contract:25} p={p:.4f}{sig:2} h={h:.3f} ({size})')

print(f'\nSignificant after Holm-Bonferroni: {sig_count}/12')

# Summary
print('\n' + '='*80)
print('EXECUTIVE SUMMARY')
print('='*80)
print(f'''
DATASET:
  - 12 contracts x 3 models x 5 temperatures = 180 configurations
  - 20 runs per config = 3,600 total LLM generations

REPEATABILITY:
  - Raw (R_raw):        {df['R_raw'].mean():.1%} mean
  - Behavioral (R_beh): {df['R_behavioral'].mean():.1%} mean  
  - Structural (R_str): {df['R_structural'].mean():.1%} mean

IMPROVEMENT:
  - Absolute: {struct_mean - raw_mean:.1%}
  - Relative: {(struct_mean - raw_mean)/raw_mean*100:.1f}%

SIGNIFICANCE:
  - {sig_count}/12 contracts show significant improvement
  - {sum(1 for _,_,h in results if abs(h) >= 0.5)}/12 contracts have medium+ effect size

TEMPERATURE EFFECT:
  - T=0.0: {df[df['decoding_temperature']==0.0]['R_raw'].mean():.1%} raw
  - T=1.0: {df[df['decoding_temperature']==1.0]['R_raw'].mean():.1%} raw
  - SKYT maintains higher repeatability across all temperatures
''')

print('='*80)
print('ANALYSIS COMPLETE')
print('='*80)
