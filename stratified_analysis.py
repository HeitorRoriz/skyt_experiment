#!/usr/bin/env python3
"""Stratified analysis by contract difficulty"""

import pandas as pd
import numpy as np
from scipy import stats

df = pd.read_csv('outputs/metrics_summary.csv')

print('='*80)
print('STRATIFIED ANALYSIS BY CONTRACT DIFFICULTY')
print('='*80)

# Calculate per-contract stats
contracts = []
for c in df['contract_id'].unique():
    cdf = df[df['contract_id'] == c]
    contracts.append({
        'contract': c,
        'R_raw': cdf['R_raw'].mean(),
        'R_struct': cdf['R_structural'].mean(),
        'delta': cdf['R_structural'].mean() - cdf['R_raw'].mean()
    })

cdf = pd.DataFrame(contracts)

# Stratify by baseline difficulty
cdf['stratum'] = pd.cut(cdf['R_raw'], 
    bins=[0, 0.6, 0.8, 1.0], 
    labels=['Hard (<60%)', 'Medium (60-80%)', 'Easy (>80%)'])

print('\nCONTRACTS BY DIFFICULTY STRATUM:')
print('-'*80)
for stratum in ['Hard (<60%)', 'Medium (60-80%)', 'Easy (>80%)']:
    sdf = cdf[cdf['stratum'] == stratum]
    print(f'\n{stratum}:')
    for _, row in sdf.iterrows():
        c = row['contract']
        r = row['R_raw']
        s = row['R_struct']
        d = row['delta']
        print(f'  {c:25} R_raw={r:.1%} -> R_struct={s:.1%} (+{d:.1%})')

print('\n' + '='*80)
print('AGGREGATE BY STRATUM')
print('='*80)
print(f'{"Stratum":<20} {"N":>3} {"R_raw":>10} {"R_struct":>10} {"D Abs":>10} {"D Rel":>10}')
print('-'*65)
for stratum in ['Hard (<60%)', 'Medium (60-80%)', 'Easy (>80%)']:
    sdf = cdf[cdf['stratum'] == stratum]
    n = len(sdf)
    raw = sdf['R_raw'].mean()
    struct = sdf['R_struct'].mean()
    delta_abs = struct - raw
    delta_rel = (delta_abs / raw * 100) if raw > 0 else 0
    print(f'{stratum:<20} {n:>3} {raw:>10.1%} {struct:>10.1%} {delta_abs:>+10.1%} {delta_rel:>+9.1f}%')

# Get contract lists by stratum
hard_contracts = cdf[cdf['stratum'] == 'Hard (<60%)']['contract'].tolist()
med_contracts = cdf[cdf['stratum'] == 'Medium (60-80%)']['contract'].tolist()
easy_contracts = cdf[cdf['stratum'] == 'Easy (>80%)']['contract'].tolist()

print('\n' + '='*80)
print('STATISTICAL TESTS BY STRATUM')
print('='*80)

for name, contract_list in [('Hard', hard_contracts), ('Medium', med_contracts), ('Easy', easy_contracts)]:
    if not contract_list:
        continue
    sdf = df[df['contract_id'].isin(contract_list)]
    n = len(sdf) * 20
    raw = sdf['R_raw'].mean()
    struct = sdf['R_structural'].mean()
    
    # Bootstrap CI for improvement
    improvements = sdf['R_structural'] - sdf['R_raw']
    ci = stats.bootstrap((improvements.values,), np.mean, confidence_level=0.95, n_resamples=1000).confidence_interval
    
    print(f'\n{name} contracts ({len(contract_list)}):')
    print(f'  Configs: {len(sdf)}, Generations: {n}')
    print(f'  R_raw: {raw:.1%}, R_struct: {struct:.1%}')
    print(f'  Improvement: {struct-raw:+.1%} [{ci.low:+.1%}, {ci.high:+.1%}] 95% CI')

# Paper summary
print('\n' + '='*80)
print('PAPER-READY SUMMARY')
print('='*80)

hard_df = df[df['contract_id'].isin(hard_contracts)]
med_df = df[df['contract_id'].isin(med_contracts)]
easy_df = df[df['contract_id'].isin(easy_contracts)]

h_raw = hard_df['R_raw'].mean()
h_str = hard_df['R_structural'].mean()
m_raw = med_df['R_raw'].mean()
m_str = med_df['R_structural'].mean()
e_raw = easy_df['R_raw'].mean()
e_str = easy_df['R_structural'].mean()

print(f'''
HARD CONTRACTS (baseline <60%): {hard_contracts}
  - {len(hard_contracts)} contracts, {len(hard_df)} configs, {len(hard_df)*20} generations
  - Baseline: {h_raw:.1%}
  - SKYT: {h_str:.1%}  
  - Improvement: +{h_str-h_raw:.1%} ({(h_str-h_raw)/h_raw*100:.0f}% relative)

MEDIUM CONTRACTS (baseline 60-80%): {med_contracts}
  - {len(med_contracts)} contracts, {len(med_df)} configs, {len(med_df)*20} generations
  - Baseline: {m_raw:.1%}
  - SKYT: {m_str:.1%}
  - Improvement: +{m_str-m_raw:.1%} ({(m_str-m_raw)/m_raw*100:.0f}% relative)

EASY CONTRACTS (baseline >80%): {easy_contracts}
  - {len(easy_contracts)} contracts, {len(easy_df)} configs, {len(easy_df)*20} generations
  - Baseline: {e_raw:.1%}
  - SKYT: {e_str:.1%}
  - Improvement: +{e_str-e_raw:.1%} ({(e_str-e_raw)/e_raw*100:.0f}% relative)
''')

print('='*80)
