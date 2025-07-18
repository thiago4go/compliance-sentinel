import logging
import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from datetime import datetime
import hashlib

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn
import httpx

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()  # This is critical - must be called before any LLM operations

# Disable telemetry
os.environ["LITERAL_API_KEY"] = ""
os.environ["LITERAL_DISABLE"] = "true"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import dapr-agents and related components
try:
    from dapr_agents import DurableAgent
    from dapr_agents.memory import ConversationDaprStateMemory
    from dapr_agents.llm import OpenAIChatClient
    from dapr_agents.mcp import MCPClient
    from dapr_agents.tools import AgentTool
    DAPR_AGENTS_AVAILABLE = True
    logger.info("Dapr-agents imported successfully")
except Exception as e:
    DAPR_AGENTS_AVAILABLE = False
    logger.warning(f"Dapr-agents not available: {e}")

# Try to import Dapr SDK for pub/sub
try:
    from dapr.clients import DaprClient
    from dapr.ext.grpc import App
    from cloudevents.sdk.event import v1
    DAPR_SDK_AVAILABLE = True
    logger.info("Dapr SDK imported successfully")
except Exception as e:
    DAPR_SDK_AVAILABLE = False
    logger.warning(f"Dapr SDK not available: {e}")

# Request/Response models
class InsightRequest(BaseModel):
    framework: str
    company_name: str
    industry: Optional[str] = "Technology"
    query: Optional[str] = None

class InsightResponse(BaseModel):
    status: str
    framework: str
    company_name: str
    insights: Dict[str, Any]
    timestamp: str

class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10

class SearchResponse(BaseModel):
    status: str
    query: str
    results: List[Dict[str, Any]]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    components: Dict[str, str]
    configuration: Dict[str, Any]

class HarvesterAgent:
    """Enhanced compliance intelligence harvester with Dapr Agents integration"""
    
    def __init__(self):
        self.name = "HarvesterInsightsAgent"
        self.role = "Compliance Intelligence Harvester"
        self.agent = None
        self.mcp_client = None
        self.mcp_tools = []
        self.dapr_client = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize the harvester agent with all components"""
        if self.initialized:
            return
            
        try:
            if DAPR_AGENTS_AVAILABLE:
                # Check which API key is available
                openai_key = os.getenv("OPENAI_API_KEY")
                openrouter_key = os.getenv("OPENROUTER_API_KEY")
                
                llm_client = None
                
                if openai_key:
                    # Use standard OpenAI API
                    logger.info("Using standard OpenAI API")
                    llm_client = OpenAIChatClient(
                        api_key=openai_key,
                        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                    )
                elif openrouter_key:
                    # Use OpenRouter API
                    logger.info("Using OpenRouter API")
                    llm_client = OpenAIChatClient(
                        api_key=openrouter_key,
                        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                        model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
                    )
                else:
                    logger.warning("No OpenAI or OpenRouter API key found")
                
                # Initialize Dapr Agent
                self.agent = DurableAgent(
                    name=self.name,
                    role=self.role,
                    instructions=[
                        "You are a Compliance Insight Harvester specialized in gathering and analyzing regulatory intelligence.",
                        "You extract insights from various sources including regulatory updates, industry benchmarks, and risk assessments.",
                        "You provide actionable intelligence for compliance decision-making.",
                        "You focus on practical, implementable recommendations for SMB companies.",
                        "You prioritize high-impact, low-effort compliance improvements.",
                        "Use web search tools to find current and relevant information.",
                        "Focus on factual, verifiable information from authoritative sources.",
                        "Provide structured responses with clear sections and citations."
                    ],
                    # LLM configuration
                    llm=llm_client,
                    # Memory configuration
                    memory=ConversationDaprStateMemory(
                        store_name="conversationstore",
                        session_id="harvester-default"
                    ) if DAPR_AGENTS_AVAILABLE else None,
                    # Dapr configuration
                    message_bus_name="messagepubsub",
                    state_store_name="workflowstatestore",
                    agents_registry_store_name="agentstatestore",
                    tools=[]  # Will be populated with MCP tools
                )
                
                # Initialize MCP client
                await self.initialize_mcp_client()
                
                logger.info("Dapr Agent initialized successfully")
            
            # Initialize Dapr SDK client for pub/sub
            if DAPR_SDK_AVAILABLE:
                self.dapr_client = DaprClient()
                logger.info("Dapr SDK client initialized")
                
            self.initialized = True
            
        except Exception as e:
            logger.error(f"Error initializing harvester agent: {e}")
            raise
    
    async def initialize_mcp_client(self):
        """Initialize MCP client for web search tools"""
        try:
            # Initialize MCP client
            self.mcp_client = MCPClient(persistent_connections=False)
            
            # Get MCP server configuration
            mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp")
            mcp_token = os.getenv("MCP_API_TOKEN")
            
            # Prepare headers
            headers = {}
            if mcp_token:
                headers["Authorization"] = f"Bearer {mcp_token}"
                headers["X-API-Key"] = mcp_token
            
            # Connect to MCP server
            await self.mcp_client.connect_streamable_http(
                server_name="duckduckgo",
                url=mcp_url,
                headers=headers if headers else None
            )
            
            # Load available tools
            self.mcp_tools = self.mcp_client.get_all_tools()
            if self.agent:
                self.agent.tools.extend(self.mcp_tools)
            
            logger.info(f"MCP client connected with {len(self.mcp_tools)} tools")
            
        except Exception as e:
            logger.warning(f"MCP client initialization failed: {e}")
            self.mcp_client = None
    
    async def search_web(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Perform web search using MCP tools or fallback"""
        try:
            if self.mcp_client and self.mcp_tools:
                # Use MCP tools for web search
                search_tool = next((tool for tool in self.mcp_tools if "search" in tool.name.lower()), None)
                if search_tool:
                    result = await search_tool.execute(query=query, max_results=max_results)
                    return {
                        "status": "success",
                        "source": "mcp_tools",
                        "results": result
                    }
            
            # Fallback to direct HTTP search (DuckDuckGo)
            async with httpx.AsyncClient() as client:
                # Simple DuckDuckGo search fallback
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": "1",
                        "skip_disambig": "1"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "success",
                        "source": "duckduckgo_fallback",
                        "results": data
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Search failed with status {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def harvest_insights(self, framework: str, company_name: str, industry: str = "Technology", query: str = None) -> Dict[str, Any]:
        """Generate compliance insights using the agent"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # Construct the query for the agent
            if query:
                agent_query = query
            else:
                agent_query = f"""
                Analyze compliance requirements for {company_name} in the {industry} industry regarding {framework} framework.
                
                Please provide:
                1. Key compliance requirements
                2. Risk areas to focus on
                3. Practical recommendations
                4. Implementation priorities
                
                Focus on actionable insights for SMB companies.
                """
            
            if self.agent:
                # Use Dapr Agent for intelligent analysis
                response = await self.agent.run(agent_query)
                
                return {
                    "status": "success",
                    "source": "dapr_agent",
                    "insights": {
                        "analysis": response,
                        "framework": framework,
                        "company": company_name,
                        "industry": industry,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            else:
                # Fallback to basic analysis
                return {
                    "status": "success",
                    "source": "fallback",
                    "insights": {
                        "message": f"Basic compliance analysis for {company_name} - {framework}",
                        "note": "Dapr Agent not available, using fallback mode",
                        "framework": framework,
                        "company": company_name,
                        "industry": industry,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error harvesting insights: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

# Initialize the harvester agent
harvester_agent = HarvesterAgent()

# Initialize FastAPI app
app = FastAPI(
    title="Harvester Insights Agent",
    description="Enhanced compliance intelligence harvester with Dapr Agents integration",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup"""
    await harvester_agent.initialize()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    components = {
        "agent": "✅ Running" if harvester_agent.initialized else "⚠️ Initializing",
        "dapr_agents": "✅ Available" if DAPR_AGENTS_AVAILABLE else "❌ Not Available",
        "dapr_sdk": "✅ Available" if DAPR_SDK_AVAILABLE else "❌ Not Available",
        "openai": "✅ Present" if os.getenv("OPENAI_API_KEY") else "❌ Missing",
        "openrouter": "✅ Present" if os.getenv("OPENROUTER_API_KEY") else "❌ Missing",
        "mcp_tools": f"✅ {len(harvester_agent.mcp_tools)} tools" if harvester_agent.mcp_tools else "❌ No tools"
    }
    
    return HealthResponse(
        status="healthy" if harvester_agent.initialized else "initializing",
        timestamp=datetime.now().isoformat(),
        components=components,
        configuration={
            "name": harvester_agent.name,
            "role": harvester_agent.role,
            "dapr_agents_available": DAPR_AGENTS_AVAILABLE,
            "dapr_sdk_available": DAPR_SDK_AVAILABLE,
            "mcp_tools_count": len(harvester_agent.mcp_tools)
        }
    )

@app.post("/harvest-insights", response_model=InsightResponse)
async def harvest_insights(request: InsightRequest):
    """Generate compliance insights"""
    try:
        insights = await harvester_agent.harvest_insights(
            request.framework,
            request.company_name,
            request.industry or "Technology",
            request.query
        )
        
        return InsightResponse(
            status=insights["status"],
            framework=request.framework,
            company_name=request.company_name,
            insights=insights,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error processing insights request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse)
async def search_web(request: SearchRequest):
    """Perform web search"""
    try:
        results = await harvester_agent.search_web(request.query, request.max_results or 10)
        
        return SearchResponse(
            status=results["status"],
            query=request.query,
            results=results.get("results", []),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error processing search request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/info")
async def agent_info():
    """Get agent information"""
    return {
        "name": harvester_agent.name,
        "role": harvester_agent.role,
        "status": "running" if harvester_agent.initialized else "initializing",
        "capabilities": [
            "Compliance intelligence harvesting",
            "Web search via MCP tools",
            "Dapr Agents integration",
            "Pub/Sub messaging",
            "State management"
        ],
        "components": {
            "dapr_agents": DAPR_AGENTS_AVAILABLE,
            "dapr_sdk": DAPR_SDK_AVAILABLE,
            "mcp_tools": len(harvester_agent.mcp_tools),
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY"))
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 9180))
    logger.info(f"Starting Harvester Insights Agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
