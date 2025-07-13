#!/usr/bin/env python3
"""Check OAuth configuration"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("OAuth Configuration Check")
print("=" * 50)

# Check Google OAuth
google_client_id = os.getenv('GOOGLE_CLIENT_ID', '')
google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET', '')

print("Google OAuth:")
print(f"  Client ID: {'✓ Configured' if google_client_id else '✗ Not configured'}")
print(f"  Client Secret: {'✓ Configured' if google_client_secret else '✗ Not configured'}")
if google_client_id:
    print(f"  Client ID preview: {google_client_id[:20]}...")

# Check Facebook OAuth
facebook_app_id = os.getenv('FACEBOOK_APP_ID', '')
facebook_app_secret = os.getenv('FACEBOOK_APP_SECRET', '')

print("\nFacebook OAuth:")
print(f"  App ID: {'✓ Configured' if facebook_app_id else '✗ Not configured'}")
print(f"  App Secret: {'✓ Configured' if facebook_app_secret else '✗ Not configured'}")
if facebook_app_id:
    print(f"  App ID preview: {facebook_app_id[:20]}...")

# Check other important settings
print("\nOther Settings:")
print(f"  Backend CORS Origins: {os.getenv('BACKEND_CORS_ORIGINS', 'Not set')}")
print(f"  Secret Key: {'✓ Configured' if os.getenv('SECRET_KEY') else '✗ Not configured'}")

print("\n" + "=" * 50)

if not (google_client_id and google_client_secret and facebook_app_id and facebook_app_secret):
    print("\n⚠️  OAuth is not fully configured!")
    print("\nTo configure OAuth:")
    print("1. Create a .env file in the backend directory")
    print("2. Add the following variables:")
    print("   GOOGLE_CLIENT_ID=your_google_client_id")
    print("   GOOGLE_CLIENT_SECRET=your_google_client_secret")
    print("   FACEBOOK_APP_ID=your_facebook_app_id") 
    print("   FACEBOOK_APP_SECRET=your_facebook_app_secret")
    print("\nRefer to OAUTH_SETUP_GUIDE.md for detailed instructions.")
else:
    print("\n✅ OAuth is configured!")