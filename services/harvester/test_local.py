#!/usr/bin/env python3
"""
Local testing script for the harvester service
"""
import asyncio
import httpx
import json
from datetime import datetime

async def test_harvester_service():
    """Test the harvester service locally"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Compliance Sentinel Harvester Service")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test health check
        print("\n1. 🏥 Testing health check...")
        try:
            response = await client.get(f"{base_url}/health")
            health_data = response.json()
            print(f"   Status: {response.status_code}")
            print(f"   Agent Initialized: {health_data.get('agent_initialized')}")
            print(f"   MCP Connected: {health_data.get('mcp_connected')}")
            print(f"   KV Store Connected: {health_data.get('kv_store_connected')}")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            return
        
        # Test configuration
        print("\n2. ⚙️ Testing configuration...")
        try:
            response = await client.get(f"{base_url}/config")
            config_data = response.json()
            print(f"   Status: {response.status_code}")
            print(f"   OpenRouter API Key Loaded: {config_data.get('api_keys_loaded', {}).get('openrouter')}")
            print(f"   Model: {config_data.get('openrouter_model')}")
            print(f"   MCP Server: {config_data.get('mcp_server_url')}")
        except Exception as e:
            print(f"   ❌ Configuration check failed: {e}")
        
        # Test agent info
        print("\n3. 🤖 Testing agent info...")
        try:
            response = await client.get(f"{base_url}/agent/info")
            agent_data = response.json()
            print(f"   Status: {response.status_code}")
            print(f"   Agent Name: {agent_data.get('name')}")
            print(f"   Role: {agent_data.get('role')}")
            print(f"   Tools Count: {agent_data.get('tools_count')}")
            print(f"   Secrets Loaded: {agent_data.get('secrets_loaded')}")
        except Exception as e:
            print(f"   ❌ Agent info failed: {e}")
        
        # Test query processing
        print("\n4. 🔍 Testing query processing...")
        query_data = {
            "query": "What are the latest developments in AI compliance regulations?",
            "session_id": "test-session",
            "max_results": 5,
            "save_results": True
        }
        
        try:
            print(f"   Sending query: {query_data['query'][:50]}...")
            response = await client.post(f"{base_url}/query", json=query_data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Query processed successfully!")
                print(f"   Response length: {len(result['response'])} characters")
                print(f"   Sources used: {result['sources_used']}")
                print(f"   Session ID: {result['session_id']}")
                print(f"   First 200 chars: {result['response'][:200]}...")
            else:
                print(f"   ❌ Query failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Query processing failed: {e}")
        
        # Test workflow start
        print("\n5. 🔄 Testing workflow management...")
        try:
            response = await client.post(f"{base_url}/workflow/start", json=query_data)
            print(f"   Workflow start status: {response.status_code}")
            if response.status_code == 200:
                workflow_data = response.json()
                print(f"   ✅ Workflow started: {workflow_data.get('workflow_id')}")
        except Exception as e:
            print(f"   ❌ Workflow test failed: {e}")

def test_with_curl():
    """Show curl commands for manual testing"""
    print("\n" + "=" * 50)
    print("🔧 Manual Testing Commands:")
    print("=" * 50)
    
    commands = [
        ("Health Check", "curl http://localhost:8000/health"),
        ("Configuration", "curl http://localhost:8000/config"),
        ("Agent Info", "curl http://localhost:8000/agent/info"),
        ("Query Test", 'curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d \'{"query": "test query", "session_id": "manual-test"}\'')
    ]
    
    for name, command in commands:
        print(f"\n{name}:")
        print(f"  {command}")

if __name__ == "__main__":
    print("🚀 Starting Harvester Service Tests...")
    
    try:
        asyncio.run(test_harvester_service())
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
    
    test_with_curl()
    
    print("\n✅ Test suite completed!")
    print("\n💡 Next steps:")
    print("   1. Check the test results above")
    print("   2. If tests pass, your service is ready!")
    print("   3. If tests fail, check the logs for details")
    print("   4. Use the curl commands for manual testing")
