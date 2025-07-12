import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from agents.insight_harvester_with_secrets import InsightHarvesterAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global agent instance
harvester_agent: Optional[InsightHarvesterAgent] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    global harvester_agent
    
    # Startup
    try:
        logger.info("🚀 Starting Insight Harvester Agent...")
        
        # Create agent instance (will load secrets from KV store)
        harvester_agent = InsightHarvesterAgent()
        
        # Initialize MCP client connection first
        await harvester_agent.initialize_mcp_client()
        
        # Configure as Dapr service (but don't start server - FastAPI handles that)
        harvester_agent = harvester_agent.as_service(
            port=int(os.getenv("APP_PORT", "8000")),
            start_server=False  # Let FastAPI handle the server
        )
        
        logger.info("✅ Insight Harvester Agent started successfully")
        logger.info("🔐 API keys loaded securely from KV store")
        logger.info("🌐 MCP client connected to external server")
        
    except Exception as e:
        logger.error(f"❌ Failed to start harvester agent: {e}")
        raise
    
    yield
    
    # Shutdown
    if harvester_agent:
        try:
            await harvester_agent.shutdown()
            logger.info("✅ Harvester agent shutdown completed")
        except Exception as e:
            logger.error(f"⚠️ Error during shutdown: {e}")

# FastAPI app with lifespan
app = FastAPI(
    title="Compliance Sentinel - Insight Harvester",
    description="AI-powered insight harvesting service using Dapr Agents with secure KV store integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    session_id: str = "default"
    max_results: int = 10
    save_results: bool = True

class QueryResponse(BaseModel):
    response: str
    session_id: str
    query: str
    timestamp: str
    sources_used: list = []

class HealthResponse(BaseModel):
    status: str
    agent_initialized: bool
    mcp_connected: bool
    kv_store_connected: bool
    timestamp: str

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    mcp_connected = False
    kv_store_connected = False
    
    if harvester_agent:
        # Check MCP connection
        if harvester_agent.mcp_client:
            try:
                mcp_connected = True
            except:
                mcp_connected = False
        
        # Check if secrets were loaded (indicates KV store connectivity)
        kv_store_connected = bool(os.getenv("OPENROUTER_API_KEY"))
    
    return HealthResponse(
        status="healthy" if harvester_agent else "unhealthy",
        agent_initialized=harvester_agent is not None,
        mcp_connected=mcp_connected,
        kv_store_connected=kv_store_connected,
        timestamp=datetime.now().isoformat()
    )

# Main query processing endpoint
@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """Process a query through the harvester agent"""
    if not harvester_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        logger.info(f"🔍 Processing query: {request.query[:100]}...")
        
        # Process query through agent
        response = await harvester_agent.run_harvester(
            query=request.query,
            session_id=request.session_id,
            max_results=request.max_results
        )
        
        # Save results in background if requested
        if request.save_results:
            background_tasks.add_task(
                save_query_results,
                request.query,
                response,
                request.session_id
            )
        
        logger.info(f"✅ Query processed successfully")
        
        return QueryResponse(
            response=response,
            session_id=request.session_id,
            query=request.query,
            timestamp=datetime.now().isoformat(),
            sources_used=["DuckDuckGo", "MCP Server", "KV Store Config"]
        )
        
    except Exception as e:
        logger.error(f"❌ Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

# Background task for saving results
async def save_query_results(query: str, response: str, session_id: str):
    """Save query results to state store"""
    try:
        if harvester_agent:
            await harvester_agent.save_search_results(query, response, session_id)
            logger.info(f"💾 Saved search results for session: {session_id}")
    except Exception as e:
        logger.error(f"⚠️ Error saving query results: {e}")

# Workflow management endpoints
@app.post("/workflow/start")
async def start_workflow(request: QueryRequest):
    """Start a workflow for complex query processing"""
    if not harvester_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        workflow_id = await harvester_agent.start_workflow(request.query, request.session_id)
        logger.info(f"🔄 Started workflow: {workflow_id}")
        return {"workflow_id": workflow_id, "status": "started"}
    except Exception as e:
        logger.error(f"❌ Error starting workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get workflow status"""
    if not harvester_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        status = await harvester_agent.get_workflow_status(workflow_id)
        return {"workflow_id": workflow_id, "status": status}
    except Exception as e:
        logger.error(f"❌ Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Development/testing endpoints
@app.get("/agent/info")
async def get_agent_info():
    """Get agent information"""
    if not harvester_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return {
        "name": harvester_agent.name,
        "role": harvester_agent.role,
        "goal": harvester_agent.goal,
        "tools_count": len(harvester_agent.tools),
        "mcp_connected": harvester_agent.mcp_client is not None,
        "secrets_loaded": bool(os.getenv("OPENROUTER_API_KEY")),
        "components": {
            "agent_state_store": os.getenv("AGENT_STATE_STORE", "agent-kv-store"),
            "message_pubsub": os.getenv("MESSAGE_PUBSUB", "agent-pubsub"),
            "conversation_store": os.getenv("CONVERSATION_STORE", "agent-kv-store")
        }
    }

# Configuration endpoint
@app.get("/config")
async def get_config():
    """Get current configuration (non-sensitive)"""
    return {
        "app_port": os.getenv("APP_PORT", "8000"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "mcp_server_url": os.getenv("MCP_SERVER_URL", "http://138.3.218.137/ddg/mcp"),
        "openrouter_model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o"),
        "max_search_results": os.getenv("AGENT_MAX_SEARCH_RESULTS", "10"),
        "api_keys_loaded": {
            "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
            "openai": bool(os.getenv("OPENAI_API_KEY_HARVESTER"))
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("APP_PORT", "8000"))
    host = os.getenv("APP_HOST", "0.0.0.0")
    
    logger.info(f"🌟 Starting Compliance Sentinel Harvester on {host}:{port}")
    logger.info(f"🔐 Using secure KV store for API keys")
    logger.info(f"🌐 Connecting to external MCP server")
    
    uvicorn.run(app, host=host, port=port, log_level="info")
