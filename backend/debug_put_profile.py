#!/usr/bin/env python3
"""
Debug PUT profile endpoint
"""
import asyncio
import aiohttp
import json

async def test_put_profile():
    """Test PUT profile endpoint with debug info"""
    
    # First login to get token
    async with aiohttp.ClientSession() as session:
        # Login
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        async with session.post("http://localhost:8001/api/v1/auth/login", json=login_data) as resp:
            if resp.status != 200:
                print(f"Login failed: {resp.status}")
                return
            
            data = await resp.json()
            token = data.get("access_token")
            print(f"✅ Login successful!")
        
        # Test PUT profile endpoint
        headers = {"Authorization": f"Bearer {token}"}
        
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
            }
        }
        
        print("\nTesting PUT /api/v1/users/profile...")
        print(f"Request data: {json.dumps(update_data, indent=2)}")
        
        async with session.put(
            "http://localhost:8001/api/v1/users/profile", 
            headers=headers,
            json=update_data
        ) as resp:
            print(f"Status: {resp.status}")
            response_text = await resp.text()
            print(f"Response: {response_text}")

if __name__ == "__main__":
    asyncio.run(test_put_profile())