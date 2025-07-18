#!/usr/bin/env python3
"""
Test script to verify AI search functionality
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8001"

async def test_search_results():
    """Test if AI properly triggers searches and returns results."""
    async with aiohttp.ClientSession() as session:
        print("Testing AI Search Functionality")
        print("=" * 60)
        
        # 1. Create session
        print("\n1. Creating session...")
        create_response = await session.post(
            f"{BASE_URL}/api/v1/travel/sessions",
            json={"message": "I want to plan a trip"}
        )
        create_data = await create_response.json()
        session_id = create_data["data"]["session_id"]
        print(f"✅ Session created: {session_id}")
        
        # 2. Send flight search message
        print("\n2. Sending flight search message...")
        flight_msg = "Search for flights from San Francisco to Tokyo next month"
        chat_response = await session.post(
            f"{BASE_URL}/api/v1/travel/sessions/{session_id}/chat",
            json={"message": flight_msg}
        )
        chat_data = await chat_response.json()
        
        print(f"\nAI Response:")
        print("-" * 40)
        print(chat_data["data"]["message"])
        print("-" * 40)
        
        # Check for search results
        if "searchResults" in chat_data["data"]:
            search_results = chat_data["data"]["searchResults"]
            print(f"\n✅ SEARCH RESULTS FOUND!")
            print(f"Search results keys: {list(search_results.keys())}")
            
            if "flights" in search_results:
                print(f"Number of flights found: {len(search_results['flights'])}")
        else:
            print(f"\n❌ NO SEARCH RESULTS IN RESPONSE")
            print(f"Response keys: {list(chat_data['data'].keys())}")
        
        # 3. Send hotel search message
        print("\n\n3. Sending hotel search message...")
        hotel_msg = "Find hotels in Tokyo near Shibuya"
        hotel_response = await session.post(
            f"{BASE_URL}/api/v1/travel/sessions/{session_id}/chat",
            json={"message": hotel_msg}
        )
        hotel_data = await hotel_response.json()
        
        print(f"\nAI Response:")
        print("-" * 40)
        print(hotel_data["data"]["message"])
        print("-" * 40)
        
        # Check for search results
        if "searchResults" in hotel_data["data"]:
            search_results = hotel_data["data"]["searchResults"]
            print(f"\n✅ SEARCH RESULTS FOUND!")
            print(f"Search results keys: {list(search_results.keys())}")
            
            if "hotels" in search_results:
                print(f"Number of hotels found: {len(search_results['hotels'])}")
        else:
            print(f"\n❌ NO SEARCH RESULTS IN RESPONSE")
            print(f"Response keys: {list(hotel_data['data'].keys())}")
        
        # Check if search was triggered
        if chat_data["data"].get("search_triggered") or hotel_data["data"].get("search_triggered"):
            print(f"\n✅ Search was triggered!")
        else:
            print(f"\n⚠️ Search trigger flag not set")

if __name__ == "__main__":
    asyncio.run(test_search_results())