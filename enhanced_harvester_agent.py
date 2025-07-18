"""
Enhanced compliance harvester agent with robust DurableAgent integration.
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from durable_agent_retry import durable_agent_manager, get_durable_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for structured responses
class ComplianceInsight(BaseModel):
    """Structured compliance insight data."""
    insight_id: str = Field(..., description="Unique identifier for the insight")
    title: str = Field(..., description="Title of the compliance insight")
    description: str = Field(..., description="Detailed description")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    recommendations: List[str] = Field(default_factory=list, description="List of recommendations")
    affected_systems: List[str] = Field(default_factory=list, description="List of affected systems")
    compliance_frameworks: List[str] = Field(default_factory=list, description="Relevant compliance frameworks")
    created_at: str = Field(..., description="ISO timestamp of creation")
    source: str = Field(default="durable_agent", description="Source of the insight")

class InsightRequest(BaseModel):
    """Request model for generating compliance insights."""
    query: str = Field(..., description="The compliance query or question")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    max_insights: int = Field(default=5, description="Maximum number of insights to generate")

class InsightResponse(BaseModel):
    """Response model for compliance insights."""
    success: bool = Field(..., description="Whether the request was successful")
    insights: List[ComplianceInsight] = Field(default_factory=list, description="Generated insights")
    fallback_used: bool = Field(default=False, description="Whether fallback mode was used")
    message: Optional[str] = Field(default=None, description="Additional message or error details")
    agent_status: str = Field(..., description="Status of the DurableAgent")

class SearchRequest(BaseModel):
    """Request model for searching compliance data."""
    query: str = Field(..., description="Search query")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Search filters")
    limit: int = Field(default=10, description="Maximum number of results")

class SearchResponse(BaseModel):
    """Response model for search results."""
    success: bool = Field(..., description="Whether the search was successful")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Search results")
    total_count: int = Field(default=0, description="Total number of matching results")
    fallback_used: bool = Field(default=False, description="Whether fallback mode was used")

class HealthResponse(BaseModel):
    """Response model for health checks."""
    status: str = Field(..., description="Health status")
    dapr_connected: bool = Field(..., description="Whether Dapr is connected")
    agent_initialized: bool = Field(..., description="Whether DurableAgent is initialized")
    components_healthy: bool = Field(..., description="Whether all components are healthy")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")

# Application state
app_start_time = None
dapr_health_status = {"connected": False, "last_check": None}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle with proper DurableAgent initialization."""
    global app_start_time
    app_start_time = asyncio.get_event_loop().time()
    
    logger.info("Starting compliance harvester agent...")
    
    # Start background task to initialize DurableAgent
    asyncio.create_task(initialize_agent_background())
    
    # Start health monitoring
    asyncio.create_task(monitor_dapr_health())
    
    yield
    
    # Cleanup
    logger.info("Shutting down compliance harvester agent...")
    await durable_agent_manager.shutdown()

async def initialize_agent_background():
    """Background task to initialize DurableAgent with retries."""
    logger.info("Starting DurableAgent initialization in background...")
    
    # Wait a bit for Dapr to fully start
    await asyncio.sleep(5)
    
    success = await durable_agent_manager.initialize_durable_agent()
    if success:
        logger.info("DurableAgent initialized successfully in background")
    else:
        logger.warning("DurableAgent initialization failed, will use fallback mode")

async def monitor_dapr_health():
    """Background task to monitor Dapr health."""
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:3500/v1.0/healthz", timeout=5.0)
                dapr_health_status["connected"] = response.status_code == 200
                dapr_health_status["last_check"] = asyncio.get_event_loop().time()
        except Exception as e:
            logger.warning(f"Dapr health check failed: {e}")
            dapr_health_status["connected"] = False
            dapr_health_status["last_check"] = asyncio.get_event_loop().time()
        
        await asyncio.sleep(30)  # Check every 30 seconds

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Compliance Harvester Agent",
    description="AI-powered compliance insights and analysis service",
    version="1.0.0",
    lifespan=lifespan
)

async def generate_fallback_insights(query: str, max_insights: int = 5) -> List[ComplianceInsight]:
    """Generate fallback compliance insights when DurableAgent is not available."""
    import uuid
    from datetime import datetime
    
    # Simple rule-based fallback insights
    fallback_insights = []
    
    # Basic compliance areas to check
    compliance_areas = [
        {
            "title": "Data Privacy Compliance Review",
            "description": f"Review data privacy practices related to: {query}",
            "severity": "medium",
            "frameworks": ["GDPR", "CCPA"],
            "recommendations": ["Conduct data mapping", "Review consent mechanisms", "Update privacy policies"]
        },
        {
            "title": "Security Controls Assessment",
            "description": f"Assess security controls for: {query}",
            "severity": "high",
            "frameworks": ["SOC 2", "ISO 27001"],
            "recommendations": ["Review access controls", "Audit security configurations", "Update incident response procedures"]
        },
        {
            "title": "Regulatory Compliance Check",
            "description": f"Check regulatory requirements for: {query}",
            "severity": "medium",
            "frameworks": ["SOX", "HIPAA"],
            "recommendations": ["Review regulatory requirements", "Update compliance documentation", "Schedule compliance audit"]
        }
    ]
    
    for i, area in enumerate(compliance_areas[:max_insights]):
        insight = ComplianceInsight(
            insight_id=str(uuid.uuid4()),
            title=area["title"],
            description=area["description"],
            severity=area["severity"],
            recommendations=area["recommendations"],
            affected_systems=["System under review"],
            compliance_frameworks=area["frameworks"],
            created_at=datetime.utcnow().isoformat(),
            source="fallback_mode"
        )
        fallback_insights.append(insight)
    
    return fallback_insights

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with comprehensive status."""
    global app_start_time
    
    uptime = asyncio.get_event_loop().time() - app_start_time if app_start_time else 0
    
    return HealthResponse(
        status="healthy",
        dapr_connected=dapr_health_status["connected"],
        agent_initialized=durable_agent_manager.is_initialized,
        components_healthy=dapr_health_status["connected"] and durable_agent_manager.is_initialized,
        uptime_seconds=uptime
    )

@app.post("/insights", response_model=InsightResponse)
async def generate_insights(request: InsightRequest, background_tasks: BackgroundTasks):
    """Generate compliance insights using DurableAgent or fallback mode."""
    try:
        # Try to use DurableAgent first
        if durable_agent_manager.is_initialized:
            try:
                async with get_durable_agent() as agent:
                    # Use DurableAgent to generate insights
                    # Replace this with actual DurableAgent API calls
                    agent_response = await agent.generate_insights(
                        query=request.query,
                        context=request.context,
                        max_insights=request.max_insights
                    )
                    
                    # Convert agent response to structured insights
                    insights = []
                    for item in agent_response.get("insights", []):
                        insight = ComplianceInsight(**item)
                        insights.append(insight)
                    
                    return InsightResponse(
                        success=True,
                        insights=insights,
                        fallback_used=False,
                        message="Insights generated using DurableAgent",
                        agent_status="active"
                    )
                    
            except Exception as e:
                logger.error(f"DurableAgent failed, falling back: {e}")
                # Fall through to fallback mode
        
        # Use fallback mode
        logger.info("Using fallback mode for insight generation")
        fallback_insights = await generate_fallback_insights(request.query, request.max_insights)
        
        return InsightResponse(
            success=True,
            insights=fallback_insights,
            fallback_used=True,
            message="Insights generated using fallback mode",
            agent_status="fallback"
        )
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

@app.post("/search", response_model=SearchResponse)
async def search_compliance_data(request: SearchRequest):
    """Search compliance data using DurableAgent or fallback mode."""
    try:
        # Try to use DurableAgent first
        if durable_agent_manager.is_initialized:
            try:
                async with get_durable_agent() as agent:
                    # Use DurableAgent to search
                    search_results = await agent.search(
                        query=request.query,
                        filters=request.filters,
                        limit=request.limit
                    )
                    
                    return SearchResponse(
                        success=True,
                        results=search_results.get("results", []),
                        total_count=search_results.get("total_count", 0),
                        fallback_used=False
                    )
                    
            except Exception as e:
                logger.error(f"DurableAgent search failed, falling back: {e}")
        
        # Fallback search implementation
        fallback_results = [
            {
                "id": "fallback-1",
                "title": f"Compliance item related to: {request.query}",
                "description": "This is a fallback search result",
                "relevance_score": 0.8
            }
        ]
        
        return SearchResponse(
            success=True,
            results=fallback_results,
            total_count=len(fallback_results),
            fallback_used=True
        )
        
    except Exception as e:
        logger.error(f"Error searching compliance data: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/agent/status")
async def get_agent_status():
    """Get detailed status of the DurableAgent."""
    return {
        "initialized": durable_agent_manager.is_initialized,
        "dapr_connected": dapr_health_status["connected"],
        "last_health_check": dapr_health_status["last_check"],
        "agent_type": "DurableAgent" if durable_agent_manager.is_initialized else "Fallback"
    }

@app.post("/agent/reinitialize")
async def reinitialize_agent():
    """Manually trigger DurableAgent reinitialization."""
    try:
        success = await durable_agent_manager.initialize_durable_agent()
        return {
            "success": success,
            "message": "DurableAgent reinitialization completed" if success else "DurableAgent reinitialization failed"
        }
    except Exception as e:
        logger.error(f"Error reinitializing agent: {e}")
        raise HTTPException(status_code=500, detail=f"Reinitialization failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9180)
