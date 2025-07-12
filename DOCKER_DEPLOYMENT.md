# Docker Deployment Guide

## Docker Image

The MCP server has been containerized and published to DockerHub:

**Image**: `thiago4go/compliance-sentinel-mcp:latest`

## Quick Start

### Run with Docker

```bash
# Run the container
docker run -d -p 8081:8081 --name mcp-server thiago4go/compliance-sentinel-mcp:latest

# Test the server
curl http://localhost:8081/health

# View logs
docker logs mcp-server

# Stop the container
docker stop mcp-server
docker rm mcp-server
```

### Deploy to Kubernetes

```bash
# Deploy using the provided manifest
kubectl apply -f k8s-deployment.yaml

# Or use the deployment script
./deploy.sh

# Port forward to access locally
kubectl port-forward service/compliance-sentinel-mcp-service 8080:80

# Test the service
curl http://localhost:8080/health
```

## Configuration

### Environment Variables

- `PORT`: Server port (default: 8081)
- `HOST`: Server host (default: 0.0.0.0)
- `LOG_LEVEL`: Logging level (default: INFO)

### Docker Run with Custom Config

```bash
docker run -d \
  -p 8081:8081 \
  -e LOG_LEVEL=DEBUG \
  -e PORT=8081 \
  --name mcp-server \
  thiago4go/compliance-sentinel-mcp:latest
```

## API Endpoints

- `GET /` - Server information
- `GET /health` - Health check
- `GET /metrics` - Server metrics
- `GET /tools` - List available MCP tools
- `POST /mcp` - MCP JSON-RPC endpoint
- `POST /search` - Direct search endpoint
- `POST /fetch` - Direct content fetch endpoint

## Example Usage

### Health Check
```bash
curl http://localhost:8081/health
```

### Search Example
```bash
curl -X POST http://localhost:8081/search \
  -H "Content-Type: application/json" \
  -d '{"query": "kubernetes deployment", "max_results": 5}'
```

### MCP Protocol Example
```bash
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search",
      "arguments": {
        "query": "docker best practices",
        "max_results": 3
      }
    }
  }'
```

## Kubernetes Features

- **Health Checks**: Liveness and readiness probes
- **Resource Limits**: Memory and CPU constraints
- **Security**: Non-root user, security context
- **Scaling**: Horizontal pod autoscaling ready
- **Service Discovery**: ClusterIP service
- **Ingress**: Optional ingress configuration

## Monitoring

### View Logs
```bash
# Docker
docker logs mcp-server

# Kubernetes
kubectl logs -l app=compliance-sentinel-mcp
```

### Metrics
```bash
curl http://localhost:8081/metrics
```

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port mapping
   ```bash
   docker run -d -p 8082:8081 thiago4go/compliance-sentinel-mcp:latest
   ```

2. **Container won't start**: Check logs
   ```bash
   docker logs mcp-server
   ```

3. **Kubernetes pod not ready**: Check pod status
   ```bash
   kubectl describe pod -l app=compliance-sentinel-mcp
   ```

### Debug Mode

Run with debug logging:
```bash
docker run -d -p 8081:8081 -e LOG_LEVEL=DEBUG thiago4go/compliance-sentinel-mcp:latest
```

## Security Considerations

- Container runs as non-root user (UID 1000)
- Minimal base image (Python slim)
- No unnecessary privileges
- Health checks for reliability
- Resource limits to prevent resource exhaustion
