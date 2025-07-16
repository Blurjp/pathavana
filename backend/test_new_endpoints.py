#!/usr/bin/env python3
"""
Test script for new backend endpoints (User Profile and Travelers)
"""
import asyncio
import aiohttp
import json
from datetime import date
from typing import Optional, Dict, Any

# Test configuration
BASE_URL = "http://localhost:8001"
API_VERSION = "/api/v1"

# Test user token (you'll need to get a real token by logging in)
TEST_TOKEN = None  # Will be set after login

async def login_user(session: aiohttp.ClientSession) -> Optional[str]:
    """Login to get an auth token - using test credentials"""
    print("\n🔐 Testing Login...")
    
    # Try simple auth first - auth_v2 expects email/password
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    try:
        async with session.post(f"{BASE_URL}{API_VERSION}/auth/login", json=login_data) as resp:
            if resp.status == 200:
                data = await resp.json()
                token = data.get("access_token")
                print(f"✅ Login successful! Token: {token[:20]}...")
                return token
            else:
                print(f"❌ Login failed: {resp.status}")
                error = await resp.text()
                print(f"   Error: {error}")
                return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

async def test_user_profile(session: aiohttp.ClientSession, token: str):
    """Test user profile endpoints"""
    print("\n👤 Testing User Profile Endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test GET profile
    print("\n1. GET /api/v1/users/profile")
    try:
        async with session.get(f"{BASE_URL}{API_VERSION}/users/profile", headers=headers) as resp:
            print(f"   Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"   ✅ Profile retrieved successfully")
                print(f"   User: {data.get('data', {}).get('email', 'N/A')}")
                print(f"   Name: {data.get('data', {}).get('full_name', 'N/A')}")
            else:
                error = await resp.text()
                print(f"   ❌ Error: {error}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test PUT profile
    print("\n2. PUT /api/v1/users/profile")
    update_data = {
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890",
        "profile": {
            "date_of_birth": "1990-01-15",
            "nationality": "US",
            "city": "New York",
            "preferred_language": "en",
            "preferred_currency": "USD"
        },
        "preferences": {
            "preferred_cabin_class": "economy",
            "preferred_seat_type": "aisle",
            "dietary_restrictions": ["vegetarian", "no-nuts"],
            "activity_interests": ["hiking", "museums", "food-tours"],
            "default_budget_range": {
                "min": 1000,
                "max": 3000,
                "currency": "USD"
            }
        }
    }
    
    try:
        async with session.put(
            f"{BASE_URL}{API_VERSION}/users/profile", 
            headers=headers, 
            json=update_data
        ) as resp:
            print(f"   Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"   ✅ Profile updated successfully")
                updated = data.get('data', {})
                print(f"   Name: {updated.get('first_name')} {updated.get('last_name')}")
                print(f"   Preferences saved: {bool(updated.get('preferences'))}")
            else:
                error = await resp.text()
                print(f"   ❌ Error: {error}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

async def test_travelers(session: aiohttp.ClientSession, token: str):
    """Test traveler endpoints"""
    print("\n✈️ Testing Traveler Endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    created_traveler_id = None
    
    # Test GET travelers (list)
    print("\n1. GET /api/v1/travelers/")
    try:
        async with session.get(f"{BASE_URL}{API_VERSION}/travelers/", headers=headers) as resp:
            print(f"   Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                travelers = data.get('data', [])
                print(f"   ✅ Retrieved {len(travelers)} travelers")
                for traveler in travelers[:3]:  # Show first 3
                    print(f"   - {traveler.get('full_name')} ({traveler.get('relationship_to_user', 'N/A')})")
            else:
                error = await resp.text()
                print(f"   ❌ Error: {error}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test POST traveler (create)
    print("\n2. POST /api/v1/travelers/")
    new_traveler = {
        "first_name": "Jane",
        "last_name": "Smith",
        "middle_name": "Marie",
        "date_of_birth": "1992-05-20",
        "gender": "female",
        "nationality": "US",
        "country_of_residence": "US",
        "email": "jane.smith@example.com",
        "phone": "+1987654321",
        "relationship_to_user": "spouse",
        "dietary_restrictions": ["gluten-free"],
        "emergency_contact_name": "John Doe",
        "emergency_contact_phone": "+1234567890"
    }
    
    try:
        async with session.post(
            f"{BASE_URL}{API_VERSION}/travelers/", 
            headers=headers, 
            json=new_traveler
        ) as resp:
            print(f"   Status: {resp.status}")
            if resp.status == 201:
                data = await resp.json()
                traveler = data.get('data', {})
                created_traveler_id = traveler.get('id')
                print(f"   ✅ Traveler created successfully")
                print(f"   ID: {created_traveler_id}")
                print(f"   Name: {traveler.get('full_name')}")
            else:
                error = await resp.text()
                print(f"   ❌ Error: {error}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test GET specific traveler
    if created_traveler_id:
        print(f"\n3. GET /api/v1/travelers/{created_traveler_id}")
        try:
            async with session.get(
                f"{BASE_URL}{API_VERSION}/travelers/{created_traveler_id}", 
                headers=headers
            ) as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    traveler = data.get('data', {})
                    print(f"   ✅ Traveler retrieved successfully")
                    print(f"   Full details available: {bool(traveler.get('dietary_restrictions'))}")
                else:
                    error = await resp.text()
                    print(f"   ❌ Error: {error}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    # Test PUT traveler (update)
    if created_traveler_id:
        print(f"\n4. PUT /api/v1/travelers/{created_traveler_id}")
        update_data = {
            "dietary_restrictions": ["gluten-free", "dairy-free"],
            "frequent_flyer_numbers": {
                "AA": "ABC123456",
                "UA": "XYZ789012"
            }
        }
        
        try:
            async with session.put(
                f"{BASE_URL}{API_VERSION}/travelers/{created_traveler_id}", 
                headers=headers,
                json=update_data
            ) as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    print(f"   ✅ Traveler updated successfully")
                else:
                    error = await resp.text()
                    print(f"   ❌ Error: {error}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    # Test DELETE traveler
    if created_traveler_id:
        print(f"\n5. DELETE /api/v1/travelers/{created_traveler_id}")
        try:
            async with session.delete(
                f"{BASE_URL}{API_VERSION}/travelers/{created_traveler_id}", 
                headers=headers
            ) as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    print(f"   ✅ Traveler deleted (archived) successfully")
                else:
                    error = await resp.text()
                    print(f"   ❌ Error: {error}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

async def test_invalid_requests(session: aiohttp.ClientSession):
    """Test endpoints without authentication"""
    print("\n🚫 Testing Unauthorized Access...")
    
    # Test without token
    print("\n1. GET /api/v1/users/profile (no auth)")
    try:
        async with session.get(f"{BASE_URL}{API_VERSION}/users/profile") as resp:
            print(f"   Status: {resp.status}")
            if resp.status == 401:
                print(f"   ✅ Correctly returned 401 Unauthorized")
            else:
                print(f"   ❌ Unexpected status: {resp.status}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test with invalid token
    print("\n2. GET /api/v1/travelers/ (invalid token)")
    headers = {"Authorization": "Bearer invalid_token_12345"}
    try:
        async with session.get(f"{BASE_URL}{API_VERSION}/travelers/", headers=headers) as resp:
            print(f"   Status: {resp.status}")
            if resp.status == 401:
                print(f"   ✅ Correctly returned 401 for invalid token")
            else:
                print(f"   ❌ Unexpected status: {resp.status}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

async def check_api_docs(session: aiohttp.ClientSession):
    """Check if endpoints are in API documentation"""
    print("\n📚 Checking API Documentation...")
    
    try:
        async with session.get(f"{BASE_URL}{API_VERSION}/openapi.json") as resp:
            if resp.status == 200:
                data = await resp.json()
                paths = data.get('paths', {})
                
                # Check for our endpoints
                endpoints = [
                    "/api/v1/users/profile",
                    "/api/v1/travelers/",
                    "/api/v1/travelers/{traveler_id}"
                ]
                
                for endpoint in endpoints:
                    if endpoint in paths:
                        methods = list(paths[endpoint].keys())
                        print(f"   ✅ {endpoint}: {', '.join(methods).upper()}")
                    else:
                        print(f"   ❌ {endpoint}: NOT FOUND")
            else:
                print(f"   ❌ Could not fetch API docs: {resp.status}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

async def main():
    """Run all tests"""
    print("🚀 Starting Backend Endpoint Tests")
    print(f"   Base URL: {BASE_URL}")
    print(f"   API Version: {API_VERSION}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Check API documentation
        await check_api_docs(session)
        
        # Test unauthorized access
        await test_invalid_requests(session)
        
        # Login to get token
        token = await login_user(session)
        
        if token:
            # Test with authentication
            await test_user_profile(session, token)
            await test_travelers(session, token)
        else:
            print("\n❌ Cannot test authenticated endpoints without valid token")
            print("   Please ensure test user exists or update login credentials")
    
    print("\n" + "=" * 60)
    print("✅ Test suite completed!")

if __name__ == "__main__":
    asyncio.run(main())