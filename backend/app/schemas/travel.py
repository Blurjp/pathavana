"""
Travel-related Pydantic schemas for unified travel API.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

from .base import PriceInfo, LocationInfo, DateRange


class SessionStatus(str, Enum):
    """Travel session status options."""
    ACTIVE = "active"
    PLANNING = "planning"
    BOOKED = "booked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MessageRole(str, Enum):
    """Chat message role options."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SearchType(str, Enum):
    """Search type options."""
    FLIGHTS = "flights"
    HOTELS = "hotels"
    ACTIVITIES = "activities"
    ALL = "all"


class ItemType(str, Enum):
    """Item type options for saved items."""
    FLIGHT = "flight"
    HOTEL = "hotel"
    ACTIVITY = "activity"
    RESTAURANT = "restaurant"
    TRANSPORT = "transport"
    OTHER = "other"


class ChatMessage(BaseModel):
    """Individual chat message."""
    role: MessageRole = Field(..., description="Message sender role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional message metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ParsedIntent(BaseModel):
    """Parsed travel intent from user message."""
    destination: Optional[str] = Field(None, description="Destination city or country")
    departure_city: Optional[str] = Field(None, description="Departure city")
    departure_date: Optional[date] = Field(None, description="Departure date")
    return_date: Optional[date] = Field(None, description="Return date")
    travelers: Optional[Dict[str, int]] = Field(
        default={"adults": 1, "children": 0, "infants": 0},
        description="Number of travelers by type"
    )
    budget: Optional[PriceInfo] = Field(None, description="Budget information")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Travel preferences")
    confidence: float = Field(default=0.8, description="Confidence score of parsing")
    timeframe: Optional[str] = Field(None, description="Flexible timeframe description")

    @validator('departure_date', 'return_date')
    def validate_future_dates(cls, v):
        if v and v < date.today():
            raise ValueError('Dates must be in the future')
        return v

    @validator('return_date')
    def validate_return_after_departure(cls, v, values):
        if v and 'departure_date' in values and values['departure_date']:
            if v <= values['departure_date']:
                raise ValueError('Return date must be after departure date')
        return v


class TripContext(BaseModel):
    """Comprehensive trip context with conflict tracking."""
    departure_city: Optional[str] = Field(None, description="Departure city")
    destination_city: Optional[str] = Field(None, description="Primary destination")
    destinations: Optional[List[str]] = Field(None, description="Multiple destinations for multi-city trips")
    start_date: Optional[date] = Field(None, description="Trip start date")
    end_date: Optional[date] = Field(None, description="Trip end date")
    travelers: int = Field(default=1, description="Total number of travelers")
    budget: Optional[PriceInfo] = Field(None, description="Trip budget")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    conflicts_resolved: Optional[List[str]] = Field(None, description="List of resolved conflicts")
    confidence: float = Field(default=0.8, description="Overall confidence in trip context")
    city_durations: Optional[Dict[str, int]] = Field(None, description="Days to spend in each city")


class SearchResults(BaseModel):
    """Search results container."""
    flights: Optional[List[Dict[str, Any]]] = Field(None, description="Flight search results")
    hotels: Optional[List[Dict[str, Any]]] = Field(None, description="Hotel search results")
    activities: Optional[List[Dict[str, Any]]] = Field(None, description="Activity search results")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    search_id: Optional[str] = Field(None, description="Unique search identifier")


class TravelSessionCreate(BaseModel):
    """Request to create a new travel session."""
    message: str = Field(..., description="Initial travel query message")
    source: str = Field(default="web", description="Source of the request")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional request metadata")

    @validator('message')
    def validate_message_length(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Message must be at least 3 characters long')
        if len(v) > 2000:
            raise ValueError('Message must be less than 2000 characters')
        return v.strip()


class ChatRequest(BaseModel):
    """Request to send a message to an existing session."""
    message: str = Field(..., description="Chat message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Message metadata")

    @validator('message')
    def validate_message_length(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Message cannot be empty')
        if len(v) > 2000:
            raise ValueError('Message must be less than 2000 characters')
        return v.strip()


class SearchRequest(BaseModel):
    """Request to trigger searches for a session."""
    search_types: List[SearchType] = Field(..., description="Types of searches to perform")
    force_refresh: bool = Field(default=False, description="Force refresh of cached results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Search preferences")

    @validator('search_types')
    def validate_search_types(cls, v):
        if not v:
            raise ValueError('At least one search type must be specified')
        return v


class SaveItemRequest(BaseModel):
    """Request to save an item to a trip."""
    item_type: ItemType = Field(..., description="Type of item being saved")
    item_data: Dict[str, Any] = Field(..., description="Complete item data")
    assigned_day: Optional[int] = Field(None, description="Day number in itinerary")
    notes: Optional[str] = Field(None, description="User notes for the item")
    priority: Optional[str] = Field(None, description="Item priority level")

    @validator('item_data')
    def validate_item_data(cls, v):
        if not v:
            raise ValueError('Item data cannot be empty')
        return v

    @validator('assigned_day')
    def validate_assigned_day(cls, v):
        if v is not None and v < 1:
            raise ValueError('Assigned day must be positive')
        return v


class TravelSessionResponse(BaseModel):
    """Complete travel session data response."""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[int] = Field(None, description="Associated user ID")
    status: SessionStatus = Field(..., description="Current session status")
    parsed_intent: Optional[ParsedIntent] = Field(None, description="Latest parsed travel intent")
    trip_context: Optional[TripContext] = Field(None, description="Current trip context")
    chat_history: List[ChatMessage] = Field(default_factory=list, description="Complete chat history")
    search_results: Optional[SearchResults] = Field(None, description="Latest search results")
    saved_items: Optional[List[Dict[str, Any]]] = Field(None, description="Items saved to trip")
    suggestions: Optional[List[str]] = Field(None, description="AI-generated suggestions")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_activity_at: datetime = Field(..., description="Last activity timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionUpdate(BaseModel):
    """Request to update session properties."""
    status: Optional[SessionStatus] = Field(None, description="New session status")
    trip_context: Optional[TripContext] = Field(None, description="Updated trip context")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class LocationUpdate(BaseModel):
    """Request to update location information."""
    departure_city: Optional[str] = Field(None, description="New departure city")
    destination_city: Optional[str] = Field(None, description="New destination city")
    additional_destinations: Optional[List[str]] = Field(None, description="Additional destinations")


class DateUpdate(BaseModel):
    """Request to update travel dates."""
    departure_date: Optional[date] = Field(None, description="New departure date")
    return_date: Optional[date] = Field(None, description="New return date")
    flexible_dates: bool = Field(default=False, description="Whether dates are flexible")

    @validator('departure_date', 'return_date')
    def validate_future_dates(cls, v):
        if v and v < date.today():
            raise ValueError('Dates must be in the future')
        return v