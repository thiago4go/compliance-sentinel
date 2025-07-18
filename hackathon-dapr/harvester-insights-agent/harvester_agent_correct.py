import logging
import os
import json
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn
import httpx

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Disable telemetry
os.environ["LITERAL_API_KEY"] = ""
os.environ["LITERAL_DISABLE"] = "true"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import dapr-agents
try:
    from dapr_agents import DurableAgent
    from dapr_agents.llm import OpenAIChatClient
    from dapr_agents.memory import ConversationDaprStateMemory
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

# Global agent instance
agent: Optional[DurableAgent] = None
dapr_client: Optional[DaprClient] = None

# Pydantic models for request/response
class ComplianceFramework(BaseModel):
    """Compliance framework information"""
    code: str = Field(..., description="Framework code (e.g., GDPR, SOX)")
    name: str = Field(..., description="Full framework name")
    region: str = Field(..., description="Applicable region")

class InsightRequest(BaseModel):
    """Request for compliance insights"""
    framework: str = Field(..., description="Compliance framework code")
    company_name: str = Field(..., description="Company name")
    industry: Optional[str] = Field("Technology", description="Industry sector")
    query: Optional[str] = Field(None, description="Specific query or use default analysis")

class ComplianceInsight(BaseModel):
    """Structured compliance insight"""
    analysis: str = Field(..., description="Detailed compliance analysis")
    framework: str = Field(..., description="Framework analyzed")
    company: str = Field(..., description="Company name")
    industry: str = Field(..., description="Industry sector")
    timestamp: str = Field(..., description="Analysis timestamp")

class InsightResponse(BaseModel):
    """Response containing compliance insights"""
    status: str = Field(..., description="Response status")
    framework: str = Field(..., description="Framework analyzed")
    company_name: str = Field(..., description="Company name")
    insights: ComplianceInsight = Field(..., description="Generated insights")
    timestamp: str = Field(..., description="Response timestamp")
    source: str = Field(..., description="Source of analysis (agent/fallback)")

class SearchRequest(BaseModel):
    """Web search request"""
    query: str = Field(..., description="Search query")
    max_results: Optional[int] = Field(10, description="Maximum results to return")

class SearchResult(BaseModel):
    """Search result item"""
    title: str = Field(..., description="Result title")
    url: str = Field(..., description="Result URL")
    snippet: str = Field(..., description="Result snippet")

class SearchResponse(BaseModel):
    """Web search response"""
    status: str = Field(..., description="Search status")
    query: str = Field(..., description="Original query")
    results: List[SearchResult] = Field(..., description="Search results")
    timestamp: str = Field(..., description="Search timestamp")

class ComponentStatus(BaseModel):
    """Component status information"""
    agent: str = Field(..., description="Agent status")
    dapr_agents: str = Field(..., description="Dapr agents availability")
    dapr_sdk: str = Field(..., description="Dapr SDK availability")
    dapr_sidecar: str = Field(..., description="Dapr sidecar connection")
    openai: str = Field(..., description="OpenAI API key status")
    database: str = Field(..., description="Database configuration status")

class AgentConfiguration(BaseModel):
    """Agent configuration information"""
    name: str = Field(..., description="Agent name")
    role: str = Field(..., description="Agent role")
    dapr_agents_available: bool = Field(..., description="Dapr agents availability")
    dapr_sdk_available: bool = Field(..., description="Dapr SDK availability")
    dapr_connected: bool = Field(..., description="Dapr connection status")
    agent_initialized: bool = Field(..., description="Agent initialization status")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="Health check timestamp")
    components: ComponentStatus = Field(..., description="Component statuses")
    configuration: AgentConfiguration = Field(..., description="Agent configuration")

async def search_web(query: str, max_results: int = 10) -> Dict[str, Any]:
    """Perform web search using fallback method"""
    try:
        # Fallback to direct HTTP search (DuckDuckGo)
        async with httpx.AsyncClient() as client:
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
                # Convert to structured results
                results = []
                if "RelatedTopics" in data:
                    for topic in data["RelatedTopics"][:max_results]:
                        if isinstance(topic, dict) and "Text" in topic:
                            results.append({
                                "title": topic.get("Text", "")[:100],
                                "url": topic.get("FirstURL", ""),
                                "snippet": topic.get("Text", "")
                            })
                
                return {
                    "status": "success",
                    "results": results
                }
            else:
                return {
                    "status": "error",
                    "message": f"Search failed with status {response.status_code}",
                    "results": []
                }
                
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "results": []
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
            
            Focus on actionable insights for SMB companies. Be specific and practical.
            """
        
        if DAPR_AGENTS_AVAILABLE and agent:
            try:
                # Use DurableAgent for intelligent analysis
                response = await agent.run(agent_query)
                
                return {
                    "status": "success",
                    "source": "dapr_agent",
                    "insights": ComplianceInsight(
                        analysis=response,
                        framework=framework,
                        company=company_name,
                        industry=industry,
                        timestamp=datetime.now().isoformat()
                    )
                }
            except Exception as e:
                logger.warning(f"Agent run failed, using fallback: {e}")
                # Fall through to fallback
        
        # Fallback analysis with structured response
        fallback_analysis = f"""
        **Compliance Analysis for {company_name} - {framework} Framework**
        
        **Industry Context**: {industry}
        
        **Key Requirements**:
        • Regulatory compliance documentation
        • Risk assessment procedures
        • Staff training and awareness
        • Regular compliance audits
        • Incident response procedures
        
        **Risk Areas**:
        • Data protection and privacy
        • Regulatory reporting requirements
        • Third-party vendor management
        • Documentation and record keeping
        
        **Recommendations**:
        • Conduct comprehensive compliance gap analysis
        • Implement compliance management system
        • Establish regular monitoring and reporting
        • Provide ongoing staff training
        
        **Implementation Priorities**:
        1. Immediate: Document current processes
        2. Short-term: Address critical gaps
        3. Medium-term: Implement monitoring systems
        4. Long-term: Continuous improvement program
        
        *Note: This is a basic analysis. For detailed compliance guidance, please consult with compliance professionals.*
        """
        
        return {
            "status": "success",
            "source": "fallback",
            "insights": ComplianceInsight(
                analysis=fallback_analysis,
                framework=framework,
                company=company_name,
                industry=industry,
                timestamp=datetime.now().isoformat()
            )
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

    try:
        # Check if Dapr sidecar is available
        dapr_available = False
        dapr_port = os.getenv("DAPR_HTTP_PORT", "3500")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://localhost:{dapr_port}/v1.0/healthz", timeout=2.0)
                if response.status_code == 200:
                    dapr_available = True
                    logger.info("Dapr sidecar detected and available")
        except Exception:
            logger.info("Dapr sidecar not available, will use fallback mode")

        if DAPR_AGENTS_AVAILABLE and dapr_available:
            # Check API key
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                try:
                    # Create OpenAI client
                    llm_client = OpenAIChatClient(
                        api_key=openai_key,
                        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                    )
                    
                    # Create DurableAgent
                    agent = DurableAgent(
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
                            "Always be specific and practical in your advice."
                        ],
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
                    
                    logger.info("DurableAgent initialized successfully")
                    
                except Exception as e:
                    logger.warning(f"DurableAgent initialization failed: {e}")
                    logger.info("Will use fallback mode")
            else:
                logger.warning("No OpenAI API key found")

        # Initialize Dapr client if available
        if DAPR_SDK_AVAILABLE and dapr_available:
            try:
                dapr_client = DaprClient()
                logger.info("Dapr client initialized successfully")
            except Exception as e:
                logger.warning(f"Dapr client initialization failed: {e}")

    except Exception as e:
        logger.error(f"Error during initialization: {e}")

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
    components = ComponentStatus(
        agent="✅ Running" if agent else "❌ Not Available",
        dapr_agents="✅ Available" if DAPR_AGENTS_AVAILABLE else "❌ Not Available",
        dapr_sdk="✅ Available" if DAPR_SDK_AVAILABLE else "❌ Not Available",
        dapr_sidecar="✅ Connected" if dapr_client else "❌ Not Connected",
        openai="✅ Present" if os.getenv("OPENAI_API_KEY") else "❌ Missing",
        database="✅ Present" if os.getenv("DB_URL") else "❌ Missing"
    )
    
    configuration = AgentConfiguration(
        name="HarvesterInsightsAgent",
        role="Compliance Intelligence Harvester",
        dapr_agents_available=DAPR_AGENTS_AVAILABLE,
        dapr_sdk_available=DAPR_SDK_AVAILABLE,
        dapr_connected=bool(dapr_client),
        agent_initialized=bool(agent)
    )
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        components=components,
        configuration=configuration
    )

@app.post("/harvest-insights", response_model=InsightResponse)
async def harvest_insights_endpoint(request: InsightRequest):
    """Generate compliance insights"""
    try:
        result = await harvest_insights(
            request.framework,
            request.company_name,
            request.industry or "Technology",
            request.query
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return InsightResponse(
            status=result["status"],
            framework=request.framework,
            company_name=request.company_name,
            insights=result["insights"],
            timestamp=datetime.now().isoformat(),
            source=result["source"]
        )
        
    except Exception as e:
        logger.error(f"Error processing insights request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse)
async def search_web_endpoint(request: SearchRequest):
    """Perform web search"""
    try:
        result = await search_web(request.query, request.max_results or 10)
        
        # Convert results to Pydantic models
        search_results = []
        for item in result.get("results", []):
            search_results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("snippet", "")
            ))
        
        return SearchResponse(
            status=result["status"],
            query=request.query,
            results=search_results,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error processing search request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/frameworks", response_model=List[ComplianceFramework])
async def get_frameworks():
    """Get supported compliance frameworks"""
    return [
        ComplianceFramework(code="GDPR", name="General Data Protection Regulation", region="EU"),
        ComplianceFramework(code="SOX", name="Sarbanes-Oxley Act", region="US"),
        ComplianceFramework(code="HIPAA", name="Health Insurance Portability and Accountability Act", region="US"),
        ComplianceFramework(code="PCI-DSS", name="Payment Card Industry Data Security Standard", region="Global"),
        ComplianceFramework(code="ISO27001", name="Information Security Management", region="Global"),
        ComplianceFramework(code="CCPA", name="California Consumer Privacy Act", region="US"),
        ComplianceFramework(code="NIST", name="NIST Cybersecurity Framework", region="US")
    ]

@app.get("/agent/info")
async def agent_info():
    """Get agent information"""
    return {
        "name": "HarvesterInsightsAgent",
        "role": "Compliance Intelligence Harvester",
        "status": "running" if agent else "fallback_mode",
        "capabilities": [
            "Compliance intelligence harvesting",
            "Web search functionality",
            "Dapr Agents integration" if agent else "Fallback analysis",
            "Pub/Sub messaging" if dapr_client else "Direct API calls",
            "State management" if dapr_client else "Stateless operation"
        ],
        "components": {
            "dapr_agents": DAPR_AGENTS_AVAILABLE,
            "dapr_sdk": DAPR_SDK_AVAILABLE,
            "dapr_connected": bool(dapr_client),
            "agent_active": bool(agent),
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "database_configured": bool(os.getenv("DB_URL"))
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 9180))
    logger.info(f"Starting Harvester Insights Agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
