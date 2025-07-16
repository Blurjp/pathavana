#!/usr/bin/env python3
"""
Test script to verify debug logging is working.
"""

import asyncio
import aiohttp
import json

API_BASE_URL = "http://localhost:8001/api/v1"

async def test_debug_logging():
    """Test that debug logs appear in console."""
    print("Testing Debug Logging...")
    print("Watch the backend console for debug output!")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Create a session
        print("\n1. Creating session (watch for debug logs)...")
        payload = {
            "message": "I want to plan a trip to Paris",
            "source": "debug_test",
            "metadata": {"test": True}
        }
        
        async with session.post(f"{API_BASE_URL}/travel/sessions", json=payload) as resp:
            if resp.status == 201:
                data = await resp.json()
                session_id = data["data"]["session_id"]
                print(f"✅ Session created: {session_id}")
                
                # Send a chat message
                print("\n2. Sending chat message (watch for _generate_ai_response debug logs)...")
                chat_payload = {
                    "message": "I want to go in April for 2 weeks",
                    "metadata": {"test": True}
                }
                
                async with session.post(
                    f"{API_BASE_URL}/travel/sessions/{session_id}/chat",
                    json=chat_payload
                ) as chat_resp:
                    if chat_resp.status == 200:
                        print("✅ Chat message sent successfully")
                        print("\nCheck backend console for:")
                        print("- 🗨️  PROCESSING CHAT MESSAGE")
                        print("- 🤖 _generate_ai_response called")
                        print("- Debug messages showing orchestrator status")
                    else:
                        print(f"❌ Chat failed: {chat_resp.status}")
            else:
                print(f"❌ Session creation failed: {resp.status}")

if __name__ == "__main__":
    asyncio.run(test_debug_logging())