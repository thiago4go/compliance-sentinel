import os
import logging
from datetime import datetime
from fastapi import FastAPI, Response
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app with enhanced health check
app = FastAPI(title="Harvester Health Check Enhanced")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    message: str
    app_id: str
    version: str

@app.get("/health")
async def health_check(response: Response):
    """Enhanced health check endpoint for Diagrid Catalyst"""
    try:
        # Set proper headers
        response.headers["Content-Type"] = "application/json"
        response.headers["Cache-Control"] = "no-cache"

        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "message": "Harvester service is running",
            "app_id": os.getenv("DAPR_APP_ID", "harvester-agent"),
            "version": "1.0.0"
        }

        logger.info(f"Health check requested - returning: {health_data}")
        return health_data

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        response.status_code = 500
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "message": f"Health check failed: {str(e)}",
            "app_id": os.getenv("DAPR_APP_ID", "harvester-agent"),
            "version": "1.0.0"
        }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Compliance Sentinel Harvester Service",
        "status": "running",
        "app_id": os.getenv("DAPR_APP_ID", "harvester-agent"),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/dapr/config")
async def dapr_config():
    """Dapr configuration endpoint that might be expected"""
    return {
        "entities": [],
        "actorIdleTimeout": "1h",
        "actorScanInterval": "30s",
        "drainOngoingCallTimeout": "1m",
        "drainRebalancedActors": True
    }

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("APP_PORT", "8000"))
    host = os.getenv("APP_HOST", "0.0.0.0")

    logger.info(f"🌟 Starting enhanced harvester service on {host}:{port}")
    logger.info(f"🔍 App ID: {os.getenv('DAPR_APP_ID', 'harvester-agent')}")
    logger.info(f"🏥 Health check endpoint: /health")

    uvicorn.run(app, host=host, port=port, log_level="info")
