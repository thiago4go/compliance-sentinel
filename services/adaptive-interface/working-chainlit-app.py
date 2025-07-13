import chainlit as cl
import os
import logging
from typing import Optional

# Disable telemetry to avoid traceloop issues
os.environ["LITERAL_API_KEY"] = ""
os.environ["LITERAL_DISABLE"] = "true"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import dapr-agents, fallback to basic mode if it fails
try:
    from dapr_agents import Agent
    DAPR_AGENTS_AVAILABLE = True
    logger.info("Dapr-agents imported successfully")
except Exception as e:
    DAPR_AGENTS_AVAILABLE = False
    logger.warning(f"Dapr-agents not available: {e}")

# Global agent instance
agent: Optional[object] = None

@cl.on_chat_start
async def start():
    """Initialize the adaptive compliance agent when chat starts."""
    global agent

    try:
        if DAPR_AGENTS_AVAILABLE:
            # Create compliance agent with dapr-agents
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

            welcome_msg = """
🤖 **Adaptive Compliance Interface**

Welcome! I'm your AI compliance assistant powered by Dapr Agents, ready to help with:

📄 **Document Analysis** - Upload and analyze compliance documents
🔍 **Regulatory Research** - Find relevant regulations and requirements
📋 **Strategic Planning** - Develop compliance strategies and action plans
❓ **Expert Guidance** - Get answers to compliance questions
🎯 **Risk Assessment** - Identify and mitigate compliance risks

**What can I help you with today?**

✅ Dapr Agents: **ACTIVE**
🔧 Tools: Basic mode (expandable)
"""
        else:
            # Fallback mode without dapr-agents
            agent = None
            welcome_msg = """
🤖 **Adaptive Compliance Interface**

Welcome! I'm your compliance assistant running in basic mode.

📄 **Document Analysis** - Upload and discuss compliance documents
🔍 **Regulatory Guidance** - Get general compliance advice
📋 **Best Practices** - Learn about compliance strategies
❓ **Q&A Support** - Ask compliance-related questions

**What can I help you with today?**

⚠️ Running in basic mode (Dapr Agents not available)
"""

        await cl.Message(content=welcome_msg).send()
        logger.info("Adaptive Compliance Agent initialized")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        await cl.Message(
            content=f"⚠️ **Startup Warning**\n\nI encountered an issue during initialization: {str(e)}\n\nI'm running in fallback mode and can still help with basic compliance questions."
        ).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages."""
    global agent

    try:
        if DAPR_AGENTS_AVAILABLE and agent:
            # Use dapr-agents for intelligent response
            async with cl.Step(name="🧠 AI Analysis", type="tool") as step:
                step.output = "Analyzing your compliance query with AI..."

                try:
                    response = await agent.run(message.content)
                    step.output = "✅ Analysis complete"

                    await cl.Message(content=response).send()

                except Exception as e:
                    step.output = f"⚠️ AI processing error: {str(e)}"
                    # Fallback to basic response
                    await handle_basic_response(message.content)
        else:
            # Basic fallback mode
            await handle_basic_response(message.content)

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await cl.Message(
            content=f"❌ **Error Processing Request**\n\nI encountered an error: {str(e)}\n\nPlease try rephrasing your question or contact support if the issue persists."
        ).send()

async def handle_basic_response(user_message: str):
    """Handle responses in basic mode without AI agents."""

    # Simple keyword-based responses for common compliance topics
    user_msg_lower = user_message.lower()

    if any(word in user_msg_lower for word in ['gdpr', 'privacy', 'data protection']):
        response = """
📋 **Data Protection & GDPR Compliance**

Key areas to focus on:
• **Data Mapping** - Understand what personal data you collect and process
• **Legal Basis** - Ensure you have valid legal grounds for processing
• **Consent Management** - Implement proper consent mechanisms
• **Data Subject Rights** - Enable access, rectification, erasure, and portability
• **Privacy by Design** - Build privacy into your systems from the start
• **Impact Assessments** - Conduct DPIAs for high-risk processing

Would you like me to elaborate on any of these areas?
"""

    elif any(word in user_msg_lower for word in ['sox', 'sarbanes', 'financial', 'audit']):
        response = """
💼 **SOX & Financial Compliance**

Essential compliance elements:
• **Internal Controls** - Establish and document financial processes
• **Segregation of Duties** - Prevent single-person control over transactions
• **Regular Audits** - Schedule internal and external audit procedures
• **Documentation** - Maintain comprehensive records of all processes
• **Management Certification** - Executive sign-off on financial statements
• **IT General Controls** - Secure financial systems and data

What specific aspect of financial compliance interests you?
"""

    elif any(word in user_msg_lower for word in ['iso', '27001', 'security', 'information']):
        response = """
🔒 **ISO 27001 & Information Security**

Core implementation areas:
• **Risk Assessment** - Identify and evaluate information security risks
• **Security Policies** - Develop comprehensive security documentation
• **Access Controls** - Implement user access management
• **Incident Response** - Create procedures for security incidents
• **Business Continuity** - Plan for operational resilience
• **Employee Training** - Educate staff on security practices

Which security domain would you like to explore further?
"""

    elif any(word in user_msg_lower for word in ['help', 'start', 'how', 'what']):
        response = """
🤝 **How I Can Help You**

I can assist with various compliance topics:

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
• Incident response

**💡 Best Practices:**
• Implementation strategies
• Cost-effective solutions
• Timeline planning
• Resource allocation

Try asking about a specific regulation or compliance challenge!
"""

    else:
        response = f"""
📝 **Compliance Consultation**

Thank you for your question: "{user_message}"

I understand you're looking for compliance guidance. While I'm currently in basic mode, I can help with:

• **General compliance principles** and best practices
• **Regulatory overviews** for major frameworks (GDPR, SOX, ISO 27001, etc.)
• **Implementation strategies** for compliance programs
• **Risk assessment** methodologies
• **Documentation** requirements and templates

Could you specify which regulatory framework or compliance area you're most interested in? This will help me provide more targeted guidance.

**Popular topics:** GDPR, SOX, ISO 27001, PCI DSS, HIPAA, Risk Management
"""

    await cl.Message(content=response).send()

# File upload handler removed - not available in this Chainlit version

if __name__ == "__main__":
    print("🚀 Starting Adaptive Compliance Interface...")
    print(f"📊 Dapr Agents Available: {DAPR_AGENTS_AVAILABLE}")
    print("🌐 Ready for connections on configured port")
