# Pydantic schemas for request/response validation

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """Message types for conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class TravelChatRequest(BaseModel):
    """Request schema for travel chat endpoint."""
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class TravelChatResponse(BaseModel):
    """Response schema for travel chat endpoint."""
    response: str
    intent: Optional[str] = None
    entities: Dict[str, Any] = {}
    context: Dict[str, Any] = {}
    actions_executed: List[str] = []
    action_results: Dict[str, Any] = {}
    clarifying_questions: List[str] = []
    context_validation: Dict[str, Any] = {}
    session_id: str


class SessionCreateRequest(BaseModel):
    """Request schema for creating a travel session."""
    user_id: Optional[str] = None
    context: Dict[str, Any] = {}


class SessionCreateResponse(BaseModel):
    """Response schema for session creation."""
    session_id: str
    status: str
    timestamp: str


class SessionStateResponse(BaseModel):
    """Response schema for session state."""
    session_id: str
    state: Dict[str, Any]
    timestamp: str


class FlightSearchParams(BaseModel):
    """Flight search parameters."""
    origin: Optional[str] = None
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    adults: int = Field(default=1, ge=1, le=9)
    children: int = Field(default=0, ge=0, le=9)
    infants: int = Field(default=0, ge=0, le=9)
    travel_class: str = Field(default="ECONOMY")


class HotelSearchParams(BaseModel):
    """Hotel search parameters."""
    city_code: str
    check_in_date: str
    check_out_date: str
    adults: int = Field(default=1, ge=1, le=9)
    rooms: int = Field(default=1, ge=1, le=9)


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    timestamp: str


class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str
    version: str
    timestamp: str


__all__ = [
    "MessageType",
    "TravelChatRequest",
    "TravelChatResponse", 
    "SessionCreateRequest",
    "SessionCreateResponse",
    "SessionStateResponse",
    "FlightSearchParams",
    "HotelSearchParams",
    "ErrorResponse",
    "HealthCheckResponse"
]