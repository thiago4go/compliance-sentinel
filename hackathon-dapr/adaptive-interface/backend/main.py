from fastapi import FastAPI, Request, Body, HTTPException
from dapr.clients import DaprClient
import json
import aiohttp
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '../.env')
print(f"Looking for .env file at: {dotenv_path}")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print("✅ .env file loaded successfully")
else:
    print(f"⚠️ .env file not found at {dotenv_path}")
    # Try alternative paths
    alt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(alt_path):
        load_dotenv(alt_path)
        print(f"✅ .env file loaded from alternative path: {alt_path}")
    else:
        print("⚠️ Could not find .env file in any location")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Backend service configuration
COMPLIANCE_SERVICE_URL = "http://localhost:9160"  # Direct URL to compliance agent service

@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_message = data.get("message")
    session_id = data.get("session_id")

    if not user_message:
        return {"status": "error", "message": "No message provided"}

    try:
        # First, try to process the message with the compliance agent service
        response_data = await call_compliance_service(user_message, session_id)
        
        if response_data:
            logger.info("Successfully processed message with compliance agent service")
            return response_data
        
        # If compliance service fails, publish the message to the Dapr pub/sub topic
        with DaprClient() as d:
            publish_data = {"user_message": user_message, "session_id": session_id}
            d.publish_event(pubsub_name='messagebus', topic_name='new-request', data=json.dumps(publish_data))
            logger.info(f"Published message to new-request topic: {user_message}")
        
        # Return a response in the format expected by the frontend
        return {
            "response": "Message received and forwarded to workflow agent.",
            "agent_available": False,
            "session_id": session_id
        }
    
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        return {
            "response": f"Error: {str(e)}",
            "agent_available": False,
            "session_id": session_id
        }

async def call_compliance_service(message: str, session_id: str = None):
    """Call the compliance agent service directly."""
    try:
        payload = {
            "message": message,
            "session_id": session_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{COMPLIANCE_SERVICE_URL}/query",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Compliance service call failed with status: {response.status}")
                    return None
    except Exception as e:
        logger.warning(f"Error calling compliance service: {e}")
        return None

@app.get("/dapr/subscribe")
async def subscribe():
    return [
        {
            "pubsubname": "messagebus",
            "topic": "new-request",
            "route": "/dapr/events"
        }
    ]

@app.post("/dapr/events")
async def dapr_events(request: Request):
    data = await request.json()
    # In a real scenario, you would process the event data here
    logger.info(f"Received Dapr event: {data}")
    return {"status": "success"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Main Backend Service on port 9161...")
    uvicorn.run(app, host="0.0.0.0", port=9161, log_level="info")
