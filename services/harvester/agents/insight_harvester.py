import os
from dotenv import load_dotenv
from typing import List, Optional
from pydantic import Field

load_dotenv()

from dapr_agents import DurableAgent, OpenAIChatClient, tool
from dapr_agents.memory import ConversationDaprStateMemory
from dapr_agents.tool.mcp import MCPClient
from dapr_agents.tool import AgentTool
from pydantic import BaseModel

# Define a tool for web search using DuckDuckGo
# This assumes the 'search' tool is available and configured in your Dapr environment
# For simplicity, we'll define a placeholder for it here.
# In a real scenario, we'd dynamically load tools from the MCP server.

class SearchArgs(BaseModel):
    query: str = Field(description="The search query to find information on the web.")

@tool(args_model=SearchArgs)
def search(query: str) -> str:
    """Performs a web search using DuckDuckGo and returns the results."""
    # This is a placeholder. The actual tool will be provided by the MCP server.
    print(f"[Placeholder Tool] Performing web search for: {query}")
    return f"[Placeholder] Search results for '{query}': Example result."

class InsightHarvesterAgent(DurableAgent):
    # Declare mcp_client and mcp_tools as fields
    mcp_client: Optional[MCPClient] = Field(default=None, exclude=True)
    mcp_tools: List[AgentTool] = Field(default_factory=list, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(
            name="InsightHarvesterAgent",
            role="Information Gatherer",
            goal="To efficiently search and synthesize information from the web and internal sources.",
            instructions=[
                "Use web search (DuckDuckGo) for general information.",
                "Use specific internal sources (via MCP) for specialized data.",
                "Synthesize information from multiple sources to provide comprehensive answers.",
                "If a question requires specific internal data, prioritize querying the relevant MCP source.",
                "Always cite your sources (web search, specific source)."
            ],
            # Configure LLM for OpenRouter
            llm=OpenAIChatClient(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o") # Default to gpt-4o if not set
            ),
            # Configure persistent memory
            memory=ConversationDaprStateMemory(
                store_name="conversationstore", # Ensure this Dapr state store component is configured
                session_id="insight-harvester-session" # Unique session ID for this agent
            ),
            # Tools will be added dynamically after MCPClient connection
            tools=[],
            # Dapr-specific configurations for DurableAgent
            message_bus_name="messagepubsub", # Ensure this Dapr pubsub component is configured
            state_store_name="workflowstatestore", # Ensure this Dapr state store component is configured
            state_key="harvester-workflow-state",
            agents_registry_store_name="agentstatestore", # Ensure this Dapr state store component is configured
            agents_registry_key="agents-registry",
            **kwargs
        )

    async def on_dapr_ready(self):
        """Called after Dapr application has started and is ready."""
        print("Dapr application is ready. Attempting to connect to MCP...")
        await self._connect_to_mcp()

    async def _connect_to_mcp(self):
        if self.mcp_client is None:
            # For HTTP-based MCP connections, ephemeral connections are recommended
            self.mcp_client = MCPClient(persistent_connections=False)
            try:
                # Connect to the DuckDuckGo MCP server via streamable HTTP transport
                await self.mcp_client.connect_streamable_http(
                    server_name="duckduckgo",
                    url="http://138.3.218.137/ddg/mcp"
                )
                self.mcp_tools = self.mcp_client.get_all_tools()
                self.tools.extend(self.mcp_tools)
                print("Successfully connected to DuckDuckGo MCP via streamable HTTP and loaded tools.")
            except Exception as e:
                print(f"Error connecting to DuckDuckGo MCP: {e}")
                self.mcp_client = None # Reset client if connection fails

    async def run_harvester(self, query: str) -> str:
        """
        Runs the insight harvesting process for a given query.
        This method will orchestrate the use of search tools and LLM to gather and synthesize information.
        """
        # MCP connection is now handled in on_dapr_ready
        print(f"InsightHarvesterAgent received query: {query}")
        response = await self.run(query)
        return response.get_content()

    async def _on_shutdown(self):
        """Gracefully closes the MCP connection on agent shutdown."""
        await super()._on_shutdown()
        if self.mcp_client:
            await self.mcp_client.close()
            print("Closed MCP connection.")

# Example of how to run the agent (for testing/demonstration purposes)
async def main():
    # Ensure OPENROUTER_API_KEY and optionally OPENROUTER_MODEL are set in your environment
    # or in a .env file loaded with dotenv.load_dotenv()
    
    harvester_agent = InsightHarvesterAgent()
    
    # To run as a Dapr service (recommended for DurableAgent)
    # This will expose the agent as an HTTP service
    harvester_agent.as_service(port=8000) # Choose an available port
    await harvester_agent.start()
    await harvester_agent.on_dapr_ready() # Call this after the Dapr app has started

    # You would typically interact with the agent via its HTTP endpoint
    # For example, by sending a POST request to /run_harvester with the query.
    print("InsightHarvesterAgent started as a Dapr service on port 8000.")
    print("You can interact with it via HTTP requests (e.g., POST to /run_harvester).")
    print("Press Ctrl+C to stop the agent.")

if __name__ == "__main__":
    import asyncio
    # For local testing, ensure Dapr is initialized and components are configured.
    # You would typically run this with 'dapr run --app-id harvester-agent --dapr-http-port 3500 --app-port 8000 --resources-path <path_to_components> python services/harvester/agents/insight_harvester.py'
    # And ensure you have 'conversationstore', 'messagepubsub', 'workflowstatestore', 'agentstatestore' Dapr components configured.
    
    # This part is for direct script execution for quick testing, not for Dapr deployment.
    # For actual Dapr deployment, the 'as_service' and 'start' methods handle the main loop.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("InsightHarvesterAgent stopped.")