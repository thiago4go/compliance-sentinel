#!/usr/bin/env python3
"""
Standalone DuckDuckGo MCP Server for Kubernetes
No Docker-in-Docker dependency - pure Python implementation
"""

import asyncio
import json
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import urllib.parse
import re
from datetime import datetime, timedelta
import os

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DuckDuckGo MCP Server (Standalone)",
    version="1.0.0",
    description="Standalone MCP server for DuckDuckGo search - Kubernetes ready"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RateLimiter:
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests = []

    async def acquire(self):
        now = datetime.now()
        # Remove requests older than 1 minute
        self.requests = [
            req for req in self.requests if now - req < timedelta(minutes=1)
        ]

        if len(self.requests) >= self.requests_per_minute:
            # Wait until we can make another request
            wait_time = 60 - (now - self.requests[0]).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)

        self.requests.append(now)

class DuckDuckGoSearcher:
    BASE_URL = "https://html.duckduckgo.com/html"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def __init__(self):
        self.rate_limiter = RateLimiter(30)  # 30 requests per minute
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search(self, query: str, max_results: int = 10) -> str:
        """Search DuckDuckGo and return formatted results"""
        try:
            await self.rate_limiter.acquire()
            
            params = {
                'q': query,
                'kl': 'us-en',
                's': '0',
                'dc': str(max_results)
            }
            
            logger.info(f"Searching DuckDuckGo for: {query}")
            
            response = await self.client.get(
                self.BASE_URL,
                params=params,
                headers=self.HEADERS,
                follow_redirects=True
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Find search result containers
            result_containers = soup.find_all('div', class_='result')
            
            for i, container in enumerate(result_containers[:max_results]):
                try:
                    # Extract title and link
                    title_link = container.find('a', class_='result__a')
                    if not title_link:
                        continue
                    
                    title = title_link.get_text(strip=True)
                    link = title_link.get('href', '')
                    
                    # Clean up DuckDuckGo redirect URLs
                    if link.startswith('/l/?uddg='):
                        link = urllib.parse.unquote(link.split('uddg=')[1])
                    
                    # Extract snippet
                    snippet_elem = container.find('a', class_='result__snippet')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    if title and link:
                        results.append({
                            'position': i + 1,
                            'title': title,
                            'link': link,
                            'snippet': snippet
                        })
                        
                except Exception as e:
                    logger.warning(f"Error parsing result {i}: {e}")
                    continue
            
            # Format results for LLM consumption
            if not results:
                return "No search results found."
            
            formatted_results = f"Search results for '{query}':\\n\\n"
            for result in results:
                formatted_results += f"{result['position']}. **{result['title']}**\\n"
                formatted_results += f"   URL: {result['link']}\\n"
                if result['snippet']:
                    formatted_results += f"   {result['snippet']}\\n"
                formatted_results += "\\n"
            
            logger.info(f"Found {len(results)} results for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise Exception(f"Search failed: {str(e)}")

class WebContentFetcher:
    def __init__(self):
        self.rate_limiter = RateLimiter(20)  # 20 requests per minute
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_content(self, url: str) -> str:
        """Fetch and parse content from a webpage"""
        try:
            await self.rate_limiter.acquire()
            
            logger.info(f"Fetching content from: {url}")
            
            response = await self.client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                follow_redirects=True
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\\n'.join(chunk for chunk in chunks if chunk)
            
            # Truncate if too long
            if len(text) > 5000:
                text = text[:5000] + "\\n\\n[Content truncated...]"
            
            logger.info(f"Successfully fetched {len(text)} characters from {url}")
            return text
            
        except Exception as e:
            logger.error(f"Content fetch error: {e}")
            raise Exception(f"Failed to fetch content: {str(e)}")

# Global instances
searcher = DuckDuckGoSearcher()
fetcher = WebContentFetcher()

# Metrics tracking
request_count = 0
error_count = 0

@app.middleware("http")
async def track_requests(request, call_next):
    global request_count
    request_count += 1
    
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        global error_count
        error_count += 1
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    await searcher.client.aclose()
    await fetcher.client.aclose()
    logger.info("MCP server shutdown complete")

@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "name": "DuckDuckGo MCP Server (Standalone)",
        "version": "1.0.0",
        "description": "Kubernetes-ready MCP server for DuckDuckGo search",
        "status": "operational",
        "endpoints": {
            "mcp": "/mcp (POST) - MCP JSON-RPC endpoint",
            "search": "/search (POST) - Direct search endpoint",
            "fetch": "/fetch (POST) - Direct content fetch endpoint",
            "tools": "/tools (GET) - List available tools",
            "metrics": "/metrics (GET) - Server metrics"
        },
        "kubernetes_ready": True
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes"""
    return {
        "status": "healthy",
        "server": "operational",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """Metrics endpoint for monitoring"""
    return {
        "requests_total": request_count,
        "errors_total": error_count,
        "uptime_seconds": (datetime.now() - start_time).total_seconds(),
        "rate_limits": {
            "search_requests_in_window": len(searcher.rate_limiter.requests),
            "fetch_requests_in_window": len(fetcher.rate_limiter.requests)
        }
    }

@app.get("/tools")
async def list_tools():
    """List available MCP tools"""
    return {
        "tools": [
            {
                "name": "search",
                "description": "Search DuckDuckGo and return formatted results",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "default": 10, "description": "Maximum results"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "fetch_content",
                "description": "Fetch and parse content from a webpage URL",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to fetch content from"}
                    },
                    "required": ["url"]
                }
            }
        ]
    }

@app.post("/mcp")
async def mcp_endpoint(request: Dict[str, Any]):
    """MCP JSON-RPC endpoint"""
    try:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        logger.debug(f"MCP request: {method}")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                        "prompts": {"listChanged": False}
                    },
                    "serverInfo": {
                        "name": "ddg-search-k8s",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "initialized":
            # Notification, no response needed
            return {"status": "ok"}
        
        elif method == "tools/list":
            tools_info = await list_tools()
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": tools_info
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "search":
                query = arguments.get("query")
                max_results = arguments.get("max_results", 10)
                
                if not query:
                    raise HTTPException(status_code=400, detail="Query parameter is required")
                
                result = await searcher.search(query, max_results)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": result}]
                    }
                }
            
            elif tool_name == "fetch_content":
                url = arguments.get("url")
                
                if not url:
                    raise HTTPException(status_code=400, detail="URL parameter is required")
                
                result = await fetcher.fetch_content(url)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": result}]
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Unknown method: {method}"}
            }
            
    except Exception as e:
        logger.error(f"Error in MCP endpoint: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {"code": -32603, "message": str(e)}
        }

@app.post("/search")
async def search_endpoint(request: Dict[str, Any]):
    """Direct search endpoint"""
    try:
        query = request.get("query")
        max_results = request.get("max_results", 10)
        
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        result = await searcher.search(query, max_results)
        return {"result": result}
        
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fetch")
async def fetch_content_endpoint(request: Dict[str, Any]):
    """Direct content fetch endpoint"""
    try:
        url = request.get("url")
        
        if not url:
            raise HTTPException(status_code=400, detail="URL parameter is required")
        
        result = await fetcher.fetch_content(url)
        return {"result": result}
        
    except Exception as e:
        logger.error(f"Error in fetch endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Track start time for metrics
start_time = datetime.now()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8081))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting Standalone DuckDuckGo MCP Server on {host}:{port}")
    logger.info("Kubernetes-ready with health checks and metrics")
    
    uvicorn.run(app, host=host, port=port, log_level=log_level.lower())
