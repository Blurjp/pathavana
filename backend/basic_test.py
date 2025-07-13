#!/usr/bin/env python3
"""
Basic test to verify Pathavana backend structure and configuration.
"""

import sys
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Testing Pathavana Backend Structure")
print("=" * 50)

# Test configuration loading
try:
    from app.core.config import settings
    print("✅ Configuration loaded successfully")
    print(f"   🏠 App Name: {settings.APP_NAME}")
    print(f"   🌐 API Version: {settings.API_V1_STR}")
    print(f"   🔗 CORS Origins: {settings.get_cors_origins()}")
    print(f"   🗄️  Database URL: {settings.DATABASE_URL}")
    config_loaded = True
except Exception as e:
    print(f"❌ Error loading configuration: {e}")
    config_loaded = False

# Test model imports
try:
    from app.models import unified_travel_session, user, booking, traveler
    print("✅ Database models imported successfully")
    print("   📊 Available models:")
    print("      - UnifiedTravelSession")
    print("      - User, UserProfile, TravelPreferences")
    print("      - UnifiedBooking, FlightBooking, HotelBooking")
    print("      - Traveler, TravelerDocument")
    models_loaded = True
except Exception as e:
    print(f"❌ Error importing models: {e}")
    models_loaded = False

# Test service imports
try:
    from app.services import llm_service, amadeus_service, cache_service
    print("✅ Service modules imported successfully")
    print("   🤖 Available services:")
    print("      - LLM Service (AI integration)")
    print("      - Amadeus Service (flight/hotel search)")
    print("      - Cache Service (performance optimization)")
    services_loaded = True
except Exception as e:
    print(f"❌ Error importing services: {e}")
    services_loaded = False

# Test API imports
try:
    from app.api import travel_unified, auth, bookings
    print("✅ API modules imported successfully")
    print("   🌐 Available APIs:")
    print("      - Travel Unified API (main chat interface)")
    print("      - Authentication API (JWT, OAuth)")
    print("      - Bookings API (reservation management)")
    apis_loaded = True
except Exception as e:
    print(f"❌ Error importing APIs: {e}")
    apis_loaded = False

print("\n📋 Summary")
print("=" * 30)
print(f"Configuration: {'✅ Loaded' if config_loaded else '❌ Failed'}")
print(f"Models:        {'✅ Loaded' if models_loaded else '❌ Failed'}")
print(f"Services:      {'✅ Loaded' if services_loaded else '❌ Failed'}")
print(f"APIs:          {'✅ Loaded' if apis_loaded else '❌ Failed'}")

if all([config_loaded, models_loaded, services_loaded, apis_loaded]):
    print("\n🎉 All core components loaded successfully!")
    print("   Backend structure is ready for development.")
else:
    print("\n⚠️  Some components failed to load.")
    print("   This is expected without dependencies installed.")

print(f"\n📁 Project Structure Verification:")
print(f"   Backend root: {os.getcwd()}")
print(f"   App directory: {'✅ Found' if os.path.exists('app') else '❌ Missing'}")
print(f"   Models: {'✅ Found' if os.path.exists('app/models') else '❌ Missing'}")
print(f"   Services: {'✅ Found' if os.path.exists('app/services') else '❌ Missing'}")
print(f"   APIs: {'✅ Found' if os.path.exists('app/api') else '❌ Missing'}")
print(f"   Config: {'✅ Found' if os.path.exists('.env') else '❌ Missing'}")

# Simple HTTP server for demonstration
class PathavanaHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/':
            response = {
                "message": "Welcome to Pathavana API!",
                "status": "healthy",
                "version": "1.0.0",
                "note": "This is a basic demo server. Full functionality requires FastAPI."
            }
        elif path == '/api/health':
            response = {
                "status": "healthy",
                "service": "pathavana-backend",
                "components": {
                    "configuration": config_loaded,
                    "models": models_loaded,
                    "services": services_loaded,
                    "apis": apis_loaded
                }
            }
        else:
            self.send_response(404)
            self.end_headers()
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

if __name__ == "__main__":
    print(f"\n🚀 Starting Basic Demo Server")
    print(f"   📍 URL: http://localhost:8000")
    print(f"   📍 Health: http://localhost:8000/api/health")
    print(f"   Press Ctrl+C to stop")
    
    server = HTTPServer(('localhost', 8000), PathavanaHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n👋 Server stopped")
        server.server_close()