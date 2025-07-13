import asyncio
import logging
from dapr_agents.tool.mcp import MCPClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mcp_connection():
    """Test MCP connection and DuckDuckGo search"""
    try:
        logger.info("🌐 Testing MCP connection...")
        
        # Create MCP client
        mcp_client = MCPClient()
        
        # Connect to DuckDuckGo MCP server
        await mcp_client.connect_streamable_http(
            server_name="duckduckgo",
            url="http://138.3.218.137/ddg/mcp"
        )
        
        # Get available tools
        tools = mcp_client.get_all_tools()
        logger.info(f"✅ Connected! Found {len(tools)} tools:")
        
        for tool in tools:
            logger.info(f"  📋 {tool.name}: {tool.description}")
        
        # Test DuckDuckGo search
        if tools:
            search_tool = None
            for tool in tools:
                if "search" in tool.name.lower():
                    search_tool = tool
                    break
            
            if search_tool:
                logger.info(f"🔍 Testing search with tool: {search_tool.name}")
                
                # Execute search
                result = await search_tool.execute(query="Python programming language")
                logger.info(f"✅ Search result: {str(result)[:200]}...")
                
                return True, result
            else:
                logger.warning("⚠️ No search tool found")
                return False, "No search tool available"
        
    except Exception as e:
        logger.error(f"❌ MCP test failed: {e}")
        return False, str(e)

if __name__ == "__main__":
    success, result = asyncio.run(test_mcp_connection())
    if success:
        print("🎉 MCP connection and search test PASSED!")
        print(f"Result preview: {str(result)[:300]}...")
    else:
        print(f"❌ MCP test FAILED: {result}")
