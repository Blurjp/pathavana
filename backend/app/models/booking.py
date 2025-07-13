"""
Booking Models

Comprehensive booking management models for flights, hotels, activities, and packages.
Supports multiple providers, payment tracking, and traveler relationships.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Index, text, Numeric, Table
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Use shared base - will be overridden by __init__.py import
Base = declarative_base()


class BookingStatus(str, Enum):
    """Booking status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    EXPIRED = "expired"
    REFUNDED = "refunded"
    FAILED = "failed"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class BookingType(str, Enum):
    """Booking type enumeration"""
    FLIGHT = "flight"
    HOTEL = "hotel"
    ACTIVITY = "activity"
    RESTAURANT = "restaurant"
    PACKAGE = "package"
    TRANSPORTATION = "transportation"
    INSURANCE = "insurance"


# Association table for many-to-many relationship between bookings and travelers
booking_travelers = Table(
    'booking_travelers',
    Base.metadata,
    Column('booking_id', Integer, ForeignKey('bookings.id'), primary_key=True),
    Column('traveler_id', Integer, ForeignKey('travelers.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    Index('idx_booking_travelers_booking', 'booking_id'),
    Index('idx_booking_travelers_traveler', 'traveler_id')
)


class UnifiedBooking(Base):
    """
    Main booking model that provides structured data and relationships.
    
    This provides additional structured data and relationships while maintaining
    compatibility with the unified JSONB approach.
    """
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True)
    
    # Link to unified travel session
    session_id = Column(String(36), ForeignKey("unified_travel_sessions.session_id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Booking identification
    booking_reference = Column(String(100), unique=True, nullable=False, index=True)
    booking_type = Column(String(50), nullable=False, index=True)
    provider = Column(String(100), nullable=False)
    provider_booking_id = Column(String(255), nullable=False)
    confirmation_code = Column(String(100), nullable=True)
    
    # Booking status and workflow
    status = Column(String(50), default=BookingStatus.PENDING.value, nullable=False, index=True)
    payment_status = Column(String(50), default=PaymentStatus.PENDING.value, nullable=False, index=True)
    
    # Financial information
    total_amount = Column(Numeric(10, 2), nullable=False)  # Total booking amount
    paid_amount = Column(Numeric(10, 2), default=0.00, nullable=False)  # Amount actually paid
    currency = Column(String(3), nullable=False, default="USD")  # ISO currency code
    base_amount = Column(Numeric(10, 2), nullable=True)  # Amount before taxes and fees
    taxes_amount = Column(Numeric(10, 2), nullable=True)  # Tax amount
    fees_amount = Column(Numeric(10, 2), nullable=True)  # Service fees
    
    # Travel dates and timing
    travel_start_date = Column(DateTime(timezone=True), nullable=True, index=True)
    travel_end_date = Column(DateTime(timezone=True), nullable=True, index=True)
    booking_deadline = Column(DateTime(timezone=True), nullable=True)  # When booking must be completed
    cancellation_deadline = Column(DateTime(timezone=True), nullable=True)  # Last chance to cancel
    
    # JSONB storage for detailed booking data
    booking_details = Column(JSONB, nullable=False, comment="Complete booking information from provider")
    provider_response = Column(JSONB, nullable=True, comment="Raw response from booking provider")
    payment_details = Column(JSONB, nullable=True, comment="Payment method and transaction details")
    cancellation_policy = Column(JSONB, nullable=True, comment="Cancellation terms and conditions")
    
    # Booking metadata
    booking_source = Column(String(100), nullable=True)  # web, mobile_app, api
    agent_booking = Column(Boolean, default=False, nullable=False)  # Booked by travel agent
    group_booking = Column(Boolean, default=False, nullable=False)  # Group/corporate booking
    
    # Audit and tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    booked_at = Column(DateTime(timezone=True), nullable=True)  # When booking was confirmed
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")
    session = relationship("UnifiedTravelSession")
    travelers = relationship("Traveler", secondary=booking_travelers, back_populates="bookings")
    flight_booking = relationship("FlightBooking", back_populates="booking", uselist=False, cascade="all, delete-orphan")
    hotel_booking = relationship("HotelBooking", back_populates="booking", uselist=False, cascade="all, delete-orphan")
    activity_booking = relationship("ActivityBooking", back_populates="booking", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_booking_user_type', 'user_id', 'booking_type'),
        Index('idx_booking_provider_ref', 'provider', 'provider_booking_id'),
        Index('idx_booking_status_date', 'status', 'travel_start_date'),
        Index('idx_booking_travel_dates', 'travel_start_date', 'travel_end_date'),
        Index('idx_booking_details', booking_details, postgresql_using='gin',
              postgresql_ops={'booking_details': 'jsonb_path_ops'}),
    )

    def __repr__(self):
        return f"<UnifiedBooking(id={self.id}, reference='{self.booking_reference}', type='{self.booking_type}')>"


class FlightBooking(Base):
    """
    Flight-specific booking details.
    
    Stores structured flight information including segments, passenger details,
    and airline-specific data.
    """
    __tablename__ = "flight_bookings"

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), unique=True, nullable=False)
    
    # Flight identification
    airline_code = Column(String(3), nullable=False)  # IATA airline code
    flight_number = Column(String(10), nullable=False)
    pnr = Column(String(10), nullable=True)  # Passenger Name Record
    
    # Route information
    origin_airport = Column(String(3), nullable=False)  # IATA airport code
    destination_airport = Column(String(3), nullable=False)
    departure_datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    arrival_datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Flight details
    cabin_class = Column(String(20), nullable=False)  # economy, premium_economy, business, first
    aircraft_type = Column(String(50), nullable=True)
    total_duration_minutes = Column(Integer, nullable=True)
    is_round_trip = Column(Boolean, default=False, nullable=False)
    is_multi_city = Column(Boolean, default=False, nullable=False)
    
    # Passenger and baggage information
    passenger_count = Column(Integer, nullable=False, default=1)
    infant_count = Column(Integer, nullable=False, default=0)
    baggage_allowance = Column(JSONB, nullable=True, comment="Baggage allowance details")
    seat_assignments = Column(JSONB, nullable=True, comment="Seat assignments for passengers")
    
    # Flight segments for multi-leg flights
    flight_segments = Column(JSONB, nullable=False, comment="Detailed segment information")
    
    # Airline-specific data
    frequent_flyer_used = Column(JSONB, nullable=True, comment="Frequent flyer numbers used")
    special_requests = Column(JSONB, nullable=True, comment="Special meal, assistance requests")
    
    # Check-in and boarding
    online_checkin_available = Column(Boolean, default=True, nullable=False)
    boarding_pass_data = Column(JSONB, nullable=True, comment="Digital boarding pass information")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    booking = relationship("UnifiedBooking", back_populates="flight_booking")

    __table_args__ = (
        Index('idx_flight_airline_number', 'airline_code', 'flight_number'),
        Index('idx_flight_route', 'origin_airport', 'destination_airport'),
        Index('idx_flight_departure', 'departure_datetime'),
        Index('idx_flight_pnr', 'pnr'),
        Index('idx_flight_segments', flight_segments, postgresql_using='gin',
              postgresql_ops={'flight_segments': 'jsonb_path_ops'}),
    )

    def __repr__(self):
        return f"<FlightBooking(id={self.id}, flight='{self.airline_code}{self.flight_number}', route='{self.origin_airport}-{self.destination_airport}')>"


class HotelBooking(Base):
    """
    Hotel-specific booking details.
    
    Stores structured hotel information including room details, guest information,
    and hotel-specific amenities and policies.
    """
    __tablename__ = "hotel_bookings"

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), unique=True, nullable=False)
    
    # Hotel identification
    hotel_id = Column(String(100), nullable=False)  # Provider's hotel ID
    hotel_name = Column(String(255), nullable=False)
    hotel_chain = Column(String(100), nullable=True)
    hotel_rating = Column(Integer, nullable=True)  # Star rating 1-5
    
    # Location information
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    
    # Stay details
    checkin_date = Column(DateTime(timezone=True), nullable=False, index=True)
    checkout_date = Column(DateTime(timezone=True), nullable=False, index=True)
    nights_count = Column(Integer, nullable=False)
    
    # Room information
    room_type = Column(String(100), nullable=False)
    room_count = Column(Integer, nullable=False, default=1)
    guest_count = Column(Integer, nullable=False, default=1)
    adult_count = Column(Integer, nullable=False, default=1)
    child_count = Column(Integer, nullable=False, default=0)
    
    # Room details and amenities
    room_details = Column(JSONB, nullable=True, comment="Room description, amenities, bed types")
    hotel_amenities = Column(JSONB, nullable=True, comment="Hotel facilities and services")
    
    # Booking terms
    is_refundable = Column(Boolean, default=True, nullable=False)
    free_cancellation_until = Column(DateTime(timezone=True), nullable=True)
    meal_plan = Column(String(50), nullable=True)  # room_only, breakfast, half_board, full_board, all_inclusive
    
    # Hotel loyalty and preferences
    loyalty_program_used = Column(String(100), nullable=True)
    special_requests = Column(String(1000), nullable=True)
    early_checkin_requested = Column(Boolean, default=False, nullable=False)
    late_checkout_requested = Column(Boolean, default=False, nullable=False)
    
    # Pricing breakdown
    room_rate_per_night = Column(Numeric(10, 2), nullable=True)
    taxes_per_night = Column(Numeric(10, 2), nullable=True)
    resort_fees = Column(Numeric(10, 2), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    booking = relationship("UnifiedBooking", back_populates="hotel_booking")

    __table_args__ = (
        Index('idx_hotel_booking_hotel', 'hotel_id', 'checkin_date'),
        Index('idx_hotel_booking_location', 'city', 'country'),
        Index('idx_hotel_booking_dates', 'checkin_date', 'checkout_date'),
        Index('idx_hotel_details', room_details, postgresql_using='gin',
              postgresql_ops={'room_details': 'jsonb_path_ops'}),
    )

    def __repr__(self):
        return f"<HotelBooking(id={self.id}, hotel='{self.hotel_name}', checkin='{self.checkin_date.date()}')>"


class ActivityBooking(Base):
    """
    Activity and experience booking details.
    
    Stores information about tours, attractions, experiences, and other activities.
    """
    __tablename__ = "activity_bookings"

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), unique=True, nullable=False)
    
    # Activity identification
    activity_id = Column(String(100), nullable=False)  # Provider's activity ID
    activity_name = Column(String(255), nullable=False)
    activity_type = Column(String(100), nullable=False)  # tour, attraction, experience, etc.
    provider_name = Column(String(100), nullable=True)  # Tour operator name
    
    # Location information
    location_name = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    
    # Activity details
    duration_hours = Column(Numeric(4, 2), nullable=True)  # Duration in hours
    activity_date = Column(DateTime(timezone=True), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Participant information
    participant_count = Column(Integer, nullable=False, default=1)
    adult_count = Column(Integer, nullable=False, default=1)
    child_count = Column(Integer, nullable=False, default=0)
    senior_count = Column(Integer, nullable=False, default=0)
    
    # Activity specifics
    activity_details = Column(JSONB, nullable=True, comment="Activity description, inclusions, exclusions")
    meeting_point = Column(String(500), nullable=True)
    pickup_location = Column(String(500), nullable=True)
    pickup_time = Column(DateTime(timezone=True), nullable=True)
    
    # Requirements and restrictions
    age_restrictions = Column(JSONB, nullable=True, comment="Age requirements and restrictions")
    physical_requirements = Column(String(1000), nullable=True)
    equipment_provided = Column(JSONB, nullable=True, comment="Equipment and materials provided")
    what_to_bring = Column(String(1000), nullable=True)
    
    # Booking terms
    is_refundable = Column(Boolean, default=True, nullable=False)
    cancellation_policy = Column(String(1000), nullable=True)
    weather_dependent = Column(Boolean, default=False, nullable=False)
    
    # Language and guide information
    language_options = Column(JSONB, nullable=True, comment="Available languages for the activity")
    guide_info = Column(JSONB, nullable=True, comment="Guide information and qualifications")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    booking = relationship("UnifiedBooking", back_populates="activity_booking")

    __table_args__ = (
        Index('idx_activity_booking_activity', 'activity_id', 'activity_date'),
        Index('idx_activity_booking_location', 'city', 'country'),
        Index('idx_activity_booking_date', 'activity_date'),
        Index('idx_activity_booking_type', 'activity_type'),
        Index('idx_activity_details', activity_details, postgresql_using='gin',
              postgresql_ops={'activity_details': 'jsonb_path_ops'}),
    )

    def __repr__(self):
        return f"<ActivityBooking(id={self.id}, activity='{self.activity_name}', date='{self.activity_date.date()}')>"