#!/bin/bash

# Pathavana Backend Startup Script with Enhanced Logging
# This script starts the backend server with proper logging to both console and files

set -e  # Exit on any error

# Colors for console output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Pathavana Backend Startup ===${NC}"

# Create logs directory
mkdir -p logs

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${RED}✗ Virtual environment not found at venv/bin/activate${NC}"
    exit 1
fi

# Check if required packages are installed
echo -e "${YELLOW}Checking dependencies...${NC}"
python -c "import fastapi, uvicorn, sqlalchemy, pydantic" 2>/dev/null && echo -e "${GREEN}✓ Core dependencies available${NC}" || {
    echo -e "${RED}✗ Missing dependencies. Installing...${NC}"
    pip install -r requirements.txt
}

# Set environment variables for enhanced logging
export LOG_LEVEL=${LOG_LEVEL:-INFO}
export LOG_DIR=${LOG_DIR:-logs}

# Start the server with enhanced logging
echo -e "${YELLOW}Starting Pathavana backend server...${NC}"
echo -e "${BLUE}Server will start on: http://0.0.0.0:8001${NC}"
echo -e "${BLUE}Logs will be written to: ${LOG_DIR}/app.log${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo ""

# Start uvicorn with logging configuration
exec uvicorn app.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8001 \
    --log-level info \
    --access-log