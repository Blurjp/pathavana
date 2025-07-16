#!/usr/bin/env python3
"""
Debug endpoint to see actual error
"""
import asyncio
import aiohttp
import json

async def test_profile_endpoint():
    """Test user profile endpoint with debug info"""
    
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
            print(f"✅ Login successful! Token: {token[:20]}...")
        
        # Test profile endpoint
        headers = {"Authorization": f"Bearer {token}"}
        
        print("\nTesting GET /api/v1/users/profile...")
        async with session.get("http://localhost:8001/api/v1/users/profile", headers=headers) as resp:
            print(f"Status: {resp.status}")
            response_text = await resp.text()
            print(f"Response: {response_text}")
            
            if resp.status != 200:
                # Try to get more details
                try:
                    error_data = json.loads(response_text)
                    print(f"Error detail: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"Raw response: {response_text}")

if __name__ == "__main__":
    asyncio.run(test_profile_endpoint())