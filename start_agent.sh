#!/bin/bash

# Compliance Harvester Agent Startup Script
# This script ensures proper initialization timing between Dapr and the agent

set -e

echo "Starting Compliance Harvester Agent with proper initialization timing..."

# Configuration
DAPR_HTTP_PORT=${DAPR_HTTP_PORT:-3500}
DAPR_GRPC_PORT=${DAPR_GRPC_PORT:-50001}
APP_PORT=${APP_PORT:-9180}
APP_ID=${APP_ID:-harvester-agent}
COMPONENTS_PATH=${COMPONENTS_PATH:-./components}
MAX_WAIT_TIME=${MAX_WAIT_TIME:-60}

# Function to check if Dapr is healthy
check_dapr_health() {
    local max_attempts=30
    local attempt=1
    
    echo "Checking Dapr health..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:${DAPR_HTTP_PORT}/v1.0/healthz" > /dev/null 2>&1; then
            echo "Dapr is healthy (attempt $attempt)"
            return 0
        fi
        
        echo "Waiting for Dapr to be healthy (attempt $attempt/$max_attempts)..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "ERROR: Dapr failed to become healthy after $max_attempts attempts"
    return 1
}

# Function to check if state stores are accessible
check_state_stores() {
    local stores=("workflowstatestore" "agentstatestore")
    
    echo "Checking state store accessibility..."
    
    for store in "${stores[@]}"; do
        echo "Testing state store: $store"
        
        # Try to write and read a test value
        if curl -s -X POST "http://localhost:${DAPR_HTTP_PORT}/v1.0/state/${store}" \
           -H "Content-Type: application/json" \
           -d '[{"key":"health-check","value":"ok"}]' > /dev/null 2>&1; then
            
            if curl -s "http://localhost:${DAPR_HTTP_PORT}/v1.0/state/${store}/health-check" > /dev/null 2>&1; then
                echo "State store $store is accessible"
                
                # Clean up test data
                curl -s -X DELETE "http://localhost:${DAPR_HTTP_PORT}/v1.0/state/${store}/health-check" > /dev/null 2>&1
            else
                echo "WARNING: State store $store is not readable"
                return 1
            fi
        else
            echo "WARNING: State store $store is not writable"
            return 1
        fi
    done
    
    return 0
}

# Function to check actor runtime status
check_actor_runtime() {
    echo "Checking actor runtime status..."
    
    if curl -s "http://localhost:${DAPR_HTTP_PORT}/v1.0/metadata" | grep -q "agentstatestore"; then
        echo "Actor state store is configured"
        return 0
    else
        echo "WARNING: Actor state store not found in metadata"
        return 1
    fi
}

# Function to start Dapr sidecar
start_dapr() {
    echo "Starting Dapr sidecar..."
    
    dapr run \
        --app-id "$APP_ID" \
        --app-port "$APP_PORT" \
        --dapr-http-port "$DAPR_HTTP_PORT" \
        --dapr-grpc-port "$DAPR_GRPC_PORT" \
        --components-path "$COMPONENTS_PATH" \
        --log-level info \
        --enable-metrics \
        --metrics-port 9090 &
    
    DAPR_PID=$!
    echo "Dapr started with PID: $DAPR_PID"
    
    # Wait for Dapr to be ready
    if ! check_dapr_health; then
        echo "ERROR: Dapr failed to start properly"
        kill $DAPR_PID 2>/dev/null || true
        exit 1
    fi
    
    # Additional checks
    sleep 5  # Give components time to initialize
    
    if ! check_state_stores; then
        echo "ERROR: State stores are not accessible"
        kill $DAPR_PID 2>/dev/null || true
        exit 1
    fi
    
    if ! check_actor_runtime; then
        echo "WARNING: Actor runtime may not be properly configured"
    fi
    
    echo "Dapr is ready and all components are accessible"
}

# Function to start the application
start_application() {
    echo "Starting Compliance Harvester Agent application..."
    
    # Set environment variables for the application
    export DAPR_HTTP_PORT
    export DAPR_GRPC_PORT
    export APP_PORT
    
    # Start the Python application
    python enhanced_harvester_agent.py &
    APP_PID=$!
    echo "Application started with PID: $APP_PID"
    
    # Wait a bit and check if the application is responding
    sleep 10
    
    if curl -s -f "http://localhost:${APP_PORT}/health" > /dev/null 2>&1; then
        echo "Application is responding to health checks"
    else
        echo "WARNING: Application may not be responding properly"
    fi
}

# Function to handle cleanup on exit
cleanup() {
    echo "Cleaning up processes..."
    
    if [ ! -z "$APP_PID" ]; then
        echo "Stopping application (PID: $APP_PID)"
        kill $APP_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$DAPR_PID" ]; then
        echo "Stopping Dapr (PID: $DAPR_PID)"
        kill $DAPR_PID 2>/dev/null || true
    fi
    
    # Wait for processes to stop
    sleep 2
    
    echo "Cleanup completed"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Main execution
main() {
    echo "=== Compliance Harvester Agent Startup ==="
    echo "Configuration:"
    echo "  App ID: $APP_ID"
    echo "  App Port: $APP_PORT"
    echo "  Dapr HTTP Port: $DAPR_HTTP_PORT"
    echo "  Dapr gRPC Port: $DAPR_GRPC_PORT"
    echo "  Components Path: $COMPONENTS_PATH"
    echo ""
    
    # Check prerequisites
    if ! command -v dapr &> /dev/null; then
        echo "ERROR: Dapr CLI is not installed"
        exit 1
    fi
    
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python is not installed"
        exit 1
    fi
    
    # Start Dapr first
    start_dapr
    
    # Start the application
    start_application
    
    echo ""
    echo "=== Compliance Harvester Agent is running ==="
    echo "Application URL: http://localhost:$APP_PORT"
    echo "Health Check: http://localhost:$APP_PORT/health"
    echo "Dapr Dashboard: http://localhost:8080 (if running)"
    echo ""
    echo "Press Ctrl+C to stop..."
    
    # Wait for processes
    wait
}

# Run main function
main "$@"
