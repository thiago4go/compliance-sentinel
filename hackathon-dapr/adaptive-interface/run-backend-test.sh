#!/bin/bash

# Set up environment
echo "Setting up environment..."
cd "$(dirname "$0")"
ENV_FILE="../.env"
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment from $ENV_FILE"
    source "$ENV_FILE"
else
    echo "Error: $ENV_FILE not found!"
    exit 1
fi

# Check if OpenAI API key is available
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY not found in .env file"
    exit 1
fi

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

# Check if scheduler is running
if ! pgrep -f "scheduler" > /dev/null; then
    echo "Starting Dapr scheduler..."
    ~/.dapr/bin/scheduler > /dev/null 2>&1 &
    SCHEDULER_PID=$!
    echo "Scheduler started with PID: $SCHEDULER_PID"
    sleep 2
fi

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r backend/requirements.txt

# Start the compliance agent service with Dapr
echo "Starting compliance agent service with Dapr..."
cd backend
dapr run --app-id compliance-agent-backend \
         --app-port 9160 \
         --dapr-http-port 3501 \
         --resources-path ../dapr \
         -- python3 compliance_agent_service.py &
COMPLIANCE_PID=$!

# Wait for the compliance service to start
echo "Waiting for compliance service to start..."
sleep 5

# Start the main backend service with Dapr
echo "Starting main backend service with Dapr..."
dapr run --app-id adaptive-interface-backend \
         --app-port 9161 \
         --dapr-http-port 3500 \
         --resources-path ../dapr \
         -- python3 main.py &
MAIN_PID=$!

# Function to handle cleanup
cleanup() {
    echo "Stopping services..."
    kill $COMPLIANCE_PID $MAIN_PID $SCHEDULER_PID 2>/dev/null
    deactivate  # Deactivate virtual environment
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

# Keep script running
echo "Services are running. Press Ctrl+C to stop."
wait
