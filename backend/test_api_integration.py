#!/usr/bin/env python3
"""
Test the API integration to simulate frontend requests.
"""
import aiohttp
import asyncio
import json

BASE_URL = "http://localhost:8001"

async def test_api():
    """Test the API endpoints."""
    async with aiohttp.ClientSession() as session:
        print("Testing Travel Session API")
        print("=" * 50)
        
        # Test 1: Create a session
        print("\n1. Creating travel session...")
        payload = {
            "message": "I want to plan a trip to Paris next summer",
            "source": "web",
            "metadata": {"test": True}
        }
        
        async with session.post(
            f"{BASE_URL}/api/v1/travel/sessions",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status == 201:
                data = await resp.json()
                session_id = data["data"]["session_id"]
                print(f"✓ Created session: {session_id}")
                print(f"  Initial response: {data['data']['initial_response'][:100]}...")
            else:
                print(f"❌ Failed to create session: {resp.status}")
                text = await resp.text()
                print(f"  Error: {text}")
                return
        
        # Test 2: Send a chat message
        print("\n2. Sending chat message...")
        chat_payload = {
            "message": "I prefer 5-star hotels with a pool",
            "metadata": {}
        }
        
        async with session.post(
            f"{BASE_URL}/api/v1/travel/sessions/{session_id}/chat",
            json=chat_payload,
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✓ Chat message sent successfully")
                print(f"  AI response: {data['data']['message'][:100]}...")
            else:
                print(f"❌ Failed to send chat message: {resp.status}")
                text = await resp.text()
                print(f"  Error: {text}")
        
        # Test 3: Test session recovery (simulate lost session)
        print("\n3. Testing session recovery...")
        fake_session_id = "a89dc689-ad84-407a-8fbb-0a45a7cf7a1a"  # The session ID from the user's error
        
        async with session.post(
            f"{BASE_URL}/api/v1/travel/sessions/{fake_session_id}/chat",
            json={"message": "Hello, I lost my session", "metadata": {}},
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✓ Session recovered successfully!")
                print(f"  AI response: {data['data']['message'][:100]}...")
            else:
                print(f"❌ Failed to recover session: {resp.status}")
                text = await resp.text()
                print(f"  Error: {text}")
        
        print("\n✅ API integration test complete!")

if __name__ == "__main__":
    print("Make sure the backend server is running on http://localhost:8001")
    print("You can start it with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8001")
    print("\nStarting tests...")
    
    asyncio.run(test_api())