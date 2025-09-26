#!/usr/bin/env python3
"""
Test script to verify the repair system fixes are working
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.middleware.repair import repair_code
from src.middleware.contract_enforcer import oracle_check
from src.contract import create_prompt_contract

def test_repair_system():
    """Test that repair system actually transforms code"""
    
    print("🔧 Testing Enhanced Repair System")
    print("=" * 50)
    
    # Create a fibonacci contract
    contract = create_prompt_contract(
        prompt_id="test_fibonacci",
        prompt="Generate fibonacci function",
        function_name="fibonacci",
        oracle="fibonacci20"
    )
    contract["requires_recursion"] = True
    
    # Test case 1: Code with comments and wrong function name
    test_code_1 = '''
def fib(n):
    """This is a docstring that should be removed"""
    # This is a comment that should be removed
    result = []
    for i in range(n):
        if i == 0:
            result.append(0)
        elif i == 1:
            result.append(1)
        else:
            result.append(result[i-1] + result[i-2])
    print("Debug output")  # This should be removed
    return result
'''
    
    print("📝 Original code:")
    print(test_code_1)
    print()
    
    # Check oracle before repair
    oracle_pass_before, reason_before = oracle_check(test_code_1, contract)
    print(f"🔍 Oracle check BEFORE repair: {oracle_pass_before} ({reason_before})")
    
    # Attempt repair
    print("🔧 Attempting repair...")
    canon_text = ""  # No canon for this test
    repair_result, repair_record = repair_code(
        test_code_1, canon_text, contract, "test_run", "test_sample"
    )
    
    print(f"✅ Repair success: {repair_result.success}")
    print(f"📊 Steps taken: {repair_result.steps}")
    print(f"📝 Reason: {repair_result.reason}")
    print()
    
    if repair_result.success:
        print("📝 Repaired code:")
        print(repair_result.repaired_text)
        print()
        
        # Check oracle after repair
        oracle_pass_after, reason_after = oracle_check(repair_result.repaired_text, contract)
        print(f"🔍 Oracle check AFTER repair: {oracle_pass_after} ({reason_after})")
    
    print()
    print("📋 Repair Record:")
    print(f"  Before signature: {repair_record.before_signature[:16]}...")
    print(f"  After signature:  {repair_record.after_signature[:16]}...")
    print(f"  Distance before:  {repair_record.d_before:.3f}")
    print(f"  Distance after:   {repair_record.d_after:.3f}")
    print(f"  Steps:           {repair_record.steps}")
    print(f"  Success:         {repair_record.success}")
    print(f"  Reason:          {repair_record.reason}")
    
    return repair_result.success and repair_result.steps > 0

def test_individual_repair_steps():
    """Test individual repair functions"""
    
    print("\n🔧 Testing Individual Repair Steps")
    print("=" * 50)
    
    from src.middleware.repair import _fix_function_name, _remove_comments, _remove_docstrings, _remove_extra_prints
    
    contract = {"enforce_function_name": "fibonacci"}
    
    # Test function name fix
    code_wrong_name = "def fib(n): return n"
    fixed_name = _fix_function_name(code_wrong_name, contract)
    print(f"Function name fix: {'✅' if 'def fibonacci(' in fixed_name else '❌'}")
    print(f"  Before: {code_wrong_name}")
    print(f"  After:  {fixed_name}")
    
    # Test comment removal
    code_with_comments = "def fibonacci(n):\n    # This is a comment\n    return n"
    no_comments = _remove_comments(code_with_comments, contract)
    print(f"Comment removal: {'✅' if '#' not in no_comments else '❌'}")
    print(f"  Before: {repr(code_with_comments)}")
    print(f"  After:  {repr(no_comments)}")
    
    # Test docstring removal
    code_with_docstring = 'def fibonacci(n):\n    """This is a docstring"""\n    return n'
    no_docstring = _remove_docstrings(code_with_docstring, contract)
    print(f"Docstring removal: {'✅' if '"""' not in no_docstring else '❌'}")
    print(f"  Before: {repr(code_with_docstring)}")
    print(f"  After:  {repr(no_docstring)}")
    
    # Test print removal
    code_with_print = "def fibonacci(n):\n    print('debug')\n    return n"
    no_print = _remove_extra_prints(code_with_print, contract)
    print(f"Print removal: {'✅' if 'print(' not in no_print else '❌'}")
    print(f"  Before: {repr(code_with_print)}")
    print(f"  After:  {repr(no_print)}")

if __name__ == "__main__":
    try:
        # Test individual repair steps
        test_individual_repair_steps()
        
        # Test full repair system
        success = test_repair_system()
        
        if success:
            print("\n🎉 SUCCESS: Repair system is working and making transformations!")
        else:
            print("\n❌ FAILURE: Repair system is not working properly")
            
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
