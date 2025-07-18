#!/usr/bin/env python3

import asyncio
import aiohttp
import json
import sys
import os

async def test_http_chat():
    """Test the actual HTTP chat endpoint."""
    print("Testing HTTP chat endpoint...")
    
    base_url = "http://localhost:8001/api/v1/travel"
    
    async with aiohttp.ClientSession() as session:
        # First create a session
        create_data = {
            "message": "I want to plan a trip to Paris",
            "source": "web"
        }
        
        print("1. Creating travel session...")
        async with session.post(f"{base_url}/sessions", json=create_data) as resp:
            if resp.status == 201:
                result = await resp.json()
                session_id = result["data"]["session_id"]
                print(f"   ✅ Session created: {session_id}")
            else:
                text = await resp.text()
                print(f"   ❌ Failed to create session: {resp.status} - {text}")
                return
        
        # Now test the chat endpoint
        chat_data = {
            "message": "Hello, I want to plan a trip"
        }
        
        print("2. Testing chat endpoint...")
        async with session.post(f"{base_url}/sessions/{session_id}/chat", json=chat_data) as resp:
            print(f"   Response status: {resp.status}")
            
            if resp.status == 200:
                result = await resp.json()
                print(f"   ✅ Chat successful!")
                print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
            else:
                text = await resp.text()
                print(f"   ❌ Chat failed: {resp.status}")
                print(f"   Error response: {text}")

if __name__ == "__main__":
    asyncio.run(test_http_chat())