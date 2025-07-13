# 🤖 Adaptive Compliance Interface

Welcome to your intelligent compliance assistant! This modern chat interface connects to a dedicated AI agent backend through Dapr service mesh.

## 🎯 What I Can Help With

- **📋 Regulatory Compliance** - GDPR, SOX, ISO 27001, HIPAA guidance
- **🔍 Risk Assessment** - Identify and mitigate compliance risks  
- **📄 Document Analysis** - Review policies and procedures
- **💡 Strategic Planning** - Develop compliance roadmaps
- **🎓 Training Support** - Compliance education and best practices

## 🏗️ Architecture

This application uses a **microservices architecture**:

```
Frontend (Chainlit) ↔ Dapr Service Mesh ↔ Backend (AI Agent)
```

- **Frontend**: Modern chat interface on port 9150
- **Backend**: Dedicated AI agent service on port 9160  
- **Dapr**: Service mesh handling communication and state

## 🚀 Ready to Start?

Ask me anything about compliance! Try questions like:
- "Help me understand GDPR requirements"
- "What are the key ISO 27001 controls?"
- "How do I prepare for a SOX audit?"