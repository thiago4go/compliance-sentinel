#!/usr/bin/env python3
"""
Test OpenAI configuration with dapr-agents
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

async def test_dapr_agents_openai():
    """Test OpenAI configuration with dapr-agents"""
    try:
        from dapr_agents import DurableAgent
        from dapr_agents.llm import OpenAIChatClient
        
        print("✅ Dapr-agents imported successfully")
        
        # Check API key
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print("❌ OPENAI_API_KEY not found")
            return False
            
        print(f"✅ OpenAI API key found: {openai_key[:20]}...")
        
        # Create OpenAI client
        llm_client = OpenAIChatClient(
            api_key=openai_key,
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        )
        
        print("✅ OpenAIChatClient created successfully")
        
        # Test a simple call
        try:
            # Create a simple agent
            agent = DurableAgent(
                name="TestAgent",
                role="Test Agent",
                instructions=["You are a test agent. Respond briefly."],
                llm=llm_client
            )
            
            print("✅ DurableAgent created successfully")
            
            # Test a simple query
            response = await agent.run("Say 'Hello from Dapr Agents!'")
            print(f"✅ Agent response: {response}")
            
            return True
            
        except Exception as e:
            print(f"❌ Agent test failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ General error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Dapr-Agents with OpenAI")
    print("=" * 50)
    
    result = asyncio.run(test_dapr_agents_openai())
    
    print("=" * 50)
    if result:
        print("🎉 All tests passed! Dapr-Agents with OpenAI is working!")
    else:
        print("⚠️  Tests failed. Check configuration.")
