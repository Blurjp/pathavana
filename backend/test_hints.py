#!/usr/bin/env python3
"""
Test the hint generation system with various travel queries.
"""
import aiohttp
import asyncio
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8001"


async def test_hints():
    """Test hint generation with various queries."""
    async with aiohttp.ClientSession() as session:
        print("Testing Hint Generation System")
        print("=" * 50)
        
        # Test cases with different travel queries
        test_cases = [
            {
                "name": "Paris Trip Planning",
                "message": "I want to plan a romantic trip to Paris next summer"
            },
            {
                "name": "Tokyo Adventure",
                "message": "Looking for an adventure trip to Tokyo with hiking and cultural experiences"
            },
            {
                "name": "Bali Relaxation",
                "message": "I need a relaxing beach vacation in Bali for 2 weeks"
            },
            {
                "name": "Budget Travel",
                "message": "I'm on a tight budget and want to explore Europe"
            },
            {
                "name": "Family Vacation",
                "message": "Planning a family trip with 2 kids to Disney World"
            }
        ]
        
        for test_case in test_cases:
            print(f"\n\n🧪 Test: {test_case['name']}")
            print("-" * 40)
            
            # Create session
            payload = {
                "message": test_case["message"],
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
                    session_id = data["data"]["session_id"]
                    print(f"✓ Session created: {session_id}")
                    
                    # Print initial response with hints
                    print(f"\n📝 User Query: {test_case['message']}")
                    print(f"\n🤖 AI Response: {data['data']['initial_response']}")
                    
                    # Check for hints in metadata
                    if "metadata" in data and "hints" in data["metadata"]:
                        hints = data["metadata"]["hints"]
                        print(f"\n💡 Hints Generated ({len(hints)}):")
                        for i, hint in enumerate(hints, 1):
                            print(f"   {i}. [{hint['type']}] {hint['text']}")
                            print(f"      Action: {hint['action']}")
                    
                    # Check conversation state
                    if "metadata" in data and "conversation_state" in data["metadata"]:
                        print(f"\n📊 Conversation State: {data['metadata']['conversation_state']}")
                    
                    # Check extracted entities
                    if "metadata" in data and "extracted_entities" in data["metadata"]:
                        entities = data["metadata"]["extracted_entities"]
                        if entities:
                            print(f"\n🔍 Extracted Entities:")
                            for entity in entities:
                                print(f"   - {entity['type']}: {entity['value']} (confidence: {entity['confidence']})")
                    
                    # Test follow-up message
                    follow_up_messages = {
                        "Paris Trip Planning": "I prefer 5-star hotels with a view of the Eiffel Tower",
                        "Tokyo Adventure": "What's the best time to see cherry blossoms?",
                        "Bali Relaxation": "I want to stay in Ubud and do yoga retreats",
                        "Budget Travel": "My budget is $50 per day including accommodation",
                        "Family Vacation": "The kids are 6 and 8 years old"
                    }
                    
                    if test_case["name"] in follow_up_messages:
                        print(f"\n\n📨 Sending follow-up message...")
                        chat_payload = {
                            "message": follow_up_messages[test_case["name"]],
                            "metadata": {}
                        }
                        
                        async with session.post(
                            f"{BASE_URL}/api/v1/travel/sessions/{session_id}/chat",
                            json=chat_payload,
                            headers={"Content-Type": "application/json"}
                        ) as chat_resp:
                            if chat_resp.status == 200:
                                chat_data = await chat_resp.json()
                                
                                if chat_data.get("data"):
                                    print(f"📝 Follow-up: {follow_up_messages[test_case['name']]}")
                                    print(f"🤖 Response: {chat_data['data'].get('message', 'No message')}")
                                    
                                    # Check for updated hints
                                    if "hints" in chat_data["data"]:
                                        hints = chat_data["data"]["hints"]
                                        print(f"\n💡 Updated Hints ({len(hints)}):")
                                        for i, hint in enumerate(hints, 1):
                                            print(f"   {i}. [{hint['type']}] {hint['text']}")
                else:
                    print(f"❌ Failed to create session: {resp.status}")
                    error_text = await resp.text()
                    print(f"   Error: {error_text}")
        
        print("\n\n✅ Hint generation testing complete!")


def print_summary():
    """Print summary of hint generation features."""
    print("\n" + "=" * 50)
    print("HINT GENERATION FEATURES")
    print("=" * 50)
    print("""
1. Conversation State Tracking:
   - Initial, Destination Selection, Date Selection
   - Hotel/Flight Search, Activity Planning
   - Budget Discussion, Finalization

2. Entity Extraction:
   - Destinations (cities, regions)
   - Dates (relative, absolute, seasonal)
   - Activities and interests
   - Budget preferences

3. Contextual Hints:
   - State-specific suggestions
   - Destination-specific tips
   - Activity recommendations
   - Budget optimization
   - Seasonal advice

4. Enhanced Features:
   - Destination guides and tips
   - Neighborhood recommendations
   - Price alerts and savings tips
   - Comparison tools
   - Pre-trip checklists
    """)


if __name__ == "__main__":
    print("Pathavana Hint Generation Test")
    print("Make sure the backend server is running on http://localhost:8001")
    print("\nStarting tests...")
    
    asyncio.run(test_hints())
    print_summary()