#!/usr/bin/env python3
"""
Direct test of Claude API to debug the authentication issue
"""

import os
import sys

def test_claude_direct():
    """Test Claude API directly"""
    try:
        import anthropic
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ No ANTHROPIC_API_KEY found in environment")
            return False
        
        print(f"🔑 Using API key: {api_key[:20]}...")
        
        # Create client
        client = anthropic.Anthropic(api_key=api_key)
        
        # Simple test
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=10,
            messages=[
                {"role": "user", "content": "Say 'hello'"}
            ]
        )
        
        print(f"✅ Claude API working! Response: {response.content[0].text}")
        return True
        
    except Exception as e:
        print(f"❌ Claude API failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Direct Claude API Test")
    print("=" * 40)
    test_claude_direct()
