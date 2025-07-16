#!/usr/bin/env python3
"""
Test the SSE streaming endpoint.
"""
import aiohttp
import asyncio
import json

BASE_URL = "http://localhost:8001"


async def test_sse_stream():
    """Test the SSE streaming endpoint."""
    async with aiohttp.ClientSession() as session:
        print("Testing SSE Streaming Endpoint")
        print("=" * 50)
        
        # First create a session
        print("\n1. Creating travel session...")
        payload = {
            "message": "I want to plan a trip to Tokyo",
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
            print(f"✓ Created session: {session_id}")
        
        # Test streaming endpoint
        print("\n2. Testing SSE stream...")
        chat_payload = {
            "message": "I want to stay in a traditional ryokan",
            "metadata": {}
        }
        
        try:
            async with session.post(
                f"{BASE_URL}/api/v1/travel/sessions/{session_id}/chat/stream",
                json=chat_payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                }
            ) as resp:
                print(f"Response status: {resp.status}")
                print(f"Content-Type: {resp.headers.get('Content-Type')}")
                
                if resp.status == 200:
                    print("\n📡 Streaming response:")
                    print("-" * 40)
                    
                    # Read SSE stream
                    async for line in resp.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            try:
                                data_str = line_str[6:]  # Remove 'data: ' prefix
                                data = json.loads(data_str)
                                
                                if data.get('type') == 'content':
                                    print(f"💬 {data.get('content', '')}", end='', flush=True)
                                elif data.get('type') == 'hints':
                                    print(f"\n\n💡 Hints received: {len(data.get('hints', []))}")
                                    for hint in data.get('hints', []):
                                        print(f"   - [{hint['type']}] {hint['text']}")
                                elif data.get('type') == 'metadata':
                                    print(f"\n📊 State: {data.get('conversation_state')}")
                                elif data.get('type') == 'done':
                                    print(f"\n✅ Stream complete!")
                                    break
                                elif data.get('type') == 'error':
                                    print(f"\n❌ Error: {data.get('message')}")
                                    break
                            except json.JSONDecodeError:
                                print(f"Failed to parse: {line_str}")
                else:
                    print(f"❌ Failed with status: {resp.status}")
                    error_text = await resp.text()
                    print(f"Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Connection error: {type(e).__name__}: {e}")
        
        print("\n\n✅ SSE test complete!")


if __name__ == "__main__":
    print("Starting SSE streaming test...")
    asyncio.run(test_sse_stream())