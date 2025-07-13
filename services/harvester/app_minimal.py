import os
import logging
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple FastAPI app for health check testing
app = FastAPI(title="Harvester Health Check Test")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    message: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Simple health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        message="Harvester service is running"
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Compliance Sentinel Harvester Service", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("APP_PORT", "8000"))
    host = os.getenv("APP_HOST", "0.0.0.0")
    
    logger.info(f"🌟 Starting minimal harvester service on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
