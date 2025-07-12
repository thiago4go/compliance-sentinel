#!/usr/bin/env python3
"""
Setup script to transfer API keys from .env file to Diagrid KV store
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path to import manage_secrets
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manage_secrets import SecretsManager

def setup_secrets_from_env():
    """Transfer secrets from .env file to KV store"""
    
    # Load environment variables from root .env file
    env_path = "/workspaces/compliance-sentinel/.env"
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✓ Loaded environment variables from {env_path}")
    else:
        print(f"⚠ No .env file found at {env_path}")
        return False
    
    # Set up Catalyst environment for secrets manager
    os.environ["DAPR_HTTP_ENDPOINT"] = "https://http-prj374625.api.cloud.diagrid.io:443"
    os.environ["DAPR_GRPC_ENDPOINT"] = "https://grpc-prj374625.api.cloud.diagrid.io:443"
    os.environ["DAPR_APP_ID"] = "harvester-agent"
    os.environ["DAPR_API_TOKEN"] = "diagrid://v1/1a42bad8-9d7f-4294-b190-b7d741db900f/374625/darp-lite/harvester-agent/7939927c-7f94-4062-a074-a08b83332675"
    
    # Initialize secrets manager
    manager = SecretsManager()
    
    # Transfer secrets from environment to KV store
    secrets_to_transfer = {
        "openrouter-api-key": os.getenv("OPENROUTER_API_KEY"),
        "openai-api-key-harvester": os.getenv("OPENAI_API_KEY_HARVESTER"),
    }
    
    print("\n🔐 Transferring secrets to KV store...")
    
    success_count = 0
    for secret_name, secret_value in secrets_to_transfer.items():
        if secret_value:
            if manager.set_secret(secret_name, secret_value):
                success_count += 1
                print(f"✓ Transferred {secret_name}")
            else:
                print(f"✗ Failed to transfer {secret_name}")
        else:
            print(f"⚠ No value found for {secret_name}")
    
    # Set up configuration values
    print("\n⚙️ Setting up configuration...")
    
    configs = {
        "openrouter-model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o"),
        "mcp-server-url": "http://138.3.218.137/ddg/mcp",
        "agent-max-results": 10,
        "agent-session-timeout": 3600,
        "log-level": "INFO",
        "app-port": 8000,
        "app-host": "0.0.0.0"
    }
    
    config_success = 0
    for config_name, config_value in configs.items():
        if manager.set_config(config_name, config_value):
            config_success += 1
    
    print(f"\n📊 Summary:")
    print(f"✓ Secrets transferred: {success_count}/{len(secrets_to_transfer)}")
    print(f"✓ Configurations set: {config_success}/{len(configs)}")
    
    # Verify the setup
    print(f"\n🔍 Verifying stored secrets...")
    stored_secrets = manager.list_secrets()
    for secret_name, status in stored_secrets.items():
        print(f"  {secret_name}: {status}")
    
    return success_count > 0

if __name__ == "__main__":
    print("🚀 Setting up secrets in Diagrid KV store...")
    
    if setup_secrets_from_env():
        print("\n✅ Secrets setup completed successfully!")
        print("\n💡 Next steps:")
        print("1. Your API keys are now securely stored in Diagrid KV store")
        print("2. You can remove them from .env files for better security")
        print("3. The agent will automatically load them from KV store")
    else:
        print("\n❌ Secrets setup failed!")
        print("Please check your environment configuration and try again.")
