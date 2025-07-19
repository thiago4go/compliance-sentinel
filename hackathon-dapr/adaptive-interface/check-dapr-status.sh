#!/bin/bash

echo "Checking Dapr status..."

# Check if Dapr CLI is installed
if ! command -v dapr &> /dev/null; then
    echo "❌ Dapr CLI not found. Please install Dapr first."
    echo "Visit https://docs.dapr.io/getting-started/install-dapr-cli/"
    exit 1
else
    echo "✅ Dapr CLI is installed"
fi

# Check if Dapr is initialized - without requiring Kubernetes flag
if ! dapr status 2>/dev/null | grep -q "dapr-placement"; then
    echo "❌ Dapr is not initialized. Please run 'dapr init' first."
    exit 1
else
    echo "✅ Dapr is initialized"
    # Just show the status without requiring the -k flag
    dapr status 2>/dev/null || echo "Dapr is running in standalone mode"
fi

# Check if Redis is running (used by Dapr components)
if ! nc -z localhost 6379 &> /dev/null; then
    echo "❌ Redis is not running. It should be started by Dapr init."
    echo "Try running 'dapr init' again or start Redis manually."
    exit 1
else
    echo "✅ Redis is running on localhost:6379"
fi

echo "All checks passed! You can now run the backend and frontend services."
