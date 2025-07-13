"""
Production-ready main application file for Pathavana backend.
This file handles both cases: with and without FastAPI dependencies.
"""

import sys
import os
import json
from typing import Optional, Dict, Any

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import FastAPI, fall back to basic HTTP server if not available
try:
    from fastapi import FastAPI, HTTPException, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
    print("✅ FastAPI available - using production mode")
except ImportError:
    FASTAPI_AVAILABLE = False
    print("⚠️  FastAPI not available - using fallback mode")

# Import our configuration
try:
    from app.core.config import settings
    print(f"✅ Configuration loaded: {settings.APP_NAME}")
except Exception as e:
    print(f"❌ Configuration error: {e}")
    sys.exit(1)

if FASTAPI_AVAILABLE:
    # Production FastAPI application
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-powered travel planning and booking platform",
        version=settings.VERSION,
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
    
    # Import and include routers for database endpoints
    try:
        from app.api.endpoints.auth import router as auth_router
        from app.api.endpoints.trips import router as trips_router
        from app.api.endpoints.travelers import router as travelers_router
        from app.api.endpoints.travel_sessions import router as travel_sessions_router
        
        if auth_router:
            app.include_router(auth_router, prefix=f"{settings.API_V1_STR}")
        if trips_router:
            app.include_router(trips_router, prefix=f"{settings.API_V1_STR}")
        if travelers_router:
            app.include_router(travelers_router, prefix=f"{settings.API_V1_STR}")
        if travel_sessions_router:
            app.include_router(travel_sessions_router, prefix=f"{settings.API_V1_STR}")
        
        print("✅ Database endpoints registered")
    except ImportError as e:
        print(f"⚠️  Could not import database routers: {e}")

    # Request/Response models
    class TravelSessionRequest(BaseModel):
        message: str
        source: Optional[str] = "web"

    class TravelSessionResponse(BaseModel):
        success: bool
        data: Dict[str, Any]
        metadata: Dict[str, Any]
        errors: Optional[list] = None

    # Basic endpoints
    @app.get("/")
    async def root():
        """Root endpoint - API health check."""
        return {
            "message": f"Welcome to {settings.APP_NAME}!",
            "status": "healthy",
            "version": settings.VERSION,
            "docs": f"{settings.API_V1_STR}/docs"
        }

    @app.get(f"{settings.API_V1_STR}/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "pathavana-backend",
            "version": settings.VERSION,
            "environment": "production" if not settings.DEBUG else "development"
        }

    @app.get(f"{settings.API_V1_STR}/info")
    async def app_info():
        """Application information."""
        return {
            "name": settings.APP_NAME,
            "version": settings.VERSION,
            "description": "AI-powered travel planning platform",
            "api_version": settings.API_V1_STR,
            "features": [
                "UUID-based session management",
                "AI-powered natural language processing",
                "Multi-source travel data integration",
                "Real-time booking capabilities",
                "GDPR compliance"
            ]
        }

    # Travel session endpoints are now handled by the router imported above
    # See app.api.endpoints.travel_sessions for the database-backed implementation

    # Database-backed endpoints are now handled by routers imported above
    # The trips and travelers endpoints are provided by:
    # - app.api.endpoints.trips
    # - app.api.endpoints.travelers

    # Authentication is now handled by the auth router imported above
    # See app.api.endpoints.auth for signup, signin, and user management

    def run_production_server():
        """Run the production FastAPI server."""
        print(f"\n🚀 Starting {settings.APP_NAME}")
        print("=" * 60)
        print(f"📍 API Documentation: http://localhost:{settings.PORT}{settings.API_V1_STR}/docs")
        print(f"📍 Health Check: http://localhost:{settings.PORT}{settings.API_V1_STR}/health")
        print(f"📍 API Info: http://localhost:{settings.PORT}{settings.API_V1_STR}/info")
        print(f"📍 Travel API: http://localhost:{settings.PORT}{settings.API_V1_STR}/travel/sessions")
        print("=" * 60)
        
        uvicorn.run(
            "app.main_production:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level=settings.LOG_LEVEL.lower()
        )

else:
    # Fallback HTTP server implementation
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlparse, parse_qs
    import json

    class PathavanaHandler(BaseHTTPRequestHandler):
        def _set_headers(self, status_code=200, content_type='application/json'):
            self.send_response(status_code)
            self.send_header('Content-Type', content_type)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            self.end_headers()

        def do_OPTIONS(self):
            self._set_headers()

        def do_GET(self):
            path = urlparse(self.path).path
            
            if path == '/':
                response = {
                    "message": f"Welcome to {settings.APP_NAME}!",
                    "status": "healthy",
                    "version": settings.VERSION,
                    "mode": "fallback",
                    "note": "Running in fallback mode - install FastAPI for full functionality"
                }
            elif path == f'{settings.API_V1_STR}/health':
                response = {
                    "status": "healthy",
                    "service": "pathavana-backend-fallback",
                    "version": settings.VERSION,
                    "mode": "fallback"
                }
            elif path == f'{settings.API_V1_STR}/info':
                response = {
                    "name": settings.APP_NAME,
                    "version": settings.VERSION,
                    "mode": "fallback",
                    "note": "Backend structure is ready - install dependencies for full functionality"
                }
            elif path == f'{settings.API_V1_STR}/trips':
                response = {
                    "success": True,
                    "data": [
                        {
                            "id": "trip-demo-1",
                            "name": "Demo Trip to Paris",
                            "description": "Example trip data",
                            "startDate": "2024-08-15",
                            "endDate": "2024-08-22",
                            "destinations": ["Paris, France"],
                            "travelers": 2,
                            "status": "upcoming"
                        }
                    ],
                    "metadata": {"total": 1, "page": 1, "limit": 10}
                }
            elif path == f'{settings.API_V1_STR}/travelers':
                response = {
                    "success": True,
                    "data": [
                        {
                            "id": "traveler-demo-1",
                            "firstName": "Demo",
                            "lastName": "User",
                            "email": "demo@example.com",
                            "dateOfBirth": "1990-01-01"
                        }
                    ],
                    "metadata": {"total": 1, "page": 1, "limit": 10}
                }
            else:
                self._set_headers(404)
                response = {"error": "Not Found", "path": path}
            
            self._set_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())

        def do_POST(self):
            path = urlparse(self.path).path
            
            if path == f'{settings.API_V1_STR}/travel/sessions':
                # Read request body
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                
                try:
                    request_data = json.loads(post_data) if post_data else {}
                    user_message = request_data.get('message', 'Hello')
                except:
                    user_message = 'Hello'
                
                response = {
                    "success": True,
                    "data": {
                        "session_id": "fallback-session-12345",
                        "message": f"Fallback mode - received: '{user_message}'",
                        "note": "Install FastAPI and dependencies for full AI functionality"
                    },
                    "metadata": {
                        "timestamp": "2024-07-12T00:00:00Z",
                        "version": settings.VERSION,
                        "mode": "fallback"
                    }
                }
            else:
                self._set_headers(404)
                response = {"error": "POST endpoint not found"}
            
            self._set_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())

        def do_PUT(self):
            path = urlparse(self.path).path
            
            if path.startswith(f'{settings.API_V1_STR}/travel/sessions/'):
                # Extract session ID
                session_id = path.split('/')[-1]
                
                # Read request body
                content_length = int(self.headers.get('Content-Length', 0))
                put_data = self.rfile.read(content_length).decode('utf-8')
                
                try:
                    request_data = json.loads(put_data) if put_data else {}
                    user_message = request_data.get('message', 'Update message')
                except:
                    user_message = 'Update message'
                
                response = {
                    "success": True,
                    "data": {
                        "session_id": session_id,
                        "message": f"Fallback mode - updated session with: '{user_message}'",
                        "note": "Install FastAPI and dependencies for full functionality"
                    },
                    "metadata": {
                        "timestamp": "2024-07-12T00:00:00Z",
                        "version": settings.VERSION,
                        "mode": "fallback"
                    }
                }
            else:
                self._set_headers(404)
                response = {"error": "PUT endpoint not found"}
            
            self._set_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())

        def log_message(self, format, *args):
            print(f"🌐 {self.address_string()} - {format % args}")

    def run_fallback_server():
        """Run the fallback HTTP server."""
        print(f"\n🚀 Starting {settings.APP_NAME} (Fallback Mode)")
        print("=" * 60)
        print(f"📍 Backend API: http://localhost:{settings.PORT}")
        print(f"📍 Health Check: http://localhost:{settings.PORT}{settings.API_V1_STR}/health")
        print(f"📍 API Info: http://localhost:{settings.PORT}{settings.API_V1_STR}/info")
        print("=" * 60)
        print("💡 Install FastAPI for full functionality: pip install fastapi uvicorn")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 60)
        
        server = HTTPServer((settings.HOST, settings.PORT), PathavanaHandler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print(f"\n👋 Server stopped")
            server.server_close()

if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        run_production_server()
    else:
        run_fallback_server()