import logging
import os
import json
import aiohttp
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'hackathon-dapr', '.env')
load_dotenv(dotenv_path)

# Disable telemetry to avoid trace-loop issues
os.environ["LITERAL_API_KEY"] = ""
os.environ["LITERAL_DISABLE"] = "true"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import dapr-agents
try:
    from dapr_agents import Agent  # type: ignore
    DAPR_AGENTS_AVAILABLE = True
    logger.info("Dapr-agents imported successfully")
except Exception as e:
    DAPR_AGENTS_AVAILABLE = False
    logger.warning(f"Dapr-agents not available: {e}")

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    logger.info("OpenAI SDK imported successfully")
except Exception as e:
    OPENAI_AVAILABLE = False
    logger.warning(f"OpenAI SDK not available: {e}")

# Global agent instance and secrets
agent: Optional[object] = None
openai_client: Optional[object] = None
secrets_cache: Dict[str, str] = {}

class QueryRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    agent_available: bool
    session_id: Optional[str] = None

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
    pg_host = await get_secret("database", "pg_host")
    pg_password = await get_secret("database", "pg_password")

    if pg_host and pg_password:
        os.environ["PG_HOST"] = pg_host
        os.environ["PG_PASSWORD"] = pg_password
        logger.info("✅ Database credentials loaded")
    else:
        logger.warning("⚠️ Database credentials not found")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the compliance agent on startup."""
    global agent, openai_client

    # Load secrets first
    await load_secrets()

    # Initialize OpenAI client
    if OPENAI_AVAILABLE:
        try:
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                openai_client = OpenAI(api_key=openai_key)
                logger.info("✅ OpenAI client initialized")
            else:
                logger.warning("⚠️ OpenAI API key not found, client not initialized")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            openai_client = None

    # Initialize Dapr agent
    try:
        if DAPR_AGENTS_AVAILABLE:
            agent = Agent(
                name="AdaptiveComplianceAgent",
                role="Compliance Intelligence Specialist",
                instructions=[
                    "You are an Adaptive Compliance Interface Agent for SMB companies.",
                    "Provide intelligent compliance insights and recommendations.",
                    "Help with document analysis, regulatory research, and strategic planning.",
                    "Ask clarifying questions when needed.",
                    "Always provide actionable and practical advice."
                ],
                tools=[],  # Start with basic tools
            )
            logger.info("✅ Compliance agent initialized successfully")
        else:
            logger.warning("⚠️ Running without Dapr Agents")
    except Exception as e:
        logger.error(f"Error initializing agent: {e}")

    yield

    # Cleanup on shutdown
    logger.info("Shutting down compliance agent backend")

app = FastAPI(title="Compliance Agent Backend", version="1.0.0", lifespan=lifespan)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_available": DAPR_AGENTS_AVAILABLE,
        "openai_available": OPENAI_AVAILABLE and openai_client is not None,
        "service": "compliance-agent-backend"
    }

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process compliance queries using the Dapr Agent."""
    global agent, openai_client

    try:
        if DAPR_AGENTS_AVAILABLE and agent:
            # Use dapr-agents for intelligent response
            response = await agent.run(request.message)
            return QueryResponse(
                response=response,
                agent_available=True,
                session_id=request.session_id
            )
        elif OPENAI_AVAILABLE and openai_client:
            # Use OpenAI directly as fallback
            response = await process_with_openai(request.message)
            return QueryResponse(
                response=response,
                agent_available=False,
                session_id=request.session_id
            )
        else:
            # Fallback to basic responses
            response = await handle_basic_response(request.message)
            return QueryResponse(
                response=response,
                agent_available=False,
                session_id=request.session_id
            )

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

async def process_with_openai(user_message: str) -> str:
    """Process query using OpenAI API directly."""
    global openai_client
    
    try:
        model = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")
        
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an Adaptive Compliance Interface Agent for SMB companies. Provide intelligent compliance insights and recommendations. Help with document analysis, regulatory research, and strategic planning. Ask clarifying questions when needed. Always provide actionable and practical advice."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error with OpenAI API: {e}")
        return await handle_basic_response(user_message)

async def handle_basic_response(user_message: str) -> str:
    """Handle responses in basic mode without AI agents."""

    user_msg_lower = user_message.lower()

    if any(word in user_msg_lower for word in ['gdpr', 'privacy', 'data protection']):
        return """📋 **Data Protection & GDPR Compliance**

Key areas to focus on:
• **Data Mapping** - Understand what personal data you collect and process
• **Legal Basis** - Ensure you have valid legal grounds for processing
• **Consent Management** - Implement proper consent mechanisms
• **Data Subject Rights** - Enable access, rectification, erasure, and portability
• **Privacy by Design** - Build privacy into your systems from the start
• **Impact Assessments** - Conduct DPIAs for high-risk processing

Would you like me to elaborate on any of these areas?"""

    elif any(word in user_msg_lower for word in ['sox', 'sarbanes', 'financial', 'audit']):
        return """💼 **SOX & Financial Compliance**

Essential compliance elements:
• **Internal Controls** - Establish and document financial processes
• **Segregation of Duties** - Prevent single-person control over transactions
• **Regular Audits** - Schedule internal and external audit procedures
• **Documentation** - Maintain comprehensive records of all processes
• **Management Certification** - Executive sign-off on financial statements
• **IT General Controls** - Secure financial systems and data

What specific aspect of financial compliance interests you?"""

    elif any(word in user_msg_lower for word in ['iso', '27001', 'security', 'information']):
        return """🔒 **ISO 27001 & Information Security**

Core implementation areas:
• **Risk Assessment** - Identify and evaluate information security risks
• **Security Policies** - Develop comprehensive security documentation
• **Access Controls** - Implement user access management
• **Incident Response** - Create procedures for security incidents
• **Business Continuity** - Plan for operational resilience
• **Employee Training** - Educate staff on security practices

Which security domain would you like to explore further?"""

    else:
        return f"""📝 **Compliance Consultation**

Thank you for your question: "{user_message}"

I can help with various compliance topics:

**📚 Regulatory Frameworks:**
• GDPR, CCPA (Privacy)
• SOX, PCI DSS (Financial)
• ISO 27001, NIST (Security)
• HIPAA (Healthcare)

**🔧 Compliance Activities:**
• Risk assessments
• Policy development
• Audit preparation
• Training programs

Could you specify which regulatory framework you're most interested in?"""

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Compliance Agent Backend on port 9160...")
    uvicorn.run(app, host="0.0.0.0", port=9160, log_level="info")
