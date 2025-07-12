import os
import json
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

from dapr_agents import DurableAgent, OpenAIChatClient
from dapr_agents.memory import ConversationDaprStateMemory
from dapr_agents.tool.mcp import MCPClient
from dapr_agents.tool import AgentTool
from dapr.clients import DaprClient

class SecretsAwareDaprAgent(DurableAgent):
    """
    Base class for Dapr Agents that can load secrets and configuration from KV store
    """
    
    def __init__(self, **kwargs):
        # Load secrets and config before initializing parent
        self._load_secrets_and_config()
        super().__init__(**kwargs)
    
    def _load_secrets_and_config(self):
        """Load secrets and configuration from Diagrid KV store"""
        try:
            # Get Dapr client configuration
            dapr_grpc_endpoint = os.getenv("DAPR_GRPC_ENDPOINT")
            store_name = os.getenv("AGENT_STATE_STORE", "agent-kv-store")
            
            if dapr_grpc_endpoint:
                # Configure Dapr client for Catalyst
                endpoint = dapr_grpc_endpoint.replace("https://", "").replace("http://", "")
                if ":" in endpoint:
                    host, port = endpoint.split(":")
                    port = int(port)
                else:
                    host = endpoint
                    port = 443 if "https" in dapr_grpc_endpoint else 80
                
                with DaprClient(address=f"{host}:{port}") as client:
                    # Load secrets
                    openrouter_key = self._get_state_value(client, store_name, "secrets/openrouter-api-key")
                    if openrouter_key:
                        os.environ["OPENROUTER_API_KEY"] = openrouter_key
                    
                    mcp_token = self._get_state_value(client, store_name, "secrets/mcp-api-token")
                    if mcp_token:
                        os.environ["MCP_API_TOKEN"] = mcp_token
                    
                    # Load configuration
                    configs = {
                        "OPENROUTER_MODEL": self._get_state_value(client, store_name, "config/openrouter-model", "openai/gpt-4o"),
                        "MCP_SERVER_URL": self._get_state_value(client, store_name, "config/mcp-server-url", "http://138.3.218.137/ddg/mcp"),
                        "AGENT_MAX_SEARCH_RESULTS": self._get_state_value(client, store_name, "config/agent-max-results", "10"),
                        "LOG_LEVEL": self._get_state_value(client, store_name, "config/log-level", "INFO"),
                    }
                    
                    # Set environment variables
                    for key, value in configs.items():
                        if value:
                            os.environ[key] = str(value)
                    
                    print("✓ Loaded secrets and configuration from KV store")
            
        except Exception as e:
            print(f"⚠ Warning: Could not load secrets from KV store: {e}")
            print("Using environment variables as fallback")
    
    def _get_state_value(self, client: DaprClient, store_name: str, key: str, default: str = None) -> Optional[str]:
        """Get a value from the state store"""
        try:
            result = client.get_state(store_name=store_name, key=key)
            if result.data:
                value = result.data.decode('utf-8')
                # Try to parse JSON, fallback to string
                try:
                    return json.loads(value) if value.startswith(('{', '[', '"')) else value
                except json.JSONDecodeError:
                    return value
            return default
        except Exception as e:
            print(f"Warning: Could not retrieve {key}: {e}")
            return default

class InsightHarvesterAgent(SecretsAwareDaprAgent):
    """
    AI-powered insight harvesting agent with KV store secrets management
    Uses latest MCP client with streamable HTTP transport
    """
    
    # MCP client and tools (excluded from serialization)
    mcp_client: Optional[MCPClient] = Field(default=None, exclude=True)
    mcp_tools: List[AgentTool] = Field(default_factory=list, exclude=True)
    
    def __init__(self, **kwargs):
        super().__init__(
            name="InsightHarvesterAgent",
            role="Information Gatherer and Synthesizer",
            goal="To efficiently search, gather, and synthesize information from web sources and internal data to provide comprehensive, accurate insights for compliance and regulatory analysis.",
            instructions=[
                "Use web search (DuckDuckGo) for general information and current events.",
                "Search for compliance-related information, regulations, and industry updates.",
                "Synthesize information from multiple sources to provide comprehensive answers.",
                "Always cite your sources and provide context for the information found.",
                "Save search results for future reference and analysis.",
                "Focus on accuracy and relevance for compliance and regulatory matters.",
                "If information is unclear or conflicting, note the discrepancies.",
                "Provide structured responses with clear sections and bullet points when appropriate."
            ],
            # LLM configuration using secrets from KV store
            llm=OpenAIChatClient(
                api_key=os.getenv("OPENROUTER_API_KEY", "your_key_here"),
                base_url="https://openrouter.ai/api/v1",
                model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
            ),
            # Persistent conversation memory
            memory=ConversationDaprStateMemory(
                store_name=os.getenv("CONVERSATION_STORE", "agent-kv-store"),
                session_id="insight-harvester-default"
            ),
            # Tools will be loaded from MCP server
            tools=[],
            # Dapr configuration - works with both local Dapr and Catalyst
            message_bus_name=os.getenv("MESSAGE_PUBSUB", "agent-pubsub"),
            state_store_name=os.getenv("WORKFLOW_STATE_STORE", "agent-kv-store"),
            state_key="harvester-workflow-state",
            agents_registry_store_name=os.getenv("AGENT_STATE_STORE", "agent-kv-store"),
            agents_registry_key="agents-registry",
            **kwargs
        )
    
    async def initialize_mcp_client(self):
        """Initialize MCP client connection to external server using latest streamable HTTP transport"""
        if self.mcp_client is None:
            self.mcp_client = MCPClient()
            
            try:
                # Get MCP server configuration from environment (loaded from KV store)
                mcp_url = os.getenv("MCP_SERVER_URL", "http://138.3.218.137/ddg/mcp")
                
                print(f"🌐 Connecting to MCP server at {mcp_url}")
                
                # Use the latest streamable HTTP transport API
                await self.mcp_client.connect_streamable_http(
                    server_name="duckduckgo",
                    url=mcp_url
                )
                
                # Load available tools using the latest API
                self.mcp_tools = self.mcp_client.get_all_tools()
                self.tools.extend(self.mcp_tools)
                
                print(f"✓ Connected to MCP server at {mcp_url}")
                print(f"✓ Loaded {len(self.mcp_tools)} MCP tools")
                
                # Log available tools
                if self.mcp_tools:
                    tool_names = [tool.name for tool in self.mcp_tools]
                    print(f"📋 Available tools: {', '.join(tool_names)}")
                
            except Exception as e:
                print(f"⚠ Error connecting to MCP server: {e}")
                print("Agent will continue without MCP tools")
                self.mcp_client = None
    
    async def save_search_results(self, query: str, response: str, session_id: str = "default"):
        """Save search results to Dapr state store for future reference"""
        try:
            # Create result record
            result_record = {
                "query": query,
                "response": response,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "agent_name": self.name,
                "sources": ["DuckDuckGo", "MCP Server"],
                "metadata": {
                    "query_hash": hash(query),
                    "response_length": len(response),
                    "tools_used": [tool.name for tool in self.mcp_tools] if self.mcp_tools else []
                }
            }
            
            # Save to search results store
            store_name = os.getenv("SEARCH_RESULTS_STORE", "agent-kv-store")
            key = f"search_results/query_{hash(query)}_{int(datetime.now().timestamp())}"
            
            await self.save_state(store_name, key, result_record)
            
            print(f"✓ Saved search results for query: {query[:50]}...")
            
        except Exception as e:
            print(f"⚠ Error saving search results: {e}")
    
    async def run_harvester(self, query: str, session_id: str = "default", max_results: int = None) -> str:
        """
        Main harvesting method that processes queries and returns synthesized information
        """
        try:
            print(f"🔍 Processing harvester query: {query}")
            
            # Initialize MCP client if not already done
            if self.mcp_client is None:
                await self.initialize_mcp_client()
            
            # Update memory session if different
            if self.memory.session_id != session_id:
                self.memory.session_id = session_id
            
            # Get max results from config if not provided
            if max_results is None:
                max_results = int(os.getenv("AGENT_MAX_SEARCH_RESULTS", "10"))
            
            # Enhanced prompt for better results
            enhanced_query = f"""
            Please search for and synthesize information about: {query}
            
            Instructions:
            1. Use web search tools to find current and relevant information
            2. Focus on factual, verifiable information
            3. If this relates to compliance, regulations, or legal matters, prioritize authoritative sources
            4. Provide a structured response with clear sections
            5. Cite sources and provide context
            6. Limit to top {max_results} most relevant results
            
            Query: {query}
            """
            
            # Run the agent with enhanced query
            response = await self.run(enhanced_query)
            
            # Extract response content
            response_content = response.get_content() if hasattr(response, 'get_content') else str(response)
            
            # Save results for future reference
            await self.save_search_results(query, response_content, session_id)
            
            return response_content
            
        except Exception as e:
            error_msg = f"Error in harvester processing: {str(e)}"
            print(error_msg)
            return f"I apologize, but I encountered an error while processing your query: {error_msg}"
    
    async def start_workflow(self, query: str, session_id: str = "default") -> str:
        """Start a workflow for complex query processing"""
        try:
            # This would integrate with Dapr Workflow API
            workflow_id = f"harvest_{hash(query)}_{int(datetime.now().timestamp())}"
            
            # For now, process directly
            result = await self.run_harvester(query, session_id)
            
            return workflow_id
            
        except Exception as e:
            print(f"Error starting workflow: {e}")
            raise
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status"""
        # This would integrate with Dapr Workflow API
        return {
            "status": "completed",
            "workflow_id": workflow_id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def shutdown(self):
        """Graceful shutdown"""
        try:
            if self.mcp_client:
                await self.mcp_client.close()
                print("✓ MCP client connection closed")
        except Exception as e:
            print(f"⚠ Error during shutdown: {e}")
        
        # Call parent shutdown if available
        if hasattr(super(), 'shutdown'):
            await super().shutdown()
