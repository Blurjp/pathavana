"""
User Models

Comprehensive user authentication, profile, and preference models.
Supports OAuth integration, travel preferences, and document management.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Index, text, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class UserStatus(str, Enum):
    """User account status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    DELETED = "deleted"


class AuthProvider(str, Enum):
    """Authentication provider enumeration"""
    LOCAL = "local"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    MICROSOFT = "microsoft"
    APPLE = "apple"


class DocumentType(str, Enum):
    """Travel document type enumeration"""
    PASSPORT = "passport"
    VISA = "visa"
    DRIVERS_LICENSE = "drivers_license"
    NATIONAL_ID = "national_id"
    TRAVEL_CARD = "travel_card"
    VACCINATION_CARD = "vaccination_card"


class User(Base):
    """
    Core user model for authentication and basic profile information.
    
    Supports both local authentication and OAuth providers.
    Maintains minimal required information with extended profile in separate table.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth-only users
    auth_provider = Column(String(50), default=AuthProvider.LOCAL.value, nullable=False)
    provider_user_id = Column(String(255), nullable=True)  # OAuth provider user ID
    
    # Basic profile information
    full_name = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    
    # Account status and verification
    status = Column(String(50), default=UserStatus.ACTIVE.value, nullable=False, index=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    phone_verified = Column(Boolean, default=False, nullable=False)
    
    # Security and access control
    is_admin = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # GDPR and compliance
    consent_data = Column(JSONB, nullable=True, comment="User consent tracking and preferences")
    data_retention_until = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships - simplified to avoid circular dependencies
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    travel_preferences = relationship("TravelPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    documents = relationship("UserDocument", back_populates="user", cascade="all, delete-orphan")
    # travel_sessions = relationship("UnifiedTravelSession", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_user_auth_provider', 'auth_provider', 'provider_user_id'),
        Index('idx_user_status_created', 'status', 'created_at'),
        Index('idx_user_email_verified', 'email_verified', 'status'),
        Index('idx_user_consent', consent_data, postgresql_using='gin',
              postgresql_ops={'consent_data': 'jsonb_path_ops'}),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.full_name}')>"


class UserProfile(Base):
    """
    Extended user profile information.
    
    Stores detailed personal information, preferences, and travel-related data
    that extends beyond basic authentication requirements.
    """
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Personal information
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    gender = Column(String(20), nullable=True)
    nationality = Column(String(100), nullable=True)
    country_of_residence = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True, default="UTC")
    
    # Contact preferences
    preferred_language = Column(String(10), default="en", nullable=False)
    preferred_currency = Column(String(3), default="USD", nullable=False)  # ISO currency code
    communication_preferences = Column(JSONB, nullable=True, comment="Email, SMS, push notification preferences")
    
    # Travel profile information
    frequent_flyer_numbers = Column(JSONB, nullable=True, comment="Airline loyalty program numbers")
    hotel_loyalty_numbers = Column(JSONB, nullable=True, comment="Hotel loyalty program numbers")
    travel_frequency = Column(String(50), nullable=True)  # rarely, occasionally, frequently, very_frequently
    travel_purpose = Column(String(50), nullable=True)  # leisure, business, mixed
    
    # Emergency contact information
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(100), nullable=True)
    
    # Additional profile data stored as JSONB for flexibility
    profile_data = Column(JSONB, nullable=True, comment="Additional profile information and preferences")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="profile")

    __table_args__ = (
        Index('idx_profile_nationality', 'nationality'),
        Index('idx_profile_language_currency', 'preferred_language', 'preferred_currency'),
        Index('idx_profile_data', profile_data, postgresql_using='gin',
              postgresql_ops={'profile_data': 'jsonb_path_ops'}),
    )

    def __repr__(self):
        return f"<UserProfile(id={self.id}, user_id={self.user_id})>"


class TravelPreferences(Base):
    """
    User travel preferences and defaults.
    
    Stores user's travel-related preferences to personalize search results
    and provide better recommendations.
    """
    __tablename__ = "travel_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Flight preferences
    preferred_cabin_class = Column(String(20), nullable=True)  # economy, premium_economy, business, first
    preferred_airlines = Column(JSONB, nullable=True, comment="List of preferred airline codes")
    avoided_airlines = Column(JSONB, nullable=True, comment="List of airlines to avoid")
    preferred_airports = Column(JSONB, nullable=True, comment="Preferred departure/arrival airports")
    max_flight_duration = Column(Integer, nullable=True)  # Maximum flight duration in minutes
    max_layovers = Column(Integer, default=1, nullable=False)
    preferred_seat_type = Column(String(20), nullable=True)  # aisle, window, any
    
    # Hotel preferences
    preferred_hotel_class = Column(Integer, nullable=True)  # 1-5 star rating
    preferred_hotel_chains = Column(JSONB, nullable=True, comment="List of preferred hotel chains")
    room_preferences = Column(JSONB, nullable=True, comment="Room type, amenities, etc.")
    
    # Activity and dining preferences
    activity_interests = Column(JSONB, nullable=True, comment="List of activity categories of interest")
    dietary_restrictions = Column(JSONB, nullable=True, comment="Dietary restrictions and preferences")
    mobility_requirements = Column(JSONB, nullable=True, comment="Accessibility requirements")
    
    # Budget preferences
    default_budget_range = Column(JSONB, nullable=True, comment="Default budget ranges by trip type")
    budget_currency = Column(String(3), default="USD", nullable=False)
    
    # Notification preferences
    price_alert_enabled = Column(Boolean, default=True, nullable=False)
    deal_notifications_enabled = Column(Boolean, default=True, nullable=False)
    booking_reminders_enabled = Column(Boolean, default=True, nullable=False)
    
    # Advanced preferences stored as JSONB
    advanced_preferences = Column(JSONB, nullable=True, comment="Additional travel preferences")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="travel_preferences")

    __table_args__ = (
        Index('idx_preferences_cabin_class', 'preferred_cabin_class'),
        Index('idx_preferences_hotel_class', 'preferred_hotel_class'),
        Index('idx_preferences_advanced', advanced_preferences, postgresql_using='gin',
              postgresql_ops={'advanced_preferences': 'jsonb_path_ops'}),
    )

    def __repr__(self):
        return f"<TravelPreferences(id={self.id}, user_id={self.user_id})>"


class UserDocument(Base):
    """
    User travel documents (passport, visa, etc.)
    
    Stores travel document information for booking purposes.
    Includes document verification status and expiration tracking.
    """
    __tablename__ = "user_documents"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Document identification
    document_type = Column(String(50), nullable=False)
    document_number = Column(String(100), nullable=False)
    issuing_country = Column(String(100), nullable=False)
    issuing_authority = Column(String(255), nullable=True)
    
    # Document details
    full_name_on_document = Column(String(255), nullable=False)
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    nationality = Column(String(100), nullable=True)
    gender = Column(String(20), nullable=True)
    
    # Validity information
    issue_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    
    # Document status and flags
    is_primary = Column(Boolean, default=False, nullable=False)  # Primary document for bookings
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Additional document data stored as JSONB
    document_data = Column(JSONB, nullable=True, comment="Additional document details and metadata")
    
    # Security and audit
    created_by_user = Column(Boolean, default=True, nullable=False)  # vs. imported/auto-created
    last_used_for_booking = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="documents")

    __table_args__ = (
        Index('idx_document_type_user', 'document_type', 'user_id'),
        Index('idx_document_expiry', 'expiry_date', 'is_active'),
        Index('idx_document_number', 'document_number', 'issuing_country'),
        Index('idx_document_primary', 'user_id', 'is_primary', 'is_active'),
        Index('idx_document_data', document_data, postgresql_using='gin',
              postgresql_ops={'document_data': 'jsonb_path_ops'}),
    )

    def __repr__(self):
        return f"<UserDocument(id={self.id}, user_id={self.user_id}, type='{self.document_type}', number='{self.document_number}')>"