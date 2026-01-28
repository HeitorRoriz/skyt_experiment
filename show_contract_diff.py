#!/usr/bin/env python3
"""Show difference between simple and strict contracts"""

import json

with open('contracts/templates.json') as f:
    t = json.load(f)

pairs = [
    ('is_prime', 'is_prime_strict', 'EASY'),
    ('binary_search', 'binary_search_strict', 'MEDIUM'),
    ('lru_cache', 'lru_cache_strict', 'HARD')
]

for simple, strict, difficulty in pairs:
    print('='*80)
    print(f'{difficulty}: {simple} vs {strict}')
    print('='*80)
    
    s = t[simple]
    st = t[strict]
    
    print(f'\n--- SIMPLE PROMPT (what LLM sees) ---')
    print(s['prompt'])
    
    print(f'\n--- STRICT PROMPT (what LLM sees) ---')
    print(st['prompt'])
    
    print(f'\n--- KEY CONSTRAINT DIFFERENCES ---')
    
    s_const = s.get('constraints', {})
    st_const = st.get('constraints', {})
    
    # Variable naming diff
    s_vars = s_const.get('variable_naming', {})
    st_vars = st_const.get('variable_naming', {})
    
    print(f'\nVariable Naming:')
    print(f'  Simple fixed vars:  {s_vars.get("fixed_variables", [])}')
    print(f'  Strict fixed vars:  {st_vars.get("fixed_variables", [])}')
    
    if 'misra_rules' in st_const:
        print(f'\nMISRA C Rules Added:')
        for rule, desc in st_const['misra_rules'].items():
            print(f'  - {rule}: {desc}')
    
    if 'do178c_rules' in st_const:
        print(f'\nDO-178C Rules Added:')
        for rule, val in st_const['do178c_rules'].items():
            print(f'  - {rule}: {val}')
    
    if 'required_patterns' in st_const:
        print(f'\nRequired Code Patterns:')
        for p in st_const['required_patterns']:
            print(f'  + MUST have: "{p}"')
    
    if 'forbidden_patterns' in st_const:
        print(f'\nForbidden Code Patterns:')
        for p in st_const['forbidden_patterns']:
            print(f'  - CANNOT use: "{p}"')
    
    print('\n')
