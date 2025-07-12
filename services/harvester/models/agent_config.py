from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class MCPConfig(BaseModel):
    """MCP server configuration"""
    server_url: str
    api_token: Optional[str] = None
    timeout_seconds: int = 30
    retry_attempts: int = 3

class LLMConfig(BaseModel):
    """LLM configuration"""
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "openai/gpt-4o"
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class AgentConfig(BaseModel):
    """Agent configuration"""
    name: str = "InsightHarvesterAgent"
    role: str = "Information Gatherer"
    max_search_results: int = 10
    save_results: bool = True
    session_timeout_minutes: int = 60
    
    # Component configurations
    mcp: MCPConfig
    llm: LLMConfig
    
    # Dapr component names
    state_store_name: str = "workflowstatestore"
    message_bus_name: str = "messagepubsub"
    conversation_store_name: str = "conversationstore"
    search_results_store_name: str = "searchresultsstore"
