#!/bin/bash

# Start the microservices architecture
# Backend service (port 9160) + Frontend service (port 9150)
# Both with Dapr sidecars for service mesh communication

echo "🚀 Starting Adaptive Compliance Interface - Microservices Architecture"
echo ""

# Check if dapr is installed
if ! command -v dapr &> /dev/null; then
    echo "❌ Dapr CLI not found. Please install Dapr first:"
    echo "   https://docs.dapr.io/getting-started/install-dapr-cli/"
    exit 1
fi

# Check if components directory exists
if [ ! -d "./dapr/components-minimal" ]; then
    echo "❌ Dapr components directory not found: ./dapr/components-minimal"
    exit 1
fi

echo "📋 Starting services:"
echo "   🔧 Backend: compliance-agent-backend (port 9160)"
echo "   🌐 Frontend: adaptive-interface (port 9150)"
echo "   🔗 Dapr: Service mesh communication"
echo ""

# Start backend service in background
echo "🔧 Starting backend service..."
dapr run \
    --app-id compliance-agent-backend \
    --app-port 9160 \
    --dapr-http-port 9161 \
    --dapr-grpc-port 9162 \
    --resources-path ./dapr/components-minimal/ \
    -- python backend/compliance_agent_service.py &

BACKEND_PID=$!

# Wait a moment for backend to start
sleep 5

# Start frontend service in background
echo "🌐 Starting frontend service..."
dapr run \
    --app-id adaptive-interface \
    --app-port 9150 \
    --dapr-http-port 9151 \
    --dapr-grpc-port 9152 \
    --resources-path ./dapr/components-minimal/ \
    -- chainlit run frontend/chainlit_frontend.py --port 9150 --host 0.0.0.0 &

FRONTEND_PID=$!

echo ""
echo "✅ Services started successfully!"
echo ""
echo "🌐 Frontend: http://localhost:9150"
echo "🔧 Backend Health: http://localhost:9160/health"
echo "📊 Dapr Dashboard: dapr dashboard"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup processes
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null

    # Stop any remaining dapr processes
    pkill -f "dapr run.*compliance-agent-backend" 2>/dev/null
    pkill -f "dapr run.*adaptive-interface" 2>/dev/null

    echo "✅ All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for services to complete
wait
