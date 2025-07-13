#!/bin/bash

# Pathavana Backend Startup Script
# This script activates the virtual environment and starts the backend service

set -e  # Exit on any error

echo "🚀 Pathavana Backend Startup"
echo "============================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the absolute path to the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo -e "${BLUE}📁 Project directory: $SCRIPT_DIR${NC}"
echo -e "${BLUE}📁 Backend directory: $BACKEND_DIR${NC}"

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

# Navigate to backend directory
cd "$BACKEND_DIR"
echo -e "${YELLOW}📂 Changed to backend directory: $(pwd)${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🔧 Creating Python virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Check if virtual environment activate script exists
if [ ! -f "venv/bin/activate" ]; then
    echo -e "${RED}❌ Virtual environment activation script not found${NC}"
    echo -e "${YELLOW}Trying to recreate virtual environment...${NC}"
    rm -rf venv
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Verify activation
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}❌ Failed to activate virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Virtual environment activated: $VIRTUAL_ENV${NC}"
echo -e "${YELLOW}🐍 Python version: $(python --version)${NC}"
echo -e "${YELLOW}📦 Pip version: $(pip --version)${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📋 Creating .env file from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ .env file created from template${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env file with your API keys if needed${NC}"
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
    print('✅ Configuration loaded successfully')
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

# Check for FastAPI availability and try to install if missing
echo -e "${YELLOW}🔧 Checking FastAPI availability...${NC}"
python3 -c "
try:
    import fastapi
    import uvicorn
    print('✅ FastAPI and uvicorn available - production mode')
    mode = 'production'
except ImportError:
    print('⚠️  FastAPI not available - will try to install')
    mode = 'install'
with open('.mode', 'w') as f:
    f.write(mode)
" 

MODE=$(cat .mode 2>/dev/null || echo "fallback")
rm -f .mode

# Try to install dependencies if not available
if [ "$MODE" = "install" ]; then
    echo -e "${YELLOW}📦 Attempting to install FastAPI and uvicorn...${NC}"
    
    # Create minimal requirements
    cat > requirements_minimal.txt << EOL
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
aiosqlite==0.19.0
EOL
    
    # Try to install with timeout
    timeout 60 pip install -r requirements_minimal.txt 2>/dev/null && {
        echo -e "${GREEN}✅ FastAPI and dependencies installed successfully${NC}"
        MODE="production"
    } || {
        echo -e "${YELLOW}⚠️  Could not install dependencies - using fallback mode${NC}"
        MODE="fallback"
    }
    
    rm -f requirements_minimal.txt
fi

# Start the appropriate server
echo -e "${YELLOW}🚀 Starting server in $MODE mode...${NC}"
echo "============================================"

if [ "$MODE" = "production" ]; then
    echo -e "${GREEN}🎉 Starting FastAPI Production Server${NC}"
    echo -e "${BLUE}📍 Frontend: http://localhost:3000${NC}"
    echo -e "${BLUE}📍 Backend API: http://localhost:8000${NC}"
    echo -e "${BLUE}📍 API Documentation: http://localhost:8000/api/docs${NC}"
    echo -e "${BLUE}📍 Health Check: http://localhost:8000/api/health${NC}"
    echo -e "${BLUE}📍 API Info: http://localhost:8000/api/info${NC}"
    echo "============================================"
    echo -e "${YELLOW}🛑 Press Ctrl+C to stop the server${NC}"
    echo "============================================"
    
    # Start the production server
    python3 app/main_production.py
else
    echo -e "${YELLOW}🔧 Starting Fallback HTTP Server${NC}"
    echo -e "${BLUE}📍 Frontend: http://localhost:3000${NC}"
    echo -e "${BLUE}📍 Backend API: http://localhost:8000${NC}"
    echo -e "${BLUE}📍 Health Check: http://localhost:8000/api/health${NC}"
    echo -e "${BLUE}📍 API Info: http://localhost:8000/api/info${NC}"
    echo "============================================"
    echo -e "${YELLOW}💡 Install FastAPI for full functionality:${NC}"
    echo -e "${YELLOW}   pip install fastapi uvicorn${NC}"
    echo -e "${YELLOW}🛑 Press Ctrl+C to stop the server${NC}"
    echo "============================================"
    
    # Start the fallback server
    python3 app/main_production.py
fi