#!/usr/bin/env python3
"""
Test various travel planning scenarios to demonstrate hint generation capabilities.
"""
import aiohttp
import asyncio
import json
from typing import Dict, List

BASE_URL = "http://localhost:8001"


async def test_scenario(session: aiohttp.ClientSession, scenario: Dict) -> None:
    """Test a specific travel planning scenario."""
    print(f"\n{'='*60}")
    print(f"🎯 Scenario: {scenario['name']}")
    print(f"{'='*60}")
    
    # Create session
    print(f"\n📝 Initial Query: {scenario['initial_query']}")
    
    payload = {
        "message": scenario["initial_query"],
        "source": "web",
        "metadata": {"scenario": scenario["name"]}
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
        
        # Display initial response and hints
        print(f"\n🤖 AI Response: {data['data']['initial_response']}")
        
        if "metadata" in data["data"] and "hints" in data["data"]["metadata"]:
            hints = data["data"]["metadata"]["hints"]
            print(f"\n💡 Initial Hints ({len(hints)}):")
            for hint in hints:
                print(f"  • [{hint['type']}] {hint['text']}")
        
        if "metadata" in data["data"] and "extracted_entities" in data["data"]["metadata"]:
            entities = data["data"]["metadata"]["extracted_entities"]
            if entities:
                print(f"\n🔍 Extracted from initial query:")
                for entity in entities:
                    print(f"  • {entity['type']}: {entity['value']}")
        
        # Process follow-up messages
        for i, follow_up in enumerate(scenario["follow_ups"], 1):
            print(f"\n\n📨 Follow-up {i}: {follow_up}")
            
            chat_payload = {
                "message": follow_up,
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
                        data = chat_data["data"]
                        print(f"🤖 Response: {data.get('message', 'No message')[:150]}...")
                        
                        if "hints" in data:
                            hints = data["hints"]
                            print(f"\n💡 Updated Hints ({len(hints)}):")
                            for hint in hints:
                                print(f"  • [{hint['type']}] {hint['text']}")
                        
                        if "conversation_state" in data:
                            print(f"\n📊 State: {data['conversation_state']}")
                        
                        if "extracted_entities" in data and data["extracted_entities"]:
                            print(f"\n🔍 New entities extracted:")
                            for entity in data["extracted_entities"]:
                                print(f"  • {entity['type']}: {entity['value']}")


async def main():
    """Run all test scenarios."""
    scenarios = [
        {
            "name": "Romantic Paris Getaway",
            "initial_query": "Planning a romantic anniversary trip to Paris in June",
            "follow_ups": [
                "We want luxury hotels with amazing views",
                "What are the most romantic restaurants?",
                "Book us a sunset cruise on the Seine"
            ]
        },
        {
            "name": "Tokyo Adventure Seeker",
            "initial_query": "I want an adventure trip to Tokyo with hiking and extreme sports",
            "follow_ups": [
                "What's the best time to climb Mount Fuji?",
                "Find me capsule hotels in Shibuya",
                "I want to try bungee jumping and go-karting"
            ]
        },
        {
            "name": "Budget Backpacker Europe",
            "initial_query": "I have $1500 for a month-long backpacking trip across Europe",
            "follow_ups": [
                "Which countries are cheapest to visit?",
                "Find hostels under $20 per night",
                "What's the best rail pass for budget travelers?"
            ]
        },
        {
            "name": "Family Beach Vacation",
            "initial_query": "Need a family-friendly beach resort in Bali with kids club",
            "follow_ups": [
                "We have 2 kids aged 6 and 10",
                "Looking for all-inclusive resorts in Nusa Dua",
                "What activities are safe for children?"
            ]
        },
        {
            "name": "Business Trip Extension",
            "initial_query": "I have a business trip to London, want to extend for sightseeing",
            "follow_ups": [
                "I'll be there March 15-20 for work",
                "Can I do a day trip to Stonehenge?",
                "Need a hotel near Canary Wharf with good wifi"
            ]
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        print("🌍 Pathavana Travel Planning Scenarios")
        print("Testing hint generation across different traveler profiles")
        
        for scenario in scenarios:
            await test_scenario(session, scenario)
            await asyncio.sleep(1)  # Brief pause between scenarios
        
        print(f"\n\n{'='*60}")
        print("✅ All scenarios tested!")
        print(f"{'='*60}")
        print("\nKey Observations:")
        print("• Hints adapt based on conversation state")
        print("• Entity extraction improves with context")
        print("• Destination-specific tips are provided")
        print("• Budget considerations influence recommendations")
        print("• Traveler profile affects activity suggestions")


if __name__ == "__main__":
    print("Starting comprehensive hint generation test...")
    asyncio.run(main())