import logging
import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Disable telemetry
os.environ["LITERAL_API_KEY"] = ""
os.environ["LITERAL_DISABLE"] = "true"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import dapr-agents
try:
    from dapr_agents import DurableAgent
    DAPR_AGENTS_AVAILABLE = True
    logger.info("Dapr-agents imported successfully")
except Exception as e:
    DAPR_AGENTS_AVAILABLE = False
    logger.warning(f"Dapr-agents not available: {e}")

# Request/Response models
class InsightRequest(BaseModel):
    framework: str
    company_name: str
    industry: Optional[str] = None
    assessment_id: Optional[str] = None

class ComplianceInsight(BaseModel):
    category: str
    title: str
    description: str
    severity: str  # low, medium, high, critical
    source: str
    confidence: float

class InsightResponse(BaseModel):
    assessment_id: Optional[str]
    framework: str
    insights: List[ComplianceInsight]
    risk_score: float
    recommendations: List[str]
    generated_at: str

# Global agent instance
harvester_agent: Optional[object] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the harvester agent on startup."""
    global harvester_agent
    
    try:
        if DAPR_AGENTS_AVAILABLE:
            harvester_agent = DurableAgent(
                name="ComplianceInsightHarvester",
                role="Compliance Intelligence Specialist",
                instructions=[
                    "You are a Compliance Insight Harvester specialized in gathering and analyzing regulatory intelligence.",
                    "You extract insights from various sources including regulatory updates, industry benchmarks, and risk assessments.",
                    "You provide actionable intelligence for compliance decision-making.",
                    "You focus on practical, implementable recommendations for SMB companies.",
                    "You prioritize high-impact, low-effort compliance improvements."
                ],
                tools=[],  # MCP tools would be added here
            )
            logger.info("Harvester agent initialized successfully")
        else:
            logger.warning("Running without Dapr Agents - basic mode only")
    except Exception as e:
        logger.error(f"Error initializing harvester agent: {e}")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down harvester agent")

app = FastAPI(
    title="Compliance Harvester Insights Agent",
    version="1.0.0",
    lifespan=lifespan
)

# Compliance knowledge base (in production, this would be a proper database/API)
COMPLIANCE_KNOWLEDGE = {
    "GDPR": {
        "recent_updates": [
            {
                "title": "EDPB Guidelines on Data Retention",
                "description": "New guidance on proportionate data retention periods",
                "severity": "medium",
                "date": "2024-12-01"
            },
            {
                "title": "Increased Enforcement Activity",
                "description": "15% increase in GDPR fines in 2024, focus on data mapping",
                "severity": "high",
                "date": "2024-11-15"
            }
        ],
        "common_gaps": [
            "Incomplete data mapping and inventory",
            "Inadequate breach notification procedures",
            "Missing Data Protection Impact Assessments",
            "Insufficient consent management"
        ],
        "industry_benchmarks": {
            "average_score": 72.3,
            "top_quartile": 85.0,
            "common_violations": ["Article 5 (lawfulness)", "Article 32 (security)"]
        }
    },
    "ISO 27001": {
        "recent_updates": [
            {
                "title": "ISO 27001:2022 Transition Deadline",
                "description": "Organizations must transition to 2022 version by October 2025",
                "severity": "high",
                "date": "2024-10-01"
            }
        ],
        "common_gaps": [
            "Incomplete risk assessment documentation",
            "Missing security awareness training",
            "Inadequate incident response procedures",
            "Insufficient access control management"
        ],
        "industry_benchmarks": {
            "average_score": 68.5,
            "top_quartile": 82.0,
            "common_violations": ["A.5.1 (policies)", "A.8.1 (asset management)"]
        }
    },
    "SOX": {
        "recent_updates": [
            {
                "title": "PCAOB Focus on IT Controls",
                "description": "Increased scrutiny on IT general controls and cybersecurity",
                "severity": "medium",
                "date": "2024-09-01"
            }
        ],
        "common_gaps": [
            "Inadequate segregation of duties",
            "Missing IT general controls",
            "Insufficient documentation of processes",
            "Weak change management procedures"
        ],
        "industry_benchmarks": {
            "average_score": 75.8,
            "top_quartile": 88.0,
            "common_violations": ["Section 302 (disclosure)", "Section 404 (internal controls)"]
        }
    }
}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "harvester-insights-agent",
        "dapr_agents_available": DAPR_AGENTS_AVAILABLE
    }

@app.post("/harvest-insights", response_model=InsightResponse)
async def harvest_compliance_insights(request: InsightRequest):
    """Harvest compliance insights for a specific framework and company."""
    
    try:
        logger.info(f"Harvesting insights for {request.framework} - {request.company_name}")
        
        if DAPR_AGENTS_AVAILABLE and harvester_agent:
            # Use AI agent for intelligent insight generation
            insights = await generate_ai_insights(request)
        else:
            # Fallback to rule-based insights
            insights = generate_rule_based_insights(request)
        
        return insights
        
    except Exception as e:
        logger.error(f"Error harvesting insights: {e}")
        raise HTTPException(status_code=500, detail=f"Insight harvesting failed: {str(e)}")

async def generate_ai_insights(request: InsightRequest) -> InsightResponse:
    """Generate insights using AI agent."""
    
    # Prepare context for the AI agent
    context = f"""
    Analyze compliance requirements for {request.framework} framework.
    Company: {request.company_name}
    Industry: {request.industry or 'General'}
    
    Provide specific, actionable insights focusing on:
    1. Recent regulatory changes
    2. Common compliance gaps
    3. Industry-specific risks
    4. Practical recommendations
    """
    
    try:
        # In a real implementation, this would call the AI agent
        # response = await harvester_agent.run(context)
        
        # For demo, we'll use the rule-based approach with AI-like formatting
        return generate_rule_based_insights(request)
        
    except Exception as e:
        logger.error(f"AI insight generation failed: {e}")
        return generate_rule_based_insights(request)

def generate_rule_based_insights(request: InsightRequest) -> InsightResponse:
    """Generate insights using rule-based approach."""
    
    framework_data = COMPLIANCE_KNOWLEDGE.get(request.framework, {})
    
    insights = []
    
    # Add recent regulatory updates
    for update in framework_data.get("recent_updates", []):
        insights.append(ComplianceInsight(
            category="Regulatory Update",
            title=update["title"],
            description=update["description"],
            severity=update["severity"],
            source="Regulatory Authority",
            confidence=0.95
        ))
    
    # Add common gap insights
    for gap in framework_data.get("common_gaps", [])[:3]:  # Top 3 gaps
        insights.append(ComplianceInsight(
            category="Common Gap",
            title=f"Address: {gap}",
            description=f"This is a frequently identified gap in {request.framework} compliance assessments.",
            severity="medium",
            source="Industry Analysis",
            confidence=0.85
        ))
    
    # Add industry benchmark insight
    benchmarks = framework_data.get("industry_benchmarks", {})
    if benchmarks:
        insights.append(ComplianceInsight(
            category="Benchmark",
            title="Industry Performance Comparison",
            description=f"Industry average compliance score is {benchmarks.get('average_score', 70)}%. Top quartile achieves {benchmarks.get('top_quartile', 85)}%.",
            severity="low",
            source="Industry Benchmarks",
            confidence=0.90
        ))
    
    # Calculate risk score based on framework and insights
    risk_score = calculate_risk_score(request.framework, insights)
    
    # Generate recommendations
    recommendations = generate_recommendations(request.framework, insights)
    
    return InsightResponse(
        assessment_id=request.assessment_id,
        framework=request.framework,
        insights=insights,
        risk_score=risk_score,
        recommendations=recommendations,
        generated_at="2025-01-01T00:00:00Z"
    )

def calculate_risk_score(framework: str, insights: List[ComplianceInsight]) -> float:
    """Calculate overall risk score based on insights."""
    
    severity_weights = {
        "low": 1.0,
        "medium": 2.0,
        "high": 3.0,
        "critical": 4.0
    }
    
    total_weight = 0
    weighted_score = 0
    
    for insight in insights:
        weight = severity_weights.get(insight.severity, 1.0)
        total_weight += weight
        weighted_score += weight * insight.confidence
    
    if total_weight == 0:
        return 50.0  # Default medium risk
    
    # Convert to 0-100 scale where higher = more risk
    risk_score = (weighted_score / total_weight) * 25  # Scale to reasonable range
    return min(max(risk_score, 0.0), 100.0)

def generate_recommendations(framework: str, insights: List[ComplianceInsight]) -> List[str]:
    """Generate actionable recommendations based on insights."""
    
    recommendations = []
    
    # Framework-specific recommendations
    if framework == "GDPR":
        recommendations.extend([
            "Conduct comprehensive data mapping exercise",
            "Implement Privacy by Design principles",
            "Establish clear consent management procedures",
            "Create Data Protection Impact Assessment templates"
        ])
    elif framework == "ISO 27001":
        recommendations.extend([
            "Develop comprehensive information security policies",
            "Implement risk assessment methodology",
            "Establish security awareness training program",
            "Create incident response procedures"
        ])
    elif framework == "SOX":
        recommendations.extend([
            "Document all financial processes and controls",
            "Implement segregation of duties",
            "Establish IT general controls framework",
            "Create management certification procedures"
        ])
    
    # Add insight-specific recommendations
    high_severity_insights = [i for i in insights if i.severity in ["high", "critical"]]
    if high_severity_insights:
        recommendations.append("Address high-severity compliance gaps immediately")
        recommendations.append("Conduct quarterly compliance reviews")
    
    return recommendations[:5]  # Return top 5 recommendations

@app.get("/frameworks")
async def get_supported_frameworks():
    """Get list of supported compliance frameworks."""
    return {
        "frameworks": list(COMPLIANCE_KNOWLEDGE.keys()),
        "total": len(COMPLIANCE_KNOWLEDGE)
    }

@app.get("/framework/{framework}/benchmarks")
async def get_framework_benchmarks(framework: str):
    """Get industry benchmarks for a specific framework."""
    
    if framework not in COMPLIANCE_KNOWLEDGE:
        raise HTTPException(status_code=404, detail="Framework not found")
    
    return COMPLIANCE_KNOWLEDGE[framework].get("industry_benchmarks", {})

if __name__ == "__main__":
    print("🚀 Starting Compliance Harvester Insights Agent on port 9180...")
    uvicorn.run(app, host="0.0.0.0", port=9180, log_level="info")
