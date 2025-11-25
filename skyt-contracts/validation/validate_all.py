#!/usr/bin/env python3
"""
Validate all contracts and restrictions against their JSON schemas.

Usage:
    python validate_all.py
    python validate_all.py --verbose
"""

import json
import sys
from pathlib import Path
from typing import List, Tuple

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("Warning: jsonschema not installed. Install with: pip install jsonschema")


def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_file(file_path: Path, schema: dict) -> Tuple[bool, str]:
    """Validate a single JSON file against schema."""
    try:
        data = load_json(file_path)
        if HAS_JSONSCHEMA:
            jsonschema.validate(data, schema)
        return True, "OK"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except jsonschema.ValidationError as e:
        return False, f"Schema validation failed: {e.message}"
    except Exception as e:
        return False, f"Error: {e}"


def find_files(directory: Path, pattern: str = "*.json") -> List[Path]:
    """Recursively find all JSON files."""
    return list(directory.rglob(pattern))


def main(verbose: bool = False):
    """Run validation on all contracts and restrictions."""
    root = Path(__file__).parent.parent
    schema_dir = root / "schema"
    
    # Load schemas
    contract_schema_path = schema_dir / "contract.schema.json"
    restriction_schema_path = schema_dir / "restriction.schema.json"
    
    if not contract_schema_path.exists():
        print(f"Error: Contract schema not found at {contract_schema_path}")
        sys.exit(1)
    
    if not restriction_schema_path.exists():
        print(f"Error: Restriction schema not found at {restriction_schema_path}")
        sys.exit(1)
    
    contract_schema = load_json(contract_schema_path)
    restriction_schema = load_json(restriction_schema_path)
    
    # Find all files to validate
    contracts_dir = root / "contracts"
    restrictions_dir = root / "restrictions"
    
    contracts = find_files(contracts_dir) if contracts_dir.exists() else []
    restrictions = find_files(restrictions_dir) if restrictions_dir.exists() else []
    
    # Validation results
    passed = 0
    failed = 0
    errors = []
    
    print("=" * 60)
    print("SKYT Contracts Validation")
    print("=" * 60)
    
    # Validate contracts
    print(f"\n📋 Validating {len(contracts)} contracts...")
    for contract_path in contracts:
        success, message = validate_file(contract_path, contract_schema)
        rel_path = contract_path.relative_to(root)
        
        if success:
            passed += 1
            if verbose:
                print(f"  ✅ {rel_path}")
        else:
            failed += 1
            errors.append((rel_path, message))
            print(f"  ❌ {rel_path}: {message}")
    
    # Validate restrictions
    print(f"\n🔒 Validating {len(restrictions)} restrictions...")
    for restriction_path in restrictions:
        success, message = validate_file(restriction_path, restriction_schema)
        rel_path = restriction_path.relative_to(root)
        
        if success:
            passed += 1
            if verbose:
                print(f"  ✅ {rel_path}")
        else:
            failed += 1
            errors.append((rel_path, message))
            print(f"  ❌ {rel_path}: {message}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Total files:  {passed + failed}")
    print(f"  Passed:       {passed} ✅")
    print(f"  Failed:       {failed} ❌")
    
    if errors:
        print("\nErrors:")
        for path, message in errors:
            print(f"  - {path}: {message}")
        sys.exit(1)
    else:
        print("\n✅ All validations passed!")
        sys.exit(0)


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    main(verbose=verbose)
