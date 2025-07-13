#!/bin/bash

# Final working setup for Adaptive Interface with Chainlit + Dapr
# Uses ports 9150-9152 as requested

echo "🚀 Starting Adaptive Compliance Interface"
echo "📍 Chainlit Frontend: http://localhost:9150"
echo "📍 Dapr HTTP API: http://localhost:9151"
echo "📍 Dapr gRPC API: http://localhost:9152"
echo ""

# Set environment to disable telemetry issues
export LITERAL_API_KEY=""
export LITERAL_DISABLE="true"

# Kill any existing processes
pkill -f "chainlit.*working-chainlit-app" 2>/dev/null || true
pkill -f "dapr.*adaptive-interface" 2>/dev/null || true

echo "🔧 Starting Dapr + Chainlit integration..."

# Run with Dapr
dapr run \
    --app-id adaptive-interface \
    --app-port 9150 \
    --dapr-http-port 9151 \
    --dapr-grpc-port 9152 \
    --resources-path ./dapr/components-minimal/ \
    -- chainlit run working-chainlit-app.py --port 9150 --host 0.0.0.0