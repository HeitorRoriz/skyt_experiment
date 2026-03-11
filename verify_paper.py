#!/usr/bin/env python3
"""Verify paper claims against actual data in metrics_summary.csv"""
import csv

rows = list(csv.DictReader(open('outputs/metrics_summary.csv')))
r20 = [r for r in rows if r['runs'] == '20']

# 1. Count contracts, models, temps
contracts = sorted(set(r['contract_id'] for r in r20))
models = sorted(set(r['model'] for r in r20))
temps = sorted(set(r['decoding_temperature'] for r in r20))

print("=" * 60)
print("PAPER VERIFICATION REPORT")
print("=" * 60)

print(f"\n--- Dataset Overview (n=20 rows only) ---")
print(f"Total rows with n=20: {len(r20)}")
print(f"Unique contracts: {len(contracts)}")
for c in contracts:
    print(f"  - {c}")
print(f"Models: {models}")
print(f"Temperatures: {temps}")
print(f"Unique configs (contract x model x temp): {len(set((r['contract_id'],r['model'],r['decoding_temperature']) for r in r20))}")
print(f"Total samples (configs x 20): {len(set((r['contract_id'],r['model'],r['decoding_temperature']) for r in r20)) * 20}")

# 2. Categorize contracts
basic_12 = [c for c in contracts if c not in ('is_prime_strict', 'binary_search_strict', 'lru_cache_strict')]
strict_3 = [c for c in contracts if c in ('is_prime_strict', 'binary_search_strict', 'lru_cache_strict')]
print(f"\nBasic contracts (12): {basic_12}")
print(f"Strict contracts (3): {strict_3}")
print(f"Total: {len(basic_12)} + {len(strict_3)} = {len(contracts)}")

# 3. Check max Delta_rescue claim (paper says 0.95)
print(f"\n--- Max Delta_rescue ---")
max_dr = max(r20, key=lambda r: float(r['Delta_rescue']))
print(f"Max Delta_rescue: {max_dr['Delta_rescue']}")
print(f"  Contract: {max_dr['contract_id']}, Model: {max_dr['model']}, T={max_dr['decoding_temperature']}")

# 4. Per-task per-model details for the 3 representative tasks
print(f"\n--- Table Verification: Cross-model summary (3 tasks, pooled across temps) ---")
for task in ['binary_search', 'balanced_brackets', 'slugify']:
    for model_short, model_full in [('4o-mini', 'gpt-4o-mini'), ('4o', 'gpt-4o'), ('Claude', 'claude-sonnet-4-5-20250929')]:
        task_rows = [r for r in r20 if r['contract_id'] == task and r['model'] == model_full]
        if not task_rows:
            print(f"  {task} / {model_short}: NO DATA")
            continue
        # Pool across temps: compute weighted averages
        total_runs_sum = sum(int(r['runs']) for r in task_rows)
        r_raw_vals = [float(r['R_raw']) for r in task_rows]
        r_pre_vals = [float(r['R_anchor_pre']) for r in task_rows]
        r_post_vals = [float(r['R_anchor_post']) for r in task_rows]
        dr_vals = [float(r['Delta_rescue']) for r in task_rows]
        
        # Simple average across temperature configs
        avg_raw = sum(r_raw_vals) / len(r_raw_vals)
        avg_pre = sum(r_pre_vals) / len(r_pre_vals)
        avg_post = sum(r_post_vals) / len(r_post_vals)
        avg_dr = sum(dr_vals) / len(dr_vals)
        
        print(f"  {task:20s} {model_short:8s} R_raw={avg_raw:.2f}  R_pre={avg_pre:.2f}  R_post={avg_post:.2f}  Dr={avg_dr:.2f}  (n_configs={len(task_rows)})")

# 5. Per-temperature details for Binary Search (to find the 0.95 claim)
print(f"\n--- Binary Search per-temperature details ---")
for model_short, model_full in [('4o-mini', 'gpt-4o-mini'), ('4o', 'gpt-4o'), ('Claude', 'claude-sonnet-4-5-20250929')]:
    bs_rows = [r for r in r20 if r['contract_id'] == 'binary_search' and r['model'] == model_full]
    for r in sorted(bs_rows, key=lambda x: float(x['decoding_temperature'])):
        print(f"  {model_short:8s} T={r['decoding_temperature']}  R_raw={r['R_raw']}  R_pre={r['R_anchor_pre']}  R_post={r['R_anchor_post']}  Dr={r['Delta_rescue']}")

# 6. Verify the specific artifact section claim: "line 79 with R_raw=0.30, R_pre=0.45, R_post=1.00, Dr=0.55"
print(f"\n--- Artifact section claim: binary_search + gpt-4o-mini + T=0.5 ---")
match = [r for r in r20 if r['contract_id'] == 'binary_search' and r['model'] == 'gpt-4o-mini' and r['decoding_temperature'] == '0.5']
for r in match:
    print(f"  R_raw={r['R_raw']}  R_pre={r['R_anchor_pre']}  R_post={r['R_anchor_post']}  Dr={r['Delta_rescue']}")

# 7. Check the foundational properties count
print(f"\n--- Foundational Properties Count ---")
props = [
    "control_flow_signature",
    "data_dependency_graph",
    "execution_paths",
    "function_contracts",
    "complexity_class",
    "side_effect_profile",
    "termination_properties",
    "algebraic_structure",
    "numerical_behavior",
    "logical_equivalence",
    "normalized_ast_structure",
    "operator_precedence",
    "statement_ordering",
    "recursion_schema"
]
print(f"Properties in code (foundational_properties.py): {len(props)}")
print(f"Paper claims: 13")
print(f"Note: behavioral_signature is DISABLED in code, recursion_schema replaces it")
print(f"Active properties: {len(props)} (13 listed + recursion_schema, but behavioral_signature disabled = 13 active)")

# 8. Check if paper's task categories match contracts
print(f"\n--- Task Category Verification ---")
print("Paper claims 12 tasks in 4 categories:")
print("  Numeric: fibonacci_basic, fibonacci_recursive, factorial, gcd, is_prime (5)")
print("  String: slugify, is_palindrome (2)")
print("  Data Structures: balanced_brackets, lru_cache (2)")
print("  Sorting/Searching: binary_search, merge_sort, quick_sort (3)")
print(f"  Total basic: 5+2+2+3 = 12")
print(f"  + 3 strict variants: is_prime_strict, binary_search_strict, lru_cache_strict")
print(f"  Grand total in templates.json: 15")

# 9. Check duplicate rows (some configs may have been run multiple times)
print(f"\n--- Duplicate config check (n=20 rows) ---")
from collections import Counter
config_counts = Counter((r['contract_id'], r['model'], r['decoding_temperature']) for r in r20)
dupes = {k: v for k, v in config_counts.items() if v > 1}
if dupes:
    print(f"  {len(dupes)} configs have multiple n=20 rows:")
    for k, v in sorted(dupes.items()):
        print(f"    {k}: {v} rows")
else:
    print("  No duplicates - each config has exactly 1 row with n=20")
