"""
Booking API endpoint tests.

Tests for booking-related endpoints including booking creation,
management, status tracking, and payment processing.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from fastapi import status
from httpx import AsyncClient

from app.models import UnifiedSessionBooking
from app.schemas.booking import (
    BookingRequest, BookingUpdate, BookingStatus,
    PaymentRequest, CancellationRequest
)


class TestBookingCreation:
    """Test booking creation endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_create_flight_booking_success(self, async_client: AsyncClient, auth_headers, test_travel_session, flight_data_factory):
        """Test successful flight booking creation."""
        flight_data = flight_data_factory()
        booking_data = {
            "session_id": test_travel_session.session_id,
            "booking_type": "flight",
            "provider": "amadeus",
            "external_id": "flight_123",
            "booking_data": flight_data,
            "traveler_data": {
                "travelers": [
                    {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john@example.com",
                        "phone": "+1234567890",
                        "date_of_birth": "1990-01-01",
                        "passport_number": "123456789",
                        "passport_country": "US"
                    }
                ]
            },
            "total_amount": 85000,  # $850.00 in cents
            "currency": "USD"
        }
        
        with patch('app.services.amadeus_service.AmadeusService') as mock_amadeus:
            mock_amadeus.return_value.create_booking.return_value = {
                "booking_reference": "AMADEUS123",
                "status": "confirmed",
                "booking_details": flight_data
            }
            
            response = await async_client.post(
                "/api/v1/bookings",
                json=booking_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert "booking_id" in data
        assert "provider_booking_id" in data
        assert data["booking_type"] == "flight"
        assert data["booking_status"] == "confirmed"
        assert data["total_amount"] == 85000

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_create_hotel_booking_success(self, async_client: AsyncClient, auth_headers, test_travel_session, hotel_data_factory):
        """Test successful hotel booking creation."""
        hotel_data = hotel_data_factory()
        booking_data = {
            "session_id": test_travel_session.session_id,
            "booking_type": "hotel",
            "provider": "amadeus",
            "external_id": "hotel_123",
            "booking_data": hotel_data,
            "traveler_data": {
                "guest_details": [
                    {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john@example.com",
                        "phone": "+1234567890"
                    }
                ],
                "room_preferences": {
                    "bed_type": "double",
                    "smoking": False,
                    "accessibility": False
                }
            },
            "total_amount": 140000,  # $1400.00 for 7 nights
            "currency": "USD"
        }
        
        with patch('app.services.amadeus_service.AmadeusService') as mock_amadeus:
            mock_amadeus.return_value.create_booking.return_value = {
                "booking_reference": "HOTEL123",
                "status": "confirmed",
                "booking_details": hotel_data
            }
            
            response = await async_client.post(
                "/api/v1/bookings",
                json=booking_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["booking_type"] == "hotel"
        assert data["booking_status"] == "confirmed"

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_create_booking_invalid_session(self, async_client: AsyncClient, auth_headers, flight_data_factory):
        """Test booking creation with invalid session."""
        flight_data = flight_data_factory()
        booking_data = {
            "session_id": "invalid-session-id",
            "booking_type": "flight",
            "provider": "amadeus",
            "external_id": "flight_123",
            "booking_data": flight_data,
            "traveler_data": {},
            "total_amount": 85000,
            "currency": "USD"
        }
        
        response = await async_client.post(
            "/api/v1/bookings",
            json=booking_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "session not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_create_booking_missing_traveler_data(self, async_client: AsyncClient, auth_headers, test_travel_session, flight_data_factory):
        """Test booking creation with missing traveler data."""
        flight_data = flight_data_factory()
        booking_data = {
            "session_id": test_travel_session.session_id,
            "booking_type": "flight",
            "provider": "amadeus",
            "external_id": "flight_123",
            "booking_data": flight_data,
            "traveler_data": {},  # Empty traveler data
            "total_amount": 85000,
            "currency": "USD"
        }
        
        response = await async_client.post(
            "/api/v1/bookings",
            json=booking_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_create_booking_provider_failure(self, async_client: AsyncClient, auth_headers, test_travel_session, flight_data_factory):
        """Test booking creation when provider service fails."""
        flight_data = flight_data_factory()
        booking_data = {
            "session_id": test_travel_session.session_id,
            "booking_type": "flight",
            "provider": "amadeus",
            "external_id": "flight_123",
            "booking_data": flight_data,
            "traveler_data": {
                "travelers": [
                    {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john@example.com"
                    }
                ]
            },
            "total_amount": 85000,
            "currency": "USD"
        }
        
        with patch('app.services.amadeus_service.AmadeusService') as mock_amadeus:
            mock_amadeus.return_value.create_booking.side_effect = Exception("Provider service unavailable")
            
            response = await async_client.post(
                "/api/v1/bookings",
                json=booking_data,
                headers=auth_headers
            )
        
        assert response.status_code in [
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]


class TestBookingRetrieval:
    """Test booking retrieval endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_user_bookings(self, async_client: AsyncClient, auth_headers, test_user):
        """Test retrieving user's bookings."""
        response = await async_client.get("/api/v1/bookings", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "bookings" in data
        assert "total" in data
        assert "pagination" in data
        assert isinstance(data["bookings"], list)

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_booking_by_id(self, async_client: AsyncClient, auth_headers, test_travel_session, db_session):
        """Test retrieving specific booking by ID."""
        # Create a test booking
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="flight",
            provider="amadeus",
            provider_booking_id="TEST123",
            booking_status="confirmed",
            total_amount=85000,
            currency="USD",
            booking_data={
                "flight_details": {"origin": "JFK", "destination": "CDG"}
            },
            traveler_data={
                "travelers": [{"name": "John Doe"}]
            }
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        response = await async_client.get(f"/api/v1/bookings/{booking.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["id"] == booking.id
        assert data["booking_type"] == "flight"
        assert data["provider_booking_id"] == "TEST123"

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_nonexistent_booking(self, async_client: AsyncClient, auth_headers):
        """Test retrieving non-existent booking."""
        response = await async_client.get("/api/v1/bookings/99999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_booking_unauthorized(self, async_client: AsyncClient, test_travel_session, db_session):
        """Test retrieving booking without proper authorization."""
        # Create a booking for another user
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="flight",
            provider="amadeus",
            provider_booking_id="TEST123",
            booking_status="confirmed",
            total_amount=85000,
            currency="USD",
            booking_data={},
            traveler_data={}
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        # Try to access without authentication
        response = await async_client.get(f"/api/v1/bookings/{booking.id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_session_bookings(self, async_client: AsyncClient, auth_headers, test_travel_session):
        """Test retrieving bookings for a specific session."""
        session_id = test_travel_session.session_id
        
        response = await async_client.get(
            f"/api/v1/travel/sessions/{session_id}/bookings",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "bookings" in data
        assert isinstance(data["bookings"], list)


class TestBookingUpdates:
    """Test booking update endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_update_booking_status(self, async_client: AsyncClient, auth_headers, test_travel_session, db_session):
        """Test updating booking status."""
        # Create a test booking
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="flight",
            provider="amadeus",
            provider_booking_id="TEST123",
            booking_status="pending",
            total_amount=85000,
            currency="USD",
            booking_data={},
            traveler_data={}
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        update_data = {
            "booking_status": "confirmed",
            "confirmation_code": "ABC123"
        }
        
        response = await async_client.put(
            f"/api/v1/bookings/{booking.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["booking_status"] == "confirmed"
        assert data["confirmation_code"] == "ABC123"

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_update_booking_traveler_data(self, async_client: AsyncClient, auth_headers, test_travel_session, db_session):
        """Test updating booking traveler data."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="hotel",
            provider="amadeus",
            provider_booking_id="HOTEL123",
            booking_status="confirmed",
            total_amount=140000,
            currency="USD",
            booking_data={},
            traveler_data={"guests": 2}
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        update_data = {
            "traveler_data": {
                "guests": 2,
                "special_requests": ["late checkout", "room upgrade if available"]
            }
        }
        
        response = await async_client.put(
            f"/api/v1/bookings/{booking.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "special_requests" in data["traveler_data"]

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_add_booking_payment(self, async_client: AsyncClient, auth_headers, test_travel_session, db_session):
        """Test adding payment information to a booking."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="flight",
            provider="amadeus",
            provider_booking_id="FLIGHT123",
            booking_status="confirmed",
            total_amount=85000,
            currency="USD",
            booking_data={},
            traveler_data={},
            payment_status="pending"
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        payment_data = {
            "payment_method": "credit_card",
            "payment_reference": "PAY123456",
            "payment_amount": 85000,
            "payment_currency": "USD",
            "payment_status": "completed"
        }
        
        response = await async_client.post(
            f"/api/v1/bookings/{booking.id}/payment",
            json=payment_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["payment_status"] == "completed"
        assert "payment_data" in data


class TestBookingCancellation:
    """Test booking cancellation endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_cancel_booking_success(self, async_client: AsyncClient, auth_headers, test_travel_session, db_session):
        """Test successful booking cancellation."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="flight",
            provider="amadeus",
            provider_booking_id="FLIGHT123",
            booking_status="confirmed",
            total_amount=85000,
            currency="USD",
            booking_data={},
            traveler_data={}
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        cancellation_data = {
            "reason": "Change of plans",
            "refund_requested": True
        }
        
        with patch('app.services.amadeus_service.AmadeusService') as mock_amadeus:
            mock_amadeus.return_value.cancel_booking.return_value = {
                "cancellation_reference": "CANCEL123",
                "refund_amount": 75000,
                "refund_status": "processing"
            }
            
            response = await async_client.post(
                f"/api/v1/bookings/{booking.id}/cancel",
                json=cancellation_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["booking_status"] == "cancelled"
        assert "cancellation_reference" in data

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_cancel_already_cancelled_booking(self, async_client: AsyncClient, auth_headers, test_travel_session, db_session):
        """Test cancelling an already cancelled booking."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="flight",
            provider="amadeus",
            provider_booking_id="FLIGHT123",
            booking_status="cancelled",
            total_amount=85000,
            currency="USD",
            booking_data={},
            traveler_data={}
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        cancellation_data = {
            "reason": "Change of plans",
            "refund_requested": True
        }
        
        response = await async_client.post(
            f"/api/v1/bookings/{booking.id}/cancel",
            json=cancellation_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already cancelled" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_cancel_booking_provider_failure(self, async_client: AsyncClient, auth_headers, test_travel_session, db_session):
        """Test booking cancellation when provider service fails."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="flight",
            provider="amadeus",
            provider_booking_id="FLIGHT123",
            booking_status="confirmed",
            total_amount=85000,
            currency="USD",
            booking_data={},
            traveler_data={}
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        cancellation_data = {
            "reason": "Change of plans",
            "refund_requested": True
        }
        
        with patch('app.services.amadeus_service.AmadeusService') as mock_amadeus:
            mock_amadeus.return_value.cancel_booking.side_effect = Exception("Provider service unavailable")
            
            response = await async_client.post(
                f"/api/v1/bookings/{booking.id}/cancel",
                json=cancellation_data,
                headers=auth_headers
            )
        
        assert response.status_code in [
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]


class TestBookingValidation:
    """Test booking validation and business rules."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_validate_booking_dates(self, async_client: AsyncClient, auth_headers, test_travel_session, flight_data_factory):
        """Test booking validation for travel dates."""
        flight_data = flight_data_factory(
            departure_date="2023-01-01",  # Past date
            return_date="2023-01-08"
        )
        booking_data = {
            "session_id": test_travel_session.session_id,
            "booking_type": "flight",
            "provider": "amadeus",
            "external_id": "flight_123",
            "booking_data": flight_data,
            "traveler_data": {
                "travelers": [{"first_name": "John", "last_name": "Doe"}]
            },
            "total_amount": 85000,
            "currency": "USD"
        }
        
        response = await async_client.post(
            "/api/v1/bookings",
            json=booking_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_validate_booking_amount(self, async_client: AsyncClient, auth_headers, test_travel_session, flight_data_factory):
        """Test booking validation for amount."""
        flight_data = flight_data_factory()
        booking_data = {
            "session_id": test_travel_session.session_id,
            "booking_type": "flight",
            "provider": "amadeus",
            "external_id": "flight_123",
            "booking_data": flight_data,
            "traveler_data": {
                "travelers": [{"first_name": "John", "last_name": "Doe"}]
            },
            "total_amount": -1000,  # Negative amount
            "currency": "USD"
        }
        
        response = await async_client.post(
            "/api/v1/bookings",
            json=booking_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_validate_traveler_requirements(self, async_client: AsyncClient, auth_headers, test_travel_session, flight_data_factory):
        """Test booking validation for traveler requirements."""
        flight_data = flight_data_factory()
        booking_data = {
            "session_id": test_travel_session.session_id,
            "booking_type": "flight",
            "provider": "amadeus",
            "external_id": "flight_123",
            "booking_data": flight_data,
            "traveler_data": {
                "travelers": [
                    {
                        "first_name": "John",
                        # Missing last_name and other required fields
                    }
                ]
            },
            "total_amount": 85000,
            "currency": "USD"
        }
        
        response = await async_client.post(
            "/api/v1/bookings",
            json=booking_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestBookingStatusTracking:
    """Test booking status tracking functionality."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_track_booking_status(self, async_client: AsyncClient, auth_headers, test_travel_session, db_session):
        """Test tracking booking status changes."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="flight",
            provider="amadeus",
            provider_booking_id="FLIGHT123",
            booking_status="pending",
            total_amount=85000,
            currency="USD",
            booking_data={},
            traveler_data={}
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        # Check initial status
        response = await async_client.get(
            f"/api/v1/bookings/{booking.id}/status",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["booking_status"] == "pending"
        assert "status_history" in data

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_refresh_booking_status(self, async_client: AsyncClient, auth_headers, test_travel_session, db_session):
        """Test refreshing booking status from provider."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="flight",
            provider="amadeus",
            provider_booking_id="FLIGHT123",
            booking_status="pending",
            total_amount=85000,
            currency="USD",
            booking_data={},
            traveler_data={}
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        with patch('app.services.amadeus_service.AmadeusService') as mock_amadeus:
            mock_amadeus.return_value.get_booking_status.return_value = {
                "status": "confirmed",
                "confirmation_code": "ABC123"
            }
            
            response = await async_client.post(
                f"/api/v1/bookings/{booking.id}/refresh-status",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["booking_status"] == "confirmed"


class TestBookingDocuments:
    """Test booking document generation and retrieval."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_booking_confirmation(self, async_client: AsyncClient, auth_headers, test_travel_session, db_session):
        """Test retrieving booking confirmation document."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="flight",
            provider="amadeus",
            provider_booking_id="FLIGHT123",
            booking_status="confirmed",
            confirmation_code="ABC123",
            total_amount=85000,
            currency="USD",
            booking_data={
                "flight_details": {
                    "origin": "JFK",
                    "destination": "CDG",
                    "departure_date": "2024-06-01",
                    "return_date": "2024-06-08"
                }
            },
            traveler_data={
                "travelers": [
                    {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john@example.com"
                    }
                ]
            }
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        response = await async_client.get(
            f"/api/v1/bookings/{booking.id}/confirmation",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "confirmation_document" in data
        assert "booking_reference" in data["confirmation_document"]

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_booking_voucher(self, async_client: AsyncClient, auth_headers, test_travel_session, db_session):
        """Test retrieving booking voucher/ticket."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="hotel",
            provider="amadeus",
            provider_booking_id="HOTEL123",
            booking_status="confirmed",
            confirmation_code="HOTEL456",
            total_amount=140000,
            currency="USD",
            booking_data={},
            traveler_data={}
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        response = await async_client.get(
            f"/api/v1/bookings/{booking.id}/voucher",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK


class TestBookingSearch:
    """Test booking search and filtering."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_search_bookings_by_status(self, async_client: AsyncClient, auth_headers):
        """Test searching bookings by status."""
        params = {
            "status": "confirmed",
            "limit": 10,
            "offset": 0
        }
        
        response = await async_client.get(
            "/api/v1/bookings",
            params=params,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "bookings" in data
        assert "total" in data

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_search_bookings_by_date_range(self, async_client: AsyncClient, auth_headers):
        """Test searching bookings by date range."""
        params = {
            "start_date": "2024-06-01",
            "end_date": "2024-06-30",
            "booking_type": "flight"
        }
        
        response = await async_client.get(
            "/api/v1/bookings",
            params=params,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_search_bookings_by_provider(self, async_client: AsyncClient, auth_headers):
        """Test searching bookings by provider."""
        params = {
            "provider": "amadeus",
            "sort_by": "booking_date",
            "sort_order": "desc"
        }
        
        response = await async_client.get(
            "/api/v1/bookings",
            params=params,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK