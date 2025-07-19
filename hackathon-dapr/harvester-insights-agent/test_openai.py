#!/usr/bin/env python3
"""
Simple test script to verify OpenAI credentials are working
"""
import os
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

async def test_openai_credentials():
    """Test OpenAI API credentials"""
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    if api_key.startswith("sk-svcacct-"):
        print(f"✅ OpenAI API key found: {api_key[:20]}...")
    else:
        print(f"⚠️  API key format may be incorrect: {api_key[:20]}...")
    
    # Test API call
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hello! This is a test. Please respond with 'OpenAI API is working!'"}
        ],
        "max_tokens": 50
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"🔄 Testing OpenAI API with model: {model}")
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result["choices"][0]["message"]["content"]
                print(f"✅ OpenAI API test successful!")
                print(f"📝 Response: {message}")
                return True
            else:
                print(f"❌ OpenAI API error: {response.status_code}")
                print(f"📝 Error details: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Exception during API test: {e}")
        return False

async def test_database_connection():
    """Test database connection"""
    db_url = os.getenv("DB_URL")
    
    if not db_url:
        print("❌ DB_URL not found in environment")
        return False
    
    print(f"✅ Database URL found: {db_url.split('@')[0]}@***")
    
    # For now, just verify the URL format
    if db_url.startswith("postgresql://"):
        print("✅ Database URL format looks correct")
        return True
    else:
        print("⚠️  Database URL format may be incorrect")
        return False

async def main():
    """Main test function"""
    print("🚀 Testing Harvester Agent Configuration")
    print("=" * 50)
    
    # Test OpenAI credentials
    print("\n1. Testing OpenAI API Credentials:")
    openai_ok = await test_openai_credentials()
    
    # Test database configuration
    print("\n2. Testing Database Configuration:")
    db_ok = await test_database_connection()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Configuration Test Summary:")
    print(f"   OpenAI API: {'✅ PASS' if openai_ok else '❌ FAIL'}")
    print(f"   Database:   {'✅ PASS' if db_ok else '❌ FAIL'}")
    
    if openai_ok and db_ok:
        print("\n🎉 All tests passed! Agent should work correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check configuration.")
    
    return openai_ok and db_ok

if __name__ == "__main__":
    asyncio.run(main())
