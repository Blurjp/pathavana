#!/bin/bash

# Pathavana Frontend Production Startup Script

set -e  # Exit on any error

echo "🚀 Pathavana Frontend Startup"
echo "=============================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}📁 Working directory: $PWD${NC}"

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
fi

# Verify React app structure
echo -e "${YELLOW}🔧 Verifying React app structure...${NC}"
if [ -f "src/App.tsx" ] && [ -f "src/index.tsx" ]; then
    echo -e "${GREEN}✅ React app structure verified${NC}"
else
    echo -e "${RED}❌ React app structure incomplete${NC}"
    exit 1
fi

# Start the development server
echo -e "${GREEN}🎉 Starting React Development Server${NC}"
echo "=============================="
echo -e "${YELLOW}📍 Frontend: http://localhost:3000${NC}"
echo -e "${YELLOW}📍 Backend API: http://localhost:8000${NC}"
echo -e "${YELLOW}🛑 Press Ctrl+C to stop${NC}"
echo "=============================="

# Start the React development server
npm start