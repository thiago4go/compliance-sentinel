#!/bin/bash

# Set up environment
echo "Setting up environment..."
cd "$(dirname "$0")"
source ../.env

# Check if Dapr is installed
if ! command -v dapr &> /dev/null; then
    echo "Error: Dapr CLI not found. Please install Dapr first."
    echo "Visit https://docs.dapr.io/getting-started/install-dapr-cli/"
    exit 1
fi

# Check if Dapr is initialized
if ! dapr status 2>/dev/null | grep -q "dapr-placement"; then
    echo "Initializing Dapr..."
    dapr init -s
    echo "Waiting for Dapr to initialize..."
    sleep 10
fi

# Create a virtual environment if it doesn't exist
if [ ! -d "venv_frontend" ]; then
    echo "Creating virtual environment for frontend..."
    python3 -m venv venv_frontend
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv_frontend/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r frontend/requirements.txt

# Start the frontend with Dapr
echo "Starting Chainlit frontend with Dapr..."
cd frontend
dapr run --app-id chainlit-frontend \
         --app-port 8000 \
         --dapr-http-port 3502 \
         --resources-path ../dapr \
         -- chainlit run chainlit_frontend.py

# Deactivate virtual environment when done
deactivate
