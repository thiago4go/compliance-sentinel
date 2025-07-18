"""
Enhanced DurableAgent initialization with retry logic and health checks.
"""
import asyncio
import logging
import time
from typing import Optional
import httpx
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DurableAgentManager:
    """Manages DurableAgent lifecycle with proper initialization timing."""
    
    def __init__(self, dapr_http_port: int = 3500, max_retries: int = 5, retry_delay: float = 2.0):
        self.dapr_http_port = dapr_http_port
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.durable_agent = None
        self.is_initialized = False
        
    async def wait_for_dapr_health(self) -> bool:
        """Wait for Dapr runtime to be healthy and components loaded."""
        dapr_url = f"http://localhost:{self.dapr_http_port}"
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    # Check Dapr health
                    health_response = await client.get(f"{dapr_url}/v1.0/healthz")
                    if health_response.status_code != 200:
                        logger.warning(f"Dapr health check failed (attempt {attempt + 1}): {health_response.status_code}")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    
                    # Verify state store is accessible
                    try:
                        state_response = await client.get(f"{dapr_url}/v1.0/state/workflowstatestore/health-check")
                        logger.info(f"State store health check: {state_response.status_code}")
                    except Exception as e:
                        logger.warning(f"State store check failed (attempt {attempt + 1}): {e}")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    
                    # Check if actor runtime is ready
                    try:
                        metadata_response = await client.get(f"{dapr_url}/v1.0/metadata")
                        if metadata_response.status_code == 200:
                            metadata = metadata_response.json()
                            actors_enabled = any(
                                component.get("type") == "state.redis" and 
                                component.get("name") == "agentstatestore"
                                for component in metadata.get("components", [])
                            )
                            if not actors_enabled:
                                logger.warning(f"Actor state store not found in metadata (attempt {attempt + 1})")
                                await asyncio.sleep(self.retry_delay)
                                continue
                    except Exception as e:
                        logger.warning(f"Metadata check failed (attempt {attempt + 1}): {e}")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    
                    logger.info("Dapr runtime is healthy and components are loaded")
                    return True
                    
            except Exception as e:
                logger.warning(f"Dapr health check failed (attempt {attempt + 1}): {e}")
                await asyncio.sleep(self.retry_delay)
        
        logger.error(f"Dapr health check failed after {self.max_retries} attempts")
        return False
    
    async def initialize_durable_agent(self) -> bool:
        """Initialize DurableAgent with proper error handling."""
        if self.is_initialized:
            return True
            
        try:
            # Wait for Dapr to be ready
            if not await self.wait_for_dapr_health():
                logger.error("Cannot initialize DurableAgent: Dapr is not healthy")
                return False
            
            # Import and initialize DurableAgent
            # Replace this with your actual DurableAgent import and initialization
            from your_durable_agent_module import DurableAgent, ConversationDaprStateMemory
            
            # Initialize with proper configuration
            memory = ConversationDaprStateMemory(
                dapr_client_address=f"http://localhost:{self.dapr_http_port}",
                state_store_name="agentstatestore"
            )
            
            self.durable_agent = DurableAgent(
                memory=memory,
                instructions="You are a compliance harvester agent...",
                # Add other configuration as needed
            )
            
            # Test the agent with a simple operation
            await self._test_agent_functionality()
            
            self.is_initialized = True
            logger.info("DurableAgent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize DurableAgent: {e}")
            return False
    
    async def _test_agent_functionality(self):
        """Test basic agent functionality to ensure it's working."""
        if not self.durable_agent:
            raise RuntimeError("DurableAgent not initialized")
        
        # Perform a simple test operation
        # Replace with appropriate test for your DurableAgent
        try:
            # Example: test state persistence
            test_result = await self.durable_agent.test_connection()
            logger.info(f"DurableAgent test successful: {test_result}")
        except Exception as e:
            logger.warning(f"DurableAgent test failed: {e}")
            raise
    
    async def get_agent(self):
        """Get the DurableAgent instance, initializing if necessary."""
        if not self.is_initialized:
            success = await self.initialize_durable_agent()
            if not success:
                raise RuntimeError("DurableAgent initialization failed")
        
        return self.durable_agent
    
    async def shutdown(self):
        """Gracefully shutdown the DurableAgent."""
        if self.durable_agent:
            try:
                await self.durable_agent.close()
                logger.info("DurableAgent shutdown completed")
            except Exception as e:
                logger.error(f"Error during DurableAgent shutdown: {e}")
        
        self.is_initialized = False
        self.durable_agent = None

# Global instance
durable_agent_manager = DurableAgentManager()

@asynccontextmanager
async def get_durable_agent():
    """Context manager for getting DurableAgent with proper lifecycle management."""
    try:
        agent = await durable_agent_manager.get_agent()
        yield agent
    except Exception as e:
        logger.error(f"Error getting DurableAgent: {e}")
        raise
