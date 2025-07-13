# 🏗️ Microservices Architecture

## Overview

The Adaptive Compliance Interface now implements a proper **microservices architecture** with:

- **Frontend Service** (Chainlit) - Port 9150
- **Backend Service** (Dapr Agent) - Port 9160  
- **Dapr Service Mesh** - Handles communication between services

## 📁 Structure

```
/services/adaptive-interface/
├── frontend/
│   ├── chainlit_frontend.py      # Chainlit UI service
│   ├── chainlit.md               # Welcome page
│   ├── requirements.txt          # Frontend dependencies
│   └── Dockerfile                # Frontend container
├── backend/
│   ├── compliance_agent_service.py  # FastAPI + Dapr Agent
│   ├── requirements.txt          # Backend dependencies
│   └── Dockerfile                # Backend container
├── k8s/
│   ├── microservices-deployment.yaml  # K8s deployment
│   └── dapr-components.yaml      # Dapr components
└── run-microservices.sh          # Local development script
```

## 🚀 Quick Start

### Local Development
```bash
# Start both services with Dapr
./run-microservices.sh

# Access frontend: http://localhost:9150
# Backend health: http://localhost:9160/health
```

### Build Docker Images
```bash
# Backend
cd backend
docker build -t compliance-agent-backend:latest .

# Frontend  
cd ../frontend
docker build -t adaptive-interface-frontend:latest .
```

### Deploy to Kubernetes
```bash
# Apply all resources
kubectl apply -f k8s/dapr-components.yaml
kubectl apply -f k8s/microservices-deployment.yaml

# Update OpenAI API key
kubectl create secret generic openai-secret \
  --from-literal=api-key="your-openai-api-key"
```

## 🔗 Service Communication

### Frontend → Backend (via Dapr)
```
GET  /health                     # Backend health check
POST /query                      # Process compliance queries
```

**Request Format:**
```json
{
  "message": "What is ISO 27001?",
  "session_id": "optional-session-id"
}
```

**Response Format:**
```json
{
  "response": "ISO 27001 is...",
  "agent_available": true,
  "session_id": "session-id"
}
```

### Dapr Service Invocation
Frontend calls backend using Dapr service invocation:
```
http://localhost:9151/v1.0/invoke/compliance-agent-backend/method/query
```

## 🎯 Benefits

✅ **Separation of Concerns**: UI and AI logic separated  
✅ **Independent Scaling**: Scale frontend/backend independently  
✅ **Technology Flexibility**: Different tech stacks per service  
✅ **Fault Isolation**: Frontend stays up if backend fails  
✅ **True Dapr Pattern**: Proper service-to-service communication  
✅ **Resource Optimization**: Dedicated resources per service

## 🔧 Port Configuration

| Service | App Port | Dapr HTTP | Dapr gRPC |
|---------|----------|-----------|-----------|
| Frontend | 9150 | 9151 | 9152 |
| Backend | 9160 | 9161 | 9162 |

## 📊 Monitoring

- **Frontend Health**: `http://localhost:9150/healthz`
- **Backend Health**: `http://localhost:9160/health`  
- **Dapr Dashboard**: `dapr dashboard`

## 🔒 Security

- Non-root containers
- Secret management via Kubernetes secrets
- Environment-based configuration
- Health check endpoints
- Minimal container images

Ready for production deployment! 🎉