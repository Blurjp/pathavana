#!/usr/bin/env python
"""Test script for Traveler API endpoints"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"
TOKEN = None  # Will be set after login

async def login():
    """Login to get auth token"""
    async with aiohttp.ClientSession() as session:
        data = {
            "email": "test@example.com",
            "password": "testpassword"
        }
        async with session.post(f"{BASE_URL}/api/v1/auth/login", json=data) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result.get("access_token")
            else:
                print(f"Login failed: {resp.status}")
                text = await resp.text()
                print(f"Response: {text}")
                return None

async def test_travelers_api():
    """Test all traveler endpoints"""
    global TOKEN
    
    # First, try to get a token
    TOKEN = await login()
    if not TOKEN:
        print("⚠️  No auth token available, continuing without authentication")
    
    headers = {}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    
    async with aiohttp.ClientSession() as session:
        print("\n🧪 Testing Traveler Endpoints")
        print("=" * 50)
        
        # Test 1: List travelers
        print("\n1. GET /api/v1/travelers/")
        async with session.get(f"{BASE_URL}/api/v1/travelers/", headers=headers) as resp:
            print(f"   Status: {resp.status}")
            data = await resp.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        
        # Test 2: Create traveler
        print("\n2. POST /api/v1/travelers/")
        traveler_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "date_of_birth": "1990-01-01",
            "nationality": "US",
            "dietary_restrictions": ["vegetarian"],
            "accessibility_needs": [],
            "preferences": {
                "flight": {
                    "seat_preference": "aisle",
                    "meal_preference": "vegetarian"
                },
                "hotel": {
                    "bed_preference": "king",
                    "smoking": False
                }
            }
        }
        
        async with session.post(f"{BASE_URL}/api/v1/travelers/", 
                               json=traveler_data, 
                               headers=headers) as resp:
            print(f"   Status: {resp.status}")
            data = await resp.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            if resp.status == 201 and data.get("data") and data["data"].get("id"):
                traveler_id = data["data"]["id"]
                
                # Test 3: Get specific traveler
                print(f"\n3. GET /api/v1/travelers/{traveler_id}")
                async with session.get(f"{BASE_URL}/api/v1/travelers/{traveler_id}", 
                                     headers=headers) as resp:
                    print(f"   Status: {resp.status}")
                    data = await resp.json()
                    print(f"   Response: {json.dumps(data, indent=2)}")
                
                # Test 4: Update traveler
                print(f"\n4. PUT /api/v1/travelers/{traveler_id}")
                update_data = {
                    "phone": "+9876543210",
                    "preferences": {
                        "flight": {
                            "seat_preference": "window"
                        }
                    }
                }
                async with session.put(f"{BASE_URL}/api/v1/travelers/{traveler_id}", 
                                     json=update_data,
                                     headers=headers) as resp:
                    print(f"   Status: {resp.status}")
                    data = await resp.json()
                    print(f"   Response: {json.dumps(data, indent=2)}")
                
                # Test 5: Delete traveler
                print(f"\n5. DELETE /api/v1/travelers/{traveler_id}")
                async with session.delete(f"{BASE_URL}/api/v1/travelers/{traveler_id}", 
                                        headers=headers) as resp:
                    print(f"   Status: {resp.status}")
                    data = await resp.json()
                    print(f"   Response: {json.dumps(data, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_travelers_api())