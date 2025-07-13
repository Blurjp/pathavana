#!/bin/bash

# Pathavana Terminal Multi-Tab Startup Script
# This script opens both services in separate Terminal tabs/windows

set -e  # Exit on any error

echo "🚀 Pathavana Terminal Multi-Tab Launcher"
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Get the absolute path to the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}📁 Project directory: $SCRIPT_DIR${NC}"

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ This script is designed for macOS Terminal${NC}"
    echo -e "${YELLOW}For other systems, please run the services manually in separate terminals:${NC}"
    echo -e "  Terminal 1: $SCRIPT_DIR/start_backend.sh"
    echo -e "  Terminal 2: $SCRIPT_DIR/start_frontend.sh"
    exit 1
fi

# Check if scripts exist
if [ ! -f "$SCRIPT_DIR/start_backend.sh" ]; then
    echo -e "${RED}❌ Backend startup script not found: $SCRIPT_DIR/start_backend.sh${NC}"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/start_frontend.sh" ]; then
    echo -e "${RED}❌ Frontend startup script not found: $SCRIPT_DIR/start_frontend.sh${NC}"
    exit 1
fi

echo -e "${YELLOW}🔧 Starting Pathavana in Terminal with separate tabs...${NC}"
echo ""

# AppleScript for Terminal app with tabs
osascript <<EOF
tell application "Terminal"
    -- Activate Terminal
    activate
    
    -- Open backend in new tab
    tell application "System Events" to keystroke "t" using command down
    delay 0.5
    do script "echo '🚀 Pathavana Backend Starting...' && echo '================================' && cd '$SCRIPT_DIR' && ./start_backend.sh" in front window
    
    -- Open frontend in another new tab  
    tell application "System Events" to keystroke "t" using command down
    delay 0.5
    do script "echo '🚀 Pathavana Frontend Starting...' && echo '=================================' && echo 'Waiting 5 seconds for backend to start...' && sleep 5 && cd '$SCRIPT_DIR' && ./start_frontend.sh" in front window
    
    -- Switch back to backend tab
    tell application "System Events" to keystroke "1" using command down
end tell
EOF

echo -e "${GREEN}✅ Terminal tabs created successfully!${NC}"
echo ""
echo -e "${BOLD}Services starting in Terminal tabs:${NC}"
echo -e "  📋 Tab 1: ${YELLOW}Pathavana Backend${NC} (Backend server console)"
echo -e "  📋 Tab 2: ${YELLOW}Pathavana Frontend${NC} (React dev server console)"
echo ""
echo -e "${BOLD}Access URLs (once services are running):${NC}"
echo -e "  🌐 Frontend Application: ${BLUE}http://localhost:3000${NC}"
echo -e "  🔧 Backend API: ${BLUE}http://localhost:8000${NC}"
echo -e "  📚 API Documentation: ${BLUE}http://localhost:8000/api/docs${NC}"
echo -e "  ❤️  Health Check: ${BLUE}http://localhost:8000/api/health${NC}"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo -e "  • Switch between tabs with Cmd+1 and Cmd+2"
echo -e "  • Stop services with Ctrl+C in each tab"
echo -e "  • Backend tab shows API logs and requests"
echo -e "  • Frontend tab shows React compilation and hot reload"
echo ""
echo -e "${GREEN}🎉 Happy coding!${NC}"