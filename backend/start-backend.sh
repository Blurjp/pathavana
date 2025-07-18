#!/bin/bash

# Pathavana Backend Startup Script
echo "🚀 Starting Pathavana Backend Server"
echo "========================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if we're in the backend directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    echo "Please run this script from the backend directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    echo "Please check requirements.txt and try again"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found"
    echo "📋 Creating .env from .env.example..."
    cp .env.example .env
    echo "✏️ Please edit .env file with your configuration before running the server"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs cache alembic/versions

# Check if database is configured
echo "🗄️ Checking database configuration..."
if grep -q "postgresql.*localhost" .env; then
    echo "⚠️ Default database configuration detected"
    echo "📝 Make sure PostgreSQL is running and configured properly"
fi

# Run database migrations (if alembic is configured)
if [ -f "alembic.ini" ]; then
    echo "🔄 Running database migrations..."
    alembic upgrade head
else
    echo "⚠️ Alembic not configured - skipping database migrations"
fi

# Kill any process running on port 8001
echo "🔍 Checking for processes on port 8001..."
PIDS=$(lsof -ti :8001)

if [ ! -z "$PIDS" ]; then
    echo "⚠️  Found process(es) on port 8001: $PIDS"
    echo "🛑 Killing process(es)..."
    kill -9 $PIDS 2>/dev/null
    sleep 1
    echo "✅ Port 8001 is now free"
else
    echo "✅ Port 8001 is already free"
fi

# Start the server
echo "🚀 Starting FastAPI server..."
echo "📍 Server will be available at: http://localhost:8001"
echo "📚 API documentation at: http://localhost:8001/api/v1/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run with uvicorn (with reduced logging verbosity)
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload --log-level warning

echo ""
echo "👋 Server stopped"