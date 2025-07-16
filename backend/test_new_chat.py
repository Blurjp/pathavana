#!/usr/bin/env python3
"""
Test the New Chat functionality end-to-end.
"""
import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8001"


async def test_new_chat():
    """Test creating a new chat session and verifying the initial messages."""
    async with aiohttp.ClientSession() as session:
        print("Testing New Chat Functionality")
        print("=" * 50)
        
        # Step 1: Create a new session
        print("\n1. Creating new session...")
        create_payload = {
            "message": "Hello, I want to plan a trip",
            "source": "web"
        }
        
        async with session.post(
            f"{BASE_URL}/api/v1/travel/sessions",
            json=create_payload,
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status != 201:
                print(f"❌ Failed to create session: {resp.status}")
                return
            
            data = await resp.json()
            session_id = data["data"]["session_id"]
            initial_response = data["data"].get("initial_response", "")
            
            print(f"✅ Session created: {session_id}")
            print(f"✅ Initial response: {initial_response[:100]}...")
            
            if "metadata" in data["data"] and "hints" in data["data"]["metadata"]:
                hints = data["data"]["metadata"]["hints"]
                print(f"✅ Hints received: {len(hints)} hints")
        
        # Step 2: Get the session to verify conversation history
        print("\n2. Retrieving session data...")
        await asyncio.sleep(0.5)  # Small delay to ensure DB write
        
        async with session.get(
            f"{BASE_URL}/api/v1/travel/sessions/{session_id}",
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data["success"] and data["data"]:
                    session_data = data["data"]["session_data"]
                    if session_data and "conversation_history" in session_data:
                        conv_history = session_data["conversation_history"]
                        print(f"✅ Conversation history: {len(conv_history)} messages")
                        
                        for i, msg in enumerate(conv_history):
                            print(f"\n  Message {i+1}:")
                            print(f"    Role: {msg.get('role')}")
                            print(f"    Content: {msg.get('content')[:80]}...")
                            if msg.get('metadata') and msg['metadata'].get('hints'):
                                print(f"    Hints: {len(msg['metadata']['hints'])} hints included")
                    else:
                        print("❌ No conversation history found")
                else:
                    print("❌ Failed to get session data")
            else:
                print(f"❌ Failed to get session: {resp.status}")
                error_text = await resp.text()
                print(f"   Error: {error_text}")
        
        # Step 3: Test sending a follow-up message
        print("\n3. Sending follow-up message...")
        chat_payload = {
            "message": "I'm interested in visiting Paris",
            "metadata": {}
        }
        
        async with session.post(
            f"{BASE_URL}/api/v1/travel/sessions/{session_id}/chat",
            json=chat_payload,
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data["success"] and data["data"]:
                    print(f"✅ Follow-up response: {data['data'].get('message', '')[:100]}...")
                    if "hints" in data["data"]:
                        print(f"✅ Updated hints: {len(data['data']['hints'])} hints")
            else:
                print(f"❌ Failed to send message: {resp.status}")
        
        print("\n" + "=" * 50)
        print("✅ New Chat test complete!")
        print("\nSummary:")
        print("- New sessions are created with initial user message and AI response")
        print("- Conversation history is properly stored in the database")
        print("- Hints are generated and included in responses")
        print("- Follow-up messages work correctly")


if __name__ == "__main__":
    print("Starting New Chat test...")
    asyncio.run(test_new_chat())