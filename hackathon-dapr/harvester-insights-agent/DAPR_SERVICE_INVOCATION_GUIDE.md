# Dapr Service Invocation Troubleshooting Guide

## Error: ERR_DIRECT_INVOKE

### Problem
```json
{
  "errorCode": "ERR_DIRECT_INVOKE",
  "message": "failed getting app id either from the URL path or the header dapr-app-id"
}
```

### Root Cause
This error occurs when Dapr cannot identify the target service because:
1. **Missing app-id in URL path**
2. **Missing dapr-app-id header**
3. **Incorrect URL format**

## ✅ Correct Service Invocation Patterns

### Method 1: URL Path (Recommended)
```bash
# Format: /v1.0/invoke/{app-id}/method/{method-name}
curl -X GET "http://localhost:3502/v1.0/invoke/harvester-insights-agent/method/health"

curl -X POST "http://localhost:3502/v1.0/invoke/harvester-insights-agent/method/harvest-insights" \
  -H "Content-Type: application/json" \
  -d '{"framework": "GDPR", "company_name": "Test Company"}'
```

### Method 2: Header-based
```bash
curl -X GET "http://localhost:3502/v1.0/invoke/method/health" \
  -H "dapr-app-id: harvester-insights-agent"

curl -X POST "http://localhost:3502/v1.0/invoke/method/harvest-insights" \
  -H "Content-Type: application/json" \
  -H "dapr-app-id: harvester-insights-agent" \
  -d '{"framework": "GDPR", "company_name": "Test Company"}'
```

## ❌ Common Mistakes

### Wrong URL Patterns
```bash
# ❌ Missing app-id
curl http://localhost:3502/v1.0/invoke/method/health

# ❌ Wrong path structure  
curl http://localhost:3502/v1.0/invoke/health

# ❌ Missing /method/ segment
curl http://localhost:3502/v1.0/invoke/harvester-insights-agent/health
```

### Missing Headers
```bash
# ❌ Using header method but missing dapr-app-id
curl http://localhost:3502/v1.0/invoke/method/health
```

## 🔧 Debugging Steps

### 1. Verify Dapr is Running
```bash
# Check Dapr sidecar is running
curl http://localhost:3502/v1.0/metadata

# Should return app metadata including app-id
```

### 2. Verify App is Registered
```bash
# Check if your app is discovered
curl http://localhost:3502/v1.0/metadata | grep -A5 -B5 "harvester-insights-agent"
```

### 3. Test Direct App Access First
```bash
# Test app directly (bypass Dapr)
curl http://localhost:9180/health

# If this fails, fix the app first
```

### 4. Use Correct Service Invocation
```bash
# Use full URL path method
curl "http://localhost:3502/v1.0/invoke/harvester-insights-agent/method/health"
```

## 🚀 Working Examples

### Health Check
```bash
# Direct access
curl http://localhost:9180/health

# Via Dapr
curl "http://localhost:3502/v1.0/invoke/harvester-insights-agent/method/health"
```

### POST Request
```bash
# Direct access
curl -X POST http://localhost:9180/harvest-insights \
  -H "Content-Type: application/json" \
  -d '{"framework": "GDPR", "company_name": "Test Company"}'

# Via Dapr
curl -X POST "http://localhost:3502/v1.0/invoke/harvester-insights-agent/method/harvest-insights" \
  -H "Content-Type: application/json" \
  -d '{"framework": "GDPR", "company_name": "Test Company"}'
```

### Pub/Sub Publishing
```bash
# Publish to topic
curl -X POST "http://localhost:3502/v1.0/publish/messagepubsub/harvest-request" \
  -H "Content-Type: application/json" \
  -d '{"framework": "GDPR", "company": "Test Company"}'
```

## 🔍 Service Discovery

### List All Services
```bash
# Get all registered services
dapr list

# Or via API
curl http://localhost:3502/v1.0/metadata
```

### Check Service Status
```bash
# Verify service is running and registered
curl http://localhost:3502/v1.0/metadata | python -m json.tool
```

## 📝 Configuration Checklist

### Dapr Run Command
```bash
dapr run \
  --app-id harvester-insights-agent \  # ✅ Must match invocation calls
  --app-port 9180 \                   # ✅ App listening port
  --dapr-http-port 3502 \             # ✅ Dapr HTTP API port
  --dapr-grpc-port 50003 \            # ✅ Dapr gRPC port
  --resources-path ./components \      # ✅ Components directory
  --config ./config/config.yaml \     # ✅ Dapr config
  -- python harvester_agent.py        # ✅ App command
```

### App Configuration
- ✅ App must listen on specified port (9180)
- ✅ App must respond to health checks
- ✅ App must handle Dapr pub/sub subscriptions

### Component Configuration
- ✅ Redis components properly configured
- ✅ Pub/sub component accessible
- ✅ State stores configured correctly

## 🐛 Common Issues & Solutions

### Issue: Port Already in Use
```bash
# Kill existing processes
pkill -f "python harvester_agent.py"
pkill -f "dapr run"

# Wait and retry
sleep 2
dapr run --app-id harvester-insights-agent ...
```

### Issue: App Not Responding
```bash
# Check app logs
# Look for "Uvicorn running on http://0.0.0.0:9180"

# Test direct access
curl http://localhost:9180/health
```

### Issue: Components Not Loading
```bash
# Check component files exist
ls -la ./components/

# Check Redis is running
docker ps | grep redis

# Test Redis connection
redis-cli ping
```

## 📊 Testing Workflow

1. **Start Services**: Redis, Dapr runtime
2. **Start App**: With correct Dapr configuration
3. **Test Direct**: Verify app works without Dapr
4. **Test Dapr**: Use correct service invocation syntax
5. **Debug**: Check logs and metadata if issues occur

## 🎯 Success Indicators

- ✅ `dapr initialized. Status: Running`
- ✅ `application discovered on port 9180`
- ✅ `app is subscribed to the following topics`
- ✅ Direct app access works: `curl http://localhost:9180/health`
- ✅ Dapr invocation works: `curl http://localhost:3502/v1.0/invoke/harvester-insights-agent/method/health`
