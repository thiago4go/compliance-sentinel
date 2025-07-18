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
    DAPR_AGENTS_AVAILABLE = True
    logger.info("Dapr-agents imported successfully")
except Exception as e:
    DAPR_AGENTS_AVAILABLE = False
    logger.warning(f"Dapr-agents not available: {e}")

# Try to import Dapr SDK for pub/sub (but don't fail if not available)
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
        self.dapr_client = None
        self.initialized = False
        self.dapr_available = False
        
    async def initialize(self):
        """Initialize the harvester agent with all components"""
        if self.initialized:
            return
            
        try:
            # Check if we're running with Dapr sidecar
            dapr_port = os.getenv("DAPR_HTTP_PORT", "3500")
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"http://localhost:{dapr_port}/v1.0/healthz", timeout=2.0)
                    if response.status_code == 200:
                        self.dapr_available = True
                        logger.info("Dapr sidecar detected and available")
                    else:
                        logger.info("Dapr sidecar not available, running in standalone mode")
            except Exception:
                logger.info("Dapr sidecar not available, running in standalone mode")
            
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
                
                if self.dapr_available:
                    # Initialize Dapr Agent with full configuration
                    self.agent = DurableAgent(
                        name=self.name,
                        role=self.role,
                        instructions=[
                            "You are a Compliance Insight Harvester specialized in gathering and analyzing regulatory intelligence.",
                            "You extract insights from various sources including regulatory updates, industry benchmarks, and risk assessments.",
                            "You provide actionable intelligence for compliance decision-making.",
                            "You focus on practical, implementable recommendations for SMB companies.",
                            "You prioritize high-impact, low-effort compliance improvements.",
                            "Focus on factual, verifiable information from authoritative sources.",
                            "Provide structured responses with clear sections and actionable recommendations."
                        ],
                        # LLM configuration
                        llm=llm_client,
                        # Memory configuration
                        memory=ConversationDaprStateMemory(
                            store_name="conversationstore",
                            session_id="harvester-default"
                        ),
                        # Dapr configuration
                        message_bus_name="messagepubsub",
                        state_store_name="workflowstatestore",
                        agents_registry_store_name="agentstatestore",
                        tools=[]
                    )
                    
                    # Initialize Dapr SDK client for pub/sub
                    if DAPR_SDK_AVAILABLE:
                        self.dapr_client = DaprClient()
                        logger.info("Dapr SDK client initialized")
                else:
                    # Create a simple agent without Dapr dependencies
                    logger.info("Creating standalone agent without Dapr dependencies")
                    self.agent = type('SimpleAgent', (), {
                        'llm': llm_client,
                        'run': self._simple_agent_run
                    })()
                
                logger.info("Agent initialized successfully")
            
            self.initialized = True
            
        except Exception as e:
            logger.error(f"Error initializing harvester agent: {e}")
            # Don't raise - allow the agent to start in degraded mode
            self.initialized = True
    
    async def _simple_agent_run(self, query: str) -> str:
        """Simple agent run method for standalone mode"""
        if hasattr(self.agent, 'llm') and self.agent.llm:
            try:
                # Use the LLM directly
                response = await self.agent.llm.chat_completion(
                    messages=[{"role": "user", "content": query}]
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return f"Analysis request received: {query}\n\nNote: LLM processing failed, running in basic mode."
        else:
            return f"Analysis request received: {query}\n\nNote: Running in basic mode without LLM."
    
    async def search_web(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Perform web search using fallback method"""
        try:
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
                # Use agent for intelligent analysis
                response = await self.agent.run(agent_query)
                
                return {
                    "status": "success",
                    "source": "dapr_agent" if self.dapr_available else "standalone_agent",
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
                        "note": "Agent not available, using fallback mode",
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
        "dapr_sidecar": "✅ Connected" if harvester_agent.dapr_available else "❌ Standalone Mode",
        "openai": "✅ Present" if os.getenv("OPENAI_API_KEY") else "❌ Missing",
        "openrouter": "✅ Present" if os.getenv("OPENROUTER_API_KEY") else "❌ Missing"
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
            "dapr_sidecar_available": harvester_agent.dapr_available,
            "agent_initialized": harvester_agent.initialized,
            "mode": "dapr" if harvester_agent.dapr_available else "standalone"
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
        "mode": "dapr" if harvester_agent.dapr_available else "standalone",
        "capabilities": [
            "Compliance intelligence harvesting",
            "Web search via fallback",
            "Dapr Agents integration" if harvester_agent.dapr_available else "Standalone operation",
            "Pub/Sub messaging" if harvester_agent.dapr_available else "Direct API calls",
            "State management" if harvester_agent.dapr_available else "Stateless operation"
        ],
        "components": {
            "dapr_agents": DAPR_AGENTS_AVAILABLE,
            "dapr_sdk": DAPR_SDK_AVAILABLE,
            "dapr_sidecar": harvester_agent.dapr_available,
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY"))
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 9180))
    logger.info(f"Starting Harvester Insights Agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
