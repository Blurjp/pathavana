"""
Configuration API endpoints for frontend.
"""

from fastapi import APIRouter
import os
from dotenv import load_dotenv

router = APIRouter()

@router.get("/frontend-config")
async def get_frontend_config():
    """
    Get frontend configuration from backend environment.
    Dynamically loads environment variables to reflect changes.
    """
    # Reload environment variables to get latest values
    load_dotenv(override=True)
    
    # Try to get the actual running port from environment
    # Check multiple possible port variables
    actual_port = os.getenv('PORT') or os.getenv('SERVER_PORT') or '8001'
    
    # Determine the correct backend URL
    backend_url = f"http://localhost:{actual_port}"
    frontend_url = "http://localhost:3000"  # Default frontend URL
    
    # Get CORS origins
    cors_origins = os.getenv('BACKEND_CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173')
    
    return {
        "apiBaseUrl": backend_url,
        "oauthRedirectUri": f"{frontend_url}/auth/callback",
        "corsOrigins": cors_origins.split(",") if cors_origins else [],
        "features": {
            "googleOAuth": bool(os.getenv('GOOGLE_CLIENT_ID') and os.getenv('GOOGLE_CLIENT_SECRET')),
            "facebookOAuth": bool(os.getenv('FACEBOOK_APP_ID') and os.getenv('FACEBOOK_APP_SECRET')),
        }
    }