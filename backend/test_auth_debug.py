#!/usr/bin/env python3
"""Debug authentication issue with selenium test account."""

import asyncio
import requests
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import User
from app.core.config import settings

async def check_test_user():
    """Check if test user exists and is properly configured."""
    print("🔍 Checking test user in database...")
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Query for test user
        result = await session.execute(
            select(User).where(User.email == "selenium.test@example.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ Test user not found!")
            return False
        
        print("✅ Test user found:")
        print(f"   - Email: {user.email}")
        print(f"   - Full name: {user.full_name}")
        print(f"   - Status: {user.status}")
        print(f"   - Email verified: {user.email_verified}")
        print(f"   - Has password: {bool(user.password_hash)}")
        print(f"   - Password hash starts with: {user.password_hash[:20] if user.password_hash else 'None'}...")
        
        return True

def test_login_api():
    """Test the login API endpoint."""
    print("\n🔍 Testing login API...")
    
    url = "http://localhost:8001/api/v1/auth/login"
    
    # Test 1: Correct format (JSON with email/password)
    print("\n1️⃣ Testing correct format (JSON):")
    data = {
        "email": "selenium.test@example.com",
        "password": "SeleniumTest123!"
    }
    
    try:
        response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        print(f"   - Status: {response.status_code}")
        print(f"   - Headers: {dict(response.headers)}")
        if response.status_code == 200:
            print("   ✅ Login successful!")
            result = response.json()
            print(f"   - Access token: {result.get('access_token', '')[:20]}...")
            print(f"   - User email: {result.get('user', {}).get('email')}")
        else:
            print("   ❌ Login failed!")
            print(f"   - Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 2: Wrong format (form-urlencoded with username)
    print("\n2️⃣ Testing wrong format (form-urlencoded with username):")
    form_data = {
        "username": "selenium.test@example.com",
        "password": "SeleniumTest123!"
    }
    
    try:
        response = requests.post(url, data=form_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        print(f"   - Status: {response.status_code}")
        print(f"   - Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 3: Check what the frontend is actually sending
    print("\n3️⃣ Checking actual request format...")
    print("   - Frontend should send: POST /api/v1/auth/login")
    print("   - Content-Type: application/json")
    print("   - Body: {\"email\": \"...\", \"password\": \"...\"}")

async def main():
    """Run all checks."""
    print("🚀 Authentication Debug Tool")
    print("=" * 60)
    
    # Check database
    user_exists = await check_test_user()
    
    if not user_exists:
        print("\n⚠️  Test user doesn't exist! Run create_selenium_test_user.py first.")
        return
    
    # Test API
    test_login_api()
    
    print("\n" + "=" * 60)
    print("📋 Next steps:")
    print("1. Check if the backend server is running on port 8001")
    print("2. Check browser console for any CORS errors")
    print("3. Check Network tab in browser DevTools for the actual request")
    print("4. Make sure the frontend is using the updated AuthContext.tsx")

if __name__ == "__main__":
    asyncio.run(main())