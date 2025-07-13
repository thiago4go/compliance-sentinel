# Harvester Agent Development Guide

## Step-by-Step Development Process

### Step 1: Environment Setup
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your API keys
# - OPENROUTER_API_KEY (for AI features)
# - MCP_SERVER_URL (for web search and database)
# - MCP_API_TOKEN (if required)
```

### Step 2: Local Development
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run locally (without Docker)
python harvester_agent.py

# 3. Test health endpoint
curl http://localhost:9180/health
```

### Step 3: Docker Development
```bash
# 1. Build and run with Docker Compose (development)
docker-compose -f docker-compose.dev.yml up --build

# 2. Test the service
curl http://localhost:9180/health
curl http://localhost:9180/agent/info
```

### Step 4: Test Core Features

#### 4.1 Test Web Search
```bash
curl -X POST http://localhost:9180/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "GDPR compliance requirements 2024",
    "session_id": "test-session",
    "max_results": 5
  }'
```

#### 4.2 Test Compliance Insights
```bash
curl -X POST http://localhost:9180/harvest-insights \
  -H "Content-Type: application/json" \
  -d '{
    "framework": "GDPR",
    "company_name": "Test Company",
    "industry": "Technology",
    "assessment_id": "test-001",
    "session_id": "test-session"
  }'
```

#### 4.3 Test Pub/Sub Integration
```bash
curl -X POST http://localhost:9180/trigger-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "compliance_assessment",
    "payload": {
      "framework": "GDPR",
      "company": "Test Company"
    },
    "session_id": "test-session"
  }'
```

### Step 5: Integration Testing

#### 5.1 Check Dapr Components
```bash
# Check if Dapr sidecar is running
curl http://localhost:3500/v1.0/metadata

# Check pub/sub topics
curl http://localhost:3500/v1.0/publish/messagepubsub/test-topic \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

#### 5.2 Check State Stores
```bash
# Save state
curl -X POST http://localhost:3500/v1.0/state/workflowstatestore \
  -H "Content-Type: application/json" \
  -d '[{"key": "test", "value": "hello"}]'

# Get state
curl http://localhost:3500/v1.0/state/workflowstatestore/test
```

## Architecture Overview

### Components Integration
```
┌─────────────────────┐    ┌─────────────────────┐
│   Harvester Agent   │    │    MCP Server       │
│   (FastAPI)         │◄──►│  (Web Search +      │
│   Port: 9180        │    │   PostgreSQL)       │
└─────────────────────┘    └─────────────────────┘
           │
           ▼
┌─────────────────────┐    ┌─────────────────────┐
│   Dapr Sidecar     │    │      Redis          │
│   HTTP: 3500       │◄──►│   (State + Pub/Sub) │
│   gRPC: 50001      │    │   Port: 6379        │
└─────────────────────┘    └─────────────────────┘
```

### Key Features Implemented
1. ✅ **Dapr Agents Integration** - DurableAgent with memory
2. ✅ **MCP Tools Integration** - Web search via MCP
3. ✅ **Pub/Sub Messaging** - Event-driven communication
4. ✅ **State Management** - Conversation and search result storage
5. ✅ **Compliance Intelligence** - Framework-specific insights
6. ✅ **Health Monitoring** - Comprehensive health checks

### Next Steps for Production
1. **Shared Components**: Update component configs to point to shared Redis
2. **MCP Server**: Ensure MCP server is running with DuckDuckGo and PostgreSQL tools
3. **Workflow Integration**: Connect with workflow-agent via pub/sub
4. **Monitoring**: Add metrics and logging
5. **Security**: Add authentication and authorization

## Troubleshooting

### Common Issues
1. **MCP Connection Failed**: Check MCP_SERVER_URL and ensure MCP server is running
2. **Dapr Components Not Found**: Ensure Redis is running and components are properly configured
3. **OpenRouter API Errors**: Verify OPENROUTER_API_KEY is valid
4. **Pub/Sub Not Working**: Check Redis connection and Dapr sidecar logs

### Debug Commands
```bash
# Check Dapr logs
docker logs harvester-dapr-dev

# Check agent logs
docker logs harvester-agent-dev

# Check Redis
docker exec -it redis-dev redis-cli ping
```
