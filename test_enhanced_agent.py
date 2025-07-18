#!/usr/bin/env python3
"""
Comprehensive testing script for the enhanced compliance harvester agent.
"""
import asyncio
import json
import logging
import time
from typing import Dict, Any

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentTester:
    """Test suite for the compliance harvester agent."""
    
    def __init__(self, base_url: str = "http://localhost:9180", dapr_url: str = "http://localhost:3500"):
        self.base_url = base_url
        self.dapr_url = dapr_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "PASS" if success else "FAIL"
        logger.info(f"[{status}] {test_name}: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        })
    
    async def test_dapr_health(self) -> bool:
        """Test Dapr health endpoint."""
        try:
            response = await self.client.get(f"{self.dapr_url}/v1.0/healthz")
            success = response.status_code == 200
            self.log_test_result("Dapr Health Check", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test_result("Dapr Health Check", False, f"Error: {e}")
            return False
    
    async def test_dapr_metadata(self) -> bool:
        """Test Dapr metadata endpoint."""
        try:
            response = await self.client.get(f"{self.dapr_url}/v1.0/metadata")
            if response.status_code == 200:
                metadata = response.json()
                components = metadata.get("components", [])
                
                # Check for required components
                required_components = ["workflowstatestore", "agentstatestore"]
                found_components = [comp["name"] for comp in components]
                
                missing = [comp for comp in required_components if comp not in found_components]
                
                if not missing:
                    self.log_test_result("Dapr Metadata Check", True, f"All required components found: {found_components}")
                    return True
                else:
                    self.log_test_result("Dapr Metadata Check", False, f"Missing components: {missing}")
                    return False
            else:
                self.log_test_result("Dapr Metadata Check", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Dapr Metadata Check", False, f"Error: {e}")
            return False
    
    async def test_state_store_access(self) -> bool:
        """Test state store accessibility."""
        stores = ["workflowstatestore", "agentstatestore"]
        all_success = True
        
        for store in stores:
            try:
                # Test write
                test_data = [{"key": "test-key", "value": "test-value"}]
                write_response = await self.client.post(
                    f"{self.dapr_url}/v1.0/state/{store}",
                    json=test_data
                )
                
                if write_response.status_code not in [200, 204]:
                    self.log_test_result(f"State Store Write ({store})", False, f"Status: {write_response.status_code}")
                    all_success = False
                    continue
                
                # Test read
                read_response = await self.client.get(f"{self.dapr_url}/v1.0/state/{store}/test-key")
                
                if read_response.status_code == 200:
                    data = read_response.json()
                    if data == "test-value":
                        self.log_test_result(f"State Store Access ({store})", True, "Read/Write successful")
                    else:
                        self.log_test_result(f"State Store Access ({store})", False, f"Data mismatch: {data}")
                        all_success = False
                else:
                    self.log_test_result(f"State Store Access ({store})", False, f"Read failed: {read_response.status_code}")
                    all_success = False
                
                # Cleanup
                await self.client.delete(f"{self.dapr_url}/v1.0/state/{store}/test-key")
                
            except Exception as e:
                self.log_test_result(f"State Store Access ({store})", False, f"Error: {e}")
                all_success = False
        
        return all_success
    
    async def test_app_health(self) -> bool:
        """Test application health endpoint."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                
                # Check health status
                status = health_data.get("status")
                dapr_connected = health_data.get("dapr_connected", False)
                
                success = status == "healthy" and dapr_connected
                details = f"Status: {status}, Dapr Connected: {dapr_connected}, Agent Initialized: {health_data.get('agent_initialized', False)}"
                
                self.log_test_result("Application Health", success, details)
                return success
            else:
                self.log_test_result("Application Health", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Application Health", False, f"Error: {e}")
            return False
    
    async def test_insights_generation(self) -> bool:
        """Test compliance insights generation."""
        try:
            request_data = {
                "query": "What are the key data privacy compliance requirements?",
                "max_insights": 3
            }
            
            response = await self.client.post(f"{self.base_url}/insights", json=request_data)
            
            if response.status_code == 200:
                insights_data = response.json()
                
                success = insights_data.get("success", False)
                insights = insights_data.get("insights", [])
                fallback_used = insights_data.get("fallback_used", False)
                
                details = f"Success: {success}, Insights Count: {len(insights)}, Fallback Used: {fallback_used}"
                
                # Validate insight structure
                if insights:
                    first_insight = insights[0]
                    required_fields = ["insight_id", "title", "description", "severity", "created_at"]
                    missing_fields = [field for field in required_fields if field not in first_insight]
                    
                    if missing_fields:
                        details += f", Missing Fields: {missing_fields}"
                        success = False
                
                self.log_test_result("Insights Generation", success, details)
                return success
            else:
                self.log_test_result("Insights Generation", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Insights Generation", False, f"Error: {e}")
            return False
    
    async def test_search_functionality(self) -> bool:
        """Test search functionality."""
        try:
            request_data = {
                "query": "compliance frameworks",
                "limit": 5
            }
            
            response = await self.client.post(f"{self.base_url}/search", json=request_data)
            
            if response.status_code == 200:
                search_data = response.json()
                
                success = search_data.get("success", False)
                results = search_data.get("results", [])
                fallback_used = search_data.get("fallback_used", False)
                
                details = f"Success: {success}, Results Count: {len(results)}, Fallback Used: {fallback_used}"
                
                self.log_test_result("Search Functionality", success, details)
                return success
            else:
                self.log_test_result("Search Functionality", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Search Functionality", False, f"Error: {e}")
            return False
    
    async def test_agent_status(self) -> bool:
        """Test agent status endpoint."""
        try:
            response = await self.client.get(f"{self.base_url}/agent/status")
            
            if response.status_code == 200:
                status_data = response.json()
                
                dapr_connected = status_data.get("dapr_connected", False)
                agent_type = status_data.get("agent_type", "Unknown")
                
                success = dapr_connected
                details = f"Dapr Connected: {dapr_connected}, Agent Type: {agent_type}"
                
                self.log_test_result("Agent Status", success, details)
                return success
            else:
                self.log_test_result("Agent Status", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Agent Status", False, f"Error: {e}")
            return False
    
    async def test_agent_reinitialization(self) -> bool:
        """Test agent reinitialization."""
        try:
            response = await self.client.post(f"{self.base_url}/agent/reinitialize")
            
            if response.status_code == 200:
                reinit_data = response.json()
                
                success = reinit_data.get("success", False)
                message = reinit_data.get("message", "")
                
                self.log_test_result("Agent Reinitialization", success, message)
                return success
            else:
                self.log_test_result("Agent Reinitialization", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Agent Reinitialization", False, f"Error: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return summary."""
        logger.info("Starting comprehensive test suite...")
        
        # Infrastructure tests
        await self.test_dapr_health()
        await self.test_dapr_metadata()
        await self.test_state_store_access()
        
        # Application tests
        await self.test_app_health()
        await self.test_agent_status()
        
        # Functionality tests
        await self.test_insights_generation()
        await self.test_search_functionality()
        
        # Management tests
        await self.test_agent_reinitialization()
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "results": self.test_results
        }
        
        logger.info(f"Test Summary: {passed_tests}/{total_tests} tests passed ({summary['success_rate']:.1f}%)")
        
        if failed_tests > 0:
            logger.warning("Failed tests:")
            for result in self.test_results:
                if not result["success"]:
                    logger.warning(f"  - {result['test']}: {result['details']}")
        
        return summary

async def main():
    """Main test execution."""
    print("=== Compliance Harvester Agent Test Suite ===")
    
    # Wait for services to be ready
    print("Waiting for services to be ready...")
    await asyncio.sleep(5)
    
    async with AgentTester() as tester:
        summary = await tester.run_all_tests()
        
        print("\n=== Test Results Summary ===")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        # Save detailed results
        with open("test_results.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        print("\nDetailed results saved to test_results.json")
        
        # Exit with appropriate code
        exit_code = 0 if summary['failed'] == 0 else 1
        return exit_code

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
