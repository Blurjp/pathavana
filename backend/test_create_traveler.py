#!/usr/bin/env python3
"""
Test creating a traveler to see validation error
"""
import asyncio
import aiohttp
import json

async def test_create_traveler():
    """Test creating a traveler with minimal data"""
    
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
        
        # Test different traveler data
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: Minimal required data
        traveler_data = {
            "first_name": "John",
            "last_name": "Traveler"
        }
        
        print("\nTest 1: Creating traveler with minimal data...")
        print(f"Request data: {json.dumps(traveler_data, indent=2)}")
        
        async with session.post(
            "http://localhost:8001/api/v1/travelers/", 
            headers=headers,
            json=traveler_data
        ) as resp:
            print(f"Status: {resp.status}")
            response_text = await resp.text()
            
            if resp.status == 422:
                print("❌ Validation error:")
                error_data = json.loads(response_text)
                print(json.dumps(error_data, indent=2))
            elif resp.status == 201:
                print("✅ Traveler created successfully!")
                data = json.loads(response_text)
                if 'data' in data:
                    print(f"Traveler ID: {data['data'].get('id')}")
            else:
                print(f"Response: {response_text}")
        
        # Test 2: With more fields
        traveler_data2 = {
            "first_name": "Jane",
            "last_name": "Doe",
            "date_of_birth": "1990-05-15",
            "nationality": "US",
            "relationship_to_user": "spouse"
        }
        
        print("\nTest 2: Creating traveler with more data...")
        print(f"Request data: {json.dumps(traveler_data2, indent=2)}")
        
        async with session.post(
            "http://localhost:8001/api/v1/travelers/", 
            headers=headers,
            json=traveler_data2
        ) as resp:
            print(f"Status: {resp.status}")
            response_text = await resp.text()
            
            if resp.status == 422:
                print("❌ Validation error:")
                error_data = json.loads(response_text)
                print(json.dumps(error_data, indent=2))
            elif resp.status == 201:
                print("✅ Traveler created successfully!")
                data = json.loads(response_text)
                if 'data' in data:
                    print(f"Traveler ID: {data['data'].get('id')}")
            else:
                print(f"Response: {response_text}")

if __name__ == "__main__":
    asyncio.run(test_create_traveler())