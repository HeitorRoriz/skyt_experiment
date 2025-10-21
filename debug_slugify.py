#!/usr/bin/env python3
"""Debug why slugify transformations aren't working"""

import json
from src.foundational_properties import FoundationalProperties
from src.transformations.property_explainers import (
    StatementOrderingExplainer,
    LogicalEquivalenceExplainer,
    NormalizedASTStructureExplainer,
    ControlFlowSignatureExplainer,
    StringLiteralExplainer
)

# Load slugify results (use latest)
import glob
import os
slugify_files = glob.glob("outputs/slugify_temp0.7_*.json")
latest_file = max(slugify_files, key=os.path.getctime)
print(f"Loading: {latest_file}\n")

with open(latest_file, "r") as f:
    results = json.load(f)

# Get canon
canon_code = results["canon_data"]["canonical_code"]
print("="*80)
print("CANON CODE:")
print("="*80)
print(canon_code)
print()

# Get outputs that differ
raw_outputs = results["raw_outputs"]

for i, code in enumerate(raw_outputs, 1):
    if code != canon_code:
        print("="*80)
        print(f"VARIATION {i} (differs from canon):")
        print("="*80)
        print(code)
        print()
        
        # Extract properties
        props_extractor = FoundationalProperties()
        code_props = props_extractor.extract_all_properties(code)
        canon_props = props_extractor.extract_all_properties(canon_code)
        
        # Try all explainers
        explainers = {
            "statement_ordering": StatementOrderingExplainer(),
            "logical_equivalence": LogicalEquivalenceExplainer(),
            "normalized_ast_structure": NormalizedASTStructureExplainer(),
            "control_flow_signature": ControlFlowSignatureExplainer(),
            "string_literals": StringLiteralExplainer()
        }
        
        print("PROPERTY ANALYSIS:")
        print("-" * 80)
        
        for prop_name, explainer in explainers.items():
            code_prop = code_props.get(prop_name)
            canon_prop = canon_props.get(prop_name)
            
            if code_prop is not None and canon_prop is not None:
                diff = explainer.explain_difference(code_prop, canon_prop, code, canon_code)
                if diff:
                    print(f"✓ {prop_name}: DIFFERENCE DETECTED")
                    print(f"  Type: {diff.difference_type}")
                    print(f"  Explanation: {diff.explanation}")
                    print(f"  Severity: {diff.severity}")
                    print(f"  Hints: {diff.transformation_hints}")
                else:
                    print(f"✗ {prop_name}: No difference detected")
            else:
                print(f"✗ {prop_name}: Property not available")
        
        print()
        
        # Check what the properties actually contain
        print("STATEMENT_ORDERING DETAILS:")
        print("-" * 80)
        print(f"Code statement_ordering: {code_props.get('statement_ordering')}")
        print(f"Canon statement_ordering: {canon_props.get('statement_ordering')}")
        print()
