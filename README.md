# Dapr AI Hackathon - Compliance Sentinel

Welcome to **Compliance Sentinel**, an intelligent, distributed AI system built for the **Dapr AI Hackathon x Diagrid**! This project demonstrates the power of multi-agent orchestration, workflow resilience, and distributed architecture using Dapr Workflows and Dapr Agents.

## Project Details

### 🚀 Project Name

**Compliance Sentinel** - Intelligent Compliance Monitoring and Analysis System

### 📝 Summary

Compliance Sentinel is an advanced AI-powered system that automates compliance monitoring, analysis, and reporting for organizations. The system leverages multiple specialized AI agents working collaboratively to harvest insights, perform compliance checks, and provide actionable recommendations through an intuitive user interface.

The application uses event-driven architecture with Dapr to orchestrate three specialized agents:
- **Adaptive Interface Agent**: Manages user interactions and UI communication
- **Workflow Agent**: Orchestrates the compliance process and manages agent coordination
- **Harvester Insights Agent**: Performs deep compliance analysis and data extraction

### 🏆 Category

This project targets **all three solution categories**:

- **✅ Collaborative Intelligence**: Multi-agent coordination with 3 specialized agents working together via pub/sub communication
- **✅ Workflow Resilience**: Built-in state persistence, error recovery, and fault-tolerant AI pipelines using Dapr Workflows
- **✅ Distributed Architecture**: Scalable microservices architecture with Dapr building blocks for state management, pub/sub, and secrets management

### 💻 Technology Used

- **Platform**: Dapr OSS with Dapr Agents
- **Dapr APIs**: 
  - Dapr Workflow API (orchestration and state management)
  - Dapr Pub/Sub (event-driven communication)
  - Dapr State Management (agent state persistence)
  - Dapr Service Invocation (inter-service communication)
  - Dapr Secrets Management (secure credential handling)
- **Programming Languages**: Python
- **Additional Technologies**: 
  - **Frontend**: Chainlit (Interactive UI)
  - **Database**: PostgreSQL (compliance data and insights storage)
  - **Message Broker**: Redis (Dapr pub/sub and state store)
  - **Tool Integration**: Model Context Protocol (MCP) for standardized tool access
  - **Containerization**: Docker & Docker Compose
  - **Testing**: pytest for comprehensive testing strategy

### 📋 Project Features

- **Multi-Agent Collaboration**: Three specialized AI agents with distinct roles and responsibilities
- **Event-Driven Architecture**: Asynchronous communication using Dapr Pub/Sub for scalability and resilience
- **Workflow Orchestration**: Durable workflows with built-in error handling and state persistence
- **Interactive UI**: User-friendly Chainlit interface for compliance monitoring and analysis
- **Intelligent Insights**: Advanced compliance analysis with actionable recommendations
- **Fault Tolerance**: Resilient system design with automatic retries and error recovery
- **Secure Operations**: Dapr Secrets Management for handling sensitive information
- **Audit Trail**: Complete event sourcing for compliance history and audit requirements
- **Tool Integration**: Standardized tool access via Model Context Protocol (MCP)
- **Scalable Architecture**: Microservices design allowing independent scaling of components

### 🏗️ Architecture

The Compliance Sentinel follows a distributed, event-driven microservices architecture:

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   Chainlit UI   │───▶│ Adaptive Interface   │───▶│   Workflow Agent    │
│   (Frontend)    │    │      Agent           │    │   (Orchestrator)    │
└─────────────────┘    └──────────────────────┘    └─────────────────────┘
                                │                            │
                                ▼                            ▼
                       ┌─────────────────┐         ┌─────────────────────┐
                       │  Dapr Pub/Sub   │◀────────│ Harvester Insights  │
                       │   (Redis)       │         │       Agent         │
                       └─────────────────┘         └─────────────────────┘
                                │                            │
                                ▼                            ▼
                       ┌─────────────────┐         ┌─────────────────────┐
                       │ Dapr State      │         │    PostgreSQL       │
                       │ Management      │         │    Database         │
                       │   (Redis)       │         └─────────────────────┘
                       └─────────────────┘
```

**Key Architectural Components:**

1. **User Interaction Layer**: Chainlit UI provides an intuitive interface for compliance operations
2. **Agent Orchestration**: Event-driven communication via Dapr Pub/Sub enables loose coupling and scalability
3. **Workflow Management**: Dapr Workflows provide durable execution with state persistence and error recovery
4. **Data Persistence**: PostgreSQL stores compliance results and insights with full audit trail
5. **State Management**: Redis-backed Dapr state store maintains agent states and workflow context
6. **Tool Integration**: MCP server provides standardized access to external tools and services

**Event Flow:**
1. User initiates compliance check via Chainlit UI
2. Adaptive Interface Agent publishes `new-request` event
3. Workflow Agent subscribes and initiates compliance workflow
4. Workflow Agent publishes `harvest-insights` event
5. Harvester Insights Agent performs analysis and publishes results
6. Workflow Agent aggregates results and stores in database
7. Final notification updates the UI with compliance insights

### 🎬 Demo

**Demo Video**: [3-5 minute demonstration video showing:]
- Live compliance analysis workflow execution
- Multi-agent coordination and communication
- Dapr Workflow orchestration in action
- Real-time UI updates and user interaction
- Fault tolerance and error recovery capabilities
- Database persistence and audit trail features

*[Demo video link will be provided upon completion]*

## Installation & Deployment Instructions

### Prerequisites

- **Docker & Docker Compose**: Latest version for containerized development
- **Dapr CLI**: v1.12+ for local Dapr runtime management
- **Python**: 3.9+ for agent development and testing
- **PostgreSQL**: 13+ (or use Docker container)
- **Redis**: 6+ (or use Docker container)
- **Git**: For repository management

### Additional Set-Up

#### 1. Clone and Setup Repository
```bash
git clone <your-repository-url>
cd compliance-sentinel
```

#### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Configure environment variables
# - Database credentials
# - Redis connection settings
# - API keys and secrets
```

#### 3. Local Development with Docker Compose
```bash
# Start all services including Dapr sidecars
docker-compose -f docker-compose.dev.yml up -d

# Initialize Dapr components
dapr init

# Verify all services are running
docker-compose ps
```

#### 4. Database Setup
```bash
# Run database migrations
python scripts/setup_database.py

# Load sample compliance data
python scripts/load_sample_data.py
```

#### 5. Access the Application
- **Chainlit UI**: http://localhost:8000
- **Dapr Dashboard**: http://localhost:8080
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

#### 6. Running Tests
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/
```

#### 7. Production Deployment (Kubernetes)
```bash
# Deploy to Kubernetes cluster
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n compliance-sentinel
```

### Development Workflow

1. **Local Development**: Use Docker Compose for consistent development environment
2. **Testing**: Comprehensive test suite with unit, integration, and e2e tests
3. **Monitoring**: Built-in Dapr observability and custom metrics
4. **Debugging**: Dapr dashboard and logging for troubleshooting

## Team Members

- [Thiago](https://github.com/thiago4go) 
- [Makara](https://github.com/makaracc)

## License

MIT License - See [LICENSE](LICENSE)

*This project demonstrates the power of distributed AI systems using Dapr's building blocks to create resilient, scalable, and intelligent applications.*
