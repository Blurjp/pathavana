#!/usr/bin/env python3
"""
Debug script to trace AI response generation.
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime


API_BASE_URL = "http://localhost:8001/api/v1"


async def test_session_creation():
    """Test session creation and examine the response."""
    print("\n=== Testing Session Creation ===")
    
    async with aiohttp.ClientSession() as session:
        # Create a session
        payload = {
            "message": "I want to plan a trip to Tokyo",
            "source": "debug_script",
            "metadata": {"test": True}
        }
        
        print(f"Request payload: {json.dumps(payload, indent=2)}")
        
        try:
            async with session.post(
                f"{API_BASE_URL}/travel/sessions",
                json=payload
            ) as response:
                status = response.status
                data = await response.json()
                
                print(f"\nResponse status: {status}")
                print(f"Response data: {json.dumps(data, indent=2)}")
                
                if data.get("success"):
                    session_id = data["data"]["session_id"]
                    initial_response = data["data"].get("initial_response", "NO RESPONSE")
                    
                    print(f"\n✅ Session ID: {session_id}")
                    print(f"📝 Initial Response: {initial_response}")
                    
                    return session_id
                else:
                    print(f"\n❌ Failed: {data}")
                    return None
                    
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return None


async def test_chat_message(session_id: str):
    """Test sending a chat message."""
    print("\n=== Testing Chat Message ===")
    
    async with aiohttp.ClientSession() as session:
        # Send a message
        payload = {
            "message": "I want to go next month for 2 weeks",
            "metadata": {"test": True}
        }
        
        print(f"Session ID: {session_id}")
        print(f"Request payload: {json.dumps(payload, indent=2)}")
        
        try:
            async with session.post(
                f"{API_BASE_URL}/travel/sessions/{session_id}/chat",
                json=payload
            ) as response:
                status = response.status
                data = await response.json()
                
                print(f"\nResponse status: {status}")
                print(f"Response data: {json.dumps(data, indent=2)}")
                
                if data.get("success"):
                    message_response = data["data"].get("message", "NO MESSAGE")
                    print(f"\n📝 AI Response: {message_response}")
                    
                    # Check for hints
                    if "hints" in data["data"]:
                        print(f"💡 Hints: {len(data['data']['hints'])} hints provided")
                    
                    # Check conversation history
                    if "chat_history" in data["data"]:
                        print(f"\n📚 Conversation History:")
                        for i, msg in enumerate(data["data"]["chat_history"]):
                            role = msg.get("role", "unknown")
                            content = msg.get("content", "")[:100]
                            print(f"  {i+1}. [{role}] {content}...")
                else:
                    print(f"\n❌ Failed: {data}")
                    
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def check_backend_logs():
    """Check if we can see debug logs."""
    print("\n=== Checking Backend Logs ===")
    print("Look for these in the backend terminal:")
    print("- 🗨️  PROCESSING CHAT MESSAGE")
    print("- 🤖 _generate_ai_response called")
    print("- 🎨 Using AI Orchestrator for response generation")
    print("- 📋 Using template-based response (no orchestrator)")


async def main():
    """Run all debug tests."""
    print("AI Response Debug Tool")
    print("=" * 50)
    print(f"Testing at: {datetime.now()}")
    print(f"API URL: {API_BASE_URL}")
    
    # Test session creation
    session_id = await test_session_creation()
    
    if session_id:
        # Test chat message
        await asyncio.sleep(1)
        await test_chat_message(session_id)
    
    # Remind to check logs
    await check_backend_logs()
    
    print("\n" + "=" * 50)
    print("Debug complete. Check backend logs for detailed trace.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDebug cancelled.")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)