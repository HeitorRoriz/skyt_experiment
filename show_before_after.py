#!/usr/bin/env python3
"""Show before/after comparison of simple vs strict contracts"""

import json

with open('contracts/templates.json') as f:
    t = json.load(f)

pairs = [
    ('is_prime', 'is_prime_strict', 'EASY'),
    ('binary_search', 'binary_search_strict', 'MEDIUM'),
    ('lru_cache', 'lru_cache_strict', 'HARD')
]

for simple, strict, difficulty in pairs:
    s = t[simple]
    st = t[strict]
    
    print("=" * 80)
    print(f"{difficulty}: {simple}")
    print("=" * 80)
    
    print("\n[BEFORE - SIMPLE CONTRACT]")
    print("-" * 40)
    print(f"Prompt:\n{s['prompt']}\n")
    
    s_vars = s.get('constraints', {}).get('variable_naming', {})
    print(f"Fixed variables: {s_vars.get('fixed_variables', [])}")
    print(f"Rules: None (just basic correctness)")
    
    print("\n" + "=" * 80)
    print(f"{difficulty}: {strict}")
    print("=" * 80)
    
    print("\n[AFTER - STRICT CONTRACT]")
    print("-" * 40)
    print(f"Prompt:\n{st['prompt']}\n")
    
    st_const = st.get('constraints', {})
    st_vars = st_const.get('variable_naming', {})
    
    print(f"Fixed variables: {st_vars.get('fixed_variables', [])}")
    
    print(f"\nNASA Power of 10 Rules:")
    for k, v in st_const.get('nasa_power_of_10', {}).items():
        print(f"  - {k}: {v}")
    
    print(f"\nMISRA C Rules:")
    for k, v in st_const.get('misra_c_rules', {}).items():
        print(f"  - {k}: {v}")
    
    if 'required_patterns' in st_const:
        print(f"\nRequired patterns: {st_const['required_patterns']}")
    if 'forbidden_patterns' in st_const:
        print(f"Forbidden patterns: {st_const['forbidden_patterns']}")
    
    print("\n\n")
