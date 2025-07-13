"""
Unified Travel Session Model tests.

Tests for the unified travel session model including JSONB operations,
relationships, indexing, and business logic.
"""

import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy import select, text, and_
from sqlalchemy.exc import IntegrityError
import uuid

from app.models.unified_travel_session import (
    UnifiedTravelSession, UnifiedSavedItem, UnifiedSessionBooking, SessionStatus
)
from app.models.user import User


class TestUnifiedTravelSessionModel:
    """Test UnifiedTravelSession model functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_create_session_basic(self, db_session, test_user):
        """Test basic session creation."""
        session = UnifiedTravelSession(
            user_id=test_user.id,
            status=SessionStatus.ACTIVE,
            session_data={
                "messages": [
                    {
                        "role": "user",
                        "content": "I want to go to Paris",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ]
            }
        )
        
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        assert session.session_id is not None
        assert session.user_id == test_user.id
        assert session.status == SessionStatus.ACTIVE
        assert session.created_at is not None
        assert session.updated_at is not None
        assert session.last_activity_at is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_session_id_generation(self, db_session, test_user):
        """Test automatic session ID generation."""
        session = UnifiedTravelSession(
            user_id=test_user.id,
            status=SessionStatus.ACTIVE
        )
        
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        # Should have auto-generated UUID
        assert session.session_id is not None
        assert len(session.session_id) == 36  # UUID4 length
        
        # Should be unique
        session2 = UnifiedTravelSession(
            user_id=test_user.id,
            status=SessionStatus.ACTIVE
        )
        db_session.add(session2)
        await db_session.commit()
        await db_session.refresh(session2)
        
        assert session.session_id != session2.session_id

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_session_with_complex_data(self, db_session, test_user):
        """Test session with complex JSONB data."""
        complex_session_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "I want to plan a business trip to Tokyo",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {
                        "source": "web",
                        "user_agent": "Chrome/91.0"
                    }
                },
                {
                    "role": "assistant",
                    "content": "I can help you plan your business trip to Tokyo.",
                    "timestamp": (datetime.utcnow() + timedelta(seconds=30)).isoformat(),
                    "suggestions": [
                        "Flight options",
                        "Hotel recommendations",
                        "Meeting venues"
                    ]
                }
            ],
            "parsed_intent": {
                "destination": "Tokyo",
                "travel_type": "business",
                "confidence": 0.95,
                "entities": {
                    "location": {"value": "Tokyo", "confidence": 0.98},
                    "purpose": {"value": "business", "confidence": 0.92}
                }
            },
            "search_results": {
                "flights": {
                    "cached_at": datetime.utcnow().isoformat(),
                    "results": []
                },
                "hotels": {
                    "cached_at": datetime.utcnow().isoformat(),
                    "results": []
                }
            }
        }
        
        complex_plan_data = {
            "destination": "Tokyo, Japan",
            "departure_date": "2024-06-01",
            "return_date": "2024-06-08",
            "travelers": 1,
            "travel_type": "business",
            "budget": {
                "total": 5000,
                "currency": "USD",
                "breakdown": {
                    "flights": 1500,
                    "accommodation": 2000,
                    "meals": 800,
                    "transportation": 400,
                    "activities": 300
                }
            },
            "preferences": {
                "accommodation": {
                    "type": "business_hotel",
                    "location": "city_center",
                    "amenities": ["wifi", "business_center", "gym"]
                },
                "flights": {
                    "class": "business",
                    "airline_preference": ["ANA", "JAL"],
                    "departure_time": "morning"
                }
            }
        }
        
        session = UnifiedTravelSession(
            user_id=test_user.id,
            status=SessionStatus.PLANNING,
            session_data=complex_session_data,
            plan_data=complex_plan_data
        )
        
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        # Verify complex data is stored and retrieved correctly
        assert session.session_data["parsed_intent"]["destination"] == "Tokyo"
        assert session.session_data["parsed_intent"]["confidence"] == 0.95
        assert len(session.session_data["messages"]) == 2
        
        assert session.plan_data["destination"] == "Tokyo, Japan"
        assert session.plan_data["budget"]["total"] == 5000
        assert "wifi" in session.plan_data["preferences"]["accommodation"]["amenities"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_session_metadata(self, db_session, test_user):
        """Test session metadata functionality."""
        metadata = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "ip_address": "192.168.1.100",
            "device_info": {
                "type": "desktop",
                "os": "Windows",
                "browser": "Chrome"
            },
            "analytics": {
                "page_views": 5,
                "time_spent": 1200,  # seconds
                "interactions": [
                    {"type": "click", "element": "search_button", "timestamp": datetime.utcnow().isoformat()},
                    {"type": "input", "element": "destination_field", "timestamp": datetime.utcnow().isoformat()}
                ]
            },
            "debug_info": {
                "session_version": "1.2.3",
                "feature_flags": ["new_ui", "enhanced_search"],
                "ab_test_groups": {"search_algorithm": "v2", "ui_theme": "light"}
            }
        }
        
        session = UnifiedTravelSession(
            user_id=test_user.id,
            status=SessionStatus.ACTIVE,
            session_metadata=metadata
        )
        
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        assert session.session_metadata["device_info"]["os"] == "Windows"
        assert session.session_metadata["analytics"]["page_views"] == 5
        assert "new_ui" in session.session_metadata["debug_info"]["feature_flags"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_session_status_enum(self, db_session, test_user):
        """Test session status enumeration."""
        # Test all valid statuses
        valid_statuses = [
            SessionStatus.ACTIVE,
            SessionStatus.PLANNING,
            SessionStatus.SEARCHING,
            SessionStatus.BOOKING,
            SessionStatus.COMPLETED,
            SessionStatus.ABANDONED,
            SessionStatus.ARCHIVED
        ]
        
        sessions = []
        for status in valid_statuses:
            session = UnifiedTravelSession(
                user_id=test_user.id,
                status=status
            )
            sessions.append(session)
            db_session.add(session)
        
        await db_session.commit()
        
        # Refresh and verify
        for session in sessions:
            await db_session.refresh(session)
            assert session.status in [s.value for s in valid_statuses]

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_session_user_relationship(self, db_session, test_user):
        """Test session-user relationship."""
        session = UnifiedTravelSession(
            user_id=test_user.id,
            status=SessionStatus.ACTIVE
        )
        
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        # Test relationship
        assert session.user is not None
        assert session.user.id == test_user.id
        assert session.user.email == test_user.email
        
        # Test reverse relationship
        user_sessions = test_user.travel_sessions
        assert len(user_sessions) >= 1
        assert any(s.session_id == session.session_id for s in user_sessions)

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_session_invalid_user(self, db_session):
        """Test session creation with invalid user."""
        session = UnifiedTravelSession(
            user_id=99999,  # Non-existent user
            status=SessionStatus.ACTIVE
        )
        
        db_session.add(session)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_session_timestamps(self, db_session, test_user):
        """Test session timestamp functionality."""
        session = UnifiedTravelSession(
            user_id=test_user.id,
            status=SessionStatus.ACTIVE
        )
        
        # Record creation time
        before_create = datetime.utcnow()
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        after_create = datetime.utcnow()
        
        # Verify creation timestamps
        assert before_create <= session.created_at <= after_create
        assert before_create <= session.updated_at <= after_create
        assert before_create <= session.last_activity_at <= after_create
        
        # Test update timestamp
        original_created = session.created_at
        original_updated = session.updated_at
        
        # Update session
        session.status = SessionStatus.PLANNING
        await db_session.commit()
        await db_session.refresh(session)
        
        # Created should stay same, updated should change
        assert session.created_at == original_created
        assert session.updated_at > original_updated

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_session_repr(self, db_session, test_user):
        """Test session string representation."""
        session = UnifiedTravelSession(
            user_id=test_user.id,
            status=SessionStatus.ACTIVE
        )
        
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        repr_str = repr(session)
        assert "UnifiedTravelSession" in repr_str
        assert session.session_id in repr_str
        assert str(test_user.id) in repr_str
        assert SessionStatus.ACTIVE.value in repr_str


class TestUnifiedSavedItemModel:
    """Test UnifiedSavedItem model functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_create_saved_flight(self, db_session, test_travel_session):
        """Test creating a saved flight item."""
        flight_data = {
            "origin": "JFK",
            "destination": "CDG",
            "departure_date": "2024-06-01",
            "return_date": "2024-06-08",
            "airline": "Air France",
            "flight_number": "AF123",
            "price": {
                "total": 850.00,
                "currency": "USD",
                "base_fare": 750.00,
                "taxes": 100.00
            },
            "duration": "8h 30m",
            "stops": 0,
            "cabin_class": "economy"
        }
        
        saved_item = UnifiedSavedItem(
            session_id=test_travel_session.session_id,
            item_type="flight",
            provider="amadeus",
            external_id="AF123_20240601",
            item_data=flight_data,
            user_notes="Good price for direct flight",
            assigned_day=1,
            sort_order=1
        )
        
        db_session.add(saved_item)
        await db_session.commit()
        await db_session.refresh(saved_item)
        
        assert saved_item.id is not None
        assert saved_item.session_id == test_travel_session.session_id
        assert saved_item.item_type == "flight"
        assert saved_item.item_data["origin"] == "JFK"
        assert saved_item.item_data["price"]["total"] == 850.00
        assert saved_item.user_notes == "Good price for direct flight"

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_create_saved_hotel(self, db_session, test_travel_session):
        """Test creating a saved hotel item."""
        hotel_data = {
            "hotel_id": "HOTEL123",
            "name": "Grand Hotel Paris",
            "location": {
                "address": "123 Rue de Rivoli, 75001 Paris",
                "latitude": 48.8566,
                "longitude": 2.3522,
                "district": "1st Arrondissement"
            },
            "check_in": "2024-06-01",
            "check_out": "2024-06-08",
            "room_type": "Superior Double Room",
            "price": {
                "total": 1400.00,
                "currency": "USD",
                "per_night": 200.00,
                "nights": 7,
                "taxes": 140.00
            },
            "amenities": ["WiFi", "Breakfast", "Gym", "Spa"],
            "rating": 4.5,
            "cancellation_policy": "Free cancellation until 48h before check-in"
        }
        
        saved_item = UnifiedSavedItem(
            session_id=test_travel_session.session_id,
            item_type="hotel",
            provider="amadeus",
            external_id="HOTEL123_20240601_20240608",
            item_data=hotel_data,
            booking_data={
                "room_preferences": {
                    "bed_type": "king",
                    "smoking": False,
                    "high_floor": True
                },
                "guest_info": {
                    "adults": 2,
                    "children": 0
                }
            },
            assigned_day=1,
            sort_order=2
        )
        
        db_session.add(saved_item)
        await db_session.commit()
        await db_session.refresh(saved_item)
        
        assert saved_item.item_type == "hotel"
        assert saved_item.item_data["name"] == "Grand Hotel Paris"
        assert saved_item.item_data["rating"] == 4.5
        assert "WiFi" in saved_item.item_data["amenities"]
        assert saved_item.booking_data["room_preferences"]["bed_type"] == "king"

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_create_saved_activity(self, db_session, test_travel_session):
        """Test creating a saved activity item."""
        activity_data = {
            "activity_id": "ACT123",
            "name": "Eiffel Tower Skip-the-Line Tour",
            "description": "Professional guided tour of the Eiffel Tower with skip-the-line access",
            "location": {
                "name": "Eiffel Tower",
                "address": "Champ de Mars, 5 Avenue Anatole France, 75007 Paris",
                "latitude": 48.8584,
                "longitude": 2.2945
            },
            "date": "2024-06-02",
            "time": "14:00",
            "duration": 120,  # minutes
            "price": {
                "total": 89.00,
                "currency": "USD",
                "per_person": 89.00,
                "persons": 1
            },
            "category": "sightseeing",
            "difficulty": "easy",
            "languages": ["English", "French"],
            "inclusions": ["Skip-the-line access", "Professional guide", "Audio headsets"],
            "meeting_point": "Eiffel Tower South Pillar",
            "cancellation_policy": "Free cancellation up to 24 hours in advance"
        }
        
        saved_item = UnifiedSavedItem(
            session_id=test_travel_session.session_id,
            item_type="activity",
            provider="viator",
            external_id="VIATOR_ACT123",
            item_data=activity_data,
            assigned_day=2,
            sort_order=1
        )
        
        db_session.add(saved_item)
        await db_session.commit()
        await db_session.refresh(saved_item)
        
        assert saved_item.item_type == "activity"
        assert saved_item.item_data["name"] == "Eiffel Tower Skip-the-Line Tour"
        assert saved_item.item_data["duration"] == 120
        assert "Skip-the-line access" in saved_item.item_data["inclusions"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_saved_item_session_relationship(self, db_session, test_travel_session):
        """Test saved item session relationship."""
        saved_item = UnifiedSavedItem(
            session_id=test_travel_session.session_id,
            item_type="flight",
            item_data={"test": "data"}
        )
        
        db_session.add(saved_item)
        await db_session.commit()
        await db_session.refresh(saved_item)
        
        # Test relationship
        assert saved_item.session is not None
        assert saved_item.session.session_id == test_travel_session.session_id
        
        # Test reverse relationship
        session_items = test_travel_session.saved_items
        assert len(session_items) >= 1
        assert any(item.id == saved_item.id for item in session_items)

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_saved_item_booking_status(self, db_session, test_travel_session):
        """Test saved item booking status tracking."""
        saved_item = UnifiedSavedItem(
            session_id=test_travel_session.session_id,
            item_type="flight",
            item_data={"test": "data"},
            is_booked=False
        )
        
        db_session.add(saved_item)
        await db_session.commit()
        await db_session.refresh(saved_item)
        
        assert saved_item.is_booked is False
        
        # Update booking status
        saved_item.is_booked = True
        saved_item.booking_data = {
            "booking_reference": "ABC123",
            "booked_at": datetime.utcnow().isoformat(),
            "booking_provider": "amadeus"
        }
        
        await db_session.commit()
        await db_session.refresh(saved_item)
        
        assert saved_item.is_booked is True
        assert saved_item.booking_data["booking_reference"] == "ABC123"

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_saved_item_day_organization(self, db_session, test_travel_session):
        """Test saved item day and order organization."""
        # Create items for different days
        items = []
        for day in range(1, 4):  # 3 days
            for order in range(1, 3):  # 2 items per day
                item = UnifiedSavedItem(
                    session_id=test_travel_session.session_id,
                    item_type="activity",
                    item_data={"name": f"Activity Day {day} Order {order}"},
                    assigned_day=day,
                    sort_order=order
                )
                items.append(item)
                db_session.add(item)
        
        await db_session.commit()
        
        # Refresh all items
        for item in items:
            await db_session.refresh(item)
        
        # Test day organization
        day_1_items = [item for item in items if item.assigned_day == 1]
        day_2_items = [item for item in items if item.assigned_day == 2]
        day_3_items = [item for item in items if item.assigned_day == 3]
        
        assert len(day_1_items) == 2
        assert len(day_2_items) == 2
        assert len(day_3_items) == 2
        
        # Test sort order
        for day_items in [day_1_items, day_2_items, day_3_items]:
            day_items.sort(key=lambda x: x.sort_order)
            assert day_items[0].sort_order == 1
            assert day_items[1].sort_order == 2

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_saved_item_invalid_session(self, db_session):
        """Test saved item creation with invalid session."""
        saved_item = UnifiedSavedItem(
            session_id="invalid-session-id",
            item_type="flight",
            item_data={"test": "data"}
        )
        
        db_session.add(saved_item)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_saved_item_repr(self, db_session, test_travel_session):
        """Test saved item string representation."""
        saved_item = UnifiedSavedItem(
            session_id=test_travel_session.session_id,
            item_type="hotel",
            item_data={"name": "Test Hotel"}
        )
        
        db_session.add(saved_item)
        await db_session.commit()
        await db_session.refresh(saved_item)
        
        repr_str = repr(saved_item)
        assert "UnifiedSavedItem" in repr_str
        assert str(saved_item.id) in repr_str
        assert test_travel_session.session_id in repr_str
        assert "hotel" in repr_str


class TestUnifiedSessionBookingModel:
    """Test UnifiedSessionBooking model functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_create_flight_booking(self, db_session, test_travel_session):
        """Test creating a flight booking record."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="flight",
            provider="amadeus",
            provider_booking_id="AMADEUS123456",
            confirmation_code="ABC123",
            booking_status="confirmed",
            total_amount=85000,  # $850.00 in cents
            currency="USD",
            payment_status="paid",
            booking_data={
                "flight_details": {
                    "origin": "JFK",
                    "destination": "CDG",
                    "departure": "2024-06-01T10:00:00",
                    "arrival": "2024-06-01T22:00:00",
                    "airline": "Air France",
                    "flight_number": "AF123"
                },
                "passenger_details": {
                    "name": "John Doe",
                    "passport": "123456789"
                }
            },
            traveler_data={
                "travelers": [
                    {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john@example.com",
                        "phone": "+1234567890",
                        "passport_number": "123456789"
                    }
                ]
            },
            payment_data={
                "method": "credit_card",
                "last_four": "1234",
                "transaction_id": "TXN123456789"
            },
            travel_date=datetime(2024, 6, 1)
        )
        
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        assert booking.id is not None
        assert booking.session_id == test_travel_session.session_id
        assert booking.booking_type == "flight"
        assert booking.provider == "amadeus"
        assert booking.total_amount == 85000
        assert booking.booking_data["flight_details"]["airline"] == "Air France"
        assert booking.traveler_data["travelers"][0]["first_name"] == "John"

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_create_hotel_booking(self, db_session, test_travel_session):
        """Test creating a hotel booking record."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="hotel",
            provider="booking.com",
            provider_booking_id="BOOKING789",
            confirmation_code="HOTEL456",
            booking_status="confirmed",
            total_amount=140000,  # $1400.00 in cents
            currency="USD",
            payment_status="paid",
            booking_data={
                "hotel_details": {
                    "name": "Grand Hotel Paris",
                    "address": "123 Rue de Rivoli, Paris",
                    "check_in": "2024-06-01",
                    "check_out": "2024-06-08",
                    "room_type": "Superior Double",
                    "nights": 7
                },
                "rate_plan": {
                    "plan_name": "Flexible Rate",
                    "cancellation": "free_until_24h",
                    "breakfast_included": True
                }
            },
            traveler_data={
                "primary_guest": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "phone": "+1234567890"
                },
                "guests": 2,
                "special_requests": ["High floor", "Late checkout"]
            },
            travel_date=datetime(2024, 6, 1)
        )
        
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        assert booking.booking_type == "hotel"
        assert booking.provider == "booking.com"
        assert booking.booking_data["hotel_details"]["name"] == "Grand Hotel Paris"
        assert booking.traveler_data["guests"] == 2

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_booking_status_transitions(self, db_session, test_travel_session):
        """Test booking status transitions."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="flight",
            provider="amadeus",
            provider_booking_id="TEST123",
            booking_status="pending",
            total_amount=50000,
            currency="USD",
            booking_data={},
            traveler_data={}
        )
        
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        assert booking.booking_status == "pending"
        
        # Transition to confirmed
        booking.booking_status = "confirmed"
        booking.confirmation_code = "CONF123"
        await db_session.commit()
        
        assert booking.booking_status == "confirmed"
        assert booking.confirmation_code == "CONF123"
        
        # Transition to cancelled
        booking.booking_status = "cancelled"
        await db_session.commit()
        
        assert booking.booking_status == "cancelled"

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_booking_payment_tracking(self, db_session, test_travel_session):
        """Test booking payment status tracking."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="hotel",
            provider="amadeus",
            provider_booking_id="PAY123",
            booking_status="confirmed",
            total_amount=100000,
            currency="USD",
            payment_status="pending",
            booking_data={},
            traveler_data={}
        )
        
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        assert booking.payment_status == "pending"
        
        # Update payment status and data
        booking.payment_status = "paid"
        booking.payment_data = {
            "payment_method": "credit_card",
            "transaction_id": "TXN789",
            "payment_date": datetime.utcnow().isoformat(),
            "amount_paid": 100000,
            "currency": "USD"
        }
        
        await db_session.commit()
        await db_session.refresh(booking)
        
        assert booking.payment_status == "paid"
        assert booking.payment_data["transaction_id"] == "TXN789"

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_booking_session_relationship(self, db_session, test_travel_session):
        """Test booking session relationship."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="activity",
            provider="viator",
            provider_booking_id="VIATOR123",
            booking_status="confirmed",
            total_amount=5000,
            currency="USD",
            booking_data={},
            traveler_data={}
        )
        
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        # Test relationship
        assert booking.session is not None
        assert booking.session.session_id == test_travel_session.session_id
        
        # Test reverse relationship
        session_bookings = test_travel_session.bookings
        assert len(session_bookings) >= 1
        assert any(b.id == booking.id for b in session_bookings)

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_booking_timestamps(self, db_session, test_travel_session):
        """Test booking timestamp functionality."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="flight",
            provider="amadeus",
            provider_booking_id="TIME123",
            booking_status="pending",
            total_amount=50000,
            currency="USD",
            booking_data={},
            traveler_data={},
            travel_date=datetime(2024, 6, 15)
        )
        
        before_create = datetime.utcnow()
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        after_create = datetime.utcnow()
        
        # Verify timestamps
        assert before_create <= booking.booking_date <= after_create
        assert before_create <= booking.created_at <= after_create
        assert before_create <= booking.updated_at <= after_create
        assert booking.travel_date.date() == datetime(2024, 6, 15).date()

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_booking_invalid_session(self, db_session):
        """Test booking creation with invalid session."""
        booking = UnifiedSessionBooking(
            session_id="invalid-session-id",
            booking_type="flight",
            provider="amadeus",
            provider_booking_id="INVALID123",
            booking_status="pending",
            total_amount=50000,
            currency="USD",
            booking_data={},
            traveler_data={}
        )
        
        db_session.add(booking)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_booking_repr(self, db_session, test_travel_session):
        """Test booking string representation."""
        booking = UnifiedSessionBooking(
            session_id=test_travel_session.session_id,
            booking_type="hotel",
            provider="amadeus",
            provider_booking_id="REPR123",
            booking_status="confirmed",
            total_amount=75000,
            currency="USD",
            booking_data={},
            traveler_data={}
        )
        
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        repr_str = repr(booking)
        assert "UnifiedSessionBooking" in repr_str
        assert str(booking.id) in repr_str
        assert test_travel_session.session_id in repr_str
        assert "hotel" in repr_str
        assert "amadeus" in repr_str


class TestSessionModelIndexes:
    """Test session model database indexes and performance."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_session_user_index(self, db_session, test_user):
        """Test user_id index performance."""
        # Create multiple sessions for the user
        sessions = []
        for i in range(10):
            session = UnifiedTravelSession(
                user_id=test_user.id,
                status=SessionStatus.ACTIVE
            )
            sessions.append(session)
            db_session.add(session)
        
        await db_session.commit()
        
        # Query should use index efficiently
        result = await db_session.execute(
            select(UnifiedTravelSession).where(
                UnifiedTravelSession.user_id == test_user.id
            )
        )
        user_sessions = result.scalars().all()
        
        assert len(user_sessions) >= 10

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_session_jsonb_indexes(self, db_session, test_user):
        """Test JSONB indexes functionality."""
        # Create session with specific destination
        session = UnifiedTravelSession(
            user_id=test_user.id,
            status=SessionStatus.ACTIVE,
            session_data={
                "parsed_intent": {
                    "destination": "Paris"
                }
            },
            plan_data={
                "destination": "Paris, France",
                "departure_date": "2024-06-01"
            }
        )
        
        db_session.add(session)
        await db_session.commit()
        
        # Test JSONB path queries
        result = await db_session.execute(
            text("""
                SELECT session_id FROM unified_travel_sessions 
                WHERE session_data->'parsed_intent'->>'destination' = 'Paris'
            """)
        )
        paris_sessions = result.fetchall()
        assert len(paris_sessions) >= 1
        
        result = await db_session.execute(
            text("""
                SELECT session_id FROM unified_travel_sessions 
                WHERE plan_data->>'departure_date' = '2024-06-01'
            """)
        )
        june_sessions = result.fetchall()
        assert len(june_sessions) >= 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_saved_item_indexes(self, db_session, test_travel_session):
        """Test saved item indexes."""
        # Create items of different types
        item_types = ["flight", "hotel", "activity"]
        for item_type in item_types:
            item = UnifiedSavedItem(
                session_id=test_travel_session.session_id,
                item_type=item_type,
                item_data={"name": f"Test {item_type}"}
            )
            db_session.add(item)
        
        await db_session.commit()
        
        # Test session+type index
        result = await db_session.execute(
            select(UnifiedSavedItem).where(
                and_(
                    UnifiedSavedItem.session_id == test_travel_session.session_id,
                    UnifiedSavedItem.item_type == "flight"
                )
            )
        )
        flight_items = result.scalars().all()
        assert len(flight_items) >= 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_booking_indexes(self, db_session, test_travel_session):
        """Test booking indexes."""
        # Create bookings with different statuses
        statuses = ["pending", "confirmed", "cancelled"]
        for status in statuses:
            booking = UnifiedSessionBooking(
                session_id=test_travel_session.session_id,
                booking_type="flight",
                provider="amadeus",
                provider_booking_id=f"TEST_{status.upper()}",
                booking_status=status,
                total_amount=50000,
                currency="USD",
                booking_data={},
                traveler_data={}
            )
            db_session.add(booking)
        
        await db_session.commit()
        
        # Test status index
        result = await db_session.execute(
            select(UnifiedSessionBooking).where(
                UnifiedSessionBooking.booking_status == "confirmed"
            )
        )
        confirmed_bookings = result.scalars().all()
        assert len(confirmed_bookings) >= 1


class TestSessionModelCascading:
    """Test cascading deletes and relationship management."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_session_delete_cascade_saved_items(self, db_session, test_travel_session):
        """Test that deleting session cascades to saved items."""
        # Create saved items
        for i in range(3):
            item = UnifiedSavedItem(
                session_id=test_travel_session.session_id,
                item_type="activity",
                item_data={"name": f"Activity {i}"}
            )
            db_session.add(item)
        
        await db_session.commit()
        
        # Verify items exist
        result = await db_session.execute(
            select(UnifiedSavedItem).where(
                UnifiedSavedItem.session_id == test_travel_session.session_id
            )
        )
        items_before = result.scalars().all()
        assert len(items_before) == 3
        
        # Delete session
        await db_session.delete(test_travel_session)
        await db_session.commit()
        
        # Verify items are deleted
        result = await db_session.execute(
            select(UnifiedSavedItem).where(
                UnifiedSavedItem.session_id == test_travel_session.session_id
            )
        )
        items_after = result.scalars().all()
        assert len(items_after) == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.model
    async def test_session_delete_cascade_bookings(self, db_session, test_travel_session):
        """Test that deleting session cascades to bookings."""
        # Create bookings
        for i in range(2):
            booking = UnifiedSessionBooking(
                session_id=test_travel_session.session_id,
                booking_type="flight",
                provider="amadeus",
                provider_booking_id=f"CASCADE_{i}",
                booking_status="confirmed",
                total_amount=50000,
                currency="USD",
                booking_data={},
                traveler_data={}
            )
            db_session.add(booking)
        
        await db_session.commit()
        
        # Verify bookings exist
        result = await db_session.execute(
            select(UnifiedSessionBooking).where(
                UnifiedSessionBooking.session_id == test_travel_session.session_id
            )
        )
        bookings_before = result.scalars().all()
        assert len(bookings_before) == 2
        
        # Delete session
        await db_session.delete(test_travel_session)
        await db_session.commit()
        
        # Verify bookings are deleted
        result = await db_session.execute(
            select(UnifiedSessionBooking).where(
                UnifiedSessionBooking.session_id == test_travel_session.session_id
            )
        )
        bookings_after = result.scalars().all()
        assert len(bookings_after) == 0