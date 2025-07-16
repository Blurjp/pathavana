#!/bin/bash

# Pathavana Master Startup Script
# This script can start backend, frontend, or both services

set -e  # Exit on any error

echo "🚀 Pathavana Application Launcher"
echo "=================================="

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

# Function to show usage
show_usage() {
    echo -e "${BOLD}Usage:${NC}"
    echo "  $0 [OPTION]"
    echo ""
    echo -e "${BOLD}Options:${NC}"
    echo "  backend         Start only the backend service"
    echo "  frontend        Start only the frontend service"
    echo "  iterm           Start both services in iTerm tabs (recommended)"
    echo "  terminal        Start both services in Terminal tabs"
    echo "  both            Start both services (with options)"
    echo "  help            Show this help message"
    echo ""
    echo -e "${BOLD}Examples:${NC}"
    echo "  $0 backend      # Start backend only"
    echo "  $0 frontend     # Start frontend only"
    echo "  $0 iterm        # Start both in iTerm tabs (recommended)"
    echo "  $0 terminal     # Start both in Terminal tabs"
    echo "  $0 both         # Start both with terminal choice"
    echo "  $0              # Interactive mode (default)"
}

# Function to start backend
start_backend() {
    echo -e "${YELLOW}🔧 Starting Pathavana Backend...${NC}"
    cd "$SCRIPT_DIR"
    exec ./start_backend.sh
}

# Function to start frontend
start_frontend() {
    echo -e "${YELLOW}🔧 Starting Pathavana Frontend...${NC}"
    cd "$SCRIPT_DIR"
    exec ./start_frontend.sh
}

# Function to start both services in iTerm
start_both_iterm() {
    echo -e "${YELLOW}🔧 Starting Both Services in iTerm Tabs...${NC}"
    cd "$SCRIPT_DIR"
    exec ./start_both_iterm.sh
}

# Function to start both services in Terminal
start_both_terminal() {
    echo -e "${YELLOW}🔧 Starting Both Services in Terminal Tabs...${NC}"
    cd "$SCRIPT_DIR"
    exec ./start_both_terminal.sh
}

# Function to start both services (with options)
start_both() {
    echo -e "${YELLOW}🔧 Starting Both Pathavana Services...${NC}"
    echo ""
    echo -e "${BOLD}Choose your terminal preference:${NC}"
    echo "1) iTerm2 tabs (recommended)"
    echo "2) Terminal tabs"
    echo "3) Separate windows (legacy)"
    echo ""
    
    while true; do
        echo -n -e "${YELLOW}Enter your choice (1-3): ${NC}"
        read choice
        
        case $choice in
            1)
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    start_both_iterm
                else
                    echo -e "${RED}iTerm2 is only available on macOS${NC}"
                fi
                break
                ;;
            2)
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    start_both_terminal
                else
                    echo -e "${RED}This option is only available on macOS${NC}"
                fi
                break
                ;;
            3)
                # Legacy separate windows
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    echo -e "${YELLOW}Opening backend in new terminal...${NC}"
                    osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR' && ./start_backend.sh\""
                    
                    sleep 2
                    
                    echo -e "${YELLOW}Opening frontend in new terminal...${NC}"
                    osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR' && ./start_frontend.sh\""
                    
                    echo -e "${GREEN}✅ Both services started in separate windows${NC}"
                    echo -e "${BLUE}📍 Frontend: http://localhost:3000${NC}"
                    echo -e "${BLUE}📍 Backend: http://localhost:8001${NC}"
                else
                    echo -e "${YELLOW}⚠️  Auto-opening terminals not supported on this system${NC}"
                    echo -e "${YELLOW}Please run these commands in separate terminals:${NC}"
                    echo ""
                    echo -e "${BOLD}Terminal 1 (Backend):${NC}"
                    echo "  cd '$SCRIPT_DIR' && ./start_backend.sh"
                    echo ""
                    echo -e "${BOLD}Terminal 2 (Frontend):${NC}"
                    echo "  cd '$SCRIPT_DIR' && ./start_frontend.sh"
                fi
                break
                ;;
            *)
                echo -e "${RED}Invalid choice. Please enter 1-3.${NC}"
                ;;
        esac
    done
}

# Function for interactive mode
interactive_mode() {
    echo -e "${BOLD}Pathavana Service Launcher${NC}"
    echo ""
    echo "What would you like to start?"
    echo ""
    echo "1) Backend only (API server)"
    echo "2) Frontend only (React app)"  
    echo "3) Both services in iTerm tabs (recommended)"
    echo "4) Both services in Terminal tabs"
    echo "5) Both services in separate windows"
    echo "6) Show help"
    echo "7) Exit"
    echo ""
    
    while true; do
        echo -n -e "${YELLOW}Enter your choice (1-7): ${NC}"
        read choice
        
        case $choice in
            1)
                echo -e "${GREEN}Starting backend service...${NC}"
                start_backend
                break
                ;;
            2)
                echo -e "${GREEN}Starting frontend service...${NC}"
                start_frontend
                break
                ;;
            3)
                echo -e "${GREEN}Starting both services in iTerm tabs...${NC}"
                start_both_iterm
                break
                ;;
            4)
                echo -e "${GREEN}Starting both services in Terminal tabs...${NC}"
                start_both_terminal
                break
                ;;
            5)
                echo -e "${GREEN}Starting both services in separate windows...${NC}"
                start_both
                break
                ;;
            6)
                show_usage
                echo ""
                ;;
            7)
                echo -e "${YELLOW}Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice. Please enter 1-7.${NC}"
                ;;
        esac
    done
}

# Check if scripts exist
if [ ! -f "$SCRIPT_DIR/start_backend.sh" ]; then
    echo -e "${RED}❌ Backend startup script not found: $SCRIPT_DIR/start_backend.sh${NC}"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/start_frontend.sh" ]; then
    echo -e "${RED}❌ Frontend startup script not found: $SCRIPT_DIR/start_frontend.sh${NC}"
    exit 1
fi

# Parse command line arguments
case "${1:-interactive}" in
    "backend")
        start_backend
        ;;
    "frontend")
        start_frontend
        ;;
    "iterm")
        start_both_iterm
        ;;
    "terminal")
        start_both_terminal
        ;;
    "both")
        start_both
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    "interactive"|"")
        interactive_mode
        ;;
    *)
        echo -e "${RED}❌ Unknown option: $1${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac