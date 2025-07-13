from dapr_agents import OpenAIChatClient
from dapr_agents.types import UserMessage
from pydantic import BaseModel
from dotenv import load_dotenv
import json

# Load environment variables from .env
load_dotenv()

print("=== Testing OpenAI GPT-4.1-nano ===")

# Test with explicit model specification
llm = OpenAIChatClient(model="gpt-4.1-nano")

try:
    # Test 1: Basic completion
    print("\n1. Testing basic completion with gpt-4.1-nano...")
    response = llm.generate("Tell me a fun fact about AI agents in one sentence.")
    print(f"Response: {response.get_content()}")
    
    # Test 2: Structured output with Pydantic
    print("\n2. Testing structured output...")
    
    class AIFact(BaseModel):
        topic: str
        fact: str
        relevance_score: int  # 1-10
    
    response = llm.generate(
        messages=[UserMessage("Give me an interesting fact about machine learning.")], 
        response_format=AIFact
    )
    
    print("Structured Response:")
    print(json.dumps(response.model_dump(), indent=2))
    
    # Test 3: Conversation
    print("\n3. Testing conversation...")
    response = llm.generate(messages=[
        UserMessage("Hello! I'm learning about Dapr Agents.")
    ])
    print(f"Conversation Response: {response.get_content()}")
    
    print("\n✅ GPT-4.1-nano integration successful!")
    
except Exception as e:
    print(f"❌ GPT-4.1-nano integration failed: {e}")
    print("Note: Model name might need verification or API access issues")
