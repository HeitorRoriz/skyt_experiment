#!/usr/bin/env python3
"""Debug what the LLM is actually generating for binary_search_strict"""

import json
from src.llm_client import LLMClient
from src.contract import Contract
from src.contract_compliance import make_compliant, check_contract_compliance
from src.oracle_system import OracleSystem

print("1. Load contract")
with open('contracts/templates.json') as f:
    contract_data = json.load(f)['binary_search_strict']

contract = Contract(contract_data)
client = LLMClient(model='gpt-4o-mini')
oracle = OracleSystem()

print("\n2. Generate code from LLM")
code = client.generate_code(contract.data['prompt'], temperature=1.0)
print("Generated code:")
print(code)

print("\n3. Check original oracle")
result = oracle.run_oracle_tests(code, contract.data, timeout=3)
print(f"Oracle passed: {result['passed']}")
if not result['passed']:
    print(f"Error: {result.get('error', 'Unknown')}")

print("\n4. Check original compliance")
is_compliant, violations = check_contract_compliance(code, contract.data)
print(f"Compliant: {is_compliant}")
if violations:
    print(f"Violations: {violations[:3]}")

print("\n5. Transform to compliant")
transformed = make_compliant(code, contract.data)
print("Transformed code:")
print(transformed)

print("\n6. Check transformed compliance")
is_compliant, violations = check_contract_compliance(transformed, contract.data)
print(f"Compliant: {is_compliant}")
if violations:
    print(f"Violations: {violations[:3]}")

print("\n7. Test transformed with oracle")
result = oracle.run_oracle_tests(transformed, contract.data, timeout=3)
print(f"Oracle passed: {result['passed']}")
if not result['passed']:
    print(f"Error: {result.get('error', 'Unknown')}")
else:
    print(f"Pass rate: {result.get('pass_rate', '?')}")
