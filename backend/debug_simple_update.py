#!/usr/bin/env python3
"""
Debug simple profile update
"""
import asyncio
import aiohttp
import json

async def test_simple_update():
    """Test simple profile update"""
    
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
        
        # Test simple update - just name
        headers = {"Authorization": f"Bearer {token}"}
        
        update_data = {
            "first_name": "Jane",
            "last_name": "Smith"
        }
        
        print("\nTesting PUT /api/v1/users/profile with simple data...")
        print(f"Request data: {json.dumps(update_data, indent=2)}")
        
        async with session.put(
            "http://localhost:8001/api/v1/debug/profile", 
            headers=headers,
            json=update_data
        ) as resp:
            print(f"Status: {resp.status}")
            response_text = await resp.text()
            
            if resp.status == 200:
                data = json.loads(response_text)
                print("✅ Update successful!")
                print(f"Updated name: {data['data'].get('full_name')}")
            else:
                print(f"❌ Error: {response_text}")

if __name__ == "__main__":
    asyncio.run(test_simple_update())