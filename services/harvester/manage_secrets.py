#!/usr/bin/env python3
"""
Secrets Management Utility for Diagrid Catalyst
Stores and retrieves sensitive configuration from KV store
"""

import os
import asyncio
import json
from typing import Dict, Any, Optional
from dapr.clients import DaprClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SecretsManager:
    """Manages secrets and configuration in Diagrid KV store"""
    
    def __init__(self):
        self.dapr_http_endpoint = os.getenv("DAPR_HTTP_ENDPOINT")
        self.dapr_grpc_endpoint = os.getenv("DAPR_GRPC_ENDPOINT") 
        self.app_id = os.getenv("DAPR_APP_ID", "harvester-agent")
        self.store_name = "agent-kv-store"
        
    def _get_dapr_client(self) -> DaprClient:
        """Get configured Dapr client"""
        if self.dapr_grpc_endpoint:
            # Extract host and port from gRPC endpoint
            endpoint = self.dapr_grpc_endpoint.replace("https://", "").replace("http://", "")
            if ":" in endpoint:
                host, port = endpoint.split(":")
                port = int(port)
            else:
                host = endpoint
                port = 443 if "https" in self.dapr_grpc_endpoint else 80
                
            return DaprClient(address=f"{host}:{port}")
        else:
            return DaprClient()
    
    def set_secret(self, key: str, value: str) -> bool:
        """Store a secret in the KV store"""
        try:
            with self._get_dapr_client() as client:
                client.save_state(
                    store_name=self.store_name,
                    key=f"secrets/{key}",
                    value=value
                )
                print(f"✓ Secret '{key}' stored successfully")
                return True
        except Exception as e:
            print(f"✗ Error storing secret '{key}': {e}")
            return False
    
    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret from the KV store"""
        try:
            with self._get_dapr_client() as client:
                result = client.get_state(
                    store_name=self.store_name,
                    key=f"secrets/{key}"
                )
                if result.data:
                    return result.data.decode('utf-8')
                return None
        except Exception as e:
            print(f"✗ Error retrieving secret '{key}': {e}")
            return None
    
    def set_config(self, key: str, value: Any) -> bool:
        """Store configuration in the KV store"""
        try:
            with self._get_dapr_client() as client:
                # Convert value to JSON string if it's not already a string
                if not isinstance(value, str):
                    value = json.dumps(value)
                    
                client.save_state(
                    store_name=self.store_name,
                    key=f"config/{key}",
                    value=value
                )
                print(f"✓ Config '{key}' stored successfully")
                return True
        except Exception as e:
            print(f"✗ Error storing config '{key}': {e}")
            return False
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Retrieve configuration from the KV store"""
        try:
            with self._get_dapr_client() as client:
                result = client.get_state(
                    store_name=self.store_name,
                    key=f"config/{key}"
                )
                if result.data:
                    value = result.data.decode('utf-8')
                    # Try to parse as JSON, fallback to string
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
                return default
        except Exception as e:
            print(f"✗ Error retrieving config '{key}': {e}")
            return default
    
    def list_secrets(self) -> Dict[str, str]:
        """List all stored secrets (keys only, not values)"""
        # This would require a more complex implementation
        # For now, return known secret keys
        known_secrets = [
            "openrouter-api-key",
            "mcp-api-token"
        ]
        
        secrets = {}
        for secret_key in known_secrets:
            value = self.get_secret(secret_key)
            secrets[secret_key] = "***HIDDEN***" if value else "NOT_SET"
        
        return secrets
    
    def setup_default_config(self):
        """Set up default configuration values"""
        configs = {
            "openrouter-model": "openai/gpt-4o",
            "mcp-server-url": "http://138.3.218.137/ddg/mcp",
            "agent-max-results": 10,
            "agent-session-timeout": 3600,
            "log-level": "INFO",
            "app-port": 8000,
            "app-host": "0.0.0.0"
        }
        
        print("Setting up default configuration...")
        for key, value in configs.items():
            self.set_config(key, value)
        
        print("✓ Default configuration setup complete")

def main():
    """Main function for command-line usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_secrets.py set-secret <key> <value>")
        print("  python manage_secrets.py get-secret <key>")
        print("  python manage_secrets.py set-config <key> <value>")
        print("  python manage_secrets.py get-config <key>")
        print("  python manage_secrets.py list-secrets")
        print("  python manage_secrets.py setup-defaults")
        return
    
    manager = SecretsManager()
    command = sys.argv[1]
    
    if command == "set-secret" and len(sys.argv) == 4:
        key, value = sys.argv[2], sys.argv[3]
        manager.set_secret(key, value)
    
    elif command == "get-secret" and len(sys.argv) == 3:
        key = sys.argv[2]
        value = manager.get_secret(key)
        print(f"{key}: {value if value else 'NOT_SET'}")
    
    elif command == "set-config" and len(sys.argv) == 4:
        key, value = sys.argv[2], sys.argv[3]
        manager.set_config(key, value)
    
    elif command == "get-config" and len(sys.argv) == 3:
        key = sys.argv[2]
        value = manager.get_config(key)
        print(f"{key}: {value}")
    
    elif command == "list-secrets":
        secrets = manager.list_secrets()
        print("Stored secrets:")
        for key, status in secrets.items():
            print(f"  {key}: {status}")
    
    elif command == "setup-defaults":
        manager.setup_default_config()
    
    else:
        print("Invalid command or arguments")

if __name__ == "__main__":
    main()
