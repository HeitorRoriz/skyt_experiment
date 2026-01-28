#!/usr/bin/env python3
"""Analyze strict contract experiment results"""

import pandas as pd

df = pd.read_csv('outputs/metrics_summary.csv')
s = df[df['contract_id'].str.contains('_strict', na=False)].copy()
s['needed'] = (s['rescue_rate'] > 0) | (s['Delta_rescue'] > 0)

print('=' * 80)
print('SKYT EFFECTIVENESS ON STRICT CONTRACTS')
print('=' * 80)
print(f'\nTotal experiments: {len(s)}')
print(f'SKYT needed: {int(s.needed.sum())} ({100*s.needed.mean():.1f}%)')
print(f'SKYT NOT needed: {int((~s.needed).sum())} ({100*(~s.needed).mean():.1f}%)')

print('\n' + '-' * 80)
print('BY CONTRACT')
print('-' * 80)
for c in sorted(s['contract_id'].unique()):
    cs = s[s['contract_id'] == c]
    print(f'\n{c}:')
    print(f'  Experiments: {len(cs)}')
    print(f'  SKYT needed: {int(cs.needed.sum())}/{len(cs)} ({100*cs.needed.mean():.1f}%)')
    print(f'  Avg R_raw: {cs["R_raw"].mean():.3f}')
    print(f'  Avg R_anchor (post): {cs["R_anchor_post"].mean():.3f}')
    print(f'  Avg Δ_rescue: {cs["Delta_rescue"].mean():.3f}')
    print(f'  Avg rescue_rate: {cs["rescue_rate"].mean():.3f}')

print('\n' + '-' * 80)
print('BY MODEL')
print('-' * 80)
for m in sorted(s['model'].unique()):
    ms = s[s['model'] == m]
    print(f'\n{m}:')
    print(f'  Experiments: {len(ms)}')
    print(f'  SKYT needed: {int(ms.needed.sum())}/{len(ms)} ({100*ms.needed.mean():.1f}%)')
    print(f'  Avg Δ_rescue: {ms["Delta_rescue"].mean():.3f}')

print('\n' + '-' * 80)
print('BY TEMPERATURE')
print('-' * 80)
for t in sorted(s['decoding_temperature'].unique()):
    ts = s[s['decoding_temperature'] == t]
    print(f'\nTemp {t}:')
    print(f'  Experiments: {len(ts)}')
    print(f'  SKYT needed: {int(ts.needed.sum())}/{len(ts)} ({100*ts.needed.mean():.1f}%)')
    print(f'  Avg Δ_rescue: {ts["Delta_rescue"].mean():.3f}')

print('\n' + '=' * 80)
print('OVERALL METRICS')
print('=' * 80)
print(f'Avg R_raw: {s["R_raw"].mean():.3f}')
print(f'Avg R_anchor (post): {s["R_anchor_post"].mean():.3f}')
print(f'Avg Δ_rescue: {s["Delta_rescue"].mean():.3f}')
print(f'Avg rescue_rate: {s["rescue_rate"].mean():.3f}')

print('\n' + '=' * 80)
print('KEY FINDINGS')
print('=' * 80)
print(f'1. SKYT was needed in {100*s.needed.mean():.1f}% of strict contract experiments')
print(f'2. Average transformation benefit (Δ_rescue): {s["Delta_rescue"].mean():.3f}')
print(f'3. Raw repeatability improved from {s["R_raw"].mean():.3f} to {s["R_anchor_post"].mean():.3f}')
print(f'4. Average rescue rate: {100*s["rescue_rate"].mean():.1f}% of outputs transformed')
print('=' * 80)
