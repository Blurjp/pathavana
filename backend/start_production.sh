#!/bin/bash

# Pathavana Backend Production Startup Script
# This script sets up the environment and starts the backend server

set -e  # Exit on any error

echo "🚀 Pathavana Backend Production Startup"
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}📁 Working directory: $PWD${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🔧 Creating Python virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Verify Python and pip
echo -e "${YELLOW}🐍 Python version: $(python --version)${NC}"
echo -e "${YELLOW}📦 Pip version: $(pip --version)${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo -e "${YELLOW}📋 Creating .env from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ .env file created from template${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env file with your API keys${NC}"
    else
        echo -e "${RED}❌ .env.example not found! Please create .env manually${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env file found${NC}"
fi

# Create necessary directories
echo -e "${YELLOW}📁 Creating necessary directories...${NC}"
mkdir -p logs cache alembic/versions
echo -e "${GREEN}✅ Directories created${NC}"

# Test configuration loading
echo -e "${YELLOW}🔧 Testing configuration...${NC}"
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from app.core.config import settings
    print(f'✅ Configuration loaded successfully')
    print(f'📋 App: {settings.APP_NAME}')
    print(f'🌐 API: {settings.API_V1_STR}')
    print(f'🗄️ Database: {settings.DATABASE_URL}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Configuration test failed!${NC}"
    exit 1
fi

# Check for FastAPI availability
echo -e "${YELLOW}🔧 Checking FastAPI availability...${NC}"
python3 -c "
try:
    import fastapi
    import uvicorn
    print('✅ FastAPI and uvicorn available - production mode')
    mode = 'production'
except ImportError:
    print('⚠️  FastAPI not available - fallback mode')
    mode = 'fallback'
with open('.mode', 'w') as f:
    f.write(mode)
" 

MODE=$(cat .mode)
rm .mode

# Try to install dependencies if not available
if [ "$MODE" = "fallback" ]; then
    echo -e "${YELLOW}📦 Attempting to install core dependencies...${NC}"
    
    # Try installing minimal dependencies
    echo "fastapi==0.104.1" > requirements_minimal.txt
    echo "uvicorn[standard]==0.24.0" >> requirements_minimal.txt
    echo "python-dotenv==1.0.0" >> requirements_minimal.txt
    echo "pydantic==2.5.0" >> requirements_minimal.txt
    echo "pydantic-settings==2.1.0" >> requirements_minimal.txt
    
    pip install -r requirements_minimal.txt 2>/dev/null && {
        echo -e "${GREEN}✅ Minimal dependencies installed${NC}"
        MODE="production"
    } || {
        echo -e "${YELLOW}⚠️  Could not install dependencies - using fallback mode${NC}"
    }
    
    rm requirements_minimal.txt
fi

# Start the appropriate server
echo -e "${YELLOW}🚀 Starting server in $MODE mode...${NC}"
echo "========================================"

if [ "$MODE" = "production" ]; then
    echo -e "${GREEN}🎉 Starting FastAPI Production Server${NC}"
    echo -e "${YELLOW}📍 API Documentation: http://localhost:8001/api/docs${NC}"
    echo -e "${YELLOW}📍 Health Check: http://localhost:8001/api/health${NC}"
    python3 app/main_production.py
else
    echo -e "${YELLOW}🔧 Starting Fallback Server${NC}"
    echo -e "${YELLOW}📍 API: http://localhost:8001${NC}"
    echo -e "${YELLOW}📍 Health: http://localhost:8001/api/health${NC}"
    python3 app/main_production.py
fi