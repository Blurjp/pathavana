#!/bin/bash

# Pathavana iTerm Startup Script
# This script opens both backend and frontend services in separate iTerm tabs

set -e  # Exit on any error

echo "🚀 Pathavana iTerm Multi-Tab Launcher"
echo "====================================="

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
    echo -e "${RED}❌ This script is designed for macOS with iTerm${NC}"
    echo -e "${YELLOW}For other systems, please run the services manually:${NC}"
    echo -e "  Terminal 1: $SCRIPT_DIR/start_backend.sh"
    echo -e "  Terminal 2: $SCRIPT_DIR/start_frontend.sh"
    exit 1
fi

# Check if iTerm is installed
if ! osascript -e 'tell application "System Events" to (name of processes) contains "iTerm2"' 2>/dev/null && ! command -v iterm 2>/dev/null; then
    echo -e "${RED}❌ iTerm2 not found${NC}"
    echo -e "${YELLOW}Please install iTerm2 or use regular Terminal:${NC}"
    echo -e "  Download from: https://iterm2.com/"
    echo -e "${YELLOW}Alternative commands for Terminal:${NC}"
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

echo -e "${YELLOW}🔧 Starting Pathavana in iTerm with separate tabs...${NC}"
echo ""

# AppleScript to create iTerm window with two tabs
osascript <<EOF
tell application "iTerm2"
    -- Activate iTerm
    activate
    
    -- Create new window
    create window with default profile
    
    tell current window
        tell current session
            -- Set up backend tab
            set name to "Pathavana Backend"
            write text "echo '🚀 Pathavana Backend Starting...'"
            write text "echo '================================'"
            write text "cd '$SCRIPT_DIR'"
            write text "./start_backend.sh"
        end tell
        
        -- Create new tab for frontend
        create tab with default profile
        
        tell current session
            -- Set up frontend tab  
            set name to "Pathavana Frontend"
            write text "echo '🚀 Pathavana Frontend Starting...'"
            write text "echo '================================='"
            write text "echo 'Waiting 5 seconds for backend to start...'"
            write text "sleep 5"
            write text "cd '$SCRIPT_DIR'"
            write text "./start_frontend.sh"
        end tell
        
        -- Switch back to backend tab to see startup
        select first tab
    end tell
end tell
EOF

echo -e "${GREEN}✅ iTerm tabs created successfully!${NC}"
echo ""
echo -e "${BOLD}Services starting in iTerm tabs:${NC}"
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