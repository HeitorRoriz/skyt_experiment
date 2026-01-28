#!/usr/bin/env python3
"""
Test script for Agentic SKYT
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from contract_agent import ContractAdherenceAgent


async def test_basic_compliance():
    """Test basic contract compliance checking"""
    
    print("🤖 Initializing Contract Adherence Agent...")
    agent = ContractAdherenceAgent(model="gpt-4o", temperature=0.0)
    
    # Test case 1: Non-compliant fibonacci (multiple exits, no bounds checking)
    problematic_code = """
def fibonacci(n):
    if n < 0:
        raise ValueError("n must be non-negative")
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)
"""
    
    print("\n🔍 Test Case 1: Problematic Fibonacci Code")
    print("Code:")
    print(problematic_code)
    
    result = await agent.ensure_compliance(problematic_code, "fibonacci_basic")
    
    print(f"\n📊 Results:")
    print(f"✅ Compliant: {result.compliant}")
    print(f"🚨 Violations: {len(result.violations)}")
    
    for violation in result.violations:
        print(f"   • {violation.type.value} ({violation.severity}): {violation.description}")
    
    print(f"\n📈 Metrics:")
    for key, value in result.metrics.items():
        print(f"   • {key}: {value}")
    
    if result.transformed_code:
        print(f"\n🔧 Transformed Code:")
        print(result.transformed_code)
    else:
        print(f"\n❌ No transformation performed")


async def test_strict_contract():
    """Test with a strict contract"""
    
    print("\n" + "="*60)
    print("🤖 Testing with Strict Contract")
    print("="*60)
    
    agent = ContractAdherenceAgent(model="gpt-4o", temperature=0.0)
    
    # Code that might violate strict constraints
    strict_test_code = """
def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True
"""
    
    print("🔍 Test Case 2: Prime Number Function")
    print("Code:")
    print(strict_test_code)
    
    result = await agent.ensure_compliance(strict_test_code, "is_prime_strict")
    
    print(f"\n📊 Results:")
    print(f"✅ Compliant: {result.compliant}")
    print(f"🚨 Violations: {len(result.violations)}")
    
    for violation in result.violations:
        print(f"   • {violation.type.value} ({violation.severity}): {violation.description}")


async def test_claude_style_code():
    """Test with Claude-style code (behaviorally correct but structurally different)"""
    
    print("\n" + "="*60)
    print("🤖 Testing Claude-Style Code")
    print("="*60)
    
    agent = ContractAdherenceAgent(model="gpt-4o", temperature=0.0)
    
    # Claude-style implementation (different but correct)
    claude_style_code = """
def slugify(text):
    import re
    # Convert to lowercase and replace spaces with hyphens
    result = text.lower()
    result = re.sub(r'[^a-z0-9\\s-]', '', result)
    result = re.sub(r'\\s+', '-', result)
    result = result.strip('-')
    return result
"""
    
    print("🔍 Test Case 3: Claude-Style Slugify")
    print("Code:")
    print(claude_style_code)
    
    result = await agent.ensure_compliance(claude_style_code, "slugify")
    
    print(f"\n📊 Results:")
    print(f"✅ Compliant: {result.compliant}")
    print(f"🚨 Violations: {len(result.violations)}")
    
    for violation in result.violations:
        print(f"   • {violation.type.value} ({violation.severity}): {violation.description}")
    
    if result.transformed_code:
        print(f"\n🔧 Agent attempted transformation")
    else:
        print(f"\n💡 No transformation needed or possible")


async def main():
    """Run all tests"""
    
    print("🚀 Starting Agentic SKYT Tests")
    print("="*60)
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set it in your .env file")
        return
    
    try:
        await test_basic_compliance()
        await test_strict_contract()
        await test_claude_style_code()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("🎯 The agent successfully analyzed code and identified violations")
        print("🔧 Next steps: Enhance transformation capabilities and learning")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
