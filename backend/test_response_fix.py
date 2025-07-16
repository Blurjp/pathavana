#!/usr/bin/env python3
"""
Test script to verify AI responses are working correctly after the fix.
"""

import asyncio
import aiohttp
import json
from datetime import datetime


API_BASE_URL = "http://localhost:8001/api/v1"


async def test_ai_responses():
    """Test that AI responses are properly returned."""
    print("🧪 Testing AI Response Fix")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Create a session
        print("\n1. Creating session...")
        create_payload = {
            "message": "Hi, I want to plan a trip to Paris",
            "source": "test",
            "metadata": {}
        }
        
        async with session.post(f"{API_BASE_URL}/travel/sessions", json=create_payload) as resp:
            if resp.status != 201:
                print(f"❌ Failed to create session: {resp.status}")
                return
            
            data = await resp.json()
            session_id = data["data"]["session_id"]
            initial_response = data["data"].get("initial_response", "NONE")
            print(f"✅ Session created: {session_id}")
            print(f"📝 Initial response: {initial_response[:100]}...")
        
        # Send a few messages
        test_messages = [
            "I want to go in April for 2 weeks",
            "What's the weather like there?",
            "Can you find me flights from New York?",
            "I need a hotel near the Eiffel Tower"
        ]
        
        for i, msg in enumerate(test_messages, 1):
            print(f"\n{i}. Sending: '{msg}'")
            chat_payload = {
                "message": msg,
                "metadata": {}
            }
            
            async with session.post(
                f"{API_BASE_URL}/travel/sessions/{session_id}/chat", 
                json=chat_payload
            ) as resp:
                if resp.status != 200:
                    print(f"❌ Failed to send message: {resp.status}")
                    continue
                
                data = await resp.json()
                if data.get("success") and data.get("data"):
                    # Check what field contains the response
                    response_data = data["data"]
                    
                    # The backend returns 'message' not 'response'
                    ai_message = response_data.get("message", "NO MESSAGE FIELD")
                    
                    # Check if it's the generic response
                    is_generic = ai_message == "I understand. How can I help you plan your trip?"
                    
                    print(f"📝 AI Response: {ai_message[:100]}...")
                    print(f"🔍 Is generic response: {'YES ❌' if is_generic else 'NO ✅'}")
                    
                    # Debug: show available fields
                    print(f"📊 Available fields: {list(response_data.keys())}")
                    
                    # Check for other metadata
                    if "hints" in response_data:
                        print(f"💡 Hints provided: {len(response_data['hints'])}")
                    if "suggestions" in response_data:
                        print(f"💭 Suggestions: {response_data['suggestions']}")
                else:
                    print(f"❌ Invalid response structure")
            
            await asyncio.sleep(0.5)  # Small delay between messages
    
    print("\n" + "=" * 50)
    print("✅ Test complete!")
    print("\nNOTE: If you're still seeing generic responses:")
    print("1. Make sure the frontend is rebuilt (npm start)")
    print("2. Clear browser cache and reload")
    print("3. Check that LLM credentials are configured in backend/.env")


if __name__ == "__main__":
    try:
        asyncio.run(test_ai_responses())
    except KeyboardInterrupt:
        print("\nTest cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {e}")