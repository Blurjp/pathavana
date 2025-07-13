"""
Booking-related Pydantic schemas.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import PriceInfo, PaginationParams


class BookingStatus(str, Enum):
    """Booking status options."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


class BookingType(str, Enum):
    """Booking type options."""
    FLIGHT = "flight"
    HOTEL = "hotel"
    ACTIVITY = "activity"
    PACKAGE = "package"
    TRANSPORT = "transport"


class PaymentStatus(str, Enum):
    """Payment status options."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(BaseModel):
    """Payment method information."""
    type: str = Field(..., description="Payment method type (credit_card, debit_card, paypal, etc.)")
    last_four: Optional[str] = Field(None, description="Last four digits of card")
    brand: Optional[str] = Field(None, description="Card brand (Visa, Mastercard, etc.)")
    expiry_month: Optional[int] = Field(None, description="Card expiry month")
    expiry_year: Optional[int] = Field(None, description="Card expiry year")
    
    @validator('last_four')
    def validate_last_four(cls, v):
        if v and (len(v) != 4 or not v.isdigit()):
            raise ValueError('Last four must be exactly 4 digits')
        return v


class BookingTraveler(BaseModel):
    """Traveler information for booking."""
    id: Optional[str] = Field(None, description="Traveler profile ID")
    title: Optional[str] = Field(None, description="Title (Mr, Ms, Dr, etc.)")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    middle_name: Optional[str] = Field(None, description="Middle name")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender")
    nationality: Optional[str] = Field(None, description="Nationality")
    passport_number: Optional[str] = Field(None, description="Passport number")
    passport_expiry: Optional[datetime] = Field(None, description="Passport expiry date")
    passport_country: Optional[str] = Field(None, description="Passport issuing country")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    special_requests: Optional[List[str]] = Field(None, description="Special requests or needs")

    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Name cannot be empty')
        return v.strip()

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v


class BookingCreate(BaseModel):
    """Request to create a new booking."""
    session_id: str = Field(..., description="Associated travel session ID")
    booking_type: BookingType = Field(..., description="Type of booking")
    provider: str = Field(..., description="Booking provider (amadeus, booking_com, etc.)")
    booking_data: Dict[str, Any] = Field(..., description="Provider-specific booking data")
    travelers: List[BookingTraveler] = Field(..., description="List of travelers")
    payment_method: PaymentMethod = Field(..., description="Payment method information")
    contact_info: Dict[str, str] = Field(..., description="Primary contact information")
    special_requests: Optional[List[str]] = Field(None, description="Special requests")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional booking metadata")

    @validator('travelers')
    def validate_travelers(cls, v):
        if not v:
            raise ValueError('At least one traveler is required')
        return v

    @validator('booking_data')
    def validate_booking_data(cls, v):
        if not v:
            raise ValueError('Booking data cannot be empty')
        return v


class BookingUpdate(BaseModel):
    """Request to update an existing booking."""
    status: Optional[BookingStatus] = Field(None, description="New booking status")
    travelers: Optional[List[BookingTraveler]] = Field(None, description="Updated traveler information")
    special_requests: Optional[List[str]] = Field(None, description="Updated special requests")
    contact_info: Optional[Dict[str, str]] = Field(None, description="Updated contact information")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")


class BookingResponse(BaseModel):
    """Booking details response."""
    booking_id: str = Field(..., description="Unique booking identifier")
    session_id: str = Field(..., description="Associated travel session ID")
    user_id: int = Field(..., description="User who made the booking")
    booking_type: BookingType = Field(..., description="Type of booking")
    status: BookingStatus = Field(..., description="Current booking status")
    provider: str = Field(..., description="Booking provider")
    provider_booking_id: Optional[str] = Field(None, description="Provider's booking reference")
    
    # Booking details
    booking_data: Dict[str, Any] = Field(..., description="Complete booking information")
    travelers: List[BookingTraveler] = Field(..., description="Traveler information")
    
    # Financial information
    total_price: PriceInfo = Field(..., description="Total booking price")
    payment_status: PaymentStatus = Field(..., description="Payment status")
    payment_method: PaymentMethod = Field(..., description="Payment method used")
    
    # Contact and requests
    contact_info: Dict[str, str] = Field(..., description="Contact information")
    special_requests: Optional[List[str]] = Field(None, description="Special requests")
    
    # Timestamps
    created_at: datetime = Field(..., description="Booking creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    confirmed_at: Optional[datetime] = Field(None, description="Confirmation timestamp")
    
    # Additional information
    confirmation_number: Optional[str] = Field(None, description="Booking confirmation number")
    cancellation_policy: Optional[Dict[str, Any]] = Field(None, description="Cancellation policy details")
    supplier_info: Optional[Dict[str, Any]] = Field(None, description="Supplier information")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BookingSearchParams(PaginationParams):
    """Parameters for searching bookings."""
    status: Optional[BookingStatus] = Field(None, description="Filter by booking status")
    booking_type: Optional[BookingType] = Field(None, description="Filter by booking type")
    provider: Optional[str] = Field(None, description="Filter by provider")
    date_from: Optional[datetime] = Field(None, description="Filter bookings from this date")
    date_to: Optional[datetime] = Field(None, description="Filter bookings to this date")
    search_query: Optional[str] = Field(None, description="Search in booking details")


class BookingCancellation(BaseModel):
    """Request to cancel a booking."""
    reason: str = Field(..., description="Reason for cancellation")
    refund_requested: bool = Field(default=True, description="Whether refund is requested")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional cancellation metadata")

    @validator('reason')
    def validate_reason(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError('Cancellation reason must be at least 5 characters')
        return v.strip()


class BookingSummary(BaseModel):
    """Summary information for a booking."""
    booking_id: str = Field(..., description="Booking identifier")
    booking_type: BookingType = Field(..., description="Type of booking")
    status: BookingStatus = Field(..., description="Booking status")
    total_price: PriceInfo = Field(..., description="Total price")
    created_at: datetime = Field(..., description="Creation date")
    confirmation_number: Optional[str] = Field(None, description="Confirmation number")
    provider: str = Field(..., description="Booking provider")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }