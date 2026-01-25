#!/usr/bin/env python3
"""
Check Claude API credit status and usage limits
"""

import os
import anthropic
from datetime import datetime

print("="*80)
print("CLAUDE API STATUS CHECK")
print("="*80)

# Check if API key is set
api_key = os.environ.get('ANTHROPIC_API_KEY')

if not api_key:
    print("\n❌ ANTHROPIC_API_KEY not found in environment variables")
    print("\nTo set it:")
    print("  Windows: set ANTHROPIC_API_KEY=your_key_here")
    print("  Linux/Mac: export ANTHROPIC_API_KEY=your_key_here")
    exit(1)

print(f"\n✅ API Key found: {api_key[:20]}...{api_key[-4:]}")

# Try to make a minimal API call to check status
print("\n" + "="*80)
print("TESTING API CONNECTION")
print("="*80)

try:
    client = anthropic.Anthropic(api_key=api_key)
    
    print("\n🔄 Sending minimal test request...")
    
    # Minimal request to test API
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=10,
        messages=[
            {"role": "user", "content": "Hi"}
        ]
    )
    
    print("✅ API connection successful!")
    print(f"\nResponse received:")
    print(f"  Model: {message.model}")
    print(f"  Usage: {message.usage.input_tokens} input tokens, {message.usage.output_tokens} output tokens")
    print(f"  Stop reason: {message.stop_reason}")
    
    print("\n" + "="*80)
    print("API STATUS: OPERATIONAL")
    print("="*80)
    
    print("\n✅ You can proceed with Claude experiments")
    print("\nEstimated costs for Option B:")
    print("  - is_prime_strict full run: 100 calls (20 runs × 5 temps)")
    print("  - Validation run: 10 calls")
    print("  - Total: 110 API calls")
    print("\nNote: Actual credit usage depends on your plan and rate limits")
    
except anthropic.RateLimitError as e:
    print("\n❌ RATE LIMIT ERROR")
    print(f"  Message: {e}")
    print("\n⚠️  You have hit a rate limit")
    print("\nPossible causes:")
    print("  1. Too many requests in short time period")
    print("  2. Monthly quota exceeded")
    print("  3. Tier-based rate limit reached")
    print("\nSolutions:")
    print("  - Wait before retrying")
    print("  - Check your usage dashboard")
    print("  - Upgrade your plan if needed")
    
except anthropic.AuthenticationError as e:
    print("\n❌ AUTHENTICATION ERROR")
    print(f"  Message: {e}")
    print("\n⚠️  API key is invalid or expired")
    print("\nSolutions:")
    print("  - Verify your API key")
    print("  - Generate a new API key")
    print("  - Check if your account is active")
    
except anthropic.PermissionDeniedError as e:
    print("\n❌ PERMISSION DENIED")
    print(f"  Message: {e}")
    print("\n⚠️  Your account doesn't have permission for this model")
    print("\nSolutions:")
    print("  - Check your plan tier")
    print("  - Verify model access")
    print("  - Contact Anthropic support")
    
except anthropic.APIError as e:
    print("\n❌ API ERROR")
    print(f"  Message: {e}")
    print(f"  Type: {type(e).__name__}")
    print("\n⚠️  General API error occurred")
    print("\nCheck:")
    print("  - Anthropic status page")
    print("  - Your account status")
    print("  - Error message details")
    
except Exception as e:
    print("\n❌ UNEXPECTED ERROR")
    print(f"  Message: {e}")
    print(f"  Type: {type(e).__name__}")
    print("\n⚠️  An unexpected error occurred")

print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)

print("\nBased on API status:")
print("  - If operational: Proceed with Option B (full run)")
print("  - If rate limited: Wait or use smaller validation run")
print("  - If authentication error: Fix API key before proceeding")
print("  - If permission denied: Check plan tier and model access")

print("\n" + "="*80)
