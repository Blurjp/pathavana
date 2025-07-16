#!/usr/bin/env python3
"""
Test the actual API with a 422 error handling
"""
import asyncio
import aiohttp
import json

async def test_api():
    """Test the actual API endpoint"""
    
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
        
        # Get the raw 422 error
        headers = {"Authorization": f"Bearer {token}"}
        
        # Send empty data to trigger validation error
        print("\nSending empty data to see validation error...")
        
        async with session.post(
            "http://localhost:8001/api/v1/travelers/", 
            headers=headers,
            json={}
        ) as resp:
            print(f"Status: {resp.status}")
            response_text = await resp.text()
            
            if resp.status == 422:
                print("Validation error details:")
                error_data = json.loads(response_text)
                print(json.dumps(error_data, indent=2))

if __name__ == "__main__":
    asyncio.run(test_api())