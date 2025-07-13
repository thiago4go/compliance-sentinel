# 🚀 Adaptive Compliance Interface

A production-ready AI-powered compliance assistant built with **Chainlit**, **Dapr Agents**, and **OpenAI** for SMB compliance management.

## ✨ Features

- 🤖 **AI Compliance Assistant** - Intelligent compliance guidance powered by OpenAI
- 🎨 **Modern Chat Interface** - Clean, professional Chainlit UI
- ⚡ **Dapr Integration** - Microservices architecture with state management
- 🔒 **Production Ready** - Kubernetes deployable with minimal dependencies
- 📋 **Compliance Expertise** - Specialized in ISO 27001, GDPR, SOX, and more

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Chainlit UI   │◄──►│   Dapr Sidecar   │◄──►│   AI Agent      │
│   (Port 9150)   │    │ (Ports 9151-52)  │    │   (OpenAI)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Session  │    │   Pub/Sub        │    │   State Store   │
│   Management    │    │   (In-Memory)    │    │   (In-Memory)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Dapr CLI installed
- OpenAI API key

### 1. Local Development

```bash
# Navigate to service directory
cd services/adaptive-interface

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Start the service
./run-final.sh
```

Access the interface at: **http://localhost:9150**

### 2. Kubernetes Deployment

```bash
# Build container
docker build -t adaptive-interface:latest .

# Deploy to Kubernetes with Dapr
kubectl apply -f k8s/
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4.1-nano` |
| `LITERAL_DISABLE` | Disable telemetry | `true` |

### Ports

- **9150**: Chainlit frontend
- **9151**: Dapr HTTP API  
- **9152**: Dapr gRPC API

### Dapr Components

Located in `dapr/components-minimal/`:
- `statestore.yaml` - In-memory state storage
- `pubsub.yaml` - In-memory pub/sub messaging
- `conversationstore.yaml` - Conversation history

## 🎯 Usage Examples

### Compliance Queries

1. **ISO 27001 Guidance**
   ```
   User: "ISO 27001"
   AI: Provides detailed implementation guidance, requirements, and best practices
   ```

2. **Risk Assessment**
   ```
   User: "risk assessment"
   AI: Explains risk assessment methodologies and compliance frameworks
   ```

3. **GDPR Compliance**
   ```
   User: "GDPR data protection"
   AI: Offers data protection strategies and GDPR compliance steps
   ```

## 🔒 Compliance Expertise

The AI assistant specializes in:

- **Information Security**: ISO 27001, NIST Framework
- **Data Protection**: GDPR, CCPA, Privacy frameworks
- **Financial Compliance**: SOX, PCI DSS, audit requirements
- **Healthcare**: HIPAA compliance
- **Risk Management**: Assessment methodologies, mitigation strategies

## 📊 Production Features

- **Stateless Design**: No external database dependencies
- **Horizontal Scaling**: Multiple instances supported
- **Health Checks**: Built-in health monitoring
- **Error Handling**: Graceful fallback mechanisms
- **Security**: Non-root container, minimal attack surface

## 🚀 Deployment Options

### 1. Local Development
```bash
./run-final.sh
```

### 2. Docker
```bash
docker run -p 9150:9150 -e OPENAI_API_KEY="your-key" adaptive-interface:latest
```

### 3. Kubernetes with Dapr
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: adaptive-interface
  annotations:
    dapr.io/enabled: "true"
    dapr.io/app-id: "adaptive-interface"
    dapr.io/app-port: "9150"
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: adaptive-interface
        image: adaptive-interface:latest
        ports:
        - containerPort: 9150
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
```

## 🔧 Troubleshooting

### Common Issues

1. **OpenAI API Error**: Verify API key is set correctly
2. **Port Conflicts**: Ensure ports 9150-9152 are available
3. **Dapr Not Found**: Install Dapr CLI and run `dapr init`

### Debug Mode

```bash
export DAPR_LOG_LEVEL=debug
./run-final.sh
```

## 📁 Project Structure

```
adaptive-interface/
├── working-chainlit-app.py    # Main application
├── run-final.sh              # Start script
├── requirements.txt          # Dependencies
├── .env                      # Environment config
├── Dockerfile               # Container config
├── README.md                # Documentation
├── chainlit.md              # Chainlit config
└── dapr/
    └── components-minimal/   # Dapr components
        ├── conversationstore.yaml
        ├── pubsub.yaml
        └── statestore.yaml
```

## 🎉 Ready for Production

This service is optimized for:
- ✅ Kubernetes deployment
- ✅ Horizontal scaling
- ✅ Minimal resource usage
- ✅ Professional compliance guidance
- ✅ Enterprise security requirements

---

**Built with ❤️ using Chainlit, Dapr Agents, and OpenAI**