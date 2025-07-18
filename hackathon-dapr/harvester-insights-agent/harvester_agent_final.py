import logging
import os
import json
import aiohttp
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn
import httpx

# Disable telemetry to avoid trace-loop issues
os.environ["LITERAL_API_KEY"] = ""
os.environ["LITERAL_DISABLE"] = "true"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import dapr-agents
try:
    from dapr_agents import Agent  # Use Agent instead of DurableAgent
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

# Global agent instance and secrets
agent: Optional[object] = None
secrets_cache: Dict[str, str] = {}
dapr_client: Optional[DaprClient] = None

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

async def get_secret(secret_name: str, key: str) -> Optional[str]:
    """Get secret from Dapr secret store."""
    cache_key = f"{secret_name}:{key}"

    # Check cache first
    if cache_key in secrets_cache:
        return secrets_cache[cache_key]

    try:
        # Try Dapr secret store first
        dapr_port = os.getenv("DAPR_HTTP_PORT", "3500")
        secret_store = os.getenv("SECRET_STORE", "local-secret-store")

        url = f"http://localhost:{dapr_port}/v1.0/secrets/{secret_store}/{secret_name}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    value = data.get(key)
                    if value:
                        secrets_cache[cache_key] = value
                        return value

    except Exception as e:
        logger.warning(f"Failed to get secret from Dapr: {e}")

    # Fallback to environment variable
    env_var = f"{secret_name.upper()}_{key.upper()}"
    value = os.getenv(env_var)
    if value:
        secrets_cache[cache_key] = value
        return value

    # Final fallback to direct env var
    if secret_name == "openai" and key == "api_key":
        value = os.getenv("OPENAI_API_KEY")
        if value:
            secrets_cache[cache_key] = value
            return value

    return None

async def load_secrets():
    """Load secrets on startup."""
    logger.info("Loading secrets...")

    # Load OpenAI credentials
    openai_key = await get_secret("openai", "api_key")
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
        logger.info("✅ OpenAI API key loaded")
    else:
        logger.warning("⚠️ OpenAI API key not found")

    # Load database credentials
    db_url = os.getenv("DB_URL")
    if db_url:
        logger.info("✅ Database URL available")
    else:
        logger.warning("⚠️ Database URL not found")

async def search_web(query: str, max_results: int = 10) -> Dict[str, Any]:
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

async def harvest_insights(framework: str, company_name: str, industry: str = "Technology", query: str = None) -> Dict[str, Any]:
    """Generate compliance insights using the agent"""
    global agent
    
    try:
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
        
        if DAPR_AGENTS_AVAILABLE and agent:
            # Use Dapr Agent for intelligent analysis
            response = await agent.run(agent_query)
            
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the harvester agent on startup."""
    global agent, dapr_client

    # Load secrets first
    await load_secrets()

    try:
        if DAPR_AGENTS_AVAILABLE:
            agent = Agent(
                name="HarvesterInsightsAgent",
                role="Compliance Intelligence Harvester",
                instructions=[
                    "You are a Compliance Insight Harvester specialized in gathering and analyzing regulatory intelligence.",
                    "You extract insights from various sources including regulatory updates, industry benchmarks, and risk assessments.",
                    "You provide actionable intelligence for compliance decision-making.",
                    "You focus on practical, implementable recommendations for SMB companies.",
                    "You prioritize high-impact, low-effort compliance improvements.",
                    "Focus on factual, verifiable information from authoritative sources.",
                    "Provide structured responses with clear sections and actionable recommendations.",
                    "Always ask clarifying questions when needed to provide better insights."
                ],
                tools=[],  # Start with basic tools
            )
            logger.info("Harvester agent initialized successfully")
        else:
            logger.warning("Running without Dapr Agents")

        # Initialize Dapr client if available
        if DAPR_SDK_AVAILABLE:
            try:
                # Check if Dapr sidecar is available
                dapr_port = os.getenv("DAPR_HTTP_PORT", "3500")
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"http://localhost:{dapr_port}/v1.0/healthz", timeout=2.0)
                    if response.status_code == 200:
                        dapr_client = DaprClient()
                        logger.info("Dapr client initialized successfully")
                    else:
                        logger.info("Dapr sidecar not available")
            except Exception:
                logger.info("Dapr sidecar not available")

    except Exception as e:
        logger.error(f"Error initializing agent: {e}")

    yield

    # Cleanup on shutdown
    logger.info("Shutting down harvester agent")
    if dapr_client:
        dapr_client.close()

app = FastAPI(
    title="Harvester Insights Agent",
    description="Enhanced compliance intelligence harvester with Dapr Agents integration",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    components = {
        "agent": "✅ Running" if agent else "❌ Not Available",
        "dapr_agents": "✅ Available" if DAPR_AGENTS_AVAILABLE else "❌ Not Available",
        "dapr_sdk": "✅ Available" if DAPR_SDK_AVAILABLE else "❌ Not Available",
        "dapr_sidecar": "✅ Connected" if dapr_client else "❌ Not Connected",
        "openai": "✅ Present" if os.getenv("OPENAI_API_KEY") else "❌ Missing",
        "database": "✅ Present" if os.getenv("DB_URL") else "❌ Missing"
    }
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        components=components,
        configuration={
            "name": "HarvesterInsightsAgent",
            "role": "Compliance Intelligence Harvester",
            "dapr_agents_available": DAPR_AGENTS_AVAILABLE,
            "dapr_sdk_available": DAPR_SDK_AVAILABLE,
            "dapr_connected": bool(dapr_client),
            "agent_initialized": bool(agent)
        }
    )

@app.post("/harvest-insights", response_model=InsightResponse)
async def harvest_insights_endpoint(request: InsightRequest):
    """Generate compliance insights"""
    try:
        insights = await harvest_insights(
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
async def search_web_endpoint(request: SearchRequest):
    """Perform web search"""
    try:
        results = await search_web(request.query, request.max_results or 10)
        
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
        "name": "HarvesterInsightsAgent",
        "role": "Compliance Intelligence Harvester",
        "status": "running" if agent else "not_available",
        "capabilities": [
            "Compliance intelligence harvesting",
            "Web search via fallback",
            "Dapr Agents integration" if DAPR_AGENTS_AVAILABLE else "Basic operation",
            "Pub/Sub messaging" if dapr_client else "Direct API calls",
            "State management" if dapr_client else "Stateless operation"
        ],
        "components": {
            "dapr_agents": DAPR_AGENTS_AVAILABLE,
            "dapr_sdk": DAPR_SDK_AVAILABLE,
            "dapr_connected": bool(dapr_client),
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "database_configured": bool(os.getenv("DB_URL"))
        }
    }

@app.get("/frameworks")
async def get_frameworks():
    """Get supported compliance frameworks"""
    return {
        "frameworks": [
            {"code": "GDPR", "name": "General Data Protection Regulation", "region": "EU"},
            {"code": "SOX", "name": "Sarbanes-Oxley Act", "region": "US"},
            {"code": "HIPAA", "name": "Health Insurance Portability and Accountability Act", "region": "US"},
            {"code": "PCI-DSS", "name": "Payment Card Industry Data Security Standard", "region": "Global"},
            {"code": "ISO27001", "name": "Information Security Management", "region": "Global"},
            {"code": "CCPA", "name": "California Consumer Privacy Act", "region": "US"},
            {"code": "NIST", "name": "NIST Cybersecurity Framework", "region": "US"}
        ]
    }

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 9180))
    logger.info(f"Starting Harvester Insights Agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
