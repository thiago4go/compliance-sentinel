#!/usr/bin/env python3
"""
Test DurableAgent with OpenAI LLM using correct Dapr port configuration
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

async def test_durable_agent_with_llm():
    """Test DurableAgent with proper OpenAI and Dapr configuration"""
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
        
        # Set the correct Dapr HTTP port from environment
        dapr_http_port = os.getenv("DAPR_HTTP_PORT", "3500")
        print(f"🔄 Using Dapr HTTP port: {dapr_http_port}")
        
        try:
            # Create DurableAgent with proper configuration
            agent = DurableAgent(
                name="TestDurableAgent",
                role="Test Agent",
                instructions=[
                    "You are a test agent for compliance intelligence.",
                    "Respond briefly and clearly.",
                    "When asked to test, respond with 'DurableAgent with OpenAI is working correctly!'"
                ],
                llm=llm_client,
                # Required Dapr configuration
                message_bus_name="messagepubsub",
                state_store_name="workflowstatestore",
                agents_registry_store_name="agentstatestore"
            )
            
            print("✅ DurableAgent created successfully")
            
            # Test a simple query
            test_query = "Please test your functionality and confirm you're working."
            print(f"🔄 Testing query: {test_query}")
            
            response = await agent.run(test_query)
            print(f"✅ Agent response: {response}")
            
            # Test another query to verify OpenAI integration
            compliance_query = "What are the key requirements for GDPR compliance?"
            print(f"🔄 Testing compliance query: {compliance_query}")
            
            compliance_response = await agent.run(compliance_query)
            print(f"✅ Compliance response: {compliance_response[:200]}...")
            
            return True
                    
        except Exception as e:
            print(f"❌ DurableAgent test failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ General error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing DurableAgent with OpenAI LLM (Fixed)")
    print("=" * 50)
    
    result = asyncio.run(test_durable_agent_with_llm())
    
    print("=" * 50)
    if result:
        print("🎉 DurableAgent with OpenAI is working perfectly!")
        print("📝 Ready to implement in harvester agent")
    else:
        print("⚠️  DurableAgent test failed. Check configuration.")
