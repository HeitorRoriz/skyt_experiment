#!/usr/bin/env python3
"""
Setup script for Claude API key
Run this to set up your Claude API key properly
"""

import os
import sys

def setup_claude_key():
    """Set up Claude API key for the current session"""
    
    print("🔧 Claude API Key Setup")
    print("=" * 40)
    
    # Check if API key is already set
    current_key = os.getenv("ANTHROPIC_API_KEY")
    if current_key and "YOUR_ACTUAL_API_KEY_HERE" not in current_key:
        print(f"✅ API key is already set: {current_key[:20]}...")
        return True
    
    print("⚠️  API key not set or using placeholder")
    print("Please set your Claude API key:")
    print("1. Get your API key from: https://console.anthropic.com/")
    print("2. Run one of these commands:")
    print("")
    
    if os.name == 'nt':  # Windows
        print("PowerShell:")
        print('  $env:ANTHROPIC_API_KEY = "sk-ant-api03-YOUR_ACTUAL_KEY_HERE"')
        print("")
        print("Command Prompt:")
        print('  set ANTHROPIC_API_KEY=sk-ant-api03-YOUR_ACTUAL_KEY_HERE')
    else:  # Linux/Mac
        print("Bash/Zsh:")
        print('  export ANTHROPIC_API_KEY="sk-ant-api03-YOUR_ACTUAL_KEY_HERE"')
    
    print("")
    print("3. Then run your Claude experiments:")
    print('  python main.py --contract fibonacci_basic --model claude-sonnet-4-5-20250929 --runs 3')
    
    return False

def test_claude_connection():
    """Test Claude API connection"""
    try:
        from src.llm_client import LLMClient
        
        print("🧪 Testing Claude API connection...")
        client = LLMClient(model="claude-sonnet-4-5-20250929")
        
        # Simple test
        result = client.generate("Write 'hello world'", temperature=0.0)
        
        if result and len(result.strip()) > 0:
            print("✅ Claude API connection successful!")
            print(f"Response: {result.strip()}")
            return True
        else:
            print("❌ Claude API returned empty response")
            return False
            
    except Exception as e:
        print(f"❌ Claude API connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Claude API Setup and Test")
    print("=" * 50)
    
    # Setup check
    if setup_claude_key():
        # Test connection if key is set
        test_claude_connection()
    else:
        print("\n📝 Please set your API key first, then run this script again to test the connection.")
