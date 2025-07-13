import logging
import os
import json
import asyncio
from typing import Dict, Any, Optional
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

# Try to import dapr-agents and workflow components
try:
    from dapr_agents import DurableAgent
    from dapr_agents.workflow import WorkflowApp, workflow, task
    from dapr.ext.workflow import DaprWorkflowContext
    DAPR_AGENTS_AVAILABLE = True
    logger.info("Dapr-agents imported successfully")
except Exception as e:
    DAPR_AGENTS_AVAILABLE = False
    logger.warning(f"Dapr-agents not available: {e}")

# Request/Response models
class ComplianceWorkflowRequest(BaseModel):
    company_name: str
    framework: str = "GDPR"
    assessment_type: str = "full"
    user_query: str = ""

class ComplianceWorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    message: str
    results: Optional[Dict[str, Any]] = None

# Global workflow app and agent
workflow_app: Optional[object] = None
workflow_agent: Optional[object] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the workflow agent and app on startup."""
    global workflow_app, workflow_agent
    
    try:
        if DAPR_AGENTS_AVAILABLE:
            # Initialize the workflow orchestrator agent
            workflow_agent = DurableAgent(
                name="ComplianceWorkflowOrchestrator",
                role="Compliance Workflow Coordinator",
                instructions=[
                    "You are a Compliance Workflow Orchestrator responsible for coordinating multi-agent compliance analysis.",
                    "You orchestrate the flow between different compliance agents to provide comprehensive analysis.",
                    "You ensure all steps in the compliance workflow are completed successfully.",
                    "You handle errors gracefully and provide clear status updates."
                ],
                tools=[],  # Tools will be added as needed
            )
            
            # Initialize workflow app
            workflow_app = WorkflowApp()
            
            logger.info("Workflow agent and app initialized successfully")
        else:
            logger.warning("Running without Dapr Agents - basic mode only")
    except Exception as e:
        logger.error(f"Error initializing workflow components: {e}")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down workflow agent")

app = FastAPI(
    title="Compliance Workflow Agent",
    version="1.0.0",
    lifespan=lifespan
)

# Workflow definitions
if DAPR_AGENTS_AVAILABLE:
    @workflow(name="compliance_analysis_workflow")
    def compliance_analysis_workflow(ctx: DaprWorkflowContext, input_data: dict):
        """
        Main compliance analysis workflow that orchestrates the entire process.
        
        Flow:
        1. Initialize assessment
        2. Harvest insights from external sources
        3. Analyze compliance requirements
        4. Generate recommendations
        5. Store results
        """
        logger.info(f"Starting compliance workflow for: {input_data}")
        
        try:
            # Step 1: Initialize assessment
            init_result = yield ctx.call_activity(
                initialize_assessment,
                input=input_data
            )
            
            # Step 2: Harvest insights
            harvest_result = yield ctx.call_activity(
                harvest_compliance_insights,
                input={
                    "assessment_id": init_result["assessment_id"],
                    "framework": input_data["framework"],
                    "company_name": input_data["company_name"]
                }
            )
            
            # Step 3: Analyze compliance
            analysis_result = yield ctx.call_activity(
                analyze_compliance_requirements,
                input={
                    "assessment_id": init_result["assessment_id"],
                    "insights": harvest_result["insights"],
                    "framework": input_data["framework"]
                }
            )
            
            # Step 4: Generate final report
            final_result = yield ctx.call_activity(
                generate_compliance_report,
                input={
                    "assessment_id": init_result["assessment_id"],
                    "analysis": analysis_result,
                    "company_name": input_data["company_name"]
                }
            )
            
            return {
                "status": "completed",
                "assessment_id": init_result["assessment_id"],
                "results": final_result
            }
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    @task(description="Initialize compliance assessment")
    def initialize_assessment(input_data: dict) -> dict:
        """Initialize a new compliance assessment."""
        import uuid
        
        assessment_id = str(uuid.uuid4())
        
        logger.info(f"Initializing assessment {assessment_id} for {input_data['company_name']}")
        
        # In a real implementation, this would create database records
        return {
            "assessment_id": assessment_id,
            "company_name": input_data["company_name"],
            "framework": input_data["framework"],
            "status": "initialized",
            "created_at": "2025-01-01T00:00:00Z"
        }

    @task(description="Harvest compliance insights from external sources")
    def harvest_compliance_insights(input_data: dict) -> dict:
        """Call the harvester insights agent to gather compliance data."""
        
        logger.info(f"Harvesting insights for assessment {input_data['assessment_id']}")
        
        # Simulate calling the harvester agent
        # In real implementation, this would use Dapr service invocation
        insights = {
            "regulatory_updates": [
                "GDPR enforcement increased by 15% in 2024",
                "New guidance on data retention policies published"
            ],
            "industry_benchmarks": {
                "average_compliance_score": 78.5,
                "common_gaps": ["data mapping", "incident response"]
            },
            "risk_factors": [
                "Cross-border data transfers",
                "Third-party data processors"
            ]
        }
        
        return {
            "assessment_id": input_data["assessment_id"],
            "insights": insights,
            "harvested_at": "2025-01-01T00:00:00Z"
        }

    @task(description="Analyze compliance requirements against current state")
    def analyze_compliance_requirements(input_data: dict) -> dict:
        """Analyze compliance requirements and identify gaps."""
        
        logger.info(f"Analyzing compliance for assessment {input_data['assessment_id']}")
        
        # Simulate compliance analysis
        analysis = {
            "overall_score": 72.5,
            "risk_level": "medium",
            "compliant_requirements": 15,
            "non_compliant_requirements": 8,
            "partial_requirements": 5,
            "critical_gaps": [
                "Data Protection Impact Assessments not documented",
                "Breach notification procedures incomplete"
            ],
            "recommendations": [
                "Implement DPIA template and process",
                "Update incident response plan",
                "Conduct staff training on data protection"
            ]
        }
        
        return {
            "assessment_id": input_data["assessment_id"],
            "analysis": analysis,
            "analyzed_at": "2025-01-01T00:00:00Z"
        }

    @task(description="Generate final compliance report")
    def generate_compliance_report(input_data: dict) -> dict:
        """Generate the final compliance report."""
        
        logger.info(f"Generating report for assessment {input_data['assessment_id']}")
        
        report = {
            "executive_summary": f"Compliance assessment for {input_data['company_name']} shows medium risk level with 72.5% compliance score.",
            "key_findings": input_data["analysis"]["analysis"]["critical_gaps"],
            "recommendations": input_data["analysis"]["analysis"]["recommendations"],
            "next_steps": [
                "Address critical gaps within 30 days",
                "Schedule quarterly compliance reviews",
                "Implement continuous monitoring"
            ],
            "compliance_score": input_data["analysis"]["analysis"]["overall_score"],
            "risk_level": input_data["analysis"]["analysis"]["risk_level"]
        }
        
        return {
            "assessment_id": input_data["assessment_id"],
            "report": report,
            "generated_at": "2025-01-01T00:00:00Z"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "workflow-agent",
        "dapr_agents_available": DAPR_AGENTS_AVAILABLE
    }

@app.post("/start-workflow", response_model=ComplianceWorkflowResponse)
async def start_compliance_workflow(request: ComplianceWorkflowRequest):
    """Start a new compliance analysis workflow."""
    
    try:
        if DAPR_AGENTS_AVAILABLE and workflow_app:
            # Start the Dapr workflow
            workflow_id = f"compliance-{request.company_name.lower().replace(' ', '-')}"
            
            # In a real implementation, this would start the actual Dapr workflow
            # For demo purposes, we'll simulate the workflow execution
            
            logger.info(f"Starting workflow {workflow_id} for {request.company_name}")
            
            # Simulate workflow execution
            workflow_result = {
                "status": "completed",
                "assessment_id": "demo-assessment-123",
                "results": {
                    "executive_summary": f"Compliance assessment for {request.company_name} completed successfully.",
                    "compliance_score": 75.2,
                    "risk_level": "medium",
                    "critical_gaps": [
                        "Data mapping documentation incomplete",
                        "Privacy policy needs updates"
                    ],
                    "recommendations": [
                        "Complete data inventory and mapping",
                        "Update privacy policy to reflect current practices",
                        "Implement regular compliance monitoring"
                    ]
                }
            }
            
            return ComplianceWorkflowResponse(
                workflow_id=workflow_id,
                status="completed",
                message="Compliance workflow completed successfully",
                results=workflow_result["results"]
            )
        else:
            # Fallback mode without Dapr Agents
            return ComplianceWorkflowResponse(
                workflow_id="fallback-workflow",
                status="completed",
                message="Basic compliance analysis completed (Dapr Agents not available)",
                results={
                    "executive_summary": f"Basic compliance check for {request.company_name}",
                    "compliance_score": 70.0,
                    "risk_level": "medium",
                    "note": "This is a simplified analysis. Full features require Dapr Agents."
                }
            )
            
    except Exception as e:
        logger.error(f"Error starting workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")

@app.get("/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get the status of a running workflow."""
    
    # In a real implementation, this would query the Dapr workflow state
    return {
        "workflow_id": workflow_id,
        "status": "completed",
        "progress": 100,
        "current_step": "completed",
        "message": "Workflow completed successfully"
    }

if __name__ == "__main__":
    print("🚀 Starting Compliance Workflow Agent on port 9170...")
    uvicorn.run(app, host="0.0.0.0", port=9170, log_level="info")
