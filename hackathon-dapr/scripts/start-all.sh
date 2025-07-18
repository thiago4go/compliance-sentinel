#!/bin/bash

# Compliance Sentinel - Start All Services
# This script starts all Dapr-enabled services for the hackathon demo

set -e

echo "🚀 Starting Compliance Sentinel - Dapr AI Hackathon Demo"
echo "========================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

# Check if Dapr is installed
if ! command -v dapr &> /dev/null; then
    echo -e "${RED}❌ Dapr CLI not found. Please install Dapr CLI first.${NC}"
    echo "Run: curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | /bin/bash"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Copying from .env.example${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file and add your OpenAI API key${NC}"
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check OpenAI API key
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "placeholder" ]; then
    echo -e "${RED}❌ OpenAI API key not set. Please update .env file with your API key.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Start infrastructure services
echo -e "${BLUE}🏗️  Starting infrastructure services...${NC}"
cd hackathon-dapr && docker-compose -f docker-compose.yml up -d redis postgres

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for infrastructure services to be ready...${NC}"
sleep 10

# Check if Redis is ready
echo -e "${BLUE}🔍 Checking Redis connection...${NC}"
if docker exec compliance-redis redis-cli ping | grep -q PONG; then
    echo -e "${GREEN}✅ Redis is ready${NC}"
else
    echo -e "${RED}❌ Redis is not responding${NC}"
    exit 1
fi

# Check if PostgreSQL is ready
echo -e "${BLUE}🔍 Checking PostgreSQL connection...${NC}"
if docker exec compliance-postgres pg_isready -U postgres -d compliance_sentinel | grep -q "accepting connections"; then
    echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not responding${NC}"
    exit 1
fi

# Kill any existing Dapr processes
echo -e "${BLUE}🧹 Cleaning up existing processes...${NC}"
pkill -f "dapr.*compliance" 2>/dev/null || true
pkill -f "chainlit.*working-chainlit-app" 2>/dev/null || true
sleep 2

# Function to start a Dapr service
start_dapr_service() {
    local app_id=$1
    local app_port=$2
    local dapr_http_port=$3
    local dapr_grpc_port=$4
    local working_dir=$5
    local command=$6
    
    echo -e "${BLUE}🚀 Starting $app_id...${NC}"
    
    cd "$working_dir"
    
    dapr run \
        --app-id "$app_id" \
        --app-port "$app_port" \
        --dapr-http-port "$dapr_http_port" \
        --dapr-grpc-port "$dapr_grpc_port" \
        --resources-path ../infrastructure/dapr-components/ \
        --log-level info \
        -- $command &
    
    # Store PID for cleanup
    echo $! > "/tmp/dapr-$app_id.pid"
    
    cd - > /dev/null
    sleep 3
}

# Start Harvester Insights Agent
start_dapr_service \
    "harvester-insights-agent" \
    "9180" \
    "3503" \
    "50003" \
    "./harvester-insights-agent" \
    "python harvester_agent.py"

# Start Workflow Agent
start_dapr_service \
    "workflow-agent" \
    "9170" \
    "3502" \
    "50002" \
    "./workflow-agent" \
    "python workflow_agent.py"

# Start Adaptive Interface Backend
start_dapr_service \
    "adaptive-interface-backend" \
    "9160" \
    "3501" \
    "50001" \
    "./adaptive-interface/backend" \
    "python main.py"

# Start Chainlit Frontend
echo -e "${BLUE}🚀 Starting Chainlit Frontend...${NC}"
cd adaptive-interface
dapr run \
    --app-id "adaptive-interface-frontend" \
    --app-port "9150" \
    --dapr-http-port "3500" \
    --dapr-grpc-port "50000" \
    --resources-path ../infrastructure/dapr-components/ \
    --log-level info \
    -- chainlit run frontend/chainlit_frontend.py --port 9150 --host 0.0.0.0 &

echo $! > "/tmp/dapr-frontend.pid"
cd - > /dev/null

# Wait for all services to start
echo -e "${BLUE}⏳ Waiting for all services to start...${NC}"
sleep 15

# Health check all services
echo -e "${BLUE}🏥 Performing health checks...${NC}"

services=(
    "http://localhost:9180/health:Harvester Agent"
    "http://localhost:9170/health:Workflow Agent"
    "http://localhost:9160/health:Adaptive Interface Backend"
)

all_healthy=true

for service in "${services[@]}"; do
    url=$(echo $service | cut -d: -f1-2)
    name=$(echo $service | cut -d: -f3)
    
    if curl -s -f "$url" > /dev/null; then
        echo -e "${GREEN}✅ $name is healthy${NC}"
    else
        echo -e "${RED}❌ $name is not responding${NC}"
        all_healthy=false
    fi
done

# Display service information
echo -e "\n${GREEN}🎉 Compliance Sentinel Services Started!${NC}"
echo "========================================"
echo -e "${BLUE}📱 Chainlit Frontend:${NC}        http://localhost:9150"
echo -e "${BLUE}🤖 Adaptive Interface Backend:${NC} http://localhost:9160"
echo -e "${BLUE}🔄 Workflow Agent:${NC}            http://localhost:9170"
echo -e "${BLUE}📊 Harvester Insights Agent:${NC}  http://localhost:9180"
echo -e "${BLUE}🗄️  PostgreSQL:${NC}               localhost:5432"
echo -e "${BLUE}🔴 Redis:${NC}                     localhost:6379"
echo ""

if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}✅ All services are healthy and ready!${NC}"
    echo -e "${YELLOW}🌟 Open http://localhost:9150 to start using Compliance Sentinel${NC}"
    echo ""
    echo -e "${BLUE}💡 Demo Commands:${NC}"
    echo "  - Try: 'Analyze GDPR compliance for my company'"
    echo "  - Try: 'What are the key ISO 27001 requirements?'"
    echo "  - Try: 'Help me with SOX compliance planning'"
else
    echo -e "${RED}⚠️  Some services are not healthy. Check the logs above.${NC}"
fi

echo ""
echo -e "${BLUE}🛑 To stop all services, run:${NC} ./scripts/stop-all.sh"
echo ""

# Keep script running to show logs
echo -e "${BLUE}📋 Service logs (Ctrl+C to stop):${NC}"
echo "=================================="

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping all services...${NC}"
    ./scripts/stop-all.sh
    exit 0
}

trap cleanup SIGINT SIGTERM

# Show logs from all services
tail -f /dev/null
