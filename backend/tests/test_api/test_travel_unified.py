"""
Unified Travel API endpoint tests.

Tests for all travel-related endpoints including session management,
search functionality, and travel planning features.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from fastapi import status
from httpx import AsyncClient

from app.models import UnifiedTravelSession, UnifiedSavedItem
from app.schemas.travel import (
    TravelIntentRequest, SearchFlightsRequest, SearchHotelsRequest,
    SaveItemRequest, TravelSessionUpdate
)


class TestTravelSessionManagement:
    """Test travel session management endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_create_session_success(self, async_client: AsyncClient, auth_headers):
        """Test successful creation of new travel session."""
        session_data = {
            "initial_message": "I want to plan a trip to Tokyo",
            "travel_intent": {
                "destination": "Tokyo",
                "travel_type": "leisure",
                "duration": 7
            }
        }
        
        response = await async_client.post(
            "/api/v1/travel/sessions",
            json=session_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert "session_id" in data
        assert "status" in data
        assert data["status"] == "active"
        assert "created_at" in data

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_user_sessions(self, async_client: AsyncClient, auth_headers, test_travel_session):
        """Test retrieving user's travel sessions."""
        response = await async_client.get("/api/v1/travel/sessions", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "sessions" in data
        assert "total" in data
        assert len(data["sessions"]) >= 1
        
        # Check session structure
        session = data["sessions"][0]
        assert "session_id" in session
        assert "status" in session
        assert "created_at" in session

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_session_by_id(self, async_client: AsyncClient, auth_headers, test_travel_session):
        """Test retrieving specific travel session."""
        session_id = test_travel_session.session_id
        
        response = await async_client.get(
            f"/api/v1/travel/sessions/{session_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["session_id"] == session_id
        assert "session_data" in data
        assert "plan_data" in data
        assert "status" in data

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_nonexistent_session(self, async_client: AsyncClient, auth_headers):
        """Test retrieving non-existent session."""
        response = await async_client.get(
            "/api/v1/travel/sessions/nonexistent-id",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_update_session(self, async_client: AsyncClient, auth_headers, test_travel_session):
        """Test updating travel session data."""
        session_id = test_travel_session.session_id
        update_data = {
            "status": "planning",
            "plan_data": {
                "destination": "Tokyo, Japan",
                "departure_date": "2024-07-01",
                "return_date": "2024-07-08",
                "travelers": 2,
                "budget": 8000
            }
        }
        
        response = await async_client.put(
            f"/api/v1/travel/sessions/{session_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["status"] == "planning"
        assert data["plan_data"]["budget"] == 8000

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_delete_session(self, async_client: AsyncClient, auth_headers, test_travel_session):
        """Test deleting travel session."""
        session_id = test_travel_session.session_id
        
        response = await async_client.delete(
            f"/api/v1/travel/sessions/{session_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify session is deleted
        get_response = await async_client.get(
            f"/api/v1/travel/sessions/{session_id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


class TestTravelIntentParsing:
    """Test travel intent parsing and processing."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_parse_travel_intent_success(self, async_client: AsyncClient, auth_headers, mock_llm_service):
        """Test successful travel intent parsing."""
        intent_data = {
            "message": "I want to go to Paris for a week in June with my family",
            "context": {
                "previous_messages": [],
                "user_preferences": {}
            }
        }
        
        with patch('app.services.llm_service.LLMService', return_value=mock_llm_service):
            response = await async_client.post(
                "/api/v1/travel/parse-intent",
                json=intent_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "parsed_intent" in data
        assert "destination" in data["parsed_intent"]
        assert "travel_dates" in data["parsed_intent"]
        assert data["parsed_intent"]["destination"] == "Paris"

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_parse_travel_intent_invalid_message(self, async_client: AsyncClient, auth_headers):
        """Test travel intent parsing with invalid message."""
        intent_data = {
            "message": "",  # Empty message
            "context": {}
        }
        
        response = await async_client.post(
            "/api/v1/travel/parse-intent",
            json=intent_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_generate_travel_response(self, async_client: AsyncClient, auth_headers, test_travel_session, mock_llm_service):
        """Test generating travel response based on session context."""
        session_id = test_travel_session.session_id
        response_data = {
            "message": "What are the best places to visit?",
            "session_id": session_id
        }
        
        with patch('app.services.llm_service.LLMService', return_value=mock_llm_service):
            response = await async_client.post(
                "/api/v1/travel/generate-response",
                json=response_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "response" in data
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)


class TestFlightSearch:
    """Test flight search functionality."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_search_flights_success(self, async_client: AsyncClient, auth_headers, mock_amadeus_service):
        """Test successful flight search."""
        search_data = {
            "origin": "JFK",
            "destination": "CDG",
            "departure_date": "2024-06-01",
            "return_date": "2024-06-08",
            "passengers": 2,
            "cabin_class": "economy"
        }
        
        with patch('app.services.amadeus_service.AmadeusService', return_value=mock_amadeus_service):
            response = await async_client.post(
                "/api/v1/travel/flights/search",
                json=search_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "flights" in data
        assert "search_metadata" in data
        assert len(data["flights"]) > 0
        
        # Check flight structure
        flight = data["flights"][0]
        assert "id" in flight
        assert "price" in flight
        assert "itineraries" in flight

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_search_flights_invalid_dates(self, async_client: AsyncClient, auth_headers):
        """Test flight search with invalid dates."""
        search_data = {
            "origin": "JFK",
            "destination": "CDG",
            "departure_date": "2023-01-01",  # Past date
            "return_date": "2023-01-08",
            "passengers": 2,
            "cabin_class": "economy"
        }
        
        response = await async_client.post(
            "/api/v1/travel/flights/search",
            json=search_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_search_flights_invalid_airports(self, async_client: AsyncClient, auth_headers):
        """Test flight search with invalid airport codes."""
        search_data = {
            "origin": "INVALID",
            "destination": "CODES",
            "departure_date": "2024-06-01",
            "return_date": "2024-06-08",
            "passengers": 2,
            "cabin_class": "economy"
        }
        
        response = await async_client.post(
            "/api/v1/travel/flights/search",
            json=search_data,
            headers=auth_headers
        )
        
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_flight_details(self, async_client: AsyncClient, auth_headers, mock_amadeus_service):
        """Test retrieving detailed flight information."""
        flight_id = "test_flight_123"
        
        with patch('app.services.amadeus_service.AmadeusService', return_value=mock_amadeus_service):
            response = await async_client.get(
                f"/api/v1/travel/flights/{flight_id}",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "flight_details" in data
        assert "pricing" in data
        assert "segments" in data


class TestHotelSearch:
    """Test hotel search functionality."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_search_hotels_success(self, async_client: AsyncClient, auth_headers, mock_amadeus_service):
        """Test successful hotel search."""
        search_data = {
            "city_code": "PAR",
            "check_in": "2024-06-01",
            "check_out": "2024-06-08",
            "rooms": 1,
            "adults": 2,
            "children": 0
        }
        
        with patch('app.services.amadeus_service.AmadeusService', return_value=mock_amadeus_service):
            response = await async_client.post(
                "/api/v1/travel/hotels/search",
                json=search_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "hotels" in data
        assert "search_metadata" in data
        assert len(data["hotels"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_search_hotels_by_location(self, async_client: AsyncClient, auth_headers, mock_amadeus_service):
        """Test hotel search by location coordinates."""
        search_data = {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "radius": 5,
            "check_in": "2024-06-01",
            "check_out": "2024-06-08",
            "rooms": 1,
            "adults": 2
        }
        
        with patch('app.services.amadeus_service.AmadeusService', return_value=mock_amadeus_service):
            response = await async_client.post(
                "/api/v1/travel/hotels/search-by-location",
                json=search_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_hotel_details(self, async_client: AsyncClient, auth_headers, mock_amadeus_service):
        """Test retrieving detailed hotel information."""
        hotel_id = "test_hotel_123"
        
        with patch('app.services.amadeus_service.AmadeusService', return_value=mock_amadeus_service):
            response = await async_client.get(
                f"/api/v1/travel/hotels/{hotel_id}",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK


class TestSavedItems:
    """Test saved items management."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_save_item_success(self, async_client: AsyncClient, auth_headers, test_travel_session, flight_data_factory):
        """Test successfully saving a travel item."""
        session_id = test_travel_session.session_id
        flight_data = flight_data_factory()
        
        save_data = {
            "session_id": session_id,
            "item_type": "flight",
            "provider": "amadeus",
            "external_id": "flight_123",
            "item_data": flight_data,
            "user_notes": "Good flight option"
        }
        
        response = await async_client.post(
            "/api/v1/travel/saved-items",
            json=save_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert "item_id" in data
        assert data["item_type"] == "flight"
        assert data["session_id"] == session_id

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_saved_items(self, async_client: AsyncClient, auth_headers, test_travel_session, test_saved_item):
        """Test retrieving saved items for a session."""
        session_id = test_travel_session.session_id
        
        response = await async_client.get(
            f"/api/v1/travel/sessions/{session_id}/saved-items",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "saved_items" in data
        assert "total" in data
        assert len(data["saved_items"]) >= 1
        
        # Check item structure
        item = data["saved_items"][0]
        assert "id" in item
        assert "item_type" in item
        assert "item_data" in item

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_update_saved_item(self, async_client: AsyncClient, auth_headers, test_saved_item):
        """Test updating a saved item."""
        item_id = test_saved_item.id
        update_data = {
            "user_notes": "Updated notes",
            "assigned_day": 2,
            "sort_order": 3
        }
        
        response = await async_client.put(
            f"/api/v1/travel/saved-items/{item_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["user_notes"] == "Updated notes"
        assert data["assigned_day"] == 2

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_delete_saved_item(self, async_client: AsyncClient, auth_headers, test_saved_item):
        """Test deleting a saved item."""
        item_id = test_saved_item.id
        
        response = await async_client.delete(
            f"/api/v1/travel/saved-items/{item_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify item is deleted
        get_response = await async_client.get(
            f"/api/v1/travel/saved-items/{item_id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


class TestItineraryGeneration:
    """Test itinerary generation functionality."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_generate_itinerary_success(self, async_client: AsyncClient, auth_headers, test_travel_session, mock_llm_service):
        """Test successful itinerary generation."""
        session_id = test_travel_session.session_id
        itinerary_data = {
            "session_id": session_id,
            "preferences": {
                "activity_types": ["culture", "food", "sightseeing"],
                "pace": "moderate",
                "budget_level": "mid-range"
            }
        }
        
        with patch('app.services.llm_service.LLMService', return_value=mock_llm_service):
            response = await async_client.post(
                "/api/v1/travel/generate-itinerary",
                json=itinerary_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "itinerary" in data
        assert "daily_plans" in data
        assert isinstance(data["itinerary"], list)

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_save_generated_itinerary(self, async_client: AsyncClient, auth_headers, test_travel_session):
        """Test saving a generated itinerary."""
        session_id = test_travel_session.session_id
        itinerary_data = {
            "session_id": session_id,
            "itinerary": [
                {
                    "day": 1,
                    "activities": [
                        {
                            "name": "Arrive in Paris",
                            "time": "10:00",
                            "type": "travel"
                        },
                        {
                            "name": "Visit Eiffel Tower",
                            "time": "14:00",
                            "type": "sightseeing"
                        }
                    ]
                }
            ]
        }
        
        response = await async_client.post(
            "/api/v1/travel/save-itinerary",
            json=itinerary_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert "itinerary_id" in data
        assert data["session_id"] == session_id


class TestTravelRecommendations:
    """Test travel recommendations functionality."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_destination_recommendations(self, async_client: AsyncClient, auth_headers, mock_llm_service):
        """Test getting destination recommendations."""
        rec_data = {
            "preferences": {
                "travel_type": "leisure",
                "interests": ["culture", "food", "history"],
                "budget": "mid-range",
                "season": "summer"
            },
            "current_location": "New York"
        }
        
        with patch('app.services.llm_service.LLMService', return_value=mock_llm_service):
            response = await async_client.post(
                "/api/v1/travel/recommendations/destinations",
                json=rec_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_activity_recommendations(self, async_client: AsyncClient, auth_headers, test_travel_session, mock_llm_service):
        """Test getting activity recommendations for a destination."""
        session_id = test_travel_session.session_id
        activity_data = {
            "session_id": session_id,
            "destination": "Paris",
            "activity_types": ["culture", "food"],
            "duration": 3  # days
        }
        
        with patch('app.services.llm_service.LLMService', return_value=mock_llm_service):
            response = await async_client.post(
                "/api/v1/travel/recommendations/activities",
                json=activity_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "activities" in data
        assert isinstance(data["activities"], list)


class TestTravelContextService:
    """Test travel context service integration."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_session_context(self, async_client: AsyncClient, auth_headers, test_travel_session, mock_trip_context_service):
        """Test retrieving session context."""
        session_id = test_travel_session.session_id
        
        with patch('app.services.trip_context_service.TripContextService', return_value=mock_trip_context_service):
            response = await async_client.get(
                f"/api/v1/travel/sessions/{session_id}/context",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "context" in data
        assert "destination" in data["context"]
        assert "travel_dates" in data["context"]

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_update_session_context(self, async_client: AsyncClient, auth_headers, test_travel_session):
        """Test updating session context."""
        session_id = test_travel_session.session_id
        context_data = {
            "new_message": "I also want to visit museums",
            "context_update": {
                "preferences": ["culture", "food", "museums"]
            }
        }
        
        response = await async_client.post(
            f"/api/v1/travel/sessions/{session_id}/context",
            json=context_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "updated_context" in data


class TestErrorHandling:
    """Test error handling in travel endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test accessing travel endpoints without authentication."""
        response = await async_client.get("/api/v1/travel/sessions")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_external_service_failure(self, async_client: AsyncClient, auth_headers, mock_external_api_error):
        """Test handling external service failures."""
        search_data = {
            "origin": "JFK",
            "destination": "CDG",
            "departure_date": "2024-06-01",
            "return_date": "2024-06-08",
            "passengers": 2
        }
        
        with patch('app.services.amadeus_service.AmadeusService') as mock_service:
            mock_service.return_value.search_flights.side_effect = mock_external_api_error(503, "Service Unavailable")
            
            response = await async_client.post(
                "/api/v1/travel/flights/search",
                json=search_data,
                headers=auth_headers
            )
        
        assert response.status_code in [
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_rate_limiting(self, async_client: AsyncClient, auth_headers):
        """Test rate limiting on travel endpoints."""
        # This would require implementing rate limiting
        # For now, test that endpoints handle multiple requests
        search_data = {
            "origin": "JFK",
            "destination": "CDG",
            "departure_date": "2024-06-01",
            "passengers": 1
        }
        
        responses = []
        for _ in range(5):
            response = await async_client.post(
                "/api/v1/travel/flights/search",
                json=search_data,
                headers=auth_headers
            )
            responses.append(response.status_code)
        
        # Should handle multiple requests without crashing
        assert all(code in [200, 429, 503] for code in responses)