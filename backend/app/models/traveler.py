"""
Traveler Models

Individual traveler profiles for group bookings and travel document management.
Supports multiple travelers per booking with detailed personal information.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Index, text, Table
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class TravelerType(str, Enum):
    """Traveler type enumeration"""
    ADULT = "adult"
    CHILD = "child"
    INFANT = "infant"
    SENIOR = "senior"


class TravelerStatus(str, Enum):
    """Traveler status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class TravelerDocumentStatus(str, Enum):
    """Travel document verification status"""
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    REJECTED = "rejected"
    NOT_REQUIRED = "not_required"


class Traveler(Base):
    """
    Individual traveler profiles for group bookings.
    
    Stores personal information for each person traveling, separate from the main
    user account. Allows for family/group travel with different travelers having
    different documents and preferences.
    """
    __tablename__ = "travelers"

    id = Column(Integer, primary_key=True)
    
    # Owner and organization
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    traveler_group_id = Column(String(36), nullable=True, index=True)  # UUID for grouping related travelers
    
    # Personal identification
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=False)  # Computed or manually set full name
    
    # Personal details
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    gender = Column(String(20), nullable=True)
    nationality = Column(String(100), nullable=True)
    country_of_residence = Column(String(100), nullable=True)
    
    # Traveler classification
    traveler_type = Column(String(20), default=TravelerType.ADULT.value, nullable=False, index=True)
    status = Column(String(20), default=TravelerStatus.ACTIVE.value, nullable=False, index=True)
    
    # Contact information (for adult travelers)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    
    # Travel preferences specific to this traveler
    dietary_restrictions = Column(JSONB, nullable=True, comment="Dietary restrictions and meal preferences")
    accessibility_needs = Column(JSONB, nullable=True, comment="Mobility and accessibility requirements")
    medical_conditions = Column(JSONB, nullable=True, comment="Relevant medical conditions for travel")
    
    # Frequent traveler information
    frequent_flyer_numbers = Column(JSONB, nullable=True, comment="Airline loyalty program numbers")
    hotel_loyalty_numbers = Column(JSONB, nullable=True, comment="Hotel loyalty program numbers")
    known_traveler_numbers = Column(JSONB, nullable=True, comment="TSA PreCheck, Global Entry, etc.")
    
    # Relationship to account holder
    relationship_to_user = Column(String(100), nullable=True)  # self, spouse, child, parent, friend, etc.
    is_primary = Column(Boolean, default=False, nullable=False)  # Is this the primary traveler for the user?
    
    # Travel document status tracking
    document_status = Column(String(50), default=TravelerDocumentStatus.PENDING.value, nullable=False)
    passport_verified = Column(Boolean, default=False, nullable=False)
    visa_required = Column(Boolean, nullable=True)  # null = unknown, true/false = determined
    visa_status = Column(String(50), nullable=True)
    
    # Additional traveler data stored as JSONB for flexibility
    traveler_data = Column(JSONB, nullable=True, comment="Additional traveler information and preferences")
    
    # Booking history and preferences (computed from bookings)
    total_trips = Column(Integer, default=0, nullable=False)
    last_trip_date = Column(DateTime(timezone=True), nullable=True)
    preferred_cabin_class = Column(String(20), nullable=True)
    preferred_seat_type = Column(String(20), nullable=True)
    
    # Privacy and consent (especially important for minors)
    consent_given = Column(Boolean, default=False, nullable=False)
    consent_date = Column(DateTime(timezone=True), nullable=True)
    consent_given_by = Column(String(255), nullable=True)  # Who gave consent (for minors)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    documents = relationship("TravelerDocument", back_populates="traveler", cascade="all, delete-orphan")
    bookings = relationship("UnifiedBooking", secondary="booking_travelers", back_populates="travelers")

    __table_args__ = (
        Index('idx_traveler_user_type', 'user_id', 'traveler_type'),
        Index('idx_traveler_group', 'traveler_group_id'),
        Index('idx_traveler_name', 'first_name', 'last_name'),
        Index('idx_traveler_birth', 'date_of_birth'),
        Index('idx_traveler_status', 'status', 'is_primary'),
        Index('idx_traveler_data', traveler_data, postgresql_using='gin',
              postgresql_ops={'traveler_data': 'jsonb_path_ops'}),
    )

    def __repr__(self):
        return f"<Traveler(id={self.id}, name='{self.full_name}', type='{self.traveler_type}')>"


class TravelerDocument(Base):
    """
    Travel documents associated with individual travelers.
    
    Similar to UserDocument but specific to individual travelers in a group.
    Allows for different family members to have different passports, visas, etc.
    """
    __tablename__ = "traveler_documents"

    id = Column(Integer, primary_key=True)
    traveler_id = Column(Integer, ForeignKey("travelers.id"), nullable=False, index=True)
    
    # Document identification
    document_type = Column(String(50), nullable=False, index=True)  # passport, visa, id_card, etc.
    document_number = Column(String(100), nullable=False)
    issuing_country = Column(String(100), nullable=False)
    issuing_authority = Column(String(255), nullable=True)
    
    # Document holder information (should match traveler info)
    full_name_on_document = Column(String(255), nullable=False)
    date_of_birth_on_document = Column(DateTime(timezone=True), nullable=True)
    nationality_on_document = Column(String(100), nullable=True)
    gender_on_document = Column(String(20), nullable=True)
    place_of_birth = Column(String(255), nullable=True)
    
    # Document validity
    issue_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True, index=True)
    is_valid = Column(Boolean, default=True, nullable=False)
    
    # Verification status
    verification_status = Column(String(50), default=TravelerDocumentStatus.PENDING.value, nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(255), nullable=True)  # System or agent who verified
    
    # Document usage tracking
    is_primary = Column(Boolean, default=False, nullable=False)  # Primary document for this traveler
    last_used_for_booking = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Visa-specific information (if applicable)
    visa_type = Column(String(100), nullable=True)
    visa_entries_allowed = Column(String(50), nullable=True)  # single, multiple, etc.
    visa_purpose = Column(String(100), nullable=True)  # tourism, business, transit, etc.
    
    # Document image and data storage
    document_images = Column(JSONB, nullable=True, comment="Document scan/photo metadata")
    document_data = Column(JSONB, nullable=True, comment="Additional document details and metadata")
    
    # Security and audit
    created_by_user = Column(Boolean, default=True, nullable=False)
    automated_verification = Column(Boolean, default=False, nullable=False)
    verification_confidence = Column(Integer, nullable=True)  # 0-100 confidence score
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    traveler = relationship("Traveler", back_populates="documents")

    __table_args__ = (
        Index('idx_traveler_doc_type', 'traveler_id', 'document_type'),
        Index('idx_traveler_doc_number', 'document_number', 'issuing_country'),
        Index('idx_traveler_doc_expiry', 'expiry_date', 'is_valid'),
        Index('idx_traveler_doc_verification', 'verification_status', 'verified_at'),
        Index('idx_traveler_doc_primary', 'traveler_id', 'is_primary', 'is_valid'),
        Index('idx_document_data', document_data, postgresql_using='gin',
              postgresql_ops={'document_data': 'jsonb_path_ops'}),
    )

    def __repr__(self):
        return f"<TravelerDocument(id={self.id}, traveler_id={self.traveler_id}, type='{self.document_type}', number='{self.document_number}')>"


class TravelerPreference(Base):
    """
    Individual traveler preferences and special requirements.
    
    Stores traveler-specific preferences that may differ from the account holder's
    preferences. Useful for families with different dietary needs, seat preferences, etc.
    """
    __tablename__ = "traveler_preferences"

    id = Column(Integer, primary_key=True)
    traveler_id = Column(Integer, ForeignKey("travelers.id"), unique=True, nullable=False)
    
    # Flight preferences
    preferred_cabin_class = Column(String(20), nullable=True)
    preferred_seat_type = Column(String(20), nullable=True)  # aisle, window, any
    preferred_seat_location = Column(String(20), nullable=True)  # front, middle, back
    extra_legroom_preferred = Column(Boolean, default=False, nullable=False)
    
    # Meal and dietary preferences
    meal_preference = Column(String(50), nullable=True)  # vegetarian, kosher, halal, etc.
    dietary_restrictions = Column(JSONB, nullable=True, comment="Detailed dietary restrictions")
    food_allergies = Column(JSONB, nullable=True, comment="Food allergies and severity")
    
    # Accessibility and special needs
    wheelchair_assistance = Column(Boolean, default=False, nullable=False)
    visual_assistance = Column(Boolean, default=False, nullable=False)
    hearing_assistance = Column(Boolean, default=False, nullable=False)
    special_assistance_notes = Column(String(1000), nullable=True)
    
    # Hotel preferences
    room_preferences = Column(JSONB, nullable=True, comment="Room type, floor, view preferences")
    bed_preferences = Column(String(50), nullable=True)  # single, double, twin, etc.
    
    # Activity preferences
    activity_interests = Column(JSONB, nullable=True, comment="Types of activities of interest")
    activity_restrictions = Column(JSONB, nullable=True, comment="Physical or other activity limitations")
    
    # Communication preferences
    preferred_language = Column(String(10), default="en", nullable=False)
    notification_preferences = Column(JSONB, nullable=True, comment="How to contact this traveler")
    
    # Emergency and medical information
    emergency_medical_info = Column(JSONB, nullable=True, comment="Critical medical information for emergencies")
    medication_requirements = Column(JSONB, nullable=True, comment="Regular medications and requirements")
    travel_insurance_info = Column(JSONB, nullable=True, comment="Travel insurance details")
    
    # Additional preferences stored as JSONB
    additional_preferences = Column(JSONB, nullable=True, comment="Other traveler-specific preferences")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    traveler = relationship("Traveler", uselist=False)

    __table_args__ = (
        Index('idx_traveler_pref_cabin', 'preferred_cabin_class'),
        Index('idx_traveler_pref_meal', 'meal_preference'),
        Index('idx_traveler_pref_accessibility', 'wheelchair_assistance', 'visual_assistance', 'hearing_assistance'),
        Index('idx_additional_preferences', additional_preferences, postgresql_using='gin',
              postgresql_ops={'additional_preferences': 'jsonb_path_ops'}),
    )

    def __repr__(self):
        return f"<TravelerPreference(id={self.id}, traveler_id={self.traveler_id})>"