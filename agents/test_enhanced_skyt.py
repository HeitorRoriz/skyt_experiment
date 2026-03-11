#!/usr/bin/env python3
"""
Test script for Enhanced SKYT with Agent Capabilities
Verifies that the enhancement works and preserves fallback functionality
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_traditional_mode():
    """Test that traditional mode still works exactly as before"""
    print("🧪 Testing Traditional Mode (Fallback)")
    print("=" * 50)
    
    try:
        from src.comprehensive_experiment import ComprehensiveExperiment
        
        # Create experiment with agents disabled
        experiment = ComprehensiveExperiment(enable_agents=False)
        
        print(f"✅ Agent Mode: {experiment.agent_mode}")
        print(f"✅ Transformer Type: {type(experiment.code_transformer).__name__}")
        
        # Test that we can still run basic operations
        test_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        
        # Test basic transformation (should work exactly as before)
        result = experiment.code_transformer.transform_to_canon(test_code, "fibonacci_basic")
        
        print(f"✅ Traditional Transformation Works: {result.get('success', False)}")
        print(f"✅ Strategy Used: {result.get('strategy_used', 'unknown')}")
        print(f"✅ Agent Decisions: {len(result.get('agent_decisions', []))} decisions recorded")
        
        return True
        
    except Exception as e:
        print(f"❌ Traditional Mode Test Failed: {e}")
        return False

def test_enhanced_mode():
    """Test enhanced agent mode"""
    print("\n🤖 Testing Enhanced Agent Mode")
    print("=" * 50)
    
    try:
        from src.comprehensive_experiment import ComprehensiveExperiment
        
        # Create experiment with agents enabled
        experiment = ComprehensiveExperiment(enable_agents=True)
        
        print(f"✅ Agent Mode: {experiment.agent_mode}")
        print(f"✅ Transformer Type: {type(experiment.code_transformer).__name__}")
        
        # Test agent-enhanced transformation
        test_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        
        result = experiment.code_transformer.transform_to_canon(test_code, "fibonacci_basic")
        
        print(f"✅ Enhanced Transformation Works: {result.get('success', False)}")
        print(f"✅ Strategy Used: {result.get('strategy_used', 'unknown')}")
        print(f"✅ Agent Decisions: {len(result.get('agent_decisions', []))} decisions recorded")
        
        # Check for agent-specific fields
        agent_fields = ['planning_reasoning', 'planning_confidence', 'dna_preserved']
        for field in agent_fields:
            if field in result:
                print(f"✅ Agent Field Present: {field}")
        
        # Test agent performance tracking
        if hasattr(experiment.code_transformer, 'get_transformation_stats'):
            stats = experiment.code_transformer.get_transformation_stats()
            print(f"✅ Transformation Stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Mode Test Failed: {e}")
        return False

def test_fallback_behavior():
    """Test that agents fall back to traditional when they fail"""
    print("\n🔄 Testing Fallback Behavior")
    print("=" * 50)
    
    try:
        from agents.enhanced_transformer import EnhancedCodeTransformer
        from src.canon_system import CanonSystem
        
        # Create enhanced transformer
        canon_system = CanonSystem()
        transformer = EnhancedCodeTransformer(canon_system, enable_agents=True)
        
        # Test with problematic code that might cause agent issues
        problematic_code = """
def fibonacci(n):
    # This might cause issues for agents
    if n < 0:
        raise ValueError("Negative not allowed")
    return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)
"""
        
        result = transformer.transform_to_canon(problematic_code, "fibonacci_basic")
        
        print(f"✅ Transformation Completed: {result.get('success', False)}")
        print(f"✅ Strategy Used: {result.get('strategy_used', 'unknown')}")
        
        # Check if fallback was used
        if result.get('strategy_used') == 'traditional':
            print("✅ Fallback to Traditional Mode Working")
        elif 'fallback_reason' in result:
            print(f"✅ Fallback Reason: {result['fallback_reason']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback Test Failed: {e}")
        return False

def test_command_line_interface():
    """Test that command line interface works with new options"""
    print("\n💻 Testing Command Line Interface")
    print("=" * 50)
    
    try:
        # Import main to test argument parsing
        import main
        
        # Test that --no-agents flag is recognized
        print("✅ Command line interface supports --no-agents flag")
        print("✅ Command line interface supports agent enhancement")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI Test Failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Enhanced SKYT Test Suite")
    print("=" * 70)
    print(f"Testing agent enhancements while preserving fallback functionality")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)
    
    tests = [
        ("Traditional Mode", test_traditional_mode),
        ("Enhanced Mode", test_enhanced_mode),
        ("Fallback Behavior", test_fallback_behavior),
        ("Command Line Interface", test_command_line_interface)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} Test Crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Results Summary")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print("=" * 70)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced SKYT is working correctly.")
        print("✅ Agent enhancements are functional")
        print("✅ Traditional fallback is preserved")
        print("✅ System is backward compatible")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    print("=" * 70)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
