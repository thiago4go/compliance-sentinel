import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from dapr_agents import DurableAgent, OpenAIChatClient
from dapr_agents.memory import ConversationDaprStateMemory
from dapr_agents.tool.mcp import MCPClient
from dapr.clients import DaprClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="DuckDuckGo Research Test")

# Global agent instance
research_agent: Optional[DurableAgent] = None

class QueryRequest(BaseModel):
    query: str
    session_id: str = "test-session"

class QueryResponse(BaseModel):
    response: str
    session_id: str
    query: str
    timestamp: str
    tools_used: list = []

@app.on_event("startup")
async def startup_event():
    """Initialize the research agent"""
    global research_agent
    try:
        logger.info("🚀 Starting DuckDuckGo Research Agent...")

        # Create agent with MCP tools
        research_agent = DurableAgent(
            name="DuckDuckGoResearcher",
            role="Web Research Specialist",
            goal="Search the web using DuckDuckGo and provide comprehensive, accurate information",
            instructions=[
                "Use DuckDuckGo search to find current and relevant information",
                "Provide clear, structured responses with sources",
                "Focus on factual, verifiable information",
                "Synthesize information from multiple search results when appropriate"
            ],
            # LLM configuration
            llm=OpenAIChatClient(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
            ),
            # Dapr state memory
            memory=ConversationDaprStateMemory(
                store_name="local-state-store",
                session_id="research-default"
            ),
            # Dapr configuration
            message_bus_name="local-pubsub",
            state_store_name="local-state-store",
            state_key="research-workflow-state",
            agents_registry_store_name="local-state-store",
            agents_registry_key="agents-registry",
            tools=[]  # Will be loaded from MCP
        )

        # Initialize MCP client for DuckDuckGo
        mcp_client = MCPClient()

        logger.info("🌐 Connecting to MCP server...")
        await mcp_client.connect_streamable_http(
            server_name="duckduckgo",
            url=os.getenv("MCP_SERVER_URL", "http://138.3.218.137/ddg/mcp")
        )

        # Load MCP tools
        mcp_tools = mcp_client.get_all_tools()
        research_agent.tools.extend(mcp_tools)

        logger.info(f"✅ Loaded {len(mcp_tools)} MCP tools")
        tool_names = [tool.name for tool in mcp_tools]
        logger.info(f"📋 Available tools: {', '.join(tool_names)}")

        logger.info("✅ DuckDuckGo Research Agent initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize research agent: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_initialized": research_agent is not None,
        "tools_count": len(research_agent.tools) if research_agent else 0
    }

@app.post("/research", response_model=QueryResponse)
async def research_query(request: QueryRequest):
    """Research a query using DuckDuckGo"""
    if not research_agent:
        raise HTTPException(status_code=503, detail="Research agent not initialized")

    try:
        logger.info(f"🔍 Researching: {request.query}")

        # Update memory session
        if research_agent.memory.session_id != request.session_id:
            research_agent.memory.session_id = request.session_id

        # Enhanced prompt for better research
        research_prompt = f"""
        Please research the following topic using web search: {request.query}

        Instructions:
        1. Use DuckDuckGo search to find current and relevant information
        2. Search for multiple aspects of the topic if it's complex
        3. Provide a comprehensive summary with key findings
        4. Include sources and context where possible
        5. Structure your response clearly with sections if appropriate

        Topic to research: {request.query}
        """

        # Run the research
        response = await research_agent.run(research_prompt)

        # Extract response content
        response_content = response.get_content() if hasattr(response, 'get_content') else str(response)

        # Save research results to state store
        await save_research_results(request.query, response_content, request.session_id)

        logger.info(f"✅ Research completed for: {request.query[:50]}...")

        return QueryResponse(
            response=response_content,
            session_id=request.session_id,
            query=request.query,
            timestamp=datetime.now().isoformat(),
            tools_used=[tool.name for tool in research_agent.tools]
        )

    except Exception as e:
        logger.error(f"❌ Research failed: {e}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")

async def save_research_results(query: str, response: str, session_id: str):
    """Save research results to Dapr state store"""
    try:
        # Create result record
        result_record = {
            "query": query,
            "response": response,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "agent_name": "DuckDuckGoResearcher",
            "sources": ["DuckDuckGo", "MCP Server"],
            "metadata": {
                "query_hash": hash(query),
                "response_length": len(response),
                "research_type": "web_search"
            }
        }

        # Save using Dapr client
        with DaprClient() as dapr:
            key = f"research_results/query_{hash(query)}_{int(datetime.now().timestamp())}"
            await dapr.save_state(
                store_name="local-state-store",
                key=key,
                value=json.dumps(result_record)
            )

            logger.info(f"💾 Saved research results with key: {key}")

    except Exception as e:
        logger.error(f"⚠️ Error saving research results: {e}")

@app.get("/results/{session_id}")
async def get_research_results(session_id: str):
    """Get research results for a session"""
    try:
        with DaprClient() as dapr:
            # This is a simplified version - in practice you'd need to query by session_id
            return {"message": f"Research results for session: {session_id}"}
    except Exception as e:
        logger.error(f"❌ Error retrieving results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("APP_PORT", "8000"))
    host = os.getenv("APP_HOST", "0.0.0.0")

    logger.info(f"🌟 Starting DuckDuckGo Research Test on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
