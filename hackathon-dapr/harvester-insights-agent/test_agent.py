#!/usr/bin/env python3
"""
Simplified test version of the Harvester Agent
Works without OpenAI API for testing configuration and basic functionality
"""
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Request/Response models
class InsightRequest(BaseModel):
    framework: str
    company_name: str
    industry: Optional[str] = "Technology"

class InsightResponse(BaseModel):
    status: str
    framework: str
    company_name: str
    insights: Dict[str, Any]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    components: Dict[str, str]
    configuration: Dict[str, Any]

# Initialize FastAPI app
app = FastAPI(
    title="Harvester Insights Agent (Test Mode)",
    description="Simplified test version of the compliance intelligence harvester",
    version="1.0.0-test"
)

class TestHarvesterAgent:
    """Simplified test version of the harvester agent"""
    
    def __init__(self):
        self.name = "TestHarvesterAgent"
        self.version = "1.0.0-test"
        self.initialized = False
        
    async def initialize(self):
        """Initialize the test agent"""
        if self.initialized:
            return
            
        print(f"🚀 Initializing {self.name}")
        
        # Check configuration
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.db_url = os.getenv("DB_URL")
        self.app_port = int(os.getenv("APP_PORT", 9180))
        
        print(f"✅ Configuration loaded")
        print(f"   - OpenAI Key: {'✅ Present' if self.openai_key else '❌ Missing'}")
        print(f"   - Database: {'✅ Present' if self.db_url else '❌ Missing'}")
        print(f"   - Port: {self.app_port}")
        
        self.initialized = True
        
    async def generate_mock_insights(self, framework: str, company_name: str, industry: str) -> Dict[str, Any]:
        """Generate mock compliance insights without OpenAI"""
        
        # Mock insights based on framework
        framework_insights = {
            "GDPR": {
                "key_requirements": [
                    "Data Protection Impact Assessment (DPIA)",
                    "Consent management system",
                    "Data breach notification procedures",
                    "Privacy by design implementation"
                ],
                "risk_areas": [
                    "Cross-border data transfers",
                    "Third-party data processors",
                    "Data retention policies"
                ],
                "recommendations": [
                    "Implement automated consent management",
                    "Regular privacy audits",
                    "Staff training on GDPR compliance"
                ]
            },
            "SOX": {
                "key_requirements": [
                    "Internal controls documentation",
                    "Financial reporting accuracy",
                    "Management assessment of controls",
                    "External auditor attestation"
                ],
                "risk_areas": [
                    "IT general controls",
                    "Financial close process",
                    "Revenue recognition"
                ],
                "recommendations": [
                    "Automated control testing",
                    "Segregation of duties",
                    "Regular control assessments"
                ]
            },
            "HIPAA": {
                "key_requirements": [
                    "Administrative safeguards",
                    "Physical safeguards",
                    "Technical safeguards",
                    "Business associate agreements"
                ],
                "risk_areas": [
                    "Data encryption",
                    "Access controls",
                    "Audit logging"
                ],
                "recommendations": [
                    "End-to-end encryption",
                    "Role-based access control",
                    "Regular security assessments"
                ]
            }
        }
        
        # Get framework-specific insights or default
        insights = framework_insights.get(framework.upper(), {
            "key_requirements": [f"Framework-specific requirements for {framework}"],
            "risk_areas": [f"Common risk areas for {framework} compliance"],
            "recommendations": [f"Best practices for {framework} implementation"]
        })
        
        # Add company and industry context
        insights["company_context"] = {
            "name": company_name,
            "industry": industry,
            "framework": framework,
            "assessment_date": datetime.now().isoformat()
        }
        
        # Add mock scoring
        insights["compliance_score"] = {
            "overall": 75,
            "breakdown": {
                "documentation": 80,
                "implementation": 70,
                "monitoring": 75
            }
        }
        
        return insights

# Initialize the test agent
test_agent = TestHarvesterAgent()

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup"""
    await test_agent.initialize()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        components={
            "agent": "✅ Running",
            "openai": "✅ Present" if test_agent.openai_key else "❌ Missing",
            "database": "✅ Present" if test_agent.db_url else "❌ Missing",
            "mode": "🧪 Test Mode"
        },
        configuration={
            "name": test_agent.name,
            "version": test_agent.version,
            "port": test_agent.app_port,
            "openai_configured": bool(test_agent.openai_key),
            "database_configured": bool(test_agent.db_url)
        }
    )

@app.post("/harvest-insights", response_model=InsightResponse)
async def harvest_insights(request: InsightRequest):
    """Generate compliance insights (test mode with mock data)"""
    try:
        if not test_agent.initialized:
            await test_agent.initialize()
        
        print(f"🔍 Processing insights request for {request.company_name} - {request.framework}")
        
        # Generate mock insights
        insights = await test_agent.generate_mock_insights(
            request.framework,
            request.company_name,
            request.industry or "Technology"
        )
        
        return InsightResponse(
            status="success",
            framework=request.framework,
            company_name=request.company_name,
            insights=insights,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"❌ Error processing insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/info")
async def agent_info():
    """Get agent information"""
    return {
        "name": test_agent.name,
        "version": test_agent.version,
        "status": "running" if test_agent.initialized else "initializing",
        "mode": "test",
        "capabilities": [
            "Mock compliance insights",
            "Framework analysis",
            "Health monitoring",
            "Configuration testing"
        ],
        "supported_frameworks": ["GDPR", "SOX", "HIPAA", "PCI-DSS", "ISO27001"]
    }

@app.get("/frameworks")
async def get_frameworks():
    """Get supported compliance frameworks"""
    return {
        "frameworks": [
            {"code": "GDPR", "name": "General Data Protection Regulation", "region": "EU"},
            {"code": "SOX", "name": "Sarbanes-Oxley Act", "region": "US"},
            {"code": "HIPAA", "name": "Health Insurance Portability and Accountability Act", "region": "US"},
            {"code": "PCI-DSS", "name": "Payment Card Industry Data Security Standard", "region": "Global"},
            {"code": "ISO27001", "name": "Information Security Management", "region": "Global"}
        ]
    }

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 9180))
    print(f"🚀 Starting Test Harvester Agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
