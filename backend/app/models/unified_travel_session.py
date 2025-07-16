"""
Unified Travel Session Model

Core session model implementing the unified architecture with JSONB storage.
This is the central model that stores all travel-related data in flexible JSONB columns.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, text, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Use shared base - will be overridden by __init__.py import
Base = declarative_base()


class SessionStatus(str, Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    PLANNING = "planning"
    SEARCHING = "searching"
    BOOKING = "booking"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    ARCHIVED = "archived"


class UnifiedTravelSession(Base):
    """
    Single source of truth for entire travel session.
    
    Uses JSONB storage for maximum flexibility while maintaining
    proper relationships and performance through strategic indexing.
    """
    __tablename__ = "unified_travel_sessions"

    # Primary identifiers
    session_id = Column(String(36), primary_key=True, server_default=text("gen_random_uuid()::text"))
    user_id = Column(Integer, nullable=True, index=True)  # Removed ForeignKey for now
    status = Column(String(20), default=SessionStatus.ACTIVE.value, nullable=False, index=True)
    
    # Flexible JSONB storage for all session data
    session_data = Column(JSONB, nullable=True, comment="Chat messages, search results, UI state")
    plan_data = Column(JSONB, nullable=True, comment="Trip plans, itineraries, saved items")
    session_metadata = Column(JSONB, nullable=True, comment="Analytics, debugging info, system metadata")
    
    # Timestamps with timezone support
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    # user = relationship("User")  # Removed to avoid circular dependency
    saved_items = relationship("UnifiedSavedItem", back_populates="session", cascade="all, delete-orphan")
    bookings = relationship("UnifiedSessionBooking", back_populates="session", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        # Multi-column indexes for common queries
        Index('idx_user_sessions_created', 'user_id', 'created_at'),
        Index('idx_session_status_activity', 'status', 'last_activity_at'),
        
        # JSONB indexes for common queries
        Index('idx_session_destination', session_data, postgresql_using='gin', 
              postgresql_ops={'session_data': 'jsonb_path_ops'}),
        Index('idx_plan_destination', plan_data, postgresql_using='gin',
              postgresql_ops={'plan_data': 'jsonb_path_ops'}),
        
        # Specific JSONB field indexes
        Index('idx_session_intent_destination', 
              text("(session_data->'parsed_intent'->>'destination')"), postgresql_using='btree'),
        Index('idx_plan_departure_date', 
              text("(plan_data->>'departure_date')"), postgresql_using='btree'),
        Index('idx_plan_return_date', 
              text("(plan_data->>'return_date')"), postgresql_using='btree'),
    )

    def __repr__(self):
        return f"<UnifiedTravelSession(session_id='{self.session_id}', user_id={self.user_id}, status='{self.status}')>"


class UnifiedSavedItem(Base):
    """
    Items saved to travel sessions (flights, hotels, activities, etc.)
    
    Flexible model that can store any type of travel-related item
    with proper categorization and metadata.
    """
    __tablename__ = "unified_saved_items"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(36), ForeignKey("unified_travel_sessions.session_id"), nullable=False, index=True)
    item_type = Column(String(50), nullable=False, index=True)  # flight, hotel, activity, restaurant, etc.
    provider = Column(String(100), nullable=True)  # amadeus, booking.com, etc.
    external_id = Column(String(255), nullable=True)  # Provider's item ID
    
    # JSONB storage for all item data
    item_data = Column(JSONB, nullable=False, comment="Complete item information")
    booking_data = Column(JSONB, nullable=True, comment="Booking-specific data if applicable")
    user_notes = Column(String(1000), nullable=True)
    
    # Trip organization
    assigned_day = Column(Integer, nullable=True)  # Which day of trip this belongs to
    sort_order = Column(Integer, nullable=True)  # Order within the day
    is_booked = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    session = relationship("UnifiedTravelSession", back_populates="saved_items")

    __table_args__ = (
        Index('idx_saved_items_session_type', 'session_id', 'item_type'),
        Index('idx_saved_items_day_order', 'session_id', 'assigned_day', 'sort_order'),
        Index('idx_saved_items_provider', 'provider', 'external_id'),
        Index('idx_saved_items_data', item_data, postgresql_using='gin',
              postgresql_ops={'item_data': 'jsonb_path_ops'}),
    )

    def __repr__(self):
        return f"<UnifiedSavedItem(id={self.id}, session_id='{self.session_id}', type='{self.item_type}')>"


class UnifiedSessionBooking(Base):
    """
    Booking records with external provider tracking.
    
    Links travel sessions to actual bookings made through various providers.
    Maintains audit trail and supports both direct and third-party bookings.
    """
    __tablename__ = "unified_session_bookings"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(36), ForeignKey("unified_travel_sessions.session_id"), nullable=False, index=True)
    booking_type = Column(String(50), nullable=False)  # flight, hotel, activity, package
    provider = Column(String(100), nullable=False)  # amadeus, booking.com, viator, etc.
    
    # External booking identifiers
    provider_booking_id = Column(String(255), nullable=False)
    confirmation_code = Column(String(100), nullable=True)
    
    # Booking status tracking
    booking_status = Column(String(50), default="pending", nullable=False)  # pending, confirmed, cancelled, completed
    
    # Financial information
    total_amount = Column(Integer, nullable=True)  # Amount in cents
    currency = Column(String(3), nullable=True)  # ISO currency code
    payment_status = Column(String(50), nullable=True)  # pending, paid, refunded, failed
    
    # JSONB storage for detailed booking data
    booking_data = Column(JSONB, nullable=False, comment="Complete booking information from provider")
    traveler_data = Column(JSONB, nullable=True, comment="Traveler information used for booking")
    payment_data = Column(JSONB, nullable=True, comment="Payment method and transaction details")
    
    # Timestamps
    booking_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    travel_date = Column(DateTime(timezone=True), nullable=True)  # When the travel actually occurs
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    session = relationship("UnifiedTravelSession", back_populates="bookings")

    __table_args__ = (
        Index('idx_bookings_session_type', 'session_id', 'booking_type'),
        Index('idx_bookings_provider', 'provider', 'provider_booking_id'),
        Index('idx_bookings_status', 'booking_status', 'booking_date'),
        Index('idx_bookings_travel_date', 'travel_date'),
        Index('idx_bookings_data', booking_data, postgresql_using='gin',
              postgresql_ops={'booking_data': 'jsonb_path_ops'}),
    )

    def __repr__(self):
        return f"<UnifiedSessionBooking(id={self.id}, session_id='{self.session_id}', type='{self.booking_type}', provider='{self.provider}')>"