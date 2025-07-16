#!/usr/bin/env python3
"""
Simple demonstration of the hint generation system.
"""
import aiohttp
import asyncio
import json

BASE_URL = "http://localhost:8001"


async def demo_hints():
    """Demonstrate hint generation with a simple example."""
    async with aiohttp.ClientSession() as session:
        print("🌟 Pathavana Hint Generation Demo")
        print("="*50)
        
        # Test 1: Paris trip
        print("\n📍 Demo 1: Paris Trip Planning")
        print("-"*40)
        
        payload = {
            "message": "I want to plan a romantic trip to Paris in June",
            "source": "web"
        }
        
        try:
            async with session.post(
                f"{BASE_URL}/api/v1/travel/sessions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    
                    print(f"✅ Session created successfully!")
                    print(f"\n🤖 AI says: {data['data']['initial_response']}")
                    
                    if "metadata" in data["data"] and "hints" in data["data"]["metadata"]:
                        hints = data["data"]["metadata"]["hints"]
                        print(f"\n💡 Smart Hints Generated:")
                        for i, hint in enumerate(hints, 1):
                            print(f"\n  {i}. {hint['text']}")
                            print(f"     Type: {hint['type']} | Action: {hint['action']}")
                    
                    if "metadata" in data["data"] and "extracted_entities" in data["data"]["metadata"]:
                        entities = data["data"]["metadata"]["extracted_entities"]
                        print(f"\n🔍 What I understood from your message:")
                        for entity in entities:
                            print(f"  - {entity['type'].title()}: {entity['value']}")
                    
                    print(f"\n📊 Planning Stage: {data['data']['metadata'].get('conversation_state', 'unknown')}")
                else:
                    print(f"❌ Error: {resp.status}")
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("\nMake sure the backend server is running!")
            return
        
        print("\n" + "="*50)
        print("✨ Hint Generation Features:")
        print("  • Context-aware suggestions")
        print("  • Destination-specific tips") 
        print("  • Seasonal recommendations")
        print("  • Budget guidance")
        print("  • Smart entity extraction")


if __name__ == "__main__":
    asyncio.run(demo_hints())