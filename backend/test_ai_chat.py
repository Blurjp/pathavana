#!/usr/bin/env python3
"""
Test AI chat functionality
"""

import asyncio
import aiohttp
import json

API_BASE_URL = "http://localhost:8001/api/v1"

async def test_ai_chat():
    """Test AI chat responses."""
    print("Testing AI Chat Functionality")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Create a session
        print("\n1. Creating session...")
        payload = {
            "message": "I want to plan a trip to Paris",
            "source": "test",
            "metadata": {"test": True}
        }
        
        async with session.post(f"{API_BASE_URL}/travel/sessions", json=payload) as resp:
            if resp.status == 201:
                data = await resp.json()
                session_id = data["data"]["session_id"]
                initial_response = data["data"]["initial_response"]
                print(f"✅ Session created: {session_id}")
                print(f"Initial response: {initial_response}")
                
                # Send a chat message
                print("\n2. Sending chat message...")
                chat_payload = {
                    "message": "I want to go in April for 2 weeks with my family",
                    "metadata": {"test": True}
                }
                
                async with session.post(
                    f"{API_BASE_URL}/travel/sessions/{session_id}/chat",
                    json=chat_payload
                ) as chat_resp:
                    if chat_resp.status == 200:
                        chat_data = await chat_resp.json()
                        ai_response = chat_data["data"]["message"]
                        print("✅ Chat message sent successfully")
                        print(f"\nAI Response:\n{'-' * 40}")
                        print(ai_response)
                        print(f"{'-' * 40}")
                        
                        # Check if it's a template response
                        if "I'm here to assist with your travel planning" in ai_response:
                            print("\n⚠️  TEMPLATE RESPONSE DETECTED")
                            print("The AI orchestrator is not working properly.")
                            print("Check backend logs for errors.")
                        else:
                            print("\n✅ AI ORCHESTRATOR IS WORKING!")
                            print("The response appears to be from the AI model.")
                    else:
                        error_text = await chat_resp.text()
                        print(f"❌ Chat failed: {chat_resp.status}")
                        print(f"Error: {error_text}")
            else:
                error_text = await resp.text()
                print(f"❌ Session creation failed: {resp.status}")
                print(f"Error: {error_text}")

if __name__ == "__main__":
    asyncio.run(test_ai_chat())