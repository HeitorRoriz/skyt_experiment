#!/usr/bin/env python3
"""
Deep dive into why Claude transformations fail.
Focus on the actual transformation mechanics.
"""

import json
import glob
import ast

def get_claude_example():
    """Get a Claude experiment for detailed analysis"""
    files = glob.glob('outputs/*_strict_temp*.json')
    
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if data.get('model') == 'claude-sonnet-4-5-20250929':
                    return f, data
        except:
            pass
    return None, None

def analyze_code_differences(code1, code2, label1="Code 1", label2="Code 2"):
    """Analyze structural differences between two code snippets"""
    
    print(f"\n{'='*80}")
    print(f"COMPARING: {label1} vs {label2}")
    print(f"{'='*80}")
    
    # Basic stats
    print(f"\n{label1}:")
    print(f"  Length: {len(code1)} chars")
    print(f"  Lines: {len(code1.splitlines())}")
    
    print(f"\n{label2}:")
    print(f"  Length: {len(code2)} chars")
    print(f"  Lines: {len(code2.splitlines())}")
    
    # Try to parse both
    try:
        tree1 = ast.parse(code1)
        print(f"\n{label1} AST: Valid ✓")
    except SyntaxError as e:
        print(f"\n{label1} AST: INVALID - {e}")
        tree1 = None
    
    try:
        tree2 = ast.parse(code2)
        print(f"{label2} AST: Valid ✓")
    except SyntaxError as e:
        print(f"{label2} AST: INVALID - {e}")
        tree2 = None
    
    # Line-by-line comparison
    lines1 = code1.splitlines()
    lines2 = code2.splitlines()
    
    print(f"\n{'='*80}")
    print("LINE-BY-LINE DIFF:")
    print(f"{'='*80}")
    
    max_lines = max(len(lines1), len(lines2))
    diff_count = 0
    
    for i in range(min(10, max_lines)):  # Show first 10 lines
        line1 = lines1[i] if i < len(lines1) else "<missing>"
        line2 = lines2[i] if i < len(lines2) else "<missing>"
        
        if line1 != line2:
            diff_count += 1
            print(f"\nLine {i+1} DIFFERS:")
            print(f"  {label1}: {repr(line1)}")
            print(f"  {label2}: {repr(line2)}")
    
    if diff_count == 0:
        print("First 10 lines are identical")
    else:
        print(f"\nTotal differences in first 10 lines: {diff_count}")
    
    # Character-level diff for first difference
    if code1 != code2:
        print(f"\n{'='*80}")
        print("FIRST CHARACTER DIFFERENCE:")
        print(f"{'='*80}")
        
        for i, (c1, c2) in enumerate(zip(code1, code2)):
            if c1 != c2:
                context_start = max(0, i-30)
                context_end = min(len(code1), i+30)
                
                print(f"Position {i}:")
                print(f"  {label1}: {repr(c1)} (ord={ord(c1)})")
                print(f"  {label2}: {repr(c2)} (ord={ord(c2)})")
                print(f"\nContext ({label1}):")
                print(f"  ...{repr(code1[context_start:context_end])}...")
                print(f"\nContext ({label2}):")
                print(f"  ...{repr(code2[context_start:context_end])}...")
                break

def main():
    print("="*80)
    print("DEEP DIVE: CLAUDE TRANSFORMATION FAILURE ROOT CAUSE")
    print("="*80)
    
    filepath, data = get_claude_example()
    
    if not data:
        print("No Claude experiment found!")
        return
    
    print(f"\nAnalyzing: {filepath}")
    print(f"Contract: {data.get('contract_id')}")
    print(f"Temperature: {data.get('temperature')}")
    
    # Get canon code (using correct field name)
    canon_data = data.get('canon_data', {})
    canon_code = canon_data.get('canonical_code', '')
    
    print(f"\nCanon code length: {len(canon_code)}")
    
    if not canon_code:
        print("\n🚨 CRITICAL: Canon code is EMPTY!")
        print("This is why all transformations fail - no target to transform to!")
        
        # Check if canon was supposed to be created
        print(f"\nCanon created flag: {data.get('canon_created')}")
        print(f"Canon data keys: {list(canon_data.keys()) if canon_data else 'None'}")
        
        return
    
    # Get transformation results
    trans_results = data.get('transformation_results', [])
    
    if not trans_results:
        print("No transformation results found!")
        return
    
    # Analyze first transformation
    print(f"\n{'='*80}")
    print("ANALYZING FIRST TRANSFORMATION")
    print(f"{'='*80}")
    
    first_trans = trans_results[0]
    
    original_code = first_trans.get('original_code', '')
    transformed_code = first_trans.get('transformed_code', '')
    
    print(f"\nTransformation needed: {first_trans.get('transformation_needed')}")
    print(f"Transformation success: {first_trans.get('transformation_success')}")
    print(f"Final distance: {first_trans.get('final_distance')}")
    print(f"Transformers applied: {first_trans.get('transformations_applied')}")
    
    # Compare original vs transformed
    analyze_code_differences(original_code, transformed_code, "Original", "Transformed")
    
    # Compare transformed vs canon
    analyze_code_differences(transformed_code, canon_code, "Transformed", "Canon")
    
    # Compare original vs canon
    analyze_code_differences(original_code, canon_code, "Original", "Canon")
    
    # Check if the issue is whitespace/formatting
    print(f"\n{'='*80}")
    print("WHITESPACE ANALYSIS")
    print(f"{'='*80}")
    
    original_normalized = ' '.join(original_code.split())
    transformed_normalized = ' '.join(transformed_code.split())
    canon_normalized = ' '.join(canon_code.split())
    
    print(f"\nAfter normalizing whitespace:")
    print(f"  Original == Transformed: {original_normalized == transformed_normalized}")
    print(f"  Transformed == Canon: {transformed_normalized == canon_normalized}")
    print(f"  Original == Canon: {original_normalized == canon_normalized}")
    
    # Check for common issues
    print(f"\n{'='*80}")
    print("COMMON ISSUES CHECK")
    print(f"{'='*80}")
    
    issues = []
    
    # Check for different variable names
    if 'lru_key' in original_code and 'oldest_key' in canon_code:
        issues.append("Variable naming difference: lru_key vs oldest_key")
    
    # Check for different whitespace patterns
    if original_code.count('\n\n') != canon_code.count('\n\n'):
        issues.append(f"Blank line count differs: {original_code.count(chr(10)+chr(10))} vs {canon_code.count(chr(10)+chr(10))}")
    
    # Check for different indentation
    original_spaces = [len(line) - len(line.lstrip()) for line in original_code.splitlines() if line.strip()]
    canon_spaces = [len(line) - len(line.lstrip()) for line in canon_code.splitlines() if line.strip()]
    
    if set(original_spaces) != set(canon_spaces):
        issues.append(f"Indentation levels differ: {set(original_spaces)} vs {set(canon_spaces)}")
    
    if issues:
        print("\nIssues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nNo obvious issues found")
    
    # Show actual code samples
    print(f"\n{'='*80}")
    print("CODE SAMPLES")
    print(f"{'='*80}")
    
    print("\nOriginal code:")
    print("-" * 40)
    print(original_code[:400])
    
    print("\n\nTransformed code:")
    print("-" * 40)
    print(transformed_code[:400])
    
    print("\n\nCanon code:")
    print("-" * 40)
    print(canon_code[:400])

if __name__ == "__main__":
    main()
