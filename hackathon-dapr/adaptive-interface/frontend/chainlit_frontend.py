import chainlit as cl
import os
import logging
import aiohttp
import json
from typing import Optional

# Disable telemetry to avoid traceloop issues
os.environ["LITERAL_API_KEY"] = ""
os.environ["LITERAL_DISABLE"] = "true"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Backend service configuration
BACKEND_SERVICE_URL = "http://localhost:3500/v1.0/invoke/adaptive-interface-backend/method"
BACKEND_DIRECT_URL = "http://localhost:9161"  # Fallback for local testing (main.py)
COMPLIANCE_SERVICE_URL = "http://localhost:3501/v1.0/invoke/compliance-agent-backend/method"
COMPLIANCE_DIRECT_URL = "http://localhost:9160"  # Fallback for local testing (compliance_agent_service.py)

@cl.on_chat_start
async def start():
    """Initialize the frontend when chat starts."""

    # Test backend connectivity
    backend_available = await test_backend_connectivity()

    if backend_available:
        welcome_msg = """
# 🛡️ Compliance Sentinel

Welcome to Compliance Sentinel! I'm your intelligent compliance assistant powered by a distributed multi-agent system built with Dapr Workflows and AI.

I can help you with:

📋 **Regulatory Expertise** - Navigate complex frameworks like GDPR, SOX, ISO 27001, and HIPAA
🔍 **Compliance Analysis** - Identify gaps and provide actionable recommendations
📄 **Document Review** - Analyze policies against regulatory requirements
🗺️ **Strategic Planning** - Develop comprehensive compliance roadmaps
🔄 **Continuous Monitoring** - Stay updated on regulatory changes

What compliance challenge can I help you with today?

✅ System Status: All agents connected and operational
🏗️ Architecture: Distributed multi-agent system with Dapr Workflow orchestration
"""
    else:
        welcome_msg = """
# 🛡️ Compliance Sentinel

⚠️ **Backend Service Unavailable**

The compliance agent backend service is not responding. This could mean:
• Backend service is not running
• Dapr sidecar is not configured properly
• Network connectivity issues

**Troubleshooting:**
1. Ensure backend service is running on port 9160
2. Check Dapr configuration and components
3. Verify service-to-service invocation setup

Please start the backend service and refresh the page.
"""

    await cl.Message(content=welcome_msg).send()
    logger.info("Frontend initialized")

async def test_backend_connectivity() -> bool:
    """Test if the backend service is available."""
    try:
        # Try Dapr service invocation first
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_SERVICE_URL}/health", timeout=5) as response:
                if response.status == 200:
                    logger.info("Backend accessible via Dapr service invocation")
                    return True
    except Exception as e:
        logger.warning(f"Dapr service invocation failed: {e}")

    try:
        # Fallback to direct connection
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_DIRECT_URL}/health", timeout=5) as response:
                if response.status == 200:
                    logger.info("Backend accessible via direct connection")
                    return True
    except Exception as e:
        logger.warning(f"Direct backend connection failed: {e}")

    return False

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages by calling the backend service."""

    try:
        async with cl.Step(name="🔄 Backend Processing", type="tool") as step:
            step.output = "Sending query to compliance agent backend..."

            # Prepare the request payload
            payload = {
                "message": message.content
            }

            # Try Dapr service invocation first
            response_data = await call_backend_service(payload)

            if response_data:
                step.output = "✅ Response received from backend"

                # Display agent availability status
                agent_status = "🤖 Adaptive Compliance Agent" if response_data.get("agent_available") else "📝 Basic Mode"

                # Send the response
                full_response = f"{response_data['response']}\n\n---\n*{agent_status}*"
                await cl.Message(content=full_response).send()
            else:
                step.output = "❌ Backend service unavailable"
                await cl.Message(
                    content="❌ **Service Unavailable**\n\nThe compliance agent backend is not responding. Please ensure the backend service is running and try again."
                ).send()

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await cl.Message(
            content=f"❌ **Error Processing Request**\n\nI encountered an error: {str(e)}\n\nPlease try again or contact support if the issue persists."
        ).send()

async def call_backend_service(payload: dict) -> Optional[dict]:
    """Call the backend service via Dapr or direct connection."""

    # Try Dapr service invocation first
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_SERVICE_URL}/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Dapr service call failed with status: {response.status}")
    except Exception as e:
        logger.warning(f"Dapr service invocation failed: {e}")

    # Fallback to direct connection
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_DIRECT_URL}/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            ) as response:
                if response.status == 200:
                    logger.info("Used direct backend connection")
                    return await response.json()
                else:
                    logger.error(f"Direct backend call failed with status: {response.status}")
    except Exception as e:
        logger.error(f"Direct backend connection failed: {e}")

    return None

if __name__ == "__main__":
    print("🚀 Starting Adaptive Compliance Interface Frontend...")
    print("🔗 Backend Service: compliance-agent-backend")
    print("🌐 Ready for connections on configured port")
