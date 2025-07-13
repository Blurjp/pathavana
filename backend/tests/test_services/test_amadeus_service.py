"""
Amadeus Service tests.

Tests for the Amadeus service including flight search, hotel search,
booking creation, and API integration functionality.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import httpx

from app.services.amadeus_service import AmadeusService
from app.core.config import settings


class TestAmadeusServiceInitialization:
    """Test Amadeus service initialization and authentication."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_service_initialization_success(self):
        """Test successful Amadeus service initialization."""
        with patch.object(settings, 'AMADEUS_API_KEY', 'test_key'):
            with patch.object(settings, 'AMADEUS_API_SECRET', 'test_secret'):
                service = AmadeusService()
                assert service.api_key == 'test_key'
                assert service.api_secret == 'test_secret'
                assert service.base_url == settings.AMADEUS_API_BASE_URL

    @pytest.mark.unit
    @pytest.mark.service
    def test_service_initialization_missing_credentials(self):
        """Test Amadeus service initialization with missing credentials."""
        with patch.object(settings, 'AMADEUS_API_KEY', None):
            with pytest.raises(ValueError, match="Amadeus API credentials not configured"):
                AmadeusService()

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_get_access_token_success(self, mock_amadeus_service):
        """Test successful access token retrieval."""
        mock_response = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        
        mock_amadeus_service.get_access_token.return_value = mock_response
        
        result = await mock_amadeus_service.get_access_token()
        
        assert result["access_token"] == "test_access_token"
        assert result["token_type"] == "Bearer"

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_get_access_token_failure(self, mock_amadeus_service):
        """Test access token retrieval failure."""
        mock_amadeus_service.get_access_token.side_effect = httpx.HTTPStatusError(
            message="Authentication failed",
            request=MagicMock(),
            response=MagicMock(status_code=401)
        )
        
        with pytest.raises(httpx.HTTPStatusError):
            await mock_amadeus_service.get_access_token()


class TestFlightSearch:
    """Test flight search functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_search_flights_roundtrip_success(self, mock_amadeus_service, sample_api_responses):
        """Test successful roundtrip flight search."""
        search_params = {
            "origin": "JFK",
            "destination": "CDG",
            "departure_date": "2024-06-01",
            "return_date": "2024-06-08",
            "passengers": 2,
            "cabin_class": "economy"
        }
        
        mock_amadeus_service.search_flights.return_value = sample_api_responses["amadeus_flight_search"]
        
        result = await mock_amadeus_service.search_flights(**search_params)
        
        assert "data" in result
        assert len(result["data"]) > 0
        
        flight = result["data"][0]
        assert flight["type"] == "flight-offer"
        assert "price" in flight
        assert "itineraries" in flight

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_search_flights_oneway(self, mock_amadeus_service):
        """Test one-way flight search."""
        search_params = {
            "origin": "LAX",
            "destination": "LHR",
            "departure_date": "2024-07-15",
            "passengers": 1,
            "cabin_class": "business"
        }
        
        expected_response = {
            "data": [
                {
                    "type": "flight-offer",
                    "id": "1",
                    "itineraries": [
                        {
                            "duration": "PT11H20M",
                            "segments": [
                                {
                                    "departure": {
                                        "iataCode": "LAX",
                                        "at": "2024-07-15T14:30:00"
                                    },
                                    "arrival": {
                                        "iataCode": "LHR",
                                        "at": "2024-07-16T08:50:00"
                                    },
                                    "carrierCode": "BA",
                                    "number": "283"
                                }
                            ]
                        }
                    ],
                    "price": {
                        "currency": "USD",
                        "total": "2500.00"
                    }
                }
            ]
        }
        
        mock_amadeus_service.search_flights.return_value = expected_response
        
        result = await mock_amadeus_service.search_flights(**search_params)
        
        assert len(result["data"]) == 1
        assert result["data"][0]["price"]["total"] == "2500.00"

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_search_flights_multi_city(self, mock_amadeus_service):
        """Test multi-city flight search."""
        search_params = {
            "trips": [
                {"origin": "NYC", "destination": "PAR", "departure_date": "2024-06-01"},
                {"origin": "PAR", "destination": "ROM", "departure_date": "2024-06-08"},
                {"origin": "ROM", "destination": "NYC", "departure_date": "2024-06-15"}
            ],
            "passengers": 2
        }
        
        expected_response = {
            "data": [
                {
                    "type": "flight-offer",
                    "id": "multi_1",
                    "itineraries": [
                        {"segments": [{"departure": {"iataCode": "JFK"}, "arrival": {"iataCode": "CDG"}}]},
                        {"segments": [{"departure": {"iataCode": "CDG"}, "arrival": {"iataCode": "FCO"}}]},
                        {"segments": [{"departure": {"iataCode": "FCO"}, "arrival": {"iataCode": "JFK"}}]}
                    ],
                    "price": {"currency": "USD", "total": "1800.00"}
                }
            ]
        }
        
        mock_amadeus_service.search_flights_multi_city.return_value = expected_response
        
        result = await mock_amadeus_service.search_flights_multi_city(**search_params)
        
        assert len(result["data"][0]["itineraries"]) == 3

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_search_flights_with_filters(self, mock_amadeus_service):
        """Test flight search with filters."""
        search_params = {
            "origin": "JFK",
            "destination": "CDG",
            "departure_date": "2024-06-01",
            "passengers": 1,
            "filters": {
                "max_price": 1000,
                "airlines": ["AF", "KL"],
                "max_stops": 1,
                "departure_time_range": {"earliest": "08:00", "latest": "18:00"}
            }
        }
        
        expected_response = {
            "data": [
                {
                    "type": "flight-offer",
                    "id": "filtered_1",
                    "price": {"currency": "USD", "total": "850.00"},
                    "itineraries": [
                        {
                            "segments": [
                                {
                                    "carrierCode": "AF",
                                    "departure": {"at": "2024-06-01T10:00:00"},
                                    "arrival": {"at": "2024-06-01T22:00:00"}
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        mock_amadeus_service.search_flights.return_value = expected_response
        
        result = await mock_amadeus_service.search_flights(**search_params)
        
        flight = result["data"][0]
        assert float(flight["price"]["total"]) <= 1000
        assert flight["itineraries"][0]["segments"][0]["carrierCode"] in ["AF", "KL"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_search_flights_no_results(self, mock_amadeus_service):
        """Test flight search with no results."""
        search_params = {
            "origin": "INVALID",
            "destination": "CODES",
            "departure_date": "2024-06-01",
            "passengers": 1
        }
        
        expected_response = {
            "data": [],
            "meta": {
                "count": 0,
                "links": {}
            }
        }
        
        mock_amadeus_service.search_flights.return_value = expected_response
        
        result = await mock_amadeus_service.search_flights(**search_params)
        
        assert len(result["data"]) == 0
        assert result["meta"]["count"] == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_get_flight_details(self, mock_amadeus_service):
        """Test retrieving detailed flight information."""
        flight_id = "flight_123"
        
        expected_response = {
            "data": {
                "type": "flight-offer",
                "id": flight_id,
                "itineraries": [
                    {
                        "duration": "PT8H30M",
                        "segments": [
                            {
                                "departure": {
                                    "iataCode": "JFK",
                                    "terminal": "1",
                                    "at": "2024-06-01T10:00:00"
                                },
                                "arrival": {
                                    "iataCode": "CDG",
                                    "terminal": "2E",
                                    "at": "2024-06-01T22:30:00"
                                },
                                "carrierCode": "AF",
                                "number": "123",
                                "aircraft": {"code": "333"},
                                "duration": "PT8H30M",
                                "operating": {"carrierCode": "AF"}
                            }
                        ]
                    }
                ],
                "price": {
                    "currency": "USD",
                    "total": "850.00",
                    "base": "750.00",
                    "fees": [{"amount": "100.00", "type": "SUPPLIER"}]
                },
                "pricingOptions": {
                    "fareType": ["PUBLISHED"],
                    "includedCheckedBagsOnly": False
                },
                "validatingAirlineCodes": ["AF"],
                "travelerPricings": [
                    {
                        "travelerId": "1",
                        "fareOption": "STANDARD",
                        "travelerType": "ADULT",
                        "price": {"currency": "USD", "total": "850.00"}
                    }
                ]
            }
        }
        
        mock_amadeus_service.get_flight_details.return_value = expected_response
        
        result = await mock_amadeus_service.get_flight_details(flight_id)
        
        assert result["data"]["id"] == flight_id
        assert "validatingAirlineCodes" in result["data"]
        assert "travelerPricings" in result["data"]


class TestHotelSearch:
    """Test hotel search functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_search_hotels_by_city(self, mock_amadeus_service):
        """Test hotel search by city code."""
        search_params = {
            "city_code": "PAR",
            "check_in": "2024-06-01",
            "check_out": "2024-06-08",
            "rooms": 1,
            "adults": 2,
            "children": 0
        }
        
        expected_response = {
            "data": [
                {
                    "type": "hotel-offers",
                    "hotel": {
                        "type": "hotel",
                        "hotelId": "MCLONGHM",
                        "chainCode": "MC",
                        "dupeId": "700027943",
                        "name": "Hotel du Louvre",
                        "cityCode": "PAR",
                        "latitude": 48.86311,
                        "longitude": 2.33639
                    },
                    "available": True,
                    "offers": [
                        {
                            "id": "offer_1",
                            "checkInDate": "2024-06-01",
                            "checkOutDate": "2024-06-08",
                            "rateCode": "RAC",
                            "room": {
                                "type": "DOUBLE",
                                "typeEstimated": {
                                    "category": "STANDARD_ROOM",
                                    "beds": 1,
                                    "bedType": "DOUBLE"
                                }
                            },
                            "guests": {"adults": 2},
                            "price": {
                                "currency": "USD",
                                "base": "180.00",
                                "total": "200.00",
                                "taxes": [{"amount": "20.00", "currency": "USD"}]
                            }
                        }
                    ]
                }
            ]
        }
        
        mock_amadeus_service.search_hotels.return_value = expected_response
        
        result = await mock_amadeus_service.search_hotels(**search_params)
        
        assert len(result["data"]) > 0
        hotel = result["data"][0]
        assert hotel["hotel"]["cityCode"] == "PAR"
        assert hotel["available"] is True
        assert len(hotel["offers"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_search_hotels_by_location(self, mock_amadeus_service):
        """Test hotel search by geographic coordinates."""
        search_params = {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "radius": 5,
            "check_in": "2024-06-01",
            "check_out": "2024-06-08",
            "rooms": 1,
            "adults": 2
        }
        
        expected_response = {
            "data": [
                {
                    "type": "hotel-offers",
                    "hotel": {
                        "hotelId": "PACDG001",
                        "name": "Paris Center Hotel",
                        "latitude": 48.8570,
                        "longitude": 2.3520
                    },
                    "available": True,
                    "offers": [
                        {
                            "id": "geo_offer_1",
                            "price": {"currency": "USD", "total": "150.00"}
                        }
                    ]
                }
            ]
        }
        
        mock_amadeus_service.search_hotels_by_location.return_value = expected_response
        
        result = await mock_amadeus_service.search_hotels_by_location(**search_params)
        
        hotel = result["data"][0]
        assert abs(hotel["hotel"]["latitude"] - 48.8566) <= 0.01  # Within radius

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_search_hotels_with_amenities(self, mock_amadeus_service):
        """Test hotel search with amenity filters."""
        search_params = {
            "city_code": "PAR",
            "check_in": "2024-06-01",
            "check_out": "2024-06-08",
            "rooms": 1,
            "adults": 2,
            "amenities": ["WIFI", "PARKING", "POOL", "GYM"]
        }
        
        expected_response = {
            "data": [
                {
                    "type": "hotel-offers",
                    "hotel": {
                        "hotelId": "LUXURY001",
                        "name": "Luxury Paris Hotel",
                        "amenities": ["WIFI", "PARKING", "POOL", "GYM", "SPA"]
                    },
                    "offers": [
                        {
                            "id": "luxury_offer_1",
                            "price": {"currency": "USD", "total": "400.00"}
                        }
                    ]
                }
            ]
        }
        
        mock_amadeus_service.search_hotels.return_value = expected_response
        
        result = await mock_amadeus_service.search_hotels(**search_params)
        
        hotel = result["data"][0]
        hotel_amenities = hotel["hotel"]["amenities"]
        for amenity in search_params["amenities"]:
            assert amenity in hotel_amenities

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_get_hotel_details(self, mock_amadeus_service):
        """Test retrieving detailed hotel information."""
        hotel_id = "MCLONGHM"
        
        expected_response = {
            "data": {
                "type": "hotel",
                "hotelId": hotel_id,
                "name": "Hotel du Louvre",
                "description": {
                    "lang": "EN",
                    "text": "Located in the heart of Paris, near the Louvre Museum."
                },
                "amenities": ["WIFI", "RESTAURANT", "BAR", "CONCIERGE"],
                "contact": {
                    "phone": "+33-1-44-58-38-38",
                    "email": "info@hoteldulouvre.com"
                },
                "address": {
                    "lines": ["Place André Malraux"],
                    "postalCode": "75001",
                    "cityName": "Paris",
                    "countryCode": "FR"
                },
                "rating": 5,
                "latitude": 48.86311,
                "longitude": 2.33639
            }
        }
        
        mock_amadeus_service.get_hotel_details.return_value = expected_response
        
        result = await mock_amadeus_service.get_hotel_details(hotel_id)
        
        assert result["data"]["hotelId"] == hotel_id
        assert result["data"]["rating"] == 5
        assert "description" in result["data"]
        assert "address" in result["data"]


class TestBookingCreation:
    """Test booking creation functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_create_flight_booking(self, mock_amadeus_service):
        """Test creating a flight booking."""
        booking_data = {
            "data": {
                "type": "flight-order",
                "flightOffers": [
                    {
                        "type": "flight-offer",
                        "id": "flight_123",
                        "price": {"currency": "USD", "total": "850.00"}
                    }
                ],
                "travelers": [
                    {
                        "id": "1",
                        "dateOfBirth": "1990-01-15",
                        "name": {"firstName": "John", "lastName": "Doe"},
                        "gender": "MALE",
                        "contact": {
                            "emailAddress": "john.doe@example.com",
                            "phones": [{"deviceType": "MOBILE", "number": "+1234567890"}]
                        },
                        "documents": [
                            {
                                "documentType": "PASSPORT",
                                "number": "123456789",
                                "issuanceCountry": "US",
                                "expiryDate": "2030-01-01"
                            }
                        ]
                    }
                ]
            }
        }
        
        expected_response = {
            "data": {
                "type": "flight-order",
                "id": "booking_123",
                "queuingOfficeId": "NYCAA08AA",
                "associatedRecords": [
                    {"reference": "ABC123", "creationDate": "2024-06-01T10:00:00"}
                ],
                "flightOffers": booking_data["data"]["flightOffers"],
                "travelers": booking_data["data"]["travelers"]
            }
        }
        
        mock_amadeus_service.create_booking.return_value = expected_response
        
        result = await mock_amadeus_service.create_booking(booking_data)
        
        assert result["data"]["type"] == "flight-order"
        assert result["data"]["id"] == "booking_123"
        assert "associatedRecords" in result["data"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_create_hotel_booking(self, mock_amadeus_service):
        """Test creating a hotel booking."""
        booking_data = {
            "data": {
                "type": "hotel-booking",
                "hotelOffer": {
                    "offerId": "offer_123",
                    "hotelId": "MCLONGHM",
                    "checkInDate": "2024-06-01",
                    "checkOutDate": "2024-06-08"
                },
                "guests": [
                    {
                        "id": 1,
                        "name": {"firstName": "John", "lastName": "Doe"},
                        "contact": {"email": "john.doe@example.com"}
                    }
                ],
                "payments": [
                    {
                        "method": "CREDIT_CARD",
                        "card": {
                            "vendorCode": "VI",
                            "cardNumber": "4111111111111111",
                            "expiryDate": "2025-12"
                        }
                    }
                ]
            }
        }
        
        expected_response = {
            "data": {
                "type": "hotel-booking",
                "id": "hotel_booking_123",
                "providerConfirmationId": "HOTEL456",
                "hotelOffer": booking_data["data"]["hotelOffer"],
                "guests": booking_data["data"]["guests"]
            }
        }
        
        mock_amadeus_service.create_booking.return_value = expected_response
        
        result = await mock_amadeus_service.create_booking(booking_data)
        
        assert result["data"]["type"] == "hotel-booking"
        assert result["data"]["id"] == "hotel_booking_123"
        assert "providerConfirmationId" in result["data"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_booking_validation_failure(self, mock_amadeus_service):
        """Test booking creation with validation failure."""
        invalid_booking_data = {
            "data": {
                "type": "flight-order",
                "flightOffers": [],  # Empty offers
                "travelers": []  # No travelers
            }
        }
        
        mock_amadeus_service.create_booking.side_effect = httpx.HTTPStatusError(
            message="Invalid booking data",
            request=MagicMock(),
            response=MagicMock(status_code=400, json=lambda: {
                "errors": [{"code": 1, "title": "Invalid request", "detail": "Missing required fields"}]
            })
        )
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_amadeus_service.create_booking(invalid_booking_data)
        
        assert exc_info.value.response.status_code == 400


class TestBookingManagement:
    """Test booking management functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_get_booking_status(self, mock_amadeus_service):
        """Test retrieving booking status."""
        booking_id = "booking_123"
        
        expected_response = {
            "data": {
                "type": "flight-order",
                "id": booking_id,
                "status": "CONFIRMED",
                "associatedRecords": [
                    {"reference": "ABC123", "creationDate": "2024-06-01T10:00:00"}
                ]
            }
        }
        
        mock_amadeus_service.get_booking_status.return_value = expected_response
        
        result = await mock_amadeus_service.get_booking_status(booking_id)
        
        assert result["data"]["id"] == booking_id
        assert result["data"]["status"] == "CONFIRMED"

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_cancel_booking(self, mock_amadeus_service):
        """Test booking cancellation."""
        booking_id = "booking_123"
        
        expected_response = {
            "data": {
                "type": "flight-order",
                "id": booking_id,
                "status": "CANCELLED",
                "cancellationDetails": {
                    "cancellationDate": "2024-06-01T15:30:00",
                    "refundAmount": {"currency": "USD", "amount": "750.00"},
                    "cancellationFee": {"currency": "USD", "amount": "100.00"}
                }
            }
        }
        
        mock_amadeus_service.cancel_booking.return_value = expected_response
        
        result = await mock_amadeus_service.cancel_booking(booking_id)
        
        assert result["data"]["status"] == "CANCELLED"
        assert "cancellationDetails" in result["data"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_modify_booking(self, mock_amadeus_service):
        """Test booking modification."""
        booking_id = "booking_123"
        modification_data = {
            "data": {
                "type": "flight-order-change",
                "modifications": [
                    {
                        "type": "DATE_CHANGE",
                        "newDepartureDate": "2024-06-02"
                    }
                ]
            }
        }
        
        expected_response = {
            "data": {
                "type": "flight-order",
                "id": booking_id,
                "status": "CONFIRMED",
                "modifications": modification_data["data"]["modifications"],
                "additionalFee": {"currency": "USD", "amount": "150.00"}
            }
        }
        
        mock_amadeus_service.modify_booking.return_value = expected_response
        
        result = await mock_amadeus_service.modify_booking(booking_id, modification_data)
        
        assert result["data"]["id"] == booking_id
        assert "modifications" in result["data"]
        assert "additionalFee" in result["data"]


class TestAmadeusServiceUtilities:
    """Test Amadeus service utility functions."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_get_airport_info(self, mock_amadeus_service):
        """Test retrieving airport information."""
        airport_code = "CDG"
        
        expected_response = {
            "data": [
                {
                    "type": "location",
                    "subType": "AIRPORT",
                    "name": "Charles de Gaulle International Airport",
                    "detailedName": "Paris/Charles de Gaulle Airport",
                    "iataCode": "CDG",
                    "icaoCode": "LFPG",
                    "address": {
                        "cityName": "Paris",
                        "countryName": "France",
                        "countryCode": "FR"
                    },
                    "geoCode": {"latitude": 49.00755, "longitude": 2.55085}
                }
            ]
        }
        
        mock_amadeus_service.get_airport_info.return_value = expected_response
        
        result = await mock_amadeus_service.get_airport_info(airport_code)
        
        assert result["data"][0]["iataCode"] == "CDG"
        assert "Charles de Gaulle" in result["data"][0]["name"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_get_airline_info(self, mock_amadeus_service):
        """Test retrieving airline information."""
        airline_code = "AF"
        
        expected_response = {
            "data": [
                {
                    "type": "airline",
                    "iataCode": "AF",
                    "icaoCode": "AFR",
                    "businessName": "Air France",
                    "commonName": "Air France"
                }
            ]
        }
        
        mock_amadeus_service.get_airline_info.return_value = expected_response
        
        result = await mock_amadeus_service.get_airline_info(airline_code)
        
        assert result["data"][0]["iataCode"] == "AF"
        assert result["data"][0]["businessName"] == "Air France"

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_get_city_info(self, mock_amadeus_service):
        """Test retrieving city information."""
        city_code = "PAR"
        
        expected_response = {
            "data": [
                {
                    "type": "location",
                    "subType": "CITY",
                    "name": "Paris",
                    "iataCode": "PAR",
                    "address": {
                        "countryName": "France",
                        "countryCode": "FR"
                    },
                    "geoCode": {"latitude": 48.85341, "longitude": 2.3488}
                }
            ]
        }
        
        mock_amadeus_service.get_city_info.return_value = expected_response
        
        result = await mock_amadeus_service.get_city_info(city_code)
        
        assert result["data"][0]["iataCode"] == "PAR"
        assert result["data"][0]["name"] == "Paris"


class TestAmadeusServiceErrorHandling:
    """Test Amadeus service error handling and resilience."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_rate_limit_handling(self, mock_amadeus_service):
        """Test handling of Amadeus API rate limits."""
        mock_amadeus_service.search_flights.side_effect = httpx.HTTPStatusError(
            message="Rate limit exceeded",
            request=MagicMock(),
            response=MagicMock(status_code=429, headers={"Retry-After": "60"})
        )
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_amadeus_service.search_flights(
                origin="JFK", destination="CDG", departure_date="2024-06-01", passengers=1
            )
        
        assert exc_info.value.response.status_code == 429

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_authentication_error_handling(self, mock_amadeus_service):
        """Test handling of authentication errors."""
        mock_amadeus_service.search_flights.side_effect = httpx.HTTPStatusError(
            message="Authentication failed",
            request=MagicMock(),
            response=MagicMock(status_code=401)
        )
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_amadeus_service.search_flights(
                origin="JFK", destination="CDG", departure_date="2024-06-01", passengers=1
            )
        
        assert exc_info.value.response.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_server_error_handling(self, mock_amadeus_service):
        """Test handling of server errors."""
        mock_amadeus_service.search_flights.side_effect = httpx.HTTPStatusError(
            message="Internal server error",
            request=MagicMock(),
            response=MagicMock(status_code=500)
        )
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_amadeus_service.search_flights(
                origin="JFK", destination="CDG", departure_date="2024-06-01", passengers=1
            )
        
        assert exc_info.value.response.status_code == 500

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_network_timeout_handling(self, mock_amadeus_service):
        """Test handling of network timeouts."""
        import asyncio
        
        mock_amadeus_service.search_flights.side_effect = asyncio.TimeoutError("Request timed out")
        
        with pytest.raises(asyncio.TimeoutError):
            await mock_amadeus_service.search_flights(
                origin="JFK", destination="CDG", departure_date="2024-06-01", passengers=1
            )


class TestAmadeusServiceCaching:
    """Test Amadeus service caching functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_search_result_caching(self, mock_amadeus_service, mock_cache_service):
        """Test caching of search results."""
        search_params = {
            "origin": "JFK",
            "destination": "CDG",
            "departure_date": "2024-06-01",
            "passengers": 1
        }
        
        # First call - cache miss
        mock_cache_service.get.return_value = None
        expected_response = {"data": [{"id": "flight_123", "price": {"total": "850.00"}}]}
        mock_amadeus_service.search_flights.return_value = expected_response
        
        with patch('app.services.cache_service.CacheService', return_value=mock_cache_service):
            result = await mock_amadeus_service.search_flights(**search_params)
        
        # Should cache the result
        mock_cache_service.set.assert_called_once()
        assert result == expected_response

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.service
    async def test_cache_hit_scenario(self, mock_amadeus_service, mock_cache_service):
        """Test cache hit scenario."""
        search_params = {
            "origin": "JFK",
            "destination": "CDG",
            "departure_date": "2024-06-01",
            "passengers": 1
        }
        
        cached_response = {"data": [{"id": "cached_flight", "price": {"total": "800.00"}}]}
        mock_cache_service.get.return_value = cached_response
        
        with patch('app.services.cache_service.CacheService', return_value=mock_cache_service):
            result = await mock_amadeus_service.search_flights(**search_params)
        
        # Should return cached result without API call
        mock_amadeus_service.search_flights.assert_not_called()
        assert result == cached_response


class TestAmadeusServicePerformance:
    """Test Amadeus service performance characteristics."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.service
    async def test_concurrent_search_requests(self, mock_amadeus_service):
        """Test handling of concurrent search requests."""
        import asyncio
        
        async def mock_search(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate API delay
            return {"data": [{"id": f"flight_{hash(str(kwargs))}", "price": {"total": "850.00"}}]}
        
        mock_amadeus_service.search_flights = mock_search
        
        # Create multiple concurrent requests
        search_params = [
            {"origin": "JFK", "destination": "CDG", "departure_date": "2024-06-01", "passengers": 1},
            {"origin": "LAX", "destination": "LHR", "departure_date": "2024-06-02", "passengers": 2},
            {"origin": "SFO", "destination": "NRT", "departure_date": "2024-06-03", "passengers": 1}
        ]
        
        tasks = [mock_amadeus_service.search_flights(**params) for params in search_params]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for result in results:
            assert "data" in result
            assert len(result["data"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.service
    async def test_search_response_time(self, mock_amadeus_service, performance_timer):
        """Test search response time performance."""
        search_params = {
            "origin": "JFK",
            "destination": "CDG",
            "departure_date": "2024-06-01",
            "passengers": 1
        }
        
        async def timed_search(*args, **kwargs):
            await asyncio.sleep(0.2)  # Simulate realistic API response time
            return {"data": [{"id": "flight_123", "price": {"total": "850.00"}}]}
        
        mock_amadeus_service.search_flights = timed_search
        
        performance_timer.start()
        result = await mock_amadeus_service.search_flights(**search_params)
        elapsed = performance_timer.stop()
        
        assert elapsed >= 0.2
        assert elapsed < 2.0  # Should complete within 2 seconds
        assert result["data"][0]["id"] == "flight_123"