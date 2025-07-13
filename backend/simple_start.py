#!/usr/bin/env python3
"""
Simple starter script for Pathavana backend development.
This script bypasses the complex async setup and uses basic FastAPI with SQLite.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    
    print("✅ FastAPI imported successfully")
except ImportError as e:
    print(f"❌ Error importing FastAPI: {e}")
    print("Please install required packages or run: pip install fastapi uvicorn")
    sys.exit(1)

# Try to import our configuration
try:
    from app.core.config import settings
    print("✅ Configuration loaded successfully")
    print(f"🏠 App Name: {settings.APP_NAME}")
    print(f"🌐 API Version: {settings.API_V1_STR}")
    print(f"🔗 CORS Origins: {settings.get_cors_origins()}")
except Exception as e:
    print(f"❌ Error loading configuration: {e}")
    # Create a minimal settings object
    class SimpleSettings:
        APP_NAME = "Pathavana Travel API"
        API_V1_STR = "/api"
        BACKEND_CORS_ORIGINS = "http://localhost:3000,http://localhost:5173"
        
        def get_cors_origins(self):
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
    
    settings = SimpleSettings()
    print("⚠️  Using minimal configuration fallback")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered travel planning and booking platform",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "message": "Welcome to Pathavana API!",
        "status": "healthy",
        "version": "1.0.0",
        "docs": f"{settings.API_V1_STR}/docs"
    }

@app.get(f"{settings.API_V1_STR}/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "pathavana-backend",
        "version": "1.0.0"
    }

@app.get(f"{settings.API_V1_STR}/info")
async def app_info():
    """Application information."""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "description": "AI-powered travel planning platform",
        "api_version": settings.API_V1_STR,
        "status": "development"
    }

# Simple demo endpoint
@app.post(f"{settings.API_V1_STR}/travel/sessions")
async def create_travel_session(message: dict):
    """Demo endpoint for travel session creation."""
    user_message = message.get("message", "")
    
    return {
        "success": True,
        "data": {
            "session_id": "demo-session-12345",
            "message": f"I received your message: '{user_message}'",
            "status": "This is a demo response. Full AI integration requires external APIs.",
            "suggestions": [
                "Tell me more about your travel dates",
                "What's your preferred budget range?",
                "Any specific destinations in mind?"
            ]
        },
        "metadata": {
            "timestamp": "2024-01-01T00:00:00Z",
            "version": "1.0.0"
        }
    }

if __name__ == "__main__":
    print("\n🚀 Starting Pathavana Backend (Simple Mode)")
    print("=" * 50)
    print(f"📍 API Documentation: http://localhost:8000{settings.API_V1_STR}/docs")
    print(f"📍 Health Check: http://localhost:8000{settings.API_V1_STR}/health")
    print(f"📍 Frontend CORS: {', '.join(settings.get_cors_origins())}")
    print("=" * 50)
    
    uvicorn.run(
        "simple_start:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )