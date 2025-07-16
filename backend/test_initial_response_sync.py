#!/usr/bin/env python3
"""
Test script to verify initial_response is properly synced with chat messages.
"""

import asyncio
import aiohttp
import json
from datetime import datetime


API_BASE_URL = "http://localhost:8001/api/v1"


async def test_session_creation_flow():
    """Test that initial_response appears in chat messages."""
    print("🧪 Testing Session Creation and Initial Response Sync")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Create a new session with initial message
        print("\n1️⃣ Creating new session with initial message...")
        create_payload = {
            "message": "Hi, I want to plan a trip to Barcelona in June",
            "source": "web",
            "metadata": {"test": True}
        }
        
        print(f"Request: POST /travel/sessions")
        print(f"Payload: {json.dumps(create_payload, indent=2)}")
        
        async with session.post(
            f"{API_BASE_URL}/travel/sessions",
            json=create_payload
        ) as resp:
            if resp.status != 201:
                print(f"❌ Failed to create session: {resp.status}")
                return
            
            data = await resp.json()
            print(f"\n✅ Response Status: {resp.status}")
            print(f"Response Data Keys: {list(data.get('data', {}).keys())}")
            
            if data.get("success") and data.get("data"):
                session_data = data["data"]
                session_id = session_data.get("session_id")
                initial_response = session_data.get("initial_response")
                suggestions = session_data.get("suggestions", [])
                metadata = session_data.get("metadata", {})
                
                print(f"\n📋 Session Details:")
                print(f"  - Session ID: {session_id}")
                print(f"  - Initial Response: {initial_response[:100]}..." if initial_response else "  - Initial Response: NONE")
                print(f"  - Suggestions: {suggestions}")
                print(f"  - Has Metadata: {'Yes' if metadata else 'No'}")
                
                if initial_response:
                    print("✅ Initial response is present in session creation response")
                else:
                    print("❌ Initial response is missing!")
                
                # Step 2: Get the session to verify conversation history
                print(f"\n2️⃣ Getting session to check conversation history...")
                await asyncio.sleep(1)  # Small delay
                
                async with session.get(
                    f"{API_BASE_URL}/travel/sessions/{session_id}"
                ) as resp2:
                    if resp2.status == 200:
                        session_data = await resp2.json()
                        if session_data.get("success") and session_data.get("data"):
                            full_session = session_data["data"]
                            
                            # Check conversation history
                            conv_history = full_session.get("session_data", {}).get("conversation_history", [])
                            print(f"\n📚 Conversation History: {len(conv_history)} messages")
                            
                            for i, msg in enumerate(conv_history):
                                role = msg.get("role", "unknown")
                                content = msg.get("content", "")[:100]
                                print(f"  {i+1}. [{role}] {content}...")
                            
                            # Verify both messages are present
                            has_user_msg = any(msg.get("role") == "user" for msg in conv_history)
                            has_assistant_msg = any(msg.get("role") == "assistant" for msg in conv_history)
                            
                            if has_user_msg and has_assistant_msg:
                                print("\n✅ Both user message and assistant response are in history")
                            else:
                                print(f"\n❌ Missing messages - User: {has_user_msg}, Assistant: {has_assistant_msg}")
                    else:
                        print(f"❌ Failed to get session: {resp2.status}")
                
                # Step 3: Send another message to verify normal chat flow
                print(f"\n3️⃣ Sending follow-up message...")
                chat_payload = {
                    "message": "I prefer budget hotels near the beach",
                    "metadata": {"test": True}
                }
                
                async with session.post(
                    f"{API_BASE_URL}/travel/sessions/{session_id}/chat",
                    json=chat_payload
                ) as resp3:
                    if resp3.status == 200:
                        chat_data = await resp3.json()
                        if chat_data.get("success") and chat_data.get("data"):
                            chat_response = chat_data["data"]
                            message = chat_response.get("message")
                            
                            print(f"\n📨 Chat Response:")
                            print(f"  - Message field present: {'Yes' if 'message' in chat_response else 'No'}")
                            print(f"  - Response: {message[:100]}..." if message else "  - Response: NONE")
                            
                            if message:
                                print("✅ Chat endpoint returns message properly")
                            else:
                                print("❌ Chat endpoint missing message field!")
                    else:
                        print(f"❌ Failed to send chat message: {resp3.status}")
                
                return session_id
            else:
                print("❌ Invalid response structure")
                return None


async def main():
    """Run the test."""
    print("Initial Response Sync Test")
    print(f"Testing at: {datetime.now()}")
    print(f"API URL: {API_BASE_URL}\n")
    
    session_id = await test_session_creation_flow()
    
    if session_id:
        print(f"\n✅ Test completed successfully!")
        print(f"Session ID: {session_id}")
    else:
        print(f"\n❌ Test failed!")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("1. Session creation endpoint should return 'initial_response'")
    print("2. Chat endpoint should return 'message'")
    print("3. Frontend needs to handle both response formats")
    print("4. Both messages should be stored in conversation history")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {e}")