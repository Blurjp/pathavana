"""
Traveler profile-related Pydantic schemas.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import PaginationParams


class DocumentType(str, Enum):
    """Travel document types."""
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    DRIVERS_LICENSE = "drivers_license"
    VISA = "visa"
    VACCINATION_CARD = "vaccination_card"
    OTHER = "other"


class Gender(str, Enum):
    """Gender options."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class Title(str, Enum):
    """Title options."""
    MR = "Mr"
    MRS = "Mrs"
    MS = "Ms"
    DR = "Dr"
    PROF = "Prof"
    OTHER = "Other"


class TravelerDocument(BaseModel):
    """Travel document information."""
    document_type: DocumentType = Field(..., description="Type of document")
    document_number: str = Field(..., description="Document number")
    issuing_country: str = Field(..., description="Country that issued the document")
    issue_date: Optional[date] = Field(None, description="Document issue date")
    expiry_date: Optional[date] = Field(None, description="Document expiry date")
    issuing_authority: Optional[str] = Field(None, description="Issuing authority")
    is_primary: bool = Field(default=False, description="Whether this is the primary document")
    notes: Optional[str] = Field(None, description="Additional notes about the document")


class TravelerBase(BaseModel):
    """Base traveler information."""
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    middle_name: Optional[str] = Field(None, max_length=100, description="Middle name")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender")
    nationality: Optional[str] = Field(None, description="Nationality")
    country_of_residence: Optional[str] = Field(None, description="Country of residence")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    emergency_contact_name: Optional[str] = Field(None, description="Emergency contact name")
    emergency_contact_phone: Optional[str] = Field(None, description="Emergency contact phone")
    relationship_to_user: Optional[str] = Field(None, description="Relationship to account holder")
    dietary_restrictions: Optional[List[str]] = Field(None, description="Dietary restrictions")
    accessibility_needs: Optional[List[str]] = Field(None, description="Accessibility requirements")
    medical_conditions: Optional[List[str]] = Field(None, description="Medical conditions")
    frequent_flyer_numbers: Optional[Dict[str, str]] = Field(None, description="Airline loyalty programs")
    hotel_loyalty_numbers: Optional[Dict[str, str]] = Field(None, description="Hotel loyalty programs")
    known_traveler_numbers: Optional[Dict[str, str]] = Field(None, description="TSA PreCheck, Global Entry, etc.")


class TravelerCreate(TravelerBase):
    """Schema for creating a new traveler."""
    pass


class TravelerUpdate(BaseModel):
    """Schema for updating a traveler."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    country_of_residence: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    relationship_to_user: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = None
    accessibility_needs: Optional[List[str]] = None
    medical_conditions: Optional[List[str]] = None
    frequent_flyer_numbers: Optional[Dict[str, str]] = None
    hotel_loyalty_numbers: Optional[Dict[str, str]] = None
    known_traveler_numbers: Optional[Dict[str, str]] = None


class TravelerResponse(TravelerBase):
    """Schema for traveler response."""
    id: str
    full_name: str
    passport_verified: bool = False
    document_status: Optional[str] = None
    documents: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class TravelerListResponse(BaseModel):
    """Schema for list of travelers response."""
    travelers: List[TravelerResponse]
    total_count: int
    skip: int
    limit: int


class TravelerPreferences(BaseModel):
    """Traveler preferences and special needs."""
    dietary_restrictions: Optional[List[str]] = Field(None, description="Dietary restrictions")
    accessibility_needs: Optional[List[str]] = Field(None, description="Accessibility requirements")
    seating_preference: Optional[str] = Field(None, description="Preferred seating")
    meal_preference: Optional[str] = Field(None, description="Meal preferences")
    special_assistance: Optional[List[str]] = Field(None, description="Special assistance needs")
    loyalty_programs: Optional[Dict[str, str]] = Field(None, description="Airline/hotel loyalty numbers")
    emergency_contact: Optional[Dict[str, str]] = Field(None, description="Emergency contact information")
    medical_conditions: Optional[List[str]] = Field(None, description="Relevant medical conditions")
    medication_list: Optional[List[str]] = Field(None, description="Required medications")


