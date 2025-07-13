"""
Travelers API endpoint tests.

Tests for traveler management endpoints including traveler profiles,
document management, preferences, and travel history.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from fastapi import status
from httpx import AsyncClient

from app.models import Traveler, TravelerDocument, TravelerPreference
from app.schemas.traveler import (
    TravelerCreate, TravelerUpdate, TravelerDocumentCreate,
    TravelerPreferenceUpdate, TravelerSearch
)


class TestTravelerProfileManagement:
    """Test traveler profile management endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_create_traveler_success(self, async_client: AsyncClient, auth_headers, test_user):
        """Test successful traveler profile creation."""
        traveler_data = {
            "first_name": "John",
            "last_name": "Doe",
            "middle_name": "William",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "date_of_birth": "1990-01-15",
            "gender": "male",
            "nationality": "US",
            "emergency_contact": {
                "name": "Jane Doe",
                "relationship": "spouse",
                "phone": "+1234567891",
                "email": "jane.doe@example.com"
            },
            "dietary_restrictions": ["vegetarian"],
            "accessibility_needs": [],
            "known_traveler_number": "12345678901",
            "global_entry_number": "98765432"
        }
        
        response = await async_client.post(
            "/api/v1/travelers",
            json=traveler_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert "traveler_id" in data
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["email"] == "john.doe@example.com"
        assert data["user_id"] == test_user.id

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_create_traveler_duplicate_email(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test creating traveler with duplicate email for same user."""
        # Create first traveler
        traveler1 = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler1)
        await db_session.commit()
        
        # Try to create second traveler with same email
        traveler_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "john.doe@example.com",  # Same email
            "date_of_birth": "1985-05-20"
        }
        
        response = await async_client.post(
            "/api/v1/travelers",
            json=traveler_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email already exists" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_create_traveler_invalid_data(self, async_client: AsyncClient, auth_headers):
        """Test creating traveler with invalid data."""
        traveler_data = {
            "first_name": "",  # Empty name
            "last_name": "Doe",
            "email": "invalid-email",  # Invalid email
            "date_of_birth": "2030-01-01"  # Future date
        }
        
        response = await async_client.post(
            "/api/v1/travelers",
            json=traveler_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_user_travelers(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test retrieving user's travelers."""
        # Create test travelers
        traveler1 = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        traveler2 = Traveler(
            user_id=test_user.id,
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            date_of_birth=datetime(1985, 5, 20).date()
        )
        db_session.add_all([traveler1, traveler2])
        await db_session.commit()
        
        response = await async_client.get("/api/v1/travelers", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "travelers" in data
        assert "total" in data
        assert len(data["travelers"]) == 2
        
        # Check traveler structure
        traveler = data["travelers"][0]
        assert "traveler_id" in traveler
        assert "first_name" in traveler
        assert "last_name" in traveler

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_traveler_by_id(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test retrieving specific traveler by ID."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date(),
            phone="+1234567890",
            nationality="US"
        )
        db_session.add(traveler)
        await db_session.commit()
        await db_session.refresh(traveler)
        
        response = await async_client.get(f"/api/v1/travelers/{traveler.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["traveler_id"] == traveler.id
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["nationality"] == "US"

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_nonexistent_traveler(self, async_client: AsyncClient, auth_headers):
        """Test retrieving non-existent traveler."""
        response = await async_client.get("/api/v1/travelers/99999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_update_traveler_profile(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test updating traveler profile."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler)
        await db_session.commit()
        await db_session.refresh(traveler)
        
        update_data = {
            "phone": "+1987654321",
            "emergency_contact": {
                "name": "Jane Doe",
                "relationship": "spouse",
                "phone": "+1987654322"
            },
            "dietary_restrictions": ["gluten-free", "vegetarian"]
        }
        
        response = await async_client.put(
            f"/api/v1/travelers/{traveler.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["phone"] == "+1987654321"
        assert "gluten-free" in data["dietary_restrictions"]

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_delete_traveler(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test deleting a traveler profile."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler)
        await db_session.commit()
        await db_session.refresh(traveler)
        
        response = await async_client.delete(f"/api/v1/travelers/{traveler.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify traveler is deleted
        get_response = await async_client.get(f"/api/v1/travelers/{traveler.id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


class TestTravelerDocuments:
    """Test traveler document management endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_add_passport_document(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test adding passport document to traveler."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler)
        await db_session.commit()
        await db_session.refresh(traveler)
        
        document_data = {
            "document_type": "passport",
            "document_number": "123456789",
            "issuing_country": "US",
            "issue_date": "2020-01-01",
            "expiry_date": "2030-01-01",
            "full_name_on_document": "John William Doe"
        }
        
        response = await async_client.post(
            f"/api/v1/travelers/{traveler.id}/documents",
            json=document_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["document_type"] == "passport"
        assert data["document_number"] == "123456789"
        assert data["issuing_country"] == "US"

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_add_drivers_license_document(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test adding driver's license document."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler)
        await db_session.commit()
        await db_session.refresh(traveler)
        
        document_data = {
            "document_type": "drivers_license",
            "document_number": "DL123456789",
            "issuing_country": "US",
            "issuing_state": "NY",
            "issue_date": "2020-01-01",
            "expiry_date": "2028-01-01",
            "full_name_on_document": "John William Doe"
        }
        
        response = await async_client.post(
            f"/api/v1/travelers/{traveler.id}/documents",
            json=document_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["document_type"] == "drivers_license"
        assert data["issuing_state"] == "NY"

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_traveler_documents(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test retrieving traveler documents."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler)
        await db_session.commit()
        await db_session.refresh(traveler)
        
        # Add documents
        passport = TravelerDocument(
            traveler_id=traveler.id,
            document_type="passport",
            document_number="123456789",
            issuing_country="US",
            issue_date=datetime(2020, 1, 1).date(),
            expiry_date=datetime(2030, 1, 1).date()
        )
        license_doc = TravelerDocument(
            traveler_id=traveler.id,
            document_type="drivers_license",
            document_number="DL123456789",
            issuing_country="US",
            issue_date=datetime(2020, 1, 1).date(),
            expiry_date=datetime(2028, 1, 1).date()
        )
        db_session.add_all([passport, license_doc])
        await db_session.commit()
        
        response = await async_client.get(f"/api/v1/travelers/{traveler.id}/documents", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "documents" in data
        assert len(data["documents"]) == 2
        
        doc_types = [doc["document_type"] for doc in data["documents"]]
        assert "passport" in doc_types
        assert "drivers_license" in doc_types

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_update_document(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test updating a traveler document."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler)
        await db_session.commit()
        await db_session.refresh(traveler)
        
        document = TravelerDocument(
            traveler_id=traveler.id,
            document_type="passport",
            document_number="123456789",
            issuing_country="US",
            issue_date=datetime(2020, 1, 1).date(),
            expiry_date=datetime(2030, 1, 1).date()
        )
        db_session.add(document)
        await db_session.commit()
        await db_session.refresh(document)
        
        update_data = {
            "expiry_date": "2035-01-01",
            "notes": "Renewed passport"
        }
        
        response = await async_client.put(
            f"/api/v1/travelers/{traveler.id}/documents/{document.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["expiry_date"] == "2035-01-01"
        assert data["notes"] == "Renewed passport"

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_delete_document(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test deleting a traveler document."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler)
        await db_session.commit()
        await db_session.refresh(traveler)
        
        document = TravelerDocument(
            traveler_id=traveler.id,
            document_type="passport",
            document_number="123456789",
            issuing_country="US",
            issue_date=datetime(2020, 1, 1).date(),
            expiry_date=datetime(2030, 1, 1).date()
        )
        db_session.add(document)
        await db_session.commit()
        await db_session.refresh(document)
        
        response = await async_client.delete(
            f"/api/v1/travelers/{traveler.id}/documents/{document.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify document is deleted
        get_response = await async_client.get(f"/api/v1/travelers/{traveler.id}/documents", headers=auth_headers)
        documents = get_response.json()["documents"]
        assert len(documents) == 0

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_document_expiry_check(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test checking document expiry status."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler)
        await db_session.commit()
        await db_session.refresh(traveler)
        
        # Add expired document
        expired_passport = TravelerDocument(
            traveler_id=traveler.id,
            document_type="passport",
            document_number="123456789",
            issuing_country="US",
            issue_date=datetime(2015, 1, 1).date(),
            expiry_date=datetime(2023, 1, 1).date()  # Expired
        )
        db_session.add(expired_passport)
        await db_session.commit()
        
        response = await async_client.get(f"/api/v1/travelers/{traveler.id}/documents/expiry-check", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "expired_documents" in data
        assert "expiring_soon" in data
        assert len(data["expired_documents"]) == 1


class TestTravelerPreferences:
    """Test traveler preference management endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_set_travel_preferences(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test setting traveler preferences."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler)
        await db_session.commit()
        await db_session.refresh(traveler)
        
        preferences_data = {
            "flight_preferences": {
                "seat_preference": "aisle",
                "meal_preference": "vegetarian",
                "class_preference": "economy",
                "airline_preferences": ["AA", "UA", "DL"]
            },
            "hotel_preferences": {
                "room_type": "non_smoking",
                "bed_type": "king",
                "floor_preference": "high",
                "amenities": ["wifi", "gym", "pool"]
            },
            "general_preferences": {
                "currency": "USD",
                "language": "en",
                "time_zone": "America/New_York",
                "notification_preferences": {
                    "email": True,
                    "sms": False,
                    "push": True
                }
            }
        }
        
        response = await async_client.put(
            f"/api/v1/travelers/{traveler.id}/preferences",
            json=preferences_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "flight_preferences" in data
        assert "hotel_preferences" in data
        assert data["flight_preferences"]["seat_preference"] == "aisle"

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_get_travel_preferences(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test retrieving traveler preferences."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler)
        await db_session.commit()
        await db_session.refresh(traveler)
        
        # Add preferences
        preference = TravelerPreference(
            traveler_id=traveler.id,
            preference_type="flight",
            preference_data={
                "seat_preference": "window",
                "meal_preference": "kosher"
            }
        )
        db_session.add(preference)
        await db_session.commit()
        
        response = await async_client.get(f"/api/v1/travelers/{traveler.id}/preferences", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "preferences" in data
        assert "flight" in data["preferences"]

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_update_specific_preference(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test updating specific preference category."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler)
        await db_session.commit()
        await db_session.refresh(traveler)
        
        update_data = {
            "seat_preference": "window",
            "meal_preference": "vegan",
            "special_assistance": ["wheelchair"]
        }
        
        response = await async_client.put(
            f"/api/v1/travelers/{traveler.id}/preferences/flight",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["seat_preference"] == "window"
        assert "wheelchair" in data["special_assistance"]


class TestTravelerSearch:
    """Test traveler search functionality."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_search_travelers_by_name(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test searching travelers by name."""
        # Create test travelers
        travelers = [
            Traveler(
                user_id=test_user.id,
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                date_of_birth=datetime(1990, 1, 15).date()
            ),
            Traveler(
                user_id=test_user.id,
                first_name="Jane",
                last_name="Smith",
                email="jane@example.com",
                date_of_birth=datetime(1985, 5, 20).date()
            ),
            Traveler(
                user_id=test_user.id,
                first_name="Bob",
                last_name="Johnson",
                email="bob@example.com",
                date_of_birth=datetime(1995, 10, 10).date()
            )
        ]
        db_session.add_all(travelers)
        await db_session.commit()
        
        # Search for "John"
        params = {"search": "John"}
        response = await async_client.get("/api/v1/travelers/search", params=params, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "travelers" in data
        assert len(data["travelers"]) == 1
        assert data["travelers"][0]["first_name"] == "John"

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_search_travelers_by_email(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test searching travelers by email."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler)
        await db_session.commit()
        
        params = {"email": "john.doe@example.com"}
        response = await async_client.get("/api/v1/travelers/search", params=params, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["travelers"]) == 1
        assert data["travelers"][0]["email"] == "john.doe@example.com"

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_filter_travelers_by_age_range(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test filtering travelers by age range."""
        travelers = [
            Traveler(
                user_id=test_user.id,
                first_name="Young",
                last_name="Person",
                email="young@example.com",
                date_of_birth=datetime(2005, 1, 1).date()  # ~19 years old
            ),
            Traveler(
                user_id=test_user.id,
                first_name="Adult",
                last_name="Person",
                email="adult@example.com",
                date_of_birth=datetime(1990, 1, 1).date()  # ~34 years old
            ),
            Traveler(
                user_id=test_user.id,
                first_name="Senior",
                last_name="Person",
                email="senior@example.com",
                date_of_birth=datetime(1950, 1, 1).date()  # ~74 years old
            )
        ]
        db_session.add_all(travelers)
        await db_session.commit()
        
        # Filter for adults (25-65)
        params = {"min_age": 25, "max_age": 65}
        response = await async_client.get("/api/v1/travelers/search", params=params, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["travelers"]) == 1
        assert data["travelers"][0]["first_name"] == "Adult"


class TestTravelerValidation:
    """Test traveler data validation."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_validate_traveler_age(self, async_client: AsyncClient, auth_headers):
        """Test traveler age validation."""
        traveler_data = {
            "first_name": "Future",
            "last_name": "Person",
            "email": "future@example.com",
            "date_of_birth": "2030-01-01"  # Future date
        }
        
        response = await async_client.post(
            "/api/v1/travelers",
            json=traveler_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_validate_document_dates(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test document date validation."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler)
        await db_session.commit()
        await db_session.refresh(traveler)
        
        # Try to add document with issue date after expiry date
        document_data = {
            "document_type": "passport",
            "document_number": "123456789",
            "issuing_country": "US",
            "issue_date": "2025-01-01",
            "expiry_date": "2020-01-01",  # Before issue date
            "full_name_on_document": "John Doe"
        }
        
        response = await async_client.post(
            f"/api/v1/travelers/{traveler.id}/documents",
            json=document_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_validate_phone_number(self, async_client: AsyncClient, auth_headers):
        """Test phone number validation."""
        traveler_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "date_of_birth": "1990-01-15",
            "phone": "invalid-phone-number"
        }
        
        response = await async_client.post(
            "/api/v1/travelers",
            json=traveler_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestTravelerSecurity:
    """Test traveler data security and privacy."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_traveler_data_encryption(self, async_client: AsyncClient, auth_headers, test_user, db_session):
        """Test that sensitive traveler data is properly handled."""
        traveler_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "date_of_birth": "1990-01-15",
            "social_security_number": "123-45-6789",  # Sensitive data
            "passport_number": "123456789"
        }
        
        response = await async_client.post(
            "/api/v1/travelers",
            json=traveler_data,
            headers=auth_headers
        )
        
        # Should succeed but sensitive data should be handled securely
        assert response.status_code == status.HTTP_201_CREATED
        
        # SSN should not be returned in response
        data = response.json()
        assert "social_security_number" not in data

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_access_other_user_traveler(self, async_client: AsyncClient, auth_headers, db_session):
        """Test that users cannot access other users' travelers."""
        # Create traveler for a different user (user_id=999)
        other_traveler = Traveler(
            user_id=999,  # Different user
            first_name="Other",
            last_name="User",
            email="other@example.com",
            date_of_birth=datetime(1985, 1, 1).date()
        )
        db_session.add(other_traveler)
        await db_session.commit()
        await db_session.refresh(other_traveler)
        
        # Try to access other user's traveler
        response = await async_client.get(f"/api/v1/travelers/{other_traveler.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_update_other_user_traveler(self, async_client: AsyncClient, auth_headers, db_session):
        """Test that users cannot update other users' travelers."""
        other_traveler = Traveler(
            user_id=999,
            first_name="Other",
            last_name="User",
            email="other@example.com",
            date_of_birth=datetime(1985, 1, 1).date()
        )
        db_session.add(other_traveler)
        await db_session.commit()
        await db_session.refresh(other_traveler)
        
        update_data = {"phone": "+1234567890"}
        
        response = await async_client.put(
            f"/api/v1/travelers/{other_traveler.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTravelerIntegration:
    """Test traveler integration with other services."""

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_traveler_booking_integration(self, async_client: AsyncClient, auth_headers, test_user, test_travel_session, db_session):
        """Test traveler integration with booking system."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler)
        await db_session.commit()
        await db_session.refresh(traveler)
        
        # Test endpoint that should show traveler's booking history
        response = await async_client.get(f"/api/v1/travelers/{traveler.id}/bookings", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "bookings" in data
        assert isinstance(data["bookings"], list)

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_traveler_session_integration(self, async_client: AsyncClient, auth_headers, test_user, test_travel_session, db_session):
        """Test traveler integration with travel sessions."""
        traveler = Traveler(
            user_id=test_user.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=datetime(1990, 1, 15).date()
        )
        db_session.add(traveler)
        await db_session.commit()
        await db_session.refresh(traveler)
        
        # Add traveler to session
        session_data = {
            "traveler_ids": [traveler.id]
        }
        
        response = await async_client.post(
            f"/api/v1/travel/sessions/{test_travel_session.session_id}/travelers",
            json=session_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK