import logging
import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from datetime import datetime
import hashlib

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn
import httpx

# Disable telemetry
os.environ["LITERAL_API_KEY"] = ""
os.environ["LITERAL_DISABLE"] = "true"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dapr_agents import DurableAgent
from dapr_agents.memory import ConversationDaprStateMemory
from dapr_agents.llm import OpenAIChatClient
import dapr_agents.mcp as mcp_module
from dapr_agents.tools import AgentTool

# Try to import Dapr SDK for pub/sub
try:
    from dapr.clients import DaprClient
    from dapr.ext.grpc import App
    from cloudevents.sdk.event import v1
    DAPR_SDK_AVAILABLE = True
    logger.info("Dapr SDK imported successfully")
except Exception as e:
    DAPR_SDK_AVAILABLE = False
    logger.warning(f"Dapr SDK not available: {e}")

# Request/Response models
class InsightRequest(BaseModel):
    framework: str
    company_name: str
    industry: Optional[str] = None
    assessment_id: Optional[str] = None
    session_id: Optional[str] = "default"
    max_results: Optional[int] = 10

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
    sources_used: List[str] = Field(default_factory=list)
    processing_time_ms: Optional[int] = None

class SearchQuery(BaseModel):
    query: str
    session_id: Optional[str] = "default"
    max_results: Optional[int] = 10

class SearchResponse(BaseModel):
    query: str
    response: str
    sources_used: List[str]
    session_id: str
    timestamp: str
    processing_time_ms: Optional[int] = None

class WorkflowTrigger(BaseModel):
    workflow_type: str
    payload: Dict[str, Any]
    session_id: Optional[str] = "default"

# Enhanced Harvester Agent with MCP and Pub/Sub integration
class EnhancedHarvesterAgent:
    def __init__(self):
        self.name = "ComplianceInsightHarvester"
        self.role = "Compliance Intelligence Specialist"
        self.agent = None
        self.mcp_client = None
        self.mcp_tools = []
        self.dapr_client = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize the harvester agent with all components"""
        if self.initialized:
            return
            
        try:
            # Initialize Dapr Agent
            self.agent = DurableAgent(
                name=self.name,
                role=self.role,
                instructions=[
                    "You are a Compliance Insight Harvester specialized in gathering and analyzing regulatory intelligence.",
                    "You extract insights from various sources including regulatory updates, industry benchmarks, and risk assessments.",
                    "You provide actionable intelligence for compliance decision-making.",
                    "You focus on practical, implementable recommendations for SMB companies.",
                    "You prioritize high-impact, low-effort compliance improvements.",
                    "Use web search tools to find current and relevant information.",
                    "Focus on factual, verifiable information from authoritative sources.",
                    "Provide structured responses with clear sections and citations.",
                ],
                # LLM configuration
                llm=OpenAIChatClient(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model=os.getenv("OPENAI_MODEL", "gpt-4o")
                ) if os.getenv("OPENAI_API_KEY") else None,
                # Memory configuration
                memory=ConversationDaprStateMemory(
                    store_name="conversationstore",
                    session_id="harvester-default"
                ),
                # Dapr configuration
                message_bus_name="messagepubsub",
                state_store_name="workflowstatestore",
                agents_registry_store_name="agentstatestore",
                tools=[]  # Will be populated with MCP tools
            )
            # Initialize MCP client
            await self.initialize_mcp_client()
            logger.info("Dapr Agent initialized successfully")
            
            # Initialize Dapr SDK client for pub/sub
            if DAPR_SDK_AVAILABLE:
                self.dapr_client = DaprClient()
                logger.info("Dapr SDK client initialized")
                
            self.initialized = True
            
        except Exception as e:
            logger.error(f"Error initializing harvester agent: {e}")
            raise
    
    async def initialize_mcp_client(self):
        """Initialize MCP client for web search tools"""
        try:
            # Initialize MCP client
            self.mcp_client = mcp_module.MCPClient(persistent_connections=False)
            
            # Get MCP server configuration
            mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp")
            mcp_token = os.getenv("MCP_API_TOKEN")
            
            # Prepare headers
            headers = {}
            if mcp_token:
                headers["Authorization"] = f"Bearer {mcp_token}"
                headers["X-API-Key"] = mcp_token
            
            # Connect to MCP server
            await self.mcp_client.connect_streamable_http(
                server_name="duckduckgo",
                url=mcp_url,
                headers=headers if headers else None
            )
            
            # Load available tools
            self.mcp_tools = self.mcp_client.get_all_tools()
            if self.agent:
                self.agent.tools.extend(self.mcp_tools)
            
            logger.info(f"MCP client connected with {len(self.mcp_tools)} tools")
            
        except Exception as e:
            logger.warning(f"MCP client initialization failed: {e}")
            self.mcp_client = None
    
    async def search_web(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Perform web search using MCP tools or fallback"""
        try:
            if self.mcp_client and self.mcp_tools:
                # Use MCP tools for web search
                search_tool = next((tool for tool in self.mcp_tools if "search" in tool.name.lower()), None)
                if search_tool:
                    result = await search_tool.execute(query=query, max_results=max_results)
                    return {
                        "results": result,
                        "source": "MCP_DuckDuckGo",
                        "success": True
                    }
            
            # Fallback to direct HTTP search (if available)
            return await self.fallback_web_search(query, max_results)
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {
                "results": f"Search failed: {str(e)}",
                "source": "Error",
                "success": False
            }
    
    async def fallback_web_search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Fallback web search implementation"""
        try:
            # This would integrate with DuckDuckGo API or other search services
            # For now, return a structured response
            return {
                "results": f"Fallback search results for: {query}",
                "source": "Fallback_Search",
                "success": True,
                "note": "This is a fallback implementation. Configure MCP server for full functionality."
            }
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return {
                "results": f"All search methods failed: {str(e)}",
                "source": "Error",
                "success": False
            }
    
    async def save_search_results(self, query: str, response: str, session_id: str = "default"):
        """Save search results to Dapr state store"""
        try:
            if not self.dapr_client:
                logger.warning("Dapr client not available for saving results")
                return
                
            # Create result record
            result_record = {
                "query": query,
                "response": response,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "agent_name": self.name,
                "sources": ["DuckDuckGo", "MCP Server"],
                "metadata": {
                    "query_hash": hashlib.md5(query.encode()).hexdigest(),
                    "response_length": len(response),
                    "tools_used": [tool.name for tool in self.mcp_tools] if self.mcp_tools else []
                }
            }
            
            # Save to state store
            key = f"search_{hashlib.md5(query.encode()).hexdigest()}_{int(datetime.now().timestamp())}"
            await self.dapr_client.save_state(
                store_name="searchresultsstore",
                key=key,
                value=json.dumps(result_record)
            )
            
            logger.info(f"Saved search results for query: {query[:50]}...")
            
        except Exception as e:
            logger.error(f"Error saving search results: {e}")
    
    async def publish_event(self, topic: str, data: Dict[str, Any]):
        """Publish event to Dapr pub/sub"""
        try:
            if not self.dapr_client:
                logger.warning("Dapr client not available for publishing events")
                return
                
            await self.dapr_client.publish_event(
                pubsub_name="messagepubsub",
                topic_name=topic,
                data=json.dumps(data),
                data_content_type="application/json"
            )
            
            logger.info(f"Published event to topic: {topic}")
            
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
    
    async def process_compliance_query(self, request: InsightRequest) -> InsightResponse:
        """Process compliance insight request"""
        start_time = datetime.now()
        
        try:
            # Construct search query
            search_query = f"{request.framework} compliance requirements {request.company_name}"
            if request.industry:
                search_query += f" {request.industry} industry"
            
            # Perform web search
            search_result = await self.search_web(search_query, request.max_results or 10)
            
            # Process with AI agent if available
            enhanced_query = f"""
                Analyze compliance requirements for {request.framework} framework.
                Company: {request.company_name}
                Industry: {request.industry or 'General'}
                
                Based on the search results: {search_result.get('results', 'No search results available')}
                
                Provide specific, actionable insights focusing on:
                1. Recent regulatory changes
                2. Common compliance gaps
                3. Industry-specific risks
                4. Practical recommendations
                
                Structure your response with clear insights and recommendations.
                """
                
                # Update memory session
                if hasattr(self.agent.memory, 'session_id'):
                    self.agent.memory.session_id = request.session_id or "default"
                
                # Run agent
                agent_response = await self.agent.run(enhanced_query)
                response_content = agent_response.get_content() if hasattr(agent_response, 'get_content') else str(agent_response)
                
                # Parse agent response into structured insights
                insights = self.parse_agent_response(response_content, request.framework)
            
            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Save results
            await self.save_search_results(search_query, response_content, request.session_id or "default")
            
            # Publish completion event
            await self.publish_event("harvester-complete", {
                "assessment_id": request.assessment_id,
                "framework": request.framework,
                "company_name": request.company_name,
                "insights_count": len(insights),
                "processing_time_ms": processing_time
            })
            
            return InsightResponse(
                assessment_id=request.assessment_id,
                framework=request.framework,
                insights=insights,
                risk_score=self.calculate_risk_score(insights),
                recommendations=self.generate_recommendations(request.framework, insights),
                generated_at=datetime.now().isoformat(),
                sources_used=[search_result.get('source', 'Unknown')],
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing compliance query: {e}")
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    
    def parse_agent_response(self, response: str, framework: str) -> List[ComplianceInsight]:
        """Parse AI agent response into structured insights"""
        # This would implement more sophisticated parsing
        # For now, create sample insights based on response
        insights = []
        
        # Extract key points from response (simplified)
        if "regulatory" in response.lower():
            insights.append(ComplianceInsight(
                category="Regulatory Update",
                title="Recent Regulatory Changes",
                description="New regulatory requirements identified",
                severity="medium",
                source="AI Analysis",
                confidence=0.85
            ))
        
        if "gap" in response.lower() or "missing" in response.lower():
            insights.append(ComplianceInsight(
                category="Compliance Gap",
                title="Identified Compliance Gap",
                description="Potential compliance gap requiring attention",
                severity="high",
                source="AI Analysis",
                confidence=0.80
            ))
        
        # Ensure we have at least one insight
        if not insights:
            insights.append(ComplianceInsight(
                category="General Analysis",
                title=f"{framework} Compliance Review",
                description="Comprehensive compliance analysis completed",
                severity="low",
                source="AI Analysis",
                confidence=0.75
            ))
        
        return insights
    
    def generate_rule_based_insights(self, request: InsightRequest) -> List[ComplianceInsight]:
        """Generate rule-based insights as fallback"""
        insights = []
        
        # Framework-specific insights
        if request.framework.upper() == "GDPR":
            insights.extend([
                ComplianceInsight(
                    category="Data Protection",
                    title="Data Mapping Required",
                    description="Comprehensive data mapping is essential for GDPR compliance",
                    severity="high",
                    source="Regulatory Requirement",
                    confidence=0.95
                ),
                ComplianceInsight(
                    category="Privacy Rights",
                    title="Subject Rights Implementation",
                    description="Implement processes for handling data subject rights requests",
                    severity="medium",
                    source="Best Practice",
                    confidence=0.90
                )
            ])
        
        elif request.framework.upper() == "ISO 27001":
            insights.extend([
                ComplianceInsight(
                    category="Information Security",
                    title="Risk Assessment Framework",
                    description="Establish comprehensive information security risk assessment",
                    severity="high",
                    source="Standard Requirement",
                    confidence=0.95
                ),
                ComplianceInsight(
                    category="Security Controls",
                    title="Access Control Implementation",
                    description="Implement robust access control mechanisms",
                    severity="medium",
                    source="Control Requirement",
                    confidence=0.90
                )
            ])
        
        # Industry-specific insights
        if request.industry:
            insights.append(ComplianceInsight(
                category="Industry Specific",
                title=f"{request.industry} Sector Requirements",
                description=f"Industry-specific compliance considerations for {request.industry}",
                severity="medium",
                source="Industry Analysis",
                confidence=0.80
            ))
        
        return insights
    
    def calculate_risk_score(self, insights: List[ComplianceInsight]) -> float:
        """Calculate overall risk score"""
        if not insights:
            return 50.0
        
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
            return 50.0
        
        # Convert to 0-100 scale
        risk_score = (weighted_score / total_weight) * 25
        return min(max(risk_score, 0.0), 100.0)
    
    def generate_recommendations(self, framework: str, insights: List[ComplianceInsight]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Framework-specific recommendations
        if framework.upper() == "GDPR":
            recommendations.extend([
                "Conduct comprehensive data mapping exercise",
                "Implement Privacy by Design principles",
                "Establish clear consent management procedures",
                "Create Data Protection Impact Assessment templates"
            ])
        elif framework.upper() == "ISO 27001":
            recommendations.extend([
                "Develop comprehensive information security policies",
                "Implement risk assessment methodology",
                "Establish security awareness training program",
                "Create incident response procedures"
            ])
        
        # Insight-based recommendations
        high_severity_insights = [i for i in insights if i.severity in ["high", "critical"]]
        if high_severity_insights:
            recommendations.append("Address high-severity compliance gaps immediately")
            recommendations.append("Conduct quarterly compliance reviews")
        
        return recommendations[:5]  # Return top 5
    
    async def shutdown(self):
        """Graceful shutdown"""
        try:
            if self.mcp_client:
                await self.mcp_client.close()
                logger.info("MCP client connection closed")
            
            if self.dapr_client:
                self.dapr_client.close()
                logger.info("Dapr client connection closed")
                
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Global agent instance
harvester_agent: Optional[EnhancedHarvesterAgent] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the harvester agent on startup."""
    global harvester_agent
    
    try:
        harvester_agent = EnhancedHarvesterAgent()
        await harvester_agent.initialize()
        logger.info("Enhanced harvester agent initialized successfully")

        if DAPR_SDK_AVAILABLE:
            # Start Dapr gRPC app in a background task
            asyncio.create_task(dapr_app.run())
            logger.info("Dapr gRPC app started in background.")

    except Exception as e:
        logger.error(f"Error initializing harvester agent: {e}")
        harvester_agent = None
    
    yield
    
    # Cleanup on shutdown
    if harvester_agent:
        await harvester_agent.shutdown()
    logger.info("Shutting down harvester agent")

app = FastAPI(
    title="Compliance Harvester Insights Agent",
    version="1.0.0",
    description="Enhanced compliance intelligence harvester with MCP tools and Dapr pub/sub integration",
    lifespan=lifespan
)

# Dapr pub/sub app for event handling
if DAPR_SDK_AVAILABLE:
    dapr_app = App()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "harvester-insights-agent",
        "dapr_agents_available": DAPR_AGENTS_AVAILABLE,
        "dapr_sdk_available": DAPR_SDK_AVAILABLE,
        "mcp_connected": harvester_agent.mcp_client is not None if harvester_agent else False,
        "agent_initialized": harvester_agent is not None and harvester_agent.initialized
    }

# Agent info endpoint
@app.get("/agent/info")
async def get_agent_info():
    """Get agent information."""
    if not harvester_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return {
        "name": harvester_agent.name,
        "role": harvester_agent.role,
        "mcp_tools_count": len(harvester_agent.mcp_tools),
        "capabilities": [
            "web_search",
            "compliance_analysis",
            "regulatory_intelligence",
            "risk_assessment",
            "recommendation_generation"
        ],
        "supported_frameworks": ["GDPR", "ISO 27001", "SOX", "HIPAA", "PCI DSS"],
        "initialized": harvester_agent.initialized
    }

# Main compliance insights endpoint
@app.post("/harvest-insights", response_model=InsightResponse)
async def harvest_compliance_insights(request: InsightRequest):
    """Harvest compliance insights for a specific framework and company."""
    
    if not harvester_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        logger.info(f"Harvesting insights for {request.framework} - {request.company_name}")
        
        # Process the request
        insights = await harvester_agent.process_compliance_query(request)
        
        return insights
        
    except Exception as e:
        logger.error(f"Error harvesting insights: {e}")
        raise HTTPException(status_code=500, detail=f"Insight harvesting failed: {str(e)}")

# Web search endpoint
@app.post("/search", response_model=SearchResponse)
async def search_web_endpoint(request: SearchQuery):
    """Perform web search using MCP tools."""
    
    if not harvester_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        start_time = datetime.now()
        
        # Perform search
        search_result = await harvester_agent.search_web(request.query, request.max_results or 10)
        
        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Save results
        response_content = str(search_result.get('results', ''))
        await harvester_agent.save_search_results(request.query, response_content, request.session_id or "default")
        
        return SearchResponse(
            query=request.query,
            response=response_content,
            sources_used=[search_result.get('source', 'Unknown')],
            session_id=request.session_id or "default",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error in web search: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Workflow trigger endpoint
@app.post("/trigger-workflow")
async def trigger_workflow(request: WorkflowTrigger):
    """Trigger a workflow via Dapr pub/sub."""
    
    if not harvester_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Publish workflow trigger event
        await harvester_agent.publish_event("workflow-trigger", {
            "workflow_type": request.workflow_type,
            "payload": request.payload,
            "session_id": request.session_id,
            "timestamp": datetime.now().isoformat(),
            "source": "harvester-agent"
        })
        
        return {
            "status": "triggered",
            "workflow_type": request.workflow_type,
            "session_id": request.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow trigger failed: {str(e)}")

# Pub/Sub event handlers (if Dapr SDK is available)
if DAPR_SDK_AVAILABLE:
    @dapr_app.subscribe(pubsub_name="messagepubsub", topic="harvest-request")
    def handle_harvest_request(event: v1.Event) -> None:
        """Handle harvest request from pub/sub."""
        try:
            data = json.loads(event.Data)
            logger.info(f"Received harvest request: {data}")
            
            # Process the request asynchronously
            # This would typically trigger the harvesting process
            # For now, just log the event
            
        except Exception as e:
            logger.error(f"Error handling harvest request: {e}")
    
    @dapr_app.subscribe(pubsub_name="messagepubsub", topic="compliance-query")
    def handle_compliance_query(event: v1.Event) -> None:
        """Handle compliance query from pub/sub."""
        try:
            data = json.loads(event.Data)
            logger.info(f"Received compliance query: {data}")
            
            # This would process the compliance query
            # and publish results back
            
        except Exception as e:
            logger.error(f"Error handling compliance query: {e}")

# Legacy endpoints for backward compatibility
@app.get("/frameworks")
async def get_supported_frameworks():
    """Get list of supported compliance frameworks."""
    return {
        "frameworks": ["GDPR", "ISO 27001", "SOX", "HIPAA", "PCI DSS", "NIST", "CCPA"],
        "total": 7,
        "categories": {
            "privacy": ["GDPR", "CCPA"],
            "security": ["ISO 27001", "NIST"],
            "financial": ["SOX"],
            "healthcare": ["HIPAA"],
            "payment": ["PCI DSS"]
        }
    }

@app.get("/framework/{framework}/benchmarks")
async def get_framework_benchmarks(framework: str):
    """Get industry benchmarks for a specific framework."""
    
    # Sample benchmark data
    benchmarks = {
        "GDPR": {
            "average_score": 72.3,
            "top_quartile": 85.0,
            "common_violations": ["Article 5 (lawfulness)", "Article 32 (security)"],
            "implementation_time": "6-12 months",
            "average_cost": "$50,000-$200,000"
        },
        "ISO 27001": {
            "average_score": 68.5,
            "top_quartile": 82.0,
            "common_violations": ["A.5.1 (policies)", "A.8.1 (asset management)"],
            "implementation_time": "8-18 months",
            "average_cost": "$75,000-$300,000"
        }
    }
    
    framework_upper = framework.upper()
    if framework_upper not in benchmarks:
        raise HTTPException(status_code=404, detail="Framework not found")
    
    return benchmarks[framework_upper]

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get agent performance metrics."""
    if not harvester_agent:
        return {"status": "agent_not_initialized"}
    
    return {
        "agent_status": "running" if harvester_agent.initialized else "initializing",
        "mcp_tools_available": len(harvester_agent.mcp_tools),
        "dapr_components": {
            "pub_sub": DAPR_SDK_AVAILABLE,
            "service_invocation": DAPR_SDK_AVAILABLE
        },
        "capabilities": {
            "web_search": harvester_agent.mcp_client is not None,
            "ai_analysis": harvester_agent.agent is not None,
            "event_publishing": harvester_agent.dapr_client is not None
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Compliance Harvester Insights Agent on port 9180...")
    uvicorn.run(app, host="0.0.0.0", port=9180, log_level="info")
