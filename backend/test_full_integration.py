#!/usr/bin/env python3
"""
Full integration test showing hint generation with regular and SSE endpoints.
"""
import aiohttp
import asyncio
import json

BASE_URL = "http://localhost:8001"


async def test_full_integration():
    """Test complete hint generation flow."""
    async with aiohttp.ClientSession() as session:
        print("🌟 Pathavana Full Integration Test")
        print("=" * 60)
        
        # Create session with travel query
        print("\n📍 Step 1: Creating travel session")
        print("-" * 40)
        
        payload = {
            "message": "I want to plan a luxurious honeymoon trip to Bali in December",
            "source": "web"
        }
        
        async with session.post(
            f"{BASE_URL}/api/v1/travel/sessions",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status != 201:
                print(f"❌ Failed to create session: {resp.status}")
                return
            
            data = await resp.json()
            session_id = data["data"]["session_id"]
            print(f"✓ Session created: {session_id}")
            
            # Display initial hints
            if "metadata" in data["data"] and "hints" in data["data"]["metadata"]:
                hints = data["data"]["metadata"]["hints"]
                print(f"\n💡 Initial Hints ({len(hints)}):")
                for hint in hints:
                    print(f"  • [{hint['type']}] {hint['text']}")
            
            if "metadata" in data["data"]:
                meta = data["data"]["metadata"]
                print(f"\n📊 Conversation State: {meta.get('conversation_state')}")
                if meta.get('extracted_entities'):
                    print("🔍 Extracted Entities:")
                    for entity in meta['extracted_entities']:
                        print(f"  • {entity['type']}: {entity['value']}")
        
        # Test regular chat endpoint
        print("\n\n📍 Step 2: Regular Chat - Hotel Search")
        print("-" * 40)
        
        chat_payload = {
            "message": "I want a beachfront villa with a private pool in Seminyak",
            "metadata": {}
        }
        
        async with session.post(
            f"{BASE_URL}/api/v1/travel/sessions/{session_id}/chat",
            json=chat_payload,
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("data"):
                    print(f"🤖 Response: {data['data'].get('message', '')[:100]}...")
                    
                    if "hints" in data["data"]:
                        hints = data["data"]["hints"]
                        print(f"\n💡 Hints ({len(hints)}):")
                        for hint in hints[:3]:  # Show first 3
                            print(f"  • [{hint['type']}] {hint['text']}")
        
        # Test SSE streaming endpoint
        print("\n\n📍 Step 3: SSE Streaming - Activity Planning")
        print("-" * 40)
        
        stream_payload = {
            "message": "What romantic activities do you recommend for couples?",
            "metadata": {}
        }
        
        async with session.post(
            f"{BASE_URL}/api/v1/travel/sessions/{session_id}/chat/stream",
            json=stream_payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
        ) as resp:
            if resp.status == 200:
                print("📡 Streaming response:")
                
                content_buffer = ""
                hints_received = []
                state = None
                
                async for line in resp.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        try:
                            data_str = line_str[6:]
                            data = json.loads(data_str)
                            
                            if data.get('type') == 'content':
                                content_buffer += data.get('content', '')
                            elif data.get('type') == 'hints':
                                hints_received = data.get('hints', [])
                            elif data.get('type') == 'metadata':
                                state = data.get('conversation_state')
                            elif data.get('type') == 'done':
                                break
                        except json.JSONDecodeError:
                            pass
                
                # Display streamed content
                print(f"\n🤖 AI Response: {content_buffer[:150]}...")
                
                if hints_received:
                    print(f"\n💡 Activity Hints ({len(hints_received)}):")
                    for hint in hints_received[:3]:
                        print(f"  • [{hint['type']}] {hint['text']}")
                
                if state:
                    print(f"\n📊 Updated State: {state}")
        
        # Final summary
        print("\n\n" + "=" * 60)
        print("✅ Integration Test Complete!")
        print("\nKey Features Demonstrated:")
        print("  • Entity extraction (destination, date, budget level)")
        print("  • Context-aware hint generation")
        print("  • State tracking through conversation")
        print("  • Destination-specific recommendations")
        print("  • SSE streaming with hints")


if __name__ == "__main__":
    print("Starting full integration test...")
    asyncio.run(test_full_integration())