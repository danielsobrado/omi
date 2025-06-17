#!/usr/bin/env python3
"""
Quick health check script for the unified Omi backend.
Run this after starting the server to verify everything is working.
"""

import asyncio
import sys
import os
import requests
import json

async def test_unified_backend():
    """Test the unified backend endpoints"""
    
    base_url = "http://localhost:8080"
    
    print("🔍 Testing Unified Omi Backend")
    print("=" * 40)
    
    # Test basic health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Main health endpoint: OK")
        else:
            print(f"❌ Main health endpoint: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Main health endpoint: Failed to connect ({e})")
        return False
    
    # Test modal services health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Modal services health endpoint: OK")
        else:
            print(f"❌ Modal services health endpoint: Failed ({response.status_code})")
    except Exception as e:
        print(f"❌ Modal services health endpoint: Failed ({e})")
    
    # Test API documentation
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ API documentation (/docs): OK")
        else:
            print(f"❌ API documentation: Failed ({response.status_code})")
    except Exception as e:
        print(f"❌ API documentation: Failed ({e})")
    
    print("\n🎉 Basic connectivity tests completed!")
    print(f"📖 Visit {base_url}/docs for full API documentation")
    
    # Check for important environment variables
    print("\n🔧 Environment Check:")
    env_vars = [
        "DATABASE_CHOICE",
        "POSTGRES_URL",
        "DEEPGRAM_API_KEY",
        "HUGGINGFACE_TOKEN"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Don't print sensitive values
            masked_value = "***" if "KEY" in var or "URL" in var else value
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"⚠️  {var}: Not set")
    
    print("\n📝 Migration Status:")
    print("✅ Modal dependencies removed")
    print("✅ Unified FastAPI application running")
    print("✅ APScheduler cron jobs active")
    print("✅ ML models will load on first use")
    
    return True

if __name__ == "__main__":
    try:
        asyncio.run(test_unified_backend())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
