#!/usr/bin/env python3
"""
Detailed test of hint generation to debug the system.
"""
import aiohttp
import asyncio
import json

BASE_URL = "http://localhost:8001"


async def test_hint_details():
    """Test hint generation with detailed output."""
    async with aiohttp.ClientSession() as session:
        print("Detailed Hint Generation Test")
        print("=" * 50)
        
        # Test with Paris trip
        print("\n🧪 Creating session with Paris trip request...")
        payload = {
            "message": "I want to plan a romantic trip to Paris in June for our anniversary",
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
                print("\n✅ Session created successfully!")
                print(f"\n📋 Full Response:")
                print(json.dumps(data, indent=2))
                
                session_id = data["data"]["session_id"]
                
                # Get session details
                print(f"\n\n🔍 Getting session details for {session_id}...")
                async with session.get(
                    f"{BASE_URL}/api/v1/travel/sessions/{session_id}",
                    headers={"Content-Type": "application/json"}
                ) as get_resp:
                    if get_resp.status == 200:
                        session_data = await get_resp.json()
                        
                        # Check conversation history
                        if session_data and session_data.get("data") and session_data["data"].get("session_data", {}).get("conversation_history"):
                            conv_history = session_data["data"]["session_data"]["conversation_history"]
                            print(f"\n📜 Conversation History ({len(conv_history)} messages):")
                            
                            for i, msg in enumerate(conv_history):
                                print(f"\n  Message {i+1}:")
                                print(f"    Role: {msg.get('role')}")
                                print(f"    Content: {msg.get('content')[:100]}...")
                                
                                if msg.get('metadata'):
                                    print(f"    Metadata:")
                                    print(json.dumps(msg['metadata'], indent=6))
                
                # Test chat with hotel request
                print("\n\n📨 Sending hotel search request...")
                chat_payload = {
                    "message": "I need a luxury hotel near the Eiffel Tower with a spa",
                    "metadata": {}
                }
                
                async with session.post(
                    f"{BASE_URL}/api/v1/travel/sessions/{session_id}/chat",
                    json=chat_payload,
                    headers={"Content-Type": "application/json"}
                ) as chat_resp:
                    if chat_resp.status == 200:
                        chat_data = await chat_resp.json()
                        print("\n✅ Chat response received!")
                        
                        if chat_data.get("data"):
                            data = chat_data["data"]
                            print(f"\n🤖 AI Response: {data.get('message', 'No message')}")
                            
                            if "hints" in data:
                                hints = data["hints"]
                                print(f"\n💡 Hints ({len(hints)}):")
                                for hint in hints:
                                    print(f"\n  Hint:")
                                    print(f"    Type: {hint['type']}")
                                    print(f"    Text: {hint['text']}")
                                    print(f"    Action: {hint['action']}")
                            
                            if "conversation_state" in data:
                                print(f"\n📊 Conversation State: {data['conversation_state']}")
                            
                            if "extracted_entities" in data:
                                print(f"\n🔍 Extracted Entities:")
                                for entity in data["extracted_entities"]:
                                    print(f"  - {entity['type']}: {entity['value']} (confidence: {entity['confidence']})")
                            
                            if "next_steps" in data:
                                print(f"\n👣 Next Steps:")
                                for step in data["next_steps"]:
                                    print(f"  - {step}")
            else:
                print(f"❌ Failed to create session: {resp.status}")
                error_text = await resp.text()
                print(f"Error: {error_text}")


if __name__ == "__main__":
    print("Starting detailed hint test...")
    asyncio.run(test_hint_details())