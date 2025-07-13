# Harvester Insights Agent

Enhanced compliance intelligence harvester with Dapr Agents, MCP tools integration, and pub/sub messaging for the Compliance Sentinel system.

## 🚀 Features Implemented

### ✅ Core Agent Capabilities
- **Dapr Agents Integration**: DurableAgent with persistent memory
- **MCP Tools**: Web search via DuckDuckGo through MCP server
- **PostgreSQL Access**: Database operations through MCP tools (not direct connection)
- **Compliance Intelligence**: Framework-specific insights and recommendations

### ✅ Dapr Integration
- **Pub/Sub Messaging**: Event-driven communication with other agents
- **State Management**: Conversation memory and search result caching
- **Service Invocation**: Ready for inter-agent communication
- **Workflow Integration**: Pub/sub events for workflow orchestration

### ✅ API Endpoints
- `POST /harvest-insights` - Main compliance analysis endpoint
- `POST /search` - Web search via MCP tools
- `POST /trigger-workflow` - Workflow trigger via pub/sub
- `GET /health` - Health check with component status
- `GET /agent/info` - Agent capabilities and status
- `GET /frameworks` - Supported compliance frameworks
- `GET /metrics` - Performance and status metrics

## 🏗️ Architecture

```
┌─────────────────────┐    ┌─────────────────────┐
│   Harvester Agent   │    │    MCP Server       │
│   (Dapr Agent)      │◄──►│  - DuckDuckGo       │
│   Port: 9180        │    │  - PostgreSQL       │
└─────────────────────┘    └─────────────────────┘
           │
           ▼
┌─────────────────────┐    ┌─────────────────────┐
│   Dapr Sidecar     │    │   Shared Redis      │
│   HTTP: 3500       │◄──►│  - State Stores     │
│   gRPC: 50001      │    │  - Pub/Sub          │
└─────────────────────┘    └─────────────────────┘
```

## 📁 Project Structure

```
harvester-insights-agent/
├── harvester_agent.py          # Main agent implementation
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── docker-compose.dev.yml      # Development environment
├── .env.example               # Environment template
├── components/                # Dapr component references
│   ├── README.md             # Component documentation
│   ├── pubsub.yaml           # Pub/sub configuration
│   ├── statestore.yaml       # Workflow state store
│   ├── conversationstore.yaml # Conversation memory
│   ├── searchresultsstore.yaml # Search cache
│   └── agentstatestore.yaml  # Agent registry
├── config/
│   └── config.yaml           # Dapr configuration
├── DEVELOPMENT.md            # Development guide
└── README.md                 # This file
```

## 🔧 Quick Start

### 1. Environment Setup
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 2. Development Mode
```bash
# Local development
python harvester_agent.py

# Docker development
docker-compose -f docker-compose.dev.yml up --build
```

### 3. Test the Agent
```bash
# Health check
curl http://localhost:9180/health

# Compliance analysis
curl -X POST http://localhost:9180/harvest-insights \
  -H "Content-Type: application/json" \
  -d '{
    "framework": "GDPR",
    "company_name": "Test Company",
    "industry": "Technology"
  }'
```

## 🔌 Integration Points

### Pub/Sub Topics
- **Subscribes to**:
  - `harvest-request` - Harvest requests from workflow
  - `compliance-query` - Direct compliance queries
  
- **Publishes to**:
  - `harvester-complete` - Completion notifications
  - `workflow-trigger` - Workflow initiation

### State Stores
- `conversationstore` - Agent conversation memory
- `searchresultsstore` - Search result caching
- `workflowstatestore` - Shared workflow state
- `agentstatestore` - Agent registry

### MCP Tools Required
- **DuckDuckGo Search** - Web search capabilities
- **PostgreSQL Tools** - Database operations for compliance data

## 🎯 Hackathon Categories Addressed

### ✅ Collaborative Intelligence
- Multi-agent coordination via pub/sub messaging
- Shared state management across agents
- MCP tool orchestration for external services

### ✅ Workflow Resilience
- Dapr Workflow integration via pub/sub events
- Persistent state management with Redis
- Graceful error handling and recovery

### ✅ Distributed Architecture
- Microservice architecture with Dapr sidecar
- Event-driven communication patterns
- Scalable state management and pub/sub

## 🚀 Next Steps

1. **MCP Server Setup**: Ensure MCP server is running with required tools
2. **Shared Components**: Connect to shared Redis instance in production
3. **Workflow Integration**: Test pub/sub communication with workflow-agent
4. **Performance Testing**: Load testing and optimization
5. **Monitoring**: Add comprehensive logging and metrics

## 📋 Requirements

- Python 3.11+
- Dapr 1.12+
- Redis (shared instance)
- MCP Server with DuckDuckGo and PostgreSQL tools
- OpenRouter API key (for AI features)

## 🔍 Monitoring

The agent provides comprehensive health checks and metrics:
- Component connectivity status
- MCP tool availability
- Dapr sidecar health
- Processing performance metrics
