#!/usr/bin/env python3
"""Investigate why Claude experiments show R_anchor_post = 0.0"""

import json
import glob

# Find latest Claude experiment files
files = sorted(glob.glob('outputs/*_strict_temp*.json'))

# Check which files are Claude experiments
print("Checking experiment files for Claude model...\n")

claude_files = []
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if data.get('model') == 'claude-sonnet-4-5-20250929':
                claude_files.append(f)
    except:
        pass

print(f"Found {len(claude_files)} Claude experiment files\n")

if not claude_files:
    print("No Claude files found!")
    exit(1)

# Analyze the most recent one
latest = claude_files[-1]
print(f"Analyzing: {latest}\n")

with open(latest, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print("EXPERIMENT INFO")
print("=" * 80)
print(f"Contract: {data.get('contract_id')}")
print(f"Model: {data.get('model')}")
print(f"Temperature: {data.get('temperature')}")
print(f"Runs: {data.get('num_runs')}")

print("\n" + "=" * 80)
print("CANON INFO")
print("=" * 80)
canon_info = data.get('canon_info', {})
print(f"Canon exists: {canon_info.get('canon_exists')}")
print(f"Canon source: {canon_info.get('canon_source')}")
print(f"Canon code length: {len(canon_info.get('canon_code', ''))}")

print("\n" + "=" * 80)
print("METRICS")
print("=" * 80)
metrics = data.get('metrics', {})
print(f"R_raw: {metrics.get('R_raw')}")
print(f"R_anchor (pre): {metrics.get('R_anchor_pre')}")
print(f"R_anchor (post): {metrics.get('R_anchor_post')}")
print(f"Delta_rescue: {metrics.get('Delta_rescue')}")
print(f"Rescue rate: {metrics.get('rescue_rate')}")

print("\n" + "=" * 80)
print("TRANSFORMATION RESULTS (first 3)")
print("=" * 80)
for i, t in enumerate(data.get('transformation_results', [])[:3], 1):
    print(f"\nOutput {i}:")
    print(f"  Success: {t.get('success')}")
    print(f"  Distance pre: {t.get('distance_pre')}")
    print(f"  Distance post: {t.get('distance_post')}")
    print(f"  Matches canon: {t.get('matches_canon')}")
    print(f"  Transformation applied: {t.get('transformation_applied')}")

print("\n" + "=" * 80)
print("RAW OUTPUTS (first 2, truncated)")
print("=" * 80)
for i, output in enumerate(data.get('raw_outputs', [])[:2], 1):
    print(f"\nRaw output {i}:")
    print(output[:300] + "..." if len(output) > 300 else output)

print("\n" + "=" * 80)
print("REPAIRED OUTPUTS (first 2, truncated)")
print("=" * 80)
for i, output in enumerate(data.get('repaired_outputs', [])[:2], 1):
    print(f"\nRepaired output {i}:")
    print(output[:300] + "..." if len(output) > 300 else output)
