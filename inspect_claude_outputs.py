#!/usr/bin/env python3
"""Inspect actual Claude outputs to understand what patterns they generate"""

import json
import glob

print("="*80)
print("CLAUDE OUTPUT INSPECTION")
print("="*80)

contracts = ['binary_search_strict', 'lru_cache_strict']

for contract in contracts:
    print(f"\n{'='*80}")
    print(f"CONTRACT: {contract}")
    print(f"{'='*80}")
    
    # Get temp 0.0 file (most deterministic)
    pattern = f"outputs/{contract}_temp0.0_*.json"
    files = glob.glob(pattern)
    
    claude_file = None
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'claude' in data.get('model', '').lower():
                claude_file = filepath
                break
        except:
            pass
    
    if not claude_file:
        print("  ❌ No Claude temp 0.0 data found")
        continue
    
    with open(claude_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    raw_outputs = data.get('raw_outputs', [])
    canon_code = data.get('canon', {}).get('canonical_code', '')
    
    if not raw_outputs:
        print("  ❌ No raw outputs found")
        continue
    
    print(f"\n  Found {len(raw_outputs)} outputs")
    print(f"\n  CANONICAL CODE:")
    print("  " + "-"*76)
    for line in canon_code.split('\n')[:15]:
        print(f"  {line}")
    if len(canon_code.split('\n')) > 15:
        print(f"  ...")
    
    print(f"\n  CLAUDE OUTPUT #1:")
    print("  " + "-"*76)
    for line in raw_outputs[0].split('\n')[:15]:
        print(f"  {line}")
    if len(raw_outputs[0].split('\n')) > 15:
        print(f"  ...")
    
    # Check if outputs are identical
    if len(raw_outputs) >= 2:
        print(f"\n  CLAUDE OUTPUT #2 (checking diversity):")
        print("  " + "-"*76)
        if raw_outputs[0] == raw_outputs[1]:
            print("  ✅ IDENTICAL to output #1")
        else:
            print("  ❌ DIFFERENT from output #1:")
            for line in raw_outputs[1].split('\n')[:15]:
                print(f"  {line}")
            if len(raw_outputs[1].split('\n')) > 15:
                print(f"  ...")
    
    # Identify key differences from canon
    print(f"\n  KEY DIFFERENCES FROM CANON:")
    print("  " + "-"*76)
    
    canon_lines = set(canon_code.split('\n'))
    claude_lines = set(raw_outputs[0].split('\n'))
    
    # Lines in Claude but not in canon
    extra_lines = []
    for line in raw_outputs[0].split('\n'):
        stripped = line.strip()
        if stripped and stripped not in [l.strip() for l in canon_code.split('\n')]:
            extra_lines.append(line)
    
    if extra_lines:
        print("  Extra lines in Claude output (not in canon):")
        for line in extra_lines[:10]:
            print(f"    + {line}")
        if len(extra_lines) > 10:
            print(f"    ... and {len(extra_lines) - 10} more")
    else:
        print("  No extra lines found")

print("\n" + "="*80)
print("ANALYSIS")
print("="*80)

print("\n📊 What we learned:")
print("   - Claude's actual code patterns")
print("   - Differences from canonical form")
print("   - Why old transformation system failed")

print("\n💡 Next steps:")
print("   - Determine if new transformation system would handle these patterns")
print("   - Identify if Level 2 (simplification) or Level 3 (replacement) needed")
print("   - Assess if we can infer is_prime_strict behavior from these patterns")
