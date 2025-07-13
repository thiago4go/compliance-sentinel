#!/usr/bin/env python3
"""
Test script for remote MCP server at http://138.3.218.137/ddg/mcp
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the dapr-agents path
sys.path.append('/workspaces/compliance-sentinel/dapr-agents')

from dapr_agents import Agent
from dapr_agents.tool.mcp import MCPClient

load_dotenv('/workspaces/compliance-sentinel/dapr-agents/quickstarts/02_llm_call_open_ai/.env')

async def test_remote_mcp_server():
    """Test connection to remote MCP server"""
    print("🔍 Testing remote MCP server at http://138.3.218.137/ddg/mcp")
    
    try:
        client = MCPClient()
        
        # Try to connect to the remote MCP server
        print("📡 Attempting to connect via streamable HTTP...")
        await client.connect_streamable_http(
            server_name="remote_ddg",
            url="http://138.3.218.137/ddg/mcp"
        )
        
        # Get available tools
        tools = client.get_all_tools()
        print(f"🔧 Available tools from remote server: {[t.name for t in tools]}")
        
        if tools:
            # Create agent with remote tools
            search_agent = Agent(
                name="SearchBot",
                role="Search Assistant", 
                goal="Help users search the web using remote MCP tools",
                instructions=[
                    "Use the available search tools to help users find information",
                    "Provide clear and helpful responses based on search results"
                ],
                tools=tools
            )
            
            # Test a search query
            print("🔍 Testing search query...")
            result = await search_agent.run("Search for information about Dapr agents")
            print(f"📝 Search result: {result}")
            
        await client.close()
        print("✅ Remote MCP server test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing remote MCP server: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

async def test_local_http_streaming():
    """Test local HTTP streaming MCP server"""
    print("\n🔍 Testing local HTTP streaming MCP server")
    
    try:
        client = MCPClient()
        
        # Connect to local HTTP streaming server
        print("📡 Attempting to connect to local HTTP streaming server...")
        await client.connect_streamable_http(
            server_name="local_http",
            url="http://localhost:8002/mcp/"
        )
        
        tools = client.get_all_tools()
        print(f"🔧 Available tools from local HTTP server: {[t.name for t in tools]}")
        
        if tools:
            agent = Agent(
                name="LocalBot",
                role="Local Assistant",
                tools=tools
            )
            
            result = await agent.run("What's the weather in Paris?")
            print(f"📝 Local HTTP result: {result}")
            
        await client.close()
        print("✅ Local HTTP streaming test completed!")
        
    except Exception as e:
        print(f"❌ Error testing local HTTP streaming: {e}")

if __name__ == "__main__":
    asyncio.run(test_remote_mcp_server())
    asyncio.run(test_local_http_streaming())
