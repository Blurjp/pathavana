#!/bin/bash

# Pathavana Test Runner Script
# This script provides easy commands to run different types of tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    printf "${1}${2}${NC}\n"
}

# Function to print help
print_help() {
    echo "Pathavana Test Runner"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  backend              Run backend tests only"
    echo "  frontend             Run frontend tests only"
    echo "  backend-unit         Run backend unit tests only"
    echo "  backend-integration  Run backend integration tests only"
    echo "  frontend-unit        Run frontend unit tests only"
    echo "  frontend-integration Run frontend integration tests only"
    echo "  e2e                  Run end-to-end tests"
    echo "  coverage             Run all tests with coverage reports"
    echo "  lint                 Run linting for both frontend and backend"
    echo "  setup                Set up test environment"
    echo "  clean                Clean test artifacts"
    echo "  all                  Run all tests (default)"
    echo ""
    echo "Options:"
    echo "  --watch              Run tests in watch mode (where applicable)"
    echo "  --verbose            Run tests with verbose output"
    echo "  --parallel           Run tests in parallel"
    echo "  --fast               Skip slow tests"
    echo "  --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 backend --verbose              # Run backend tests with verbose output"
    echo "  $0 frontend --watch               # Run frontend tests in watch mode"
    echo "  $0 coverage                       # Generate coverage reports"
    echo "  $0 setup                          # Set up test environment"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_color $RED "❌ Docker is not running. Please start Docker to run tests that require a database."
        exit 1
    fi
}

# Function to set up test environment
setup_test_env() {
    print_color $BLUE "🔧 Setting up test environment..."
    
    # Check if Docker is available for database tests
    if command -v docker &> /dev/null; then
        print_color $GREEN "✅ Docker found"
        
        # Start test services
        print_color $BLUE "🐳 Starting test services..."
        docker-compose -f docker-compose.test.yml up -d postgres redis
        
        # Wait for services to be ready
        print_color $BLUE "⏳ Waiting for services to be ready..."
        sleep 10
        
        # Create test database
        print_color $BLUE "🗄️  Setting up test database..."
        cd backend
        export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/pathavana_test"
        export REDIS_URL="redis://localhost:6379/1"
        export TESTING=1
        
        python -c "
import asyncio
from app.core.database import engine, Base

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(create_tables())
"
        cd ..
        print_color $GREEN "✅ Test database created"
    else
        print_color $YELLOW "⚠️  Docker not found. Database tests may fail."
    fi
    
    # Install dependencies
    print_color $BLUE "📦 Installing backend dependencies..."
    cd backend && pip install -r requirements.txt && cd ..
    
    print_color $BLUE "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
    
    print_color $GREEN "✅ Test environment setup complete!"
}

# Function to clean test artifacts
clean_test_artifacts() {
    print_color $BLUE "🧹 Cleaning test artifacts..."
    
    # Backend cleanup
    rm -rf backend/htmlcov/
    rm -rf backend/.coverage
    rm -rf backend/coverage.xml
    rm -rf backend/.pytest_cache/
    find backend -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Frontend cleanup
    rm -rf frontend/coverage/
    rm -rf frontend/build/
    rm -rf frontend/node_modules/.cache/
    
    # E2E cleanup
    rm -rf frontend/playwright-report/
    rm -rf frontend/test-results/
    
    print_color $GREEN "✅ Test artifacts cleaned!"
}

# Function to run backend tests
run_backend_tests() {
    local test_type=${1:-"all"}
    local options=${2:-""}
    
    print_color $BLUE "🐍 Running backend tests ($test_type)..."
    
    cd backend
    
    # Set environment variables
    export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/pathavana_test"
    export REDIS_URL="redis://localhost:6379/1"
    export TESTING=1
    export SECRET_KEY="test-secret-key"
    export AMADEUS_API_KEY="test_key"
    export AMADEUS_API_SECRET="test_secret"
    export OPENAI_API_KEY="test_key"
    export ANTHROPIC_API_KEY="test_key"
    
    case $test_type in
        "unit")
            pytest tests/ -m "unit" $options
            ;;
        "integration")
            check_docker
            pytest tests/ -m "integration" $options
            ;;
        "api")
            check_docker
            pytest tests/test_api/ $options
            ;;
        "services")
            pytest tests/test_services/ $options
            ;;
        "models")
            check_docker
            pytest tests/test_models/ $options
            ;;
        *)
            check_docker
            pytest tests/ $options
            ;;
    esac
    
    cd ..
    print_color $GREEN "✅ Backend tests completed!"
}

# Function to run frontend tests
run_frontend_tests() {
    local test_type=${1:-"all"}
    local options=${2:-""}
    
    print_color $BLUE "⚛️  Running frontend tests ($test_type)..."
    
    cd frontend
    
    case $test_type in
        "unit")
            npm run test -- --testPathPattern="(components|hooks|utils)" $options
            ;;
        "integration")
            npm run test -- --testPathPattern="integration" $options
            ;;
        "watch")
            npm run test:watch
            ;;
        *)
            npm run test:ci $options
            ;;
    esac
    
    cd ..
    print_color $GREEN "✅ Frontend tests completed!"
}

# Function to run E2E tests
run_e2e_tests() {
    print_color $BLUE "🎭 Running E2E tests..."
    
    # Check if servers are running, if not start them
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_color $BLUE "🚀 Starting backend server..."
        cd backend
        export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/pathavana_test"
        export REDIS_URL="redis://localhost:6379/1"
        export TESTING=1
        uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
        cd ..
        sleep 10
    fi
    
    if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_color $BLUE "🚀 Starting frontend server..."
        cd frontend
        export REACT_APP_API_BASE_URL="http://localhost:8000"
        npm start &
        FRONTEND_PID=$!
        cd ..
        sleep 30
    fi
    
    cd frontend
    if [ ! -d "node_modules/@playwright" ]; then
        print_color $BLUE "📦 Installing Playwright..."
        npm install -D @playwright/test
        npx playwright install
    fi
    
    npx playwright test
    cd ..
    
    # Clean up if we started the servers
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    print_color $GREEN "✅ E2E tests completed!"
}

# Function to run linting
run_linting() {
    print_color $BLUE "🔍 Running linting..."
    
    # Backend linting (if available)
    if [ -f "backend/pyproject.toml" ] || [ -f "backend/.flake8" ]; then
        print_color $BLUE "🐍 Linting backend code..."
        cd backend
        if command -v black &> /dev/null; then
            black --check .
        fi
        if command -v flake8 &> /dev/null; then
            flake8 .
        fi
        if command -v mypy &> /dev/null; then
            mypy .
        fi
        cd ..
    fi
    
    # Frontend linting
    print_color $BLUE "⚛️  Linting frontend code..."
    cd frontend
    if npm list eslint &> /dev/null; then
        npm run lint
    fi
    cd ..
    
    print_color $GREEN "✅ Linting completed!"
}

# Function to generate coverage reports
run_coverage() {
    print_color $BLUE "📊 Generating coverage reports..."
    
    # Backend coverage
    print_color $BLUE "🐍 Backend coverage..."
    cd backend
    export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/pathavana_test"
    export REDIS_URL="redis://localhost:6379/1"
    export TESTING=1
    check_docker
    pytest --cov=app --cov-report=html --cov-report=xml --cov-fail-under=80
    cd ..
    
    # Frontend coverage
    print_color $BLUE "⚛️  Frontend coverage..."
    cd frontend
    npm run test:coverage
    cd ..
    
    print_color $GREEN "✅ Coverage reports generated!"
    print_color $BLUE "Backend coverage: backend/htmlcov/index.html"
    print_color $BLUE "Frontend coverage: frontend/coverage/lcov-report/index.html"
}

# Parse command line arguments
COMMAND=${1:-"all"}
shift || true

WATCH=false
VERBOSE=false
PARALLEL=false
FAST=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --watch)
            WATCH=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --fast)
            FAST=true
            shift
            ;;
        --help)
            print_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            print_help
            exit 1
            ;;
    esac
done

# Build options string
OPTIONS=""
if [ "$VERBOSE" = true ]; then
    OPTIONS="$OPTIONS -v"
fi
if [ "$PARALLEL" = true ]; then
    OPTIONS="$OPTIONS -n auto"
fi
if [ "$FAST" = true ]; then
    OPTIONS="$OPTIONS -m 'not slow'"
fi

# Main execution
print_color $GREEN "🚀 Pathavana Test Runner"
print_color $BLUE "Command: $COMMAND"

case $COMMAND in
    "setup")
        setup_test_env
        ;;
    "clean")
        clean_test_artifacts
        ;;
    "backend")
        run_backend_tests "all" "$OPTIONS"
        ;;
    "backend-unit")
        run_backend_tests "unit" "$OPTIONS"
        ;;
    "backend-integration")
        run_backend_tests "integration" "$OPTIONS"
        ;;
    "backend-api")
        run_backend_tests "api" "$OPTIONS"
        ;;
    "backend-services")
        run_backend_tests "services" "$OPTIONS"
        ;;
    "backend-models")
        run_backend_tests "models" "$OPTIONS"
        ;;
    "frontend")
        if [ "$WATCH" = true ]; then
            run_frontend_tests "watch"
        else
            run_frontend_tests "all" "$OPTIONS"
        fi
        ;;
    "frontend-unit")
        run_frontend_tests "unit" "$OPTIONS"
        ;;
    "frontend-integration")
        run_frontend_tests "integration" "$OPTIONS"
        ;;
    "e2e")
        run_e2e_tests
        ;;
    "lint")
        run_linting
        ;;
    "coverage")
        run_coverage
        ;;
    "all")
        run_backend_tests "all" "$OPTIONS"
        run_frontend_tests "all" "$OPTIONS"
        ;;
    *)
        print_color $RED "❌ Unknown command: $COMMAND"
        print_help
        exit 1
        ;;
esac

print_color $GREEN "🎉 All done!"