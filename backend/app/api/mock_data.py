"""
Mock data endpoint for testing the frontend UI.
This provides sample flight and hotel data for development and testing.
"""

from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime, timedelta

router = APIRouter(tags=["mock"])

def get_mock_flights():
    """Generate mock flight data."""
    return [
        {
            "id": "UA890-2024-03-15",
            "airline": "United Airlines",
            "flightNumber": "UA890",
            "origin": {
                "code": "SFO",
                "city": "San Francisco",
                "airport": "San Francisco International",
                "terminal": "3"
            },
            "destination": {
                "code": "NRT",
                "city": "Tokyo",
                "airport": "Narita International",
                "terminal": "1"
            },
            "departureTime": "2024-03-15T08:00:00-07:00",
            "arrivalTime": "2024-03-16T14:30:00+09:00",
            "duration": "10h 30m",
            "price": {
                "amount": 850,
                "currency": "USD",
                "displayPrice": "$850"
            },
            "stops": 0,
            "amenities": ["WiFi", "Entertainment", "Meals", "Power Outlets"],
            "aircraft": "Boeing 787-9"
        },
        {
            "id": "JL001-2024-03-15",
            "airline": "Japan Airlines",
            "flightNumber": "JL001",
            "origin": {
                "code": "SFO",
                "city": "San Francisco",
                "airport": "San Francisco International",
                "terminal": "I"
            },
            "destination": {
                "code": "HND",
                "city": "Tokyo",
                "airport": "Haneda",
                "terminal": "3"
            },
            "departureTime": "2024-03-15T11:00:00-07:00",
            "arrivalTime": "2024-03-16T16:20:00+09:00",
            "duration": "11h 20m",
            "price": {
                "amount": 920,
                "currency": "USD",
                "displayPrice": "$920"
            },
            "stops": 0,
            "amenities": ["WiFi", "Premium Meals", "Entertainment", "Lie-flat Seats"],
            "aircraft": "Boeing 777-300ER"
        },
        {
            "id": "ANA007-2024-03-15",
            "airline": "All Nippon Airways",
            "flightNumber": "NH007",
            "origin": {
                "code": "SFO",
                "city": "San Francisco",
                "airport": "San Francisco International"
            },
            "destination": {
                "code": "NRT",
                "city": "Tokyo",
                "airport": "Narita International"
            },
            "departureTime": "2024-03-15T14:00:00-07:00",
            "arrivalTime": "2024-03-16T18:30:00+09:00",
            "duration": "10h 30m",
            "price": {
                "amount": 895,
                "currency": "USD",
                "displayPrice": "$895"
            },
            "stops": 0,
            "amenities": ["WiFi", "Entertainment", "Japanese Cuisine", "Premium Economy"],
            "aircraft": "Boeing 777-300ER"
        }
    ]

def get_mock_hotels():
    """Generate mock hotel data."""
    return [
        {
            "id": "park-hyatt-tokyo",
            "name": "Park Hyatt Tokyo",
            "location": {
                "address": "3-7-1-2 Nishi-Shinjuku",
                "city": "Tokyo",
                "neighborhood": "Shinjuku",
                "country": "Japan",
                "coordinates": {"lat": 35.6852, "lng": 139.6891}
            },
            "price": {
                "amount": 450,
                "currency": "USD",
                "displayPrice": "$450",
                "period": "per night"
            },
            "rating": 4.8,
            "reviewCount": 1842,
            "amenities": ["Free WiFi", "Pool", "Spa", "Restaurant", "Bar", "Fitness Center", "Business Center"],
            "roomTypes": ["Deluxe Room", "Park Suite", "Tokyo Suite"],
            "images": ["https://example.com/park-hyatt-1.jpg"],
            "checkIn": "2024-03-15",
            "checkOut": "2024-03-20"
        },
        {
            "id": "mandarin-oriental-tokyo",
            "name": "Mandarin Oriental Tokyo",
            "location": {
                "address": "2-1-1 Nihonbashi Muromachi",
                "city": "Tokyo",
                "neighborhood": "Nihonbashi",
                "country": "Japan",
                "coordinates": {"lat": 35.6847, "lng": 139.7738}
            },
            "price": {
                "amount": 520,
                "currency": "USD",
                "displayPrice": "$520",
                "period": "per night"
            },
            "rating": 4.9,
            "reviewCount": 2156,
            "amenities": ["Free WiFi", "Spa", "Restaurant", "Bar", "Concierge", "Room Service"],
            "roomTypes": ["Deluxe Room", "Premier Room", "Mandarin Suite"],
            "images": ["https://example.com/mandarin-1.jpg"],
            "checkIn": "2024-03-15",
            "checkOut": "2024-03-20"
        },
        {
            "id": "grand-hyatt-tokyo",
            "name": "Grand Hyatt Tokyo",
            "location": {
                "address": "6-10-3 Roppongi",
                "city": "Tokyo",
                "neighborhood": "Roppongi",
                "country": "Japan",
                "coordinates": {"lat": 35.6595, "lng": 139.7307}
            },
            "price": {
                "amount": 380,
                "currency": "USD",
                "displayPrice": "$380",
                "period": "per night"
            },
            "rating": 4.7,
            "reviewCount": 2341,
            "amenities": ["Free WiFi", "Pool", "Spa", "Multiple Restaurants", "Bar", "Club Lounge"],
            "roomTypes": ["Standard Room", "Club Room", "Suite"],
            "images": ["https://example.com/grand-hyatt-1.jpg"],
            "checkIn": "2024-03-15",
            "checkOut": "2024-03-20"
        }
    ]

@router.post("/chat-with-results")
async def chat_with_mock_results(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock endpoint that returns a chat response with search results.
    """
    message = request.get("message", "").lower()
    
    response_data = {
        "success": True,
        "data": {
            "message": "",
            "searchResults": {
                "flights": [],
                "hotels": [],
                "activities": []
            },
            "suggestions": [],
            "hints": []
        }
    }
    
    if "flight" in message:
        response_data["data"]["message"] = "I found several great flight options from San Francisco to Tokyo. Here are the best options based on price and convenience:"
        response_data["data"]["searchResults"]["flights"] = get_mock_flights()
        response_data["data"]["suggestions"] = [
            "Show me business class options",
            "Find flights with one stop",
            "What about return flights?"
        ]
        response_data["data"]["hints"] = [
            {"text": "United Airlines has the earliest departure", "type": "tip"},
            {"text": "JAL offers lie-flat seats in business class", "type": "tip"}
        ]
    elif "hotel" in message:
        response_data["data"]["message"] = "I found excellent hotels in Tokyo for your stay. Here are the top recommendations in popular neighborhoods:"
        response_data["data"]["searchResults"]["hotels"] = get_mock_hotels()
        response_data["data"]["suggestions"] = [
            "Show hotels near Tokyo Station",
            "Find budget-friendly options",
            "Hotels with airport shuttle"
        ]
        response_data["data"]["hints"] = [
            {"text": "Park Hyatt Tokyo is famous from Lost in Translation", "type": "tip"},
            {"text": "Roppongi area has great nightlife", "type": "tip"}
        ]
    else:
        response_data["data"]["message"] = "I can help you search for flights, hotels, and activities. What would you like to explore?"
        response_data["data"]["suggestions"] = [
            "Search for flights to Tokyo",
            "Find hotels in Tokyo",
            "Discover activities in Tokyo"
        ]
    
    return response_data

@router.get("/test-search/{search_type}")
async def get_test_search_results(search_type: str) -> Dict[str, Any]:
    """
    Get mock search results by type.
    """
    results = {
        "flights": [],
        "hotels": [],
        "activities": []
    }
    
    if search_type == "flights":
        results["flights"] = get_mock_flights()
    elif search_type == "hotels":
        results["hotels"] = get_mock_hotels()
    elif search_type == "all":
        results["flights"] = get_mock_flights()
        results["hotels"] = get_mock_hotels()
    
    return {
        "success": True,
        "data": {
            "searchResults": results,
            "message": f"Found {len(results['flights'])} flights and {len(results['hotels'])} hotels"
        }
    }