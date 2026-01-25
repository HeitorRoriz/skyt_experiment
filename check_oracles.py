#!/usr/bin/env python3
"""Check oracle tests for failing contracts"""

import json

f = open('contracts/templates.json')
data = json.load(f)

for contract in ['quick_sort', 'factorial', 'is_palindrome', 'is_prime']:
    print(f'\n=== {contract} ===')
    if contract in data:
        c = data[contract]
        tests = c.get('oracle_tests', [])
        print(f'Oracle tests: {len(tests)} tests')
        for t in tests[:3]:
            print(f'  {t}')
        
        # Check function name
        print(f'Function name: {c.get("function_name", "NOT SPECIFIED")}')
        print(f'Description: {c.get("description", "")[:50]}...')
    else:
        print('NOT FOUND in templates.json')
