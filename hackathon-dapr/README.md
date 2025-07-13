# 🚀 Compliance Sentinel - Dapr AI Hackathon Submission

**Intelligent, Resilient, and Scalable AI-Powered Compliance Management System**

## 📝 Summary

Compliance Sentinel is a distributed AI system that revolutionizes compliance management for SMB companies through intelligent multi-agent orchestration. The system combines Dapr Workflows, Dapr Agents, and advanced AI capabilities to provide automated compliance checking, risk assessment, and regulatory guidance across multiple frameworks (GDPR, ISO 27001, SOX, HIPAA).

Built using the **Nexus-Oracle-Forge Architecture**, this system demonstrates true collaborative intelligence through specialized agents working in concert, orchestrated by Dapr Workflows with built-in resilience and fault tolerance.

## 🏆 Category

**All Three Categories Achieved:**
- ✅ **Collaborative Intelligence** - Multi-agent coordination with specialized DurableAgent instances
- ✅ **Workflow Resilience** - Fault-tolerant AI pipelines with Dapr Workflow state persistence  
- ✅ **Distributed Architecture** - Scalable microservices with comprehensive Dapr building blocks

## 💻 Technology Used

- **Platform**: Dapr OSS with Dapr Agents Framework
- **Dapr APIs**: Workflow API, Pub/Sub (Redis), State Management (Redis), Service Invocation, Secrets Management
- **Programming Languages**: Python 3.11+
- **Frontend**: Chainlit (Modern Chat Interface)
- **Database**: PostgreSQL (Compliance data & audit trails)
- **Message Broker**: Redis (Pub/Sub & State persistence)
- **Additional Technologies**: FastAPI, Docker, Docker Compose, MCP (Model Context Protocol)

## 📋 Project Features

- 🤖 **Multi-Agent Intelligence** - 3 specialized DurableAgent instances with distinct roles
- 🔄 **Workflow Orchestration** - Dapr Workflows for complex compliance processes with automatic retry
- 💬 **Interactive UI** - Professional Chainlit interface with Dapr service invocation
- 📊 **Real-time Insights** - Live compliance status and risk assessments
- 🔒 **Secure by Design** - Dapr secrets management and secure inter-service communication
- 📈 **Audit Trails** - Complete compliance history with event sourcing patterns
- 🌐 **Distributed & Scalable** - Microservices architecture with horizontal scaling capability
- 🛡️ **Fault Tolerant** - Built-in resilience with state persistence and automatic recovery

## 🏗️ Architecture

### System Overview
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Chainlit UI   │◄──►│ Adaptive Interface│◄──►│ Workflow Agent  │
│   (Port 9150)   │    │     Agent         │    │ (Orchestrator)  │
│                 │    │   (Port 9160)     │    │  (Port 9170)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Dapr Pub/Sub  │◄──►│   Dapr State     │◄──►│ Harvester Agent │
│   (Redis:6379)  │    │   (Redis)        │    │ (Insights)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PostgreSQL    │◄──►│   Dapr Secrets   │◄──►│   MCP Tools     │
│   (Port 5432)   │    │   Management     │    │   Integration   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Agent Responsibilities

1. **Adaptive Interface Agent** (DurableAgent)
   - User interaction and request routing via Chainlit
   - Dapr service invocation to workflow orchestrator
   - Session management and response formatting

2. **Workflow Agent** (DurableAgent + Dapr Workflow)
   - Process orchestration using Dapr Workflow activities
   - State persistence and error recovery
   - Event-driven coordination via Pub/Sub

3. **Harvester Insights Agent** (DurableAgent)
   - Compliance analysis and risk assessment
   - PostgreSQL integration for data persistence
   - MCP tool integration for external data sources

### Event-Driven Flow

1. User submits compliance query via Chainlit UI
2. Adaptive Interface Agent publishes `new-request` event to Dapr Pub/Sub
3. Workflow Agent receives event and initiates Dapr Workflow
4. Workflow orchestrates activities: `harvest_insights` → `analyze_compliance` → `generate_report`
5. Harvester Agent processes insights and stores results in PostgreSQL
6. Results flow back through Pub/Sub to update UI with final compliance analysis

## 🎬 Demo

**Demo Video**: [3-5 minute demonstration showing:]
- Multi-agent collaboration in real-time compliance analysis
- Workflow resilience with automatic failure recovery
- Distributed architecture scaling across microservices
- Live compliance scenarios (GDPR, ISO 27001, SOX)

**Live Demo Access**: `http://localhost:9150` (after running setup)

## Installation & Deployment Instructions

### Prerequisites

- Docker & Docker Compose
- Dapr CLI (`dapr init`)
- Python 3.11+
- OpenAI API Key

### Quick Start

```bash
# Clone and navigate
cd hackathon-dapr

# Initialize Dapr locally (sets up Redis containers)
dapr init

# Copy environment template
cp .env.example .env

# Add your OpenAI API key
echo "OPENAI_API_KEY=your-key-here" >> .env

# Start infrastructure services
docker-compose up -d redis postgres

# Start all Dapr agents
./scripts/start-all.sh

# Access Compliance Sentinel UI
open http://localhost:9150
```

### Environment Setup

```bash
# Required environment variables
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=compliance_sentinel
PG_USER=postgres
PG_PASSWORD=postgres123
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Service Architecture

| Service | Port | Type | Description |
|---------|------|------|-------------|
| Chainlit Frontend | 9150 | UI | User interface |
| Adaptive Interface Agent | 9160 | DurableAgent | Backend API |
| Workflow Agent | 9170 | DurableAgent + Workflow | Orchestrator |
| Harvester Insights Agent | 9180 | DurableAgent | Analysis engine |
| PostgreSQL | 5432 | Database | Data persistence |
| Redis | 6379 | Cache/Pub-Sub | State & messaging |

### Dapr Components

- **State Store**: Redis-based with actor state support
- **Pub/Sub**: Redis message broker for event-driven communication
- **Secrets**: Local file-based secret management
- **Workflow**: Built-in Dapr Workflow engine with Redis persistence

## 🔧 Development Workflow

### Local Development
```bash
# Start individual services for development
cd adaptive-interface
./run-final.sh

# Or start all services
./scripts/start-all.sh
```

### Testing
```bash
# Unit tests
python -m pytest tests/

# Integration tests
./scripts/test-integration.sh

# End-to-end demo
./scripts/demo-compliance-flow.sh
```

## 🎯 Hackathon Victory Strategy

### Collaborative Intelligence Demonstration
- **Multi-Agent Coordination**: 3 specialized DurableAgent instances with distinct expertise
- **Intelligent Orchestration**: Dapr Workflow managing complex compliance analysis flows
- **Dynamic Collaboration**: Agents sharing context and building on each other's insights

### Workflow Resilience Showcase
- **Automatic Recovery**: Dapr Workflow state persistence survives service restarts
- **Error Handling**: Built-in retry mechanisms and compensation patterns
- **Durable Execution**: Guaranteed task completion regardless of failures

### Distributed Architecture Excellence
- **Microservices Design**: Independent, scalable agent services
- **Event-Driven Communication**: Decoupled messaging via Dapr Pub/Sub
- **State Management**: Distributed state with Redis backend
- **Service Discovery**: Dapr service invocation with load balancing

## 🏆 Success Criteria Achievement

✅ **Functional End-to-End Demo**: Complete compliance analysis workflow  
✅ **Collaborative Intelligence**: Multi-agent coordination with specialized roles  
✅ **Dapr Technology Showcase**: Workflow, Pub/Sub, State, Service Invocation, Secrets  
✅ **Production Readiness**: Docker containerization, health checks, monitoring  
✅ **Innovation Factor**: Novel application of Dapr Agents for compliance automation  

## Team Members

- [Your Name](https://github.com/yourusername) - Full-Stack Developer & Dapr Architect

## License

MIT License - Built for Dapr AI Hackathon 2025

---

**🎯 Triple Category Victory Through:**
- **Collaborative Intelligence**: Sophisticated multi-agent coordination with DurableAgent framework
- **Workflow Resilience**: Dapr Workflows with automatic retry, state persistence, and fault tolerance  
- **Distributed Architecture**: Scalable microservices leveraging all major Dapr building blocks

**Built with ❤️ using Dapr Agents, Dapr Workflows, and Modern AI**
