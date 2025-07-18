#!/usr/bin/env python3
"""
Simple test to check if AI search is working
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8001"

async def test_simple_search():
    """Test simple search messages."""
    async with aiohttp.ClientSession() as session:
        print("Testing Simple AI Search")
        print("=" * 60)
        
        # 1. Create session
        print("\n1. Creating session...")
        create_response = await session.post(
            f"{BASE_URL}/api/v1/travel/sessions",
            json={"message": "Hello"}
        )
        create_data = await create_response.json()
        session_id = create_data["data"]["session_id"]
        print(f"✅ Session created: {session_id}")
        
        # 2. Simple flight search
        print("\n2. Testing simple flight search...")
        messages = [
            "Find flights to Tokyo",
            "Show me flights from NYC to Paris",
            "I need a flight to London"
        ]
        
        for msg in messages:
            print(f"\nTrying: '{msg}'")
            chat_response = await session.post(
                f"{BASE_URL}/api/v1/travel/sessions/{session_id}/chat",
                json={"message": msg}
            )
            chat_data = await chat_response.json()
            
            if chat_data.get("success"):
                print(f"✅ Response received")
                print(f"Message preview: {chat_data['data']['message'][:100]}...")
                
                # Check for search results
                if "searchResults" in chat_data["data"]:
                    print("✅ SEARCH RESULTS FOUND!")
                else:
                    print("❌ No search results")
                    
                # Check if search was triggered
                if chat_data["data"].get("search_triggered"):
                    print("✅ Search was triggered!")
            else:
                print(f"❌ Error: {chat_data}")

if __name__ == "__main__":
    asyncio.run(test_simple_search())