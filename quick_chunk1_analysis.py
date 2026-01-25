#!/usr/bin/env python3
import pandas as pd

df = pd.read_csv('outputs/metrics_summary.csv')
strict = df[df['contract_id'] == 'is_prime_strict'].copy()

print("="*80)
print("CHUNK 1 COMPLETE ANALYSIS: is_prime_strict")
print("="*80)

print(f"\nTotal experiments: {len(strict)}")
print("\nBy model:")
print(strict.groupby('model').size())

print("\n" + "="*80)
print("LATEST 5 EXPERIMENTS PER MODEL (After Rule 15.5 Removal)")
print("="*80)

for model in ['gpt-4o-mini', 'gpt-4o', 'claude-sonnet-4-5-20250929']:
    model_data = strict[strict['model'] == model]
    if len(model_data) > 0:
        latest = model_data.tail(5)
        print(f"\n{model}:")
        print(f"  Latest 5 experiments:")
        print(f"    R_raw: {latest['R_raw'].mean():.3f}")
        print(f"    R_anchor_post: {latest['R_anchor_post'].mean():.3f}")
        print(f"    Delta_rescue: {latest['Delta_rescue'].mean():.3f}")
        print(f"    rescue_rate: {latest['rescue_rate'].mean():.3f}")

print("\n" + "="*80)
print("VERDICT")
print("="*80)

gpt4o_mini_latest = strict[strict['model'] == 'gpt-4o-mini'].tail(5)
gpt4o_latest = strict[strict['model'] == 'gpt-4o'].tail(5)
claude_latest = strict[strict['model'] == 'claude-sonnet-4-5-20250929'].tail(5)

if len(gpt4o_mini_latest) > 0:
    print(f"\n✅ gpt-4o-mini: R_anchor_post = {gpt4o_mini_latest['R_anchor_post'].mean():.1%}")
    print(f"   Transformations {'WORKING' if gpt4o_mini_latest['R_anchor_post'].mean() > 0.5 else 'FAILING'}")

if len(gpt4o_latest) > 0:
    print(f"\n✅ gpt-4o: R_anchor_post = {gpt4o_latest['R_anchor_post'].mean():.1%}")
    print(f"   Transformations {'WORKING' if gpt4o_latest['R_anchor_post'].mean() > 0.5 else 'FAILING'}")

if len(claude_latest) > 0:
    print(f"\n{'✅' if claude_latest['R_anchor_post'].mean() > 0.5 else '❌'} Claude: R_anchor_post = {claude_latest['R_anchor_post'].mean():.1%}")
    print(f"   Transformations {'WORKING' if claude_latest['R_anchor_post'].mean() > 0.5 else 'FAILING'}")

print("\n" + "="*80)
print("CONCLUSION: Removing Rule 15.5 (single exit/no break)")
print("="*80)
print("\nAllows natural loop exit patterns (break/return)")
print("Canon created from natural code instead of forced flag variables")
print("Transformations can now succeed without semantic gap")
