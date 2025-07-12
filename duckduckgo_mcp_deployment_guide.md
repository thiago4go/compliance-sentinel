# DuckDuckGo MCP Server Deployment Guide

## What is the `mcp/duckduckgo` Docker Image?

The `mcp/duckduckgo` Docker image is a **Model Context Protocol (MCP) server** that provides web search capabilities through DuckDuckGo. It's designed to be used as a remote tool server that AI agents can connect to for web search functionality.

### Key Features:
- **Web Search**: Search DuckDuckGo with advanced rate limiting and result formatting
- **Content Fetching**: Retrieve and parse webpage content with intelligent text extraction
- **Rate Limiting**: Built-in protection against rate limits (30 searches/min, 20 content fetches/min)
- **Error Handling**: Comprehensive error handling and logging
- **LLM-Friendly Output**: Results formatted specifically for large language model consumption

### Available Tools:
1. **`search`** - Search DuckDuckGo and return formatted results
   - Parameters: `query` (string), `max_results` (int, default: 10)
   - Returns: Formatted search results with titles, URLs, and snippets

2. **`fetch_content`** - Fetch and parse content from a webpage URL
   - Parameters: `url` (string)
   - Returns: Cleaned and formatted text content from the webpage

## Server Information:
- **Name**: `ddg-search`
- **Version**: `1.9.4`
- **Protocol**: MCP (Model Context Protocol) 2024-11-05
- **Transport**: stdio (standard input/output)

## Deployment Options

### 1. Local Development with Docker

#### Basic Run (stdio transport):
```bash
# Run the server (it expects JSON-RPC messages via stdin)
docker run --rm -i mcp/duckduckgo
```

#### Interactive Testing:
```bash
# Initialize the server
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}' | docker run --rm -i mcp/duckduckgo
```

### 2. Remote MCP Server Deployment

For deploying as a remote MCP server that Dapr Agents can connect to, you have several options:

#### Option A: Docker with Network Exposure

Since the current image only supports stdio transport, you'll need to create a wrapper that exposes it over HTTP or WebSocket. Here's a basic approach:

```bash
# Create a docker-compose.yml for easier management
version: '3.8'
services:
  duckduckgo-mcp:
    image: mcp/duckduckgo:latest
    container_name: duckduckgo-mcp-server
    restart: unless-stopped
    # Note: This image uses stdio, so you'll need a transport adapter
```

#### Option B: Using MCP over HTTP/WebSocket (Recommended)

Create a transport adapter that converts HTTP/WebSocket to stdio:

```python
# mcp_http_adapter.py
import asyncio
import json
import subprocess
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse

app = FastAPI()

class MCPAdapter:
    def __init__(self):
        self.process = None
        
    async def start_server(self):
        self.process = subprocess.Popen(
            ['docker', 'run', '--rm', '-i', 'mcp/duckduckgo'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
    async def send_request(self, request):
        if not self.process:
            await self.start_server()
            
        request_str = json.dumps(request) + '\n'
        self.process.stdin.write(request_str)
        self.process.stdin.flush()
        
        response_line = self.process.stdout.readline()
        return json.loads(response_line)

adapter = MCPAdapter()

@app.websocket("/mcp")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        try:
            data = await websocket.receive_text()
            request = json.loads(data)
            response = await adapter.send_request(request)
            await websocket.send_text(json.dumps(response))
        except Exception as e:
            await websocket.send_text(json.dumps({
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)}
            }))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### Option C: Kubernetes Deployment

```yaml
# duckduckgo-mcp-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: duckduckgo-mcp-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: duckduckgo-mcp-server
  template:
    metadata:
      labels:
        app: duckduckgo-mcp-server
    spec:
      containers:
      - name: duckduckgo-mcp
        image: mcp/duckduckgo:latest
        # You'll need to add a sidecar or init container for transport adaptation
---
apiVersion: v1
kind: Service
metadata:
  name: duckduckgo-mcp-service
spec:
  selector:
    app: duckduckgo-mcp-server
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

### 3. Integration with Dapr Agents

Once you have the MCP server running remotely, you can integrate it with Dapr Agents:

```python
from dapr_agents import DurableAgent
from dapr_agents.mcp import MCPClient

# Create MCP client for remote server
mcp_client = MCPClient(
    transport="sse",  # or "websocket" depending on your adapter
    endpoint="http://your-mcp-server:8000/mcp"
)

# Create agent with MCP tools
agent = DurableAgent(
    name="SearchAgent",
    role="Web Search Assistant",
    instructions=[
        "Use the search tool to find information on the web",
        "Fetch content from URLs when needed for detailed information"
    ],
    mcp_client=mcp_client,
    # ... other agent configuration
)
```

## Usage Examples

### Basic Search:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search",
    "arguments": {
      "query": "Dapr Agents framework",
      "max_results": 5
    }
  }
}
```

### Content Fetching:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "fetch_content",
    "arguments": {
      "url": "https://dapr.github.io/dapr-agents/"
    }
  }
}
```

## Rate Limiting

The server includes built-in rate limiting:
- **Search**: 30 requests per minute
- **Content Fetching**: 20 requests per minute
- Automatic queue management and wait times

## Troubleshooting

### Common Issues:

1. **"Invalid request parameters" error**: 
   - Ensure you've sent the `initialize` request first
   - Send the `initialized` notification after initialization
   - Check that your JSON-RPC format is correct

2. **Server not responding**:
   - The server expects continuous stdin input
   - Make sure to keep the Docker container running with `-i` flag

3. **Rate limiting**:
   - The server will automatically handle rate limits
   - Consider implementing client-side caching for frequently accessed content

### Debug Mode:
```bash
# Run with stderr output to see debug information
docker run --rm -i mcp/duckduckgo 2>&1
```

## Security Considerations

- The server makes external HTTP requests to DuckDuckGo
- Consider implementing authentication for remote deployments
- Use HTTPS/WSS for production deployments
- Monitor rate limiting to prevent abuse

## Next Steps

1. **Create Transport Adapter**: Build an HTTP/WebSocket adapter for remote access
2. **Deploy to Cloud**: Use cloud services like AWS ECS, Google Cloud Run, or Azure Container Instances
3. **Add Authentication**: Implement API keys or OAuth for secure access
4. **Monitoring**: Add logging and metrics for production use
5. **Caching**: Implement Redis or similar for caching search results

This MCP server provides a powerful foundation for adding web search capabilities to your Dapr Agents applications!
