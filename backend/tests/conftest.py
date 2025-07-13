"""
Pytest configuration and fixtures for Pathavana backend testing.

This module provides shared fixtures, test configuration, and utilities
for all backend tests including database setup, authentication, and mocking.
"""

import asyncio
import os
import pytest
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import app components
from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models import (
    User, UserProfile, UnifiedTravelSession, UnifiedSavedItem,
    UnifiedSessionBooking, UserSession
)
from app.schemas.auth import UserRegister
from app.services.llm_service import LLMService
from app.services.amadeus_service import AmadeusService
from app.services.cache_service import CacheService
from app.services.trip_context_service import TripContextService


# Test database configuration
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/pathavana_test"

# Configure test settings
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # Create test database if it doesn't exist
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        pytest.fail(f"Failed to create test database: {e}")
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Start a transaction
        await session.begin()
        
        try:
            yield session
        finally:
            # Rollback transaction to clean up
            await session.rollback()


@pytest.fixture
def client(db_session):
    """Create FastAPI test client with database dependency override."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(db_session):
    """Create async HTTP client for testing."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# User and Authentication Fixtures
@pytest.fixture
async def test_user_data() -> Dict[str, Any]:
    """Test user registration data."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "phone": "+1234567890",
        "terms_accepted": True,
        "marketing_consent": False
    }


@pytest.fixture
async def test_user(db_session: AsyncSession, test_user_data: Dict[str, Any]) -> User:
    """Create a test user in the database."""
    user = User(
        email=test_user_data["email"],
        password_hash=get_password_hash(test_user_data["password"]),
        full_name=test_user_data["full_name"],
        first_name="Test",
        last_name="User",
        phone=test_user_data["phone"],
        email_verified=True,
        status="active"
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create user profile
    profile = UserProfile(
        user_id=user.id,
        preferred_language="en",
        preferred_currency="USD"
    )
    db_session.add(profile)
    await db_session.commit()
    
    return user


@pytest.fixture
async def authenticated_user(test_user: User) -> Dict[str, Any]:
    """Create authenticated user with access token."""
    access_token = create_access_token(
        data={"sub": str(test_user.id), "email": test_user.email}
    )
    
    return {
        "user": test_user,
        "access_token": access_token,
        "headers": {"Authorization": f"Bearer {access_token}"}
    }


@pytest.fixture
async def auth_headers(authenticated_user: Dict[str, Any]) -> Dict[str, str]:
    """Get authentication headers for API requests."""
    return authenticated_user["headers"]


# Travel Session Fixtures
@pytest.fixture
async def test_travel_session(db_session: AsyncSession, test_user: User) -> UnifiedTravelSession:
    """Create a test travel session."""
    session = UnifiedTravelSession(
        user_id=test_user.id,
        status="active",
        session_data={
            "messages": [
                {
                    "role": "user",
                    "content": "I want to plan a trip to Paris",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ],
            "parsed_intent": {
                "destination": "Paris",
                "travel_type": "leisure",
                "preferences": ["culture", "food"]
            }
        },
        plan_data={
            "destination": "Paris, France",
            "departure_date": "2024-06-01",
            "return_date": "2024-06-08",
            "travelers": 2,
            "budget": 5000
        }
    )
    
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    
    return session


@pytest.fixture
async def test_saved_item(db_session: AsyncSession, test_travel_session: UnifiedTravelSession) -> UnifiedSavedItem:
    """Create a test saved item."""
    item = UnifiedSavedItem(
        session_id=test_travel_session.session_id,
        item_type="flight",
        provider="amadeus",
        external_id="test_flight_123",
        item_data={
            "origin": "JFK",
            "destination": "CDG",
            "departure_date": "2024-06-01",
            "return_date": "2024-06-08",
            "price": 850,
            "currency": "USD",
            "airline": "Air France"
        },
        assigned_day=1,
        sort_order=1
    )
    
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    
    return item


# Mock Service Fixtures
@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    mock_service = AsyncMock(spec=LLMService)
    
    # Mock typical responses
    mock_service.parse_travel_intent.return_value = {
        "destination": "Paris",
        "travel_dates": {
            "departure": "2024-06-01",
            "return": "2024-06-08"
        },
        "travelers": 2,
        "travel_type": "leisure",
        "preferences": ["culture", "food"]
    }
    
    mock_service.generate_response.return_value = {
        "response": "I'd be happy to help you plan your trip to Paris!",
        "suggestions": [
            "Visit the Eiffel Tower",
            "Explore the Louvre Museum",
            "Try French cuisine"
        ]
    }
    
    mock_service.generate_itinerary.return_value = {
        "itinerary": [
            {
                "day": 1,
                "activities": ["Arrive in Paris", "Check into hotel", "Visit Eiffel Tower"]
            },
            {
                "day": 2,
                "activities": ["Louvre Museum", "Seine River cruise", "Dinner in Montmartre"]
            }
        ]
    }
    
    return mock_service


@pytest.fixture
def mock_amadeus_service():
    """Mock Amadeus service for testing."""
    mock_service = AsyncMock(spec=AmadeusService)
    
    # Mock flight search response
    mock_service.search_flights.return_value = {
        "data": [
            {
                "id": "flight_123",
                "itineraries": [
                    {
                        "segments": [
                            {
                                "departure": {
                                    "iataCode": "JFK",
                                    "at": "2024-06-01T10:00:00"
                                },
                                "arrival": {
                                    "iataCode": "CDG",
                                    "at": "2024-06-01T22:00:00"
                                },
                                "carrierCode": "AF",
                                "number": "123"
                            }
                        ]
                    }
                ],
                "price": {
                    "total": "850.00",
                    "currency": "USD"
                }
            }
        ]
    }
    
    # Mock hotel search response
    mock_service.search_hotels.return_value = {
        "data": [
            {
                "hotel": {
                    "hotelId": "hotel_123",
                    "name": "Paris Grand Hotel",
                    "cityCode": "PAR"
                },
                "offers": [
                    {
                        "id": "offer_123",
                        "price": {
                            "total": "200.00",
                            "currency": "USD"
                        },
                        "room": {
                            "type": "DOUBLE",
                            "typeEstimated": {
                                "category": "STANDARD"
                            }
                        }
                    }
                ]
            }
        ]
    }
    
    return mock_service


@pytest.fixture
def mock_cache_service():
    """Mock cache service for testing."""
    mock_service = AsyncMock(spec=CacheService)
    
    # Mock cache operations
    mock_service.get.return_value = None  # Cache miss by default
    mock_service.set.return_value = True
    mock_service.delete.return_value = True
    mock_service.exists.return_value = False
    
    return mock_service


@pytest.fixture
def mock_trip_context_service():
    """Mock trip context service for testing."""
    mock_service = AsyncMock(spec=TripContextService)
    
    mock_service.build_context.return_value = {
        "destination": "Paris, France",
        "travel_dates": {
            "departure": "2024-06-01",
            "return": "2024-06-08"
        },
        "travelers": 2,
        "preferences": ["culture", "food"],
        "saved_items": [],
        "conversation_history": []
    }
    
    return mock_service


# Test Data Factories
@pytest.fixture
def flight_data_factory():
    """Factory for creating flight test data."""
    def create_flight_data(**kwargs):
        default_data = {
            "origin": "JFK",
            "destination": "CDG",
            "departure_date": "2024-06-01",
            "return_date": "2024-06-08",
            "passengers": 2,
            "class": "economy",
            "price": 850,
            "currency": "USD",
            "airline": "Air France",
            "flight_number": "AF123"
        }
        default_data.update(kwargs)
        return default_data
    
    return create_flight_data


@pytest.fixture
def hotel_data_factory():
    """Factory for creating hotel test data."""
    def create_hotel_data(**kwargs):
        default_data = {
            "hotel_id": "hotel_123",
            "name": "Paris Grand Hotel",
            "city": "Paris",
            "country": "France",
            "check_in": "2024-06-01",
            "check_out": "2024-06-08",
            "rooms": 1,
            "guests": 2,
            "price": 200,
            "currency": "USD",
            "rating": 4.5
        }
        default_data.update(kwargs)
        return default_data
    
    return create_hotel_data


@pytest.fixture
def activity_data_factory():
    """Factory for creating activity test data."""
    def create_activity_data(**kwargs):
        default_data = {
            "activity_id": "activity_123",
            "name": "Eiffel Tower Tour",
            "description": "Guided tour of the Eiffel Tower",
            "location": "Paris, France",
            "date": "2024-06-02",
            "duration": 180,
            "price": 50,
            "currency": "USD",
            "category": "sightseeing"
        }
        default_data.update(kwargs)
        return default_data
    
    return create_activity_data


# Utility Fixtures
@pytest.fixture
def test_session_id():
    """Generate a test session ID."""
    return str(uuid.uuid4())


@pytest.fixture
def test_timestamps():
    """Generate test timestamps."""
    now = datetime.utcnow()
    return {
        "now": now,
        "past": now - timedelta(days=7),
        "future": now + timedelta(days=7),
        "iso_now": now.isoformat(),
        "iso_past": (now - timedelta(days=7)).isoformat(),
        "iso_future": (now + timedelta(days=7)).isoformat()
    }


# Error Testing Fixtures
@pytest.fixture
def mock_external_api_error():
    """Mock external API error responses."""
    def create_error_response(status_code: int = 500, message: str = "External API Error"):
        error = Exception(message)
        error.status_code = status_code
        return error
    
    return create_error_response


# Performance Testing Fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.elapsed
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Database Cleanup Utilities
@pytest.fixture
async def cleanup_db(db_session: AsyncSession):
    """Cleanup database after tests."""
    yield
    
    # Clean up test data
    tables_to_clean = [
        UnifiedSessionBooking,
        UnifiedSavedItem,
        UnifiedTravelSession,
        UserSession,
        UserProfile,
        User
    ]
    
    for table in tables_to_clean:
        await db_session.execute(text(f"TRUNCATE TABLE {table.__tablename__} CASCADE"))
    
    await db_session.commit()


# Mock Request/Response Fixtures
@pytest.fixture
def mock_request():
    """Mock FastAPI request object."""
    mock_request = MagicMock()
    mock_request.client.host = "127.0.0.1"
    mock_request.headers = {"user-agent": "test-client"}
    mock_request.method = "GET"
    mock_request.url = "http://test.example.com/api/test"
    return mock_request


@pytest.fixture
def sample_api_responses():
    """Sample API responses for testing."""
    return {
        "amadeus_flight_search": {
            "data": [
                {
                    "type": "flight-offer",
                    "id": "1",
                    "itineraries": [
                        {
                            "duration": "PT8H35M",
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
                                        "at": "2024-06-01T22:35:00"
                                    },
                                    "carrierCode": "AF",
                                    "number": "123",
                                    "aircraft": {"code": "333"},
                                    "duration": "PT8H35M"
                                }
                            ]
                        }
                    ],
                    "price": {
                        "currency": "USD",
                        "total": "850.00",
                        "base": "750.00",
                        "fees": [
                            {
                                "amount": "100.00",
                                "type": "SUPPLIER"
                            }
                        ]
                    }
                }
            ]
        }
    }


# Test configuration marker utilities
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (deselect with '-m \"not unit\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "external: marks tests that require external services"
    )