"""
Analyze transformation failures to identify common patterns
"""

import os
import json
from collections import defaultdict, Counter

def analyze_failed_transformations(results_dir="results"):
    """
    Analyze logs to find patterns in failed transformations
    """
    
    failures = defaultdict(list)
    pattern_counts = Counter()
    detailed_failures = defaultdict(list)
    
    # Walk through all experiment results
    for contract_name in os.listdir(results_dir):
        contract_dir = os.path.join(results_dir, contract_name)
        if not os.path.isdir(contract_dir):
            continue
            
        log_file = os.path.join(contract_dir, "experiment_log.json")
        if not os.path.exists(log_file):
            continue
            
        with open(log_file, 'r') as f:
            data = json.load(f)
        
        # Analyze each run
        for run_idx, run in enumerate(data.get("runs", [])):
            # Check if transformation was attempted but failed
            if run.get("distance_pre", 0) > 0 and run.get("distance_post", 0) == run.get("distance_pre", 0):
                # No improvement - transformation failed
                failures[contract_name].append({
                    "run": run_idx,
                    "distance": run.get("distance_pre"),
                    "code_snippet": run.get("code", "")[:200]
                })
                detailed_failures[contract_name].append({
                    "run": run_idx,
                    "distance_pre": run.get("distance_pre", 0),
                    "distance_post": run.get("distance_post", 0),
                    "code": run.get("code", ""),
                    "transformed_code": run.get("transformed_code", ""),
                    "transformations_applied": run.get("transformations_applied", [])
                })
                
                # Look for common patterns in failed code
                code = run.get("code", "")
                if "raise ValueError" in code:
                    pattern_counts["raise_value_error"] += 1
                if "raise TypeError" in code:
                    pattern_counts["raise_type_error"] += 1
                if "if n < 0:" in code:
                    pattern_counts["negative_check"] += 1
                if "elif" in code:
                    pattern_counts["elif_clause"] += 1
                if "else:" in code:
                    pattern_counts["else_clause"] += 1
                if "len(" in code and "== 0" in code:
                    pattern_counts["len_zero_check"] += 1
                if "not " in code:
                    pattern_counts["not_operator"] += 1
                if "stack" in code or "list" in code:
                    pattern_counts["stack_usage"] += 1
                if "for char in" in code or "for c in" in code:
                    pattern_counts["char_iteration"] += 1
    
    # Print report
    print("=" * 70)
    print("TRANSFORMATION FAILURE ANALYSIS")
    print("=" * 70)
    
    for contract_name, fails in failures.items():
        print(f"\n{contract_name}: {len(fails)} failed transformations")
        if fails:
            print(f"  Average distance: {sum(f['distance'] for f in fails) / len(fails):.3f}")
            print("  Detailed Failures:")
            for fail in detailed_failures[contract_name][:3]:  # Limit to first 3 for brevity
                print(f"    Run {fail['run']}: Distance {fail['distance_pre']:.3f} -> {fail['distance_post']:.3f}")
                print(f"      Original Code (snippet): {fail['code'][:100]}...")
                if fail['transformed_code']:
                    print(f"      Transformed Code (snippet): {fail['transformed_code'][:100]}...")
                print(f"      Transformations Attempted: {fail['transformations_applied'] if fail['transformations_applied'] else 'None'}")
    
    print("\n" + "=" * 70)
    print("COMMON PATTERNS IN FAILED TRANSFORMATIONS")
    print("=" * 70)
    for pattern, count in pattern_counts.most_common(10):
        print(f"  {pattern}: {count} occurrences")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    if pattern_counts["raise_value_error"] > 0 or pattern_counts["raise_type_error"] > 0:
        print("  Add OOD policy: must_return or must_raise")
        print("    → Normalizes error handling")
    
    if pattern_counts["len_zero_check"] > 0:
        print("  Enhance property-driven transformer")
        print("    → Add rule: len(x) == 0 → not x")
    
    if pattern_counts["elif_clause"] > 0 or pattern_counts["else_clause"] > 0:
        print("  Add control flow normalization")
        print("    → Flatten elif chains, remove redundant else")
    
    if pattern_counts["stack_usage"] > 0 or pattern_counts["char_iteration"] > 0:
        print("  Add algorithm-specific transformation for balanced_brackets or slugify")
        print("    → Normalize stack-based or iteration approaches")
    
    return failures, pattern_counts


if __name__ == "__main__":
    analyze_failed_transformations()
