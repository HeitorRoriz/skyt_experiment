#!/usr/bin/env python3
"""Check the actual JSON structure of Claude experiment files"""

import json
import glob

# Find Claude experiment files
files = sorted(glob.glob('outputs/*_strict_temp*.json'))

claude_files = []
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if data.get('model') == 'claude-sonnet-4-5-20250929':
                claude_files.append(f)
    except:
        pass

if not claude_files:
    print("No Claude files found!")
    exit(1)

# Check the latest one
latest = claude_files[-1]
print(f"Checking: {latest}\n")

with open(latest, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Top-level keys in experiment result:")
for key in sorted(data.keys()):
    value = data[key]
    if isinstance(value, (str, int, float, bool)):
        print(f"  {key}: {value}")
    elif isinstance(value, dict):
        print(f"  {key}: <dict with {len(value)} keys>")
    elif isinstance(value, list):
        print(f"  {key}: <list with {len(value)} items>")
    else:
        print(f"  {key}: {type(value)}")

print("\n" + "="*80)
print("Checking canon-related fields:")
print("="*80)
print(f"canon_data: {data.get('canon_data')}")
print(f"canon_created: {data.get('canon_created')}")
print(f"canon_info: {data.get('canon_info')}")

print("\n" + "="*80)
print("Checking transformation_results structure:")
print("="*80)
if 'transformation_results' in data and len(data['transformation_results']) > 0:
    print(f"Number of transformation results: {len(data['transformation_results'])}")
    print(f"First transformation result keys: {list(data['transformation_results'][0].keys())}")
    print(f"First transformation result: {data['transformation_results'][0]}")
else:
    print("No transformation_results or empty list")

print("\n" + "="*80)
print("Checking metrics:")
print("="*80)
metrics = data.get('metrics', {})
for key in ['R_raw', 'R_anchor_pre', 'R_anchor_post', 'Delta_rescue', 'rescue_rate']:
    print(f"{key}: {metrics.get(key)}")
