#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Pathavana Backend Server${NC}"
echo "========================================"

# Navigate to backend directory
cd /Users/jianphua/projects/pathavana/backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Please create it first with: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# Kill any process running on port 8001
echo -e "${YELLOW}🔍 Checking for processes on port 8001...${NC}"
PIDS=$(lsof -ti :8001)

if [ ! -z "$PIDS" ]; then
    echo -e "${YELLOW}⚠️  Found process(es) on port 8001: $PIDS${NC}"
    echo -e "${YELLOW}🛑 Killing process(es)...${NC}"
    kill -9 $PIDS 2>/dev/null
    sleep 1
    echo -e "${GREEN}✅ Port 8001 is now free${NC}"
else
    echo -e "${GREEN}✅ Port 8001 is already free${NC}"
fi

# Start the FastAPI server
echo -e "${GREEN}🚀 Starting FastAPI server on http://0.0.0.0:8001${NC}"
echo -e "${GREEN}📚 API documentation: http://localhost:8001/api/v1/docs${NC}"
echo -e "${YELLOW}🛑 Press Ctrl+C to stop the server${NC}"
echo "========================================"

uvicorn app.main:app --reload --host 0.0.0.0 --port 8001