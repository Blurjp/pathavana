#!/bin/bash

# Pathavana Frontend Startup Script
# This script starts the React frontend application

set -e  # Exit on any error

echo "🚀 Pathavana Frontend Startup"
echo "=============================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the absolute path to the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo -e "${BLUE}📁 Project directory: $SCRIPT_DIR${NC}"
echo -e "${BLUE}📁 Frontend directory: $FRONTEND_DIR${NC}"

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Frontend directory not found: $FRONTEND_DIR${NC}"
    exit 1
fi

# Navigate to frontend directory
cd "$FRONTEND_DIR"
echo -e "${YELLOW}📂 Changed to frontend directory: $(pwd)${NC}"

# Check Node.js and npm
echo -e "${YELLOW}🔧 Checking Node.js and npm...${NC}"
if command -v node >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Node.js version: $(node --version)${NC}"
else
    echo -e "${RED}❌ Node.js not found! Please install Node.js${NC}"
    exit 1
fi

if command -v npm >/dev/null 2>&1; then
    echo -e "${GREEN}✅ npm version: $(npm --version)${NC}"
else
    echo -e "${RED}❌ npm not found! Please install npm${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📋 Creating .env file...${NC}"
    cat > .env << EOL
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_API_VERSION=/api
REACT_APP_GOOGLE_CLIENT_ID=55013767303-slk94mloce0s2l4ipqdftbtobflppksf.apps.googleusercontent.com
REACT_APP_ENVIRONMENT=development
REACT_APP_GOOGLE_MAPS_API_KEY=
REACT_APP_APP_NAME=Pathavana
REACT_APP_VERSION=1.0.0
EOL
    echo -e "${GREEN}✅ .env file created${NC}"
else
    echo -e "${GREEN}✅ .env file found${NC}"
fi

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ package.json not found!${NC}"
    exit 1
fi

# Check if node_modules exists and install if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing npm dependencies...${NC}"
    npm install
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install dependencies${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
    
    # Check if dependencies are up to date
    echo -e "${YELLOW}🔧 Checking for dependency updates...${NC}"
    npm outdated > /dev/null 2>&1 || echo -e "${YELLOW}⚠️  Some dependencies may be outdated${NC}"
fi

# Verify React app structure
echo -e "${YELLOW}🔧 Verifying React app structure...${NC}"
if [ -f "src/App.tsx" ] && [ -f "src/index.tsx" ]; then
    echo -e "${GREEN}✅ React app structure verified${NC}"
else
    echo -e "${RED}❌ React app structure incomplete${NC}"
    exit 1
fi

# Check if backend is running
echo -e "${YELLOW}🔧 Checking backend connection...${NC}"
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running and accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Backend is not running at http://localhost:8000${NC}"
    echo -e "${YELLOW}   Please start the backend first with: ./start_backend.sh${NC}"
fi

# Start the development server
echo -e "${GREEN}🎉 Starting React Development Server${NC}"
echo "=========================================="
echo -e "${BLUE}📍 Frontend Application: http://localhost:3000${NC}"
echo -e "${BLUE}📍 Backend API: http://localhost:8000${NC}"
echo -e "${BLUE}📍 API Documentation: http://localhost:8000/api/docs${NC}"
echo "=========================================="
echo -e "${YELLOW}🔄 Hot reload enabled - changes will update automatically${NC}"
echo -e "${YELLOW}🛑 Press Ctrl+C to stop the development server${NC}"
echo "=========================================="

# Start the React development server
exec npm start