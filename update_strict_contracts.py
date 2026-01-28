#!/usr/bin/env python3
"""Update strict contracts with all NASA P10 rules + relevant MISRA C rules"""

import json

# All 10 NASA Power of 10 Rules
NASA_P10_ALL = {
    "p10_1": "Avoid complex flow constructs (goto, setjmp, longjmp, recursion)",
    "p10_2": "All loops must have fixed upper bounds (must be provably terminable)",
    "p10_3": "No dynamic memory allocation after initialization",
    "p10_4": "No function longer than 60 lines (fits on single page)",
    "p10_5": "Average of at least 2 assertions per function",
    "p10_6": "Declare data at smallest possible scope",
    "p10_7": "Check return value of all non-void functions, validate parameters",
    "p10_8": "Limit preprocessor use to includes and simple macros (N/A for Python)",
    "p10_9": "Restrict pointer use; no more than 1 level of dereferencing",
    "p10_10": "Compile with all warnings enabled; use static analyzers (N/A for Python)"
}

# Relevant MISRA C rules (applicable to Python/code generation)
MISRA_C_RELEVANT = {
    # Control Flow
    "rule_15_1": "goto shall not be used",
    "rule_15_2": "label shall only be used with goto (N/A if no goto)",
    "rule_15_4": "No more than one break/continue in a loop",
    "rule_15_5": "Function shall have single point of exit",
    
    # Functions
    "rule_17_2": "Functions shall not call themselves recursively",
    "rule_17_7": "Return value of non-void function shall be used",
    
    # Variables/Scope
    "rule_8_7": "Functions/objects should be local if only used in one unit",
    "rule_8_9": "Object should be defined at block scope if only used in single function",
    
    # Loops
    "rule_14_2": "For loop counter shall not be modified in body",
    
    # Expressions
    "rule_12_1": "Precedence of operators should be explicit (use parentheses)",
    "rule_13_5": "Side effects in && or || operands only if essential",
    
    # Memory
    "rule_21_3": "Memory allocation functions of stdlib shall not be used"
}

with open('contracts/templates.json', 'r') as f:
    templates = json.load(f)

# Update is_prime_strict
templates['is_prime_strict']['constraints']['nasa_power_of_10'] = {
    "p10_1": "No recursion, no goto",
    "p10_2": "Bounded loop: for i in range(2, int(n**0.5) + 1)",
    "p10_4": "Function under 60 lines",
    "p10_6": "Use result variable at function scope",
    "p10_7": "Validate input n > 0"
}
templates['is_prime_strict']['constraints']['misra_c_rules'] = {
    "rule_15_5": "Single exit point - one return at end",
    "rule_15_4": "No break or continue",
    "rule_17_2": "No recursion",
    "rule_14_2": "Loop counter i not modified in body"
}

# Update binary_search_strict
templates['binary_search_strict']['constraints']['nasa_power_of_10'] = {
    "p10_1": "No recursion, no goto",
    "p10_2": "Bounded loop: while left <= right (terminates)",
    "p10_4": "Function under 60 lines",
    "p10_6": "result variable at smallest scope",
    "p10_7": "Handle empty array case",
    "p10_9": "Safe arithmetic: left + (right-left)//2"
}
templates['binary_search_strict']['constraints']['misra_c_rules'] = {
    "rule_15_5": "Single exit point - one return at end",
    "rule_15_4": "No break statement",
    "rule_17_2": "No recursion (use iterative)",
    "rule_12_1": "Explicit precedence with parentheses"
}

# Update lru_cache_strict
templates['lru_cache_strict']['constraints']['nasa_power_of_10'] = {
    "p10_1": "No recursion, no goto",
    "p10_2": "All loops bounded",
    "p10_3": "No dynamic memory imports (no OrderedDict)",
    "p10_4": "Each method under 60 lines",
    "p10_6": "Use self.cache, self.order, self.capacity",
    "p10_7": "Check if key in cache before access"
}
templates['lru_cache_strict']['constraints']['misra_c_rules'] = {
    "rule_15_5": "Single exit per method",
    "rule_21_3": "No stdlib dynamic memory (no collections)",
    "rule_8_7": "Encapsulate data in class",
    "rule_8_9": "Attributes defined in __init__"
}

with open('contracts/templates.json', 'w') as f:
    json.dump(templates, f, indent=2)

print("="*60)
print("NASA POWER OF 10 - ALL 10 RULES")
print("="*60)
for k, v in NASA_P10_ALL.items():
    applicable = "N/A" if "N/A" in v else "YES"
    print(f"  {k}: {v[:60]}... [{applicable}]")

print("\n" + "="*60)
print("MISRA C:2012 - RELEVANT RULES (12 of 143)")
print("="*60)
for k, v in MISRA_C_RELEVANT.items():
    print(f"  {k}: {v}")

print("\n" + "="*60)
print("RULES APPLIED PER CONTRACT")
print("="*60)
for name in ['is_prime_strict', 'binary_search_strict', 'lru_cache_strict']:
    c = templates[name]['constraints']
    p10 = list(c.get('nasa_power_of_10', {}).keys())
    misra = list(c.get('misra_c_rules', {}).keys())
    print(f"\n{name}:")
    print(f"  NASA P10: {p10}")
    print(f"  MISRA C:  {misra}")

print("\nContracts updated successfully!")
