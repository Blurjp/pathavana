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

    @validator('document_number')
    def validate_document_number(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Document number must be at least 3 characters')
        return v.strip().upper()

    @validator('expiry_date')
    def validate_expiry_date(cls, v):
        if v and v <= date.today():
            raise ValueError('Document expiry date must be in the future')
        return v


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


class TravelerCreate(BaseModel):
    """Request to create a new traveler profile."""
    title: Optional[Title] = Field(None, description="Title")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    middle_name: Optional[str] = Field(None, description="Middle name")
    date_of_birth: date = Field(..., description="Date of birth")
    gender: Optional[Gender] = Field(None, description="Gender")
    nationality: str = Field(..., description="Nationality")
    
    # Contact information
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[Dict[str, str]] = Field(None, description="Address information")
    
    # Travel documents
    documents: Optional[List[TravelerDocument]] = Field(None, description="Travel documents")
    
    # Preferences
    preferences: Optional[TravelerPreferences] = Field(None, description="Travel preferences")
    
    # Metadata
    is_primary: bool = Field(default=False, description="Whether this is the primary traveler")
    notes: Optional[str] = Field(None, description="Additional notes")

    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Name cannot be empty')
        if len(v.strip()) > 50:
            raise ValueError('Name must be less than 50 characters')
        return v.strip()

    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        if v >= date.today():
            raise ValueError('Date of birth must be in the past')
        if date.today().year - v.year > 120:
            raise ValueError('Age cannot exceed 120 years')
        return v

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v


class TravelerUpdate(BaseModel):
    """Request to update an existing traveler profile."""
    title: Optional[Title] = Field(None, description="Title")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    middle_name: Optional[str] = Field(None, description="Middle name")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[Gender] = Field(None, description="Gender")
    nationality: Optional[str] = Field(None, description="Nationality")
    
    # Contact information
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[Dict[str, str]] = Field(None, description="Address information")
    
    # Travel documents
    documents: Optional[List[TravelerDocument]] = Field(None, description="Travel documents")
    
    # Preferences
    preferences: Optional[TravelerPreferences] = Field(None, description="Travel preferences")
    
    # Metadata
    notes: Optional[str] = Field(None, description="Additional notes")

    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v is not None and (not v or len(v.strip()) < 1):
            raise ValueError('Name cannot be empty')
        if v and len(v.strip()) > 50:
            raise ValueError('Name must be less than 50 characters')
        return v.strip() if v else v

    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        if v and v >= date.today():
            raise ValueError('Date of birth must be in the past')
        if v and date.today().year - v.year > 120:
            raise ValueError('Age cannot exceed 120 years')
        return v

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v


class TravelerResponse(BaseModel):
    """Traveler profile response."""
    traveler_id: str = Field(..., description="Unique traveler identifier")
    user_id: int = Field(..., description="Associated user ID")
    
    # Personal information
    title: Optional[Title] = Field(None, description="Title")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    middle_name: Optional[str] = Field(None, description="Middle name")
    full_name: str = Field(..., description="Complete formatted name")
    date_of_birth: date = Field(..., description="Date of birth")
    age: int = Field(..., description="Current age")
    gender: Optional[Gender] = Field(None, description="Gender")
    nationality: str = Field(..., description="Nationality")
    
    # Contact information
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[Dict[str, str]] = Field(None, description="Address information")
    
    # Travel documents
    documents: List[TravelerDocument] = Field(default_factory=list, description="Travel documents")
    primary_document: Optional[TravelerDocument] = Field(None, description="Primary travel document")
    
    # Preferences
    preferences: Optional[TravelerPreferences] = Field(None, description="Travel preferences")
    
    # Metadata
    is_primary: bool = Field(..., description="Whether this is the primary traveler")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Usage statistics
    total_bookings: int = Field(default=0, description="Total number of bookings")
    last_trip_date: Optional[date] = Field(None, description="Date of last trip")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class TravelerSearchParams(PaginationParams):
    """Parameters for searching travelers."""
    search_query: Optional[str] = Field(None, description="Search in traveler names")
    nationality: Optional[str] = Field(None, description="Filter by nationality")
    has_passport: Optional[bool] = Field(None, description="Filter by passport availability")
    age_min: Optional[int] = Field(None, description="Minimum age")
    age_max: Optional[int] = Field(None, description="Maximum age")
    is_primary: Optional[bool] = Field(None, description="Filter by primary traveler status")


class TravelerSummary(BaseModel):
    """Summary information for a traveler."""
    traveler_id: str = Field(..., description="Traveler identifier")
    full_name: str = Field(..., description="Complete name")
    age: int = Field(..., description="Current age")
    nationality: str = Field(..., description="Nationality")
    has_passport: bool = Field(..., description="Whether traveler has passport")
    is_primary: bool = Field(..., description="Whether this is primary traveler")
    total_bookings: int = Field(..., description="Total bookings count")


class DocumentUpload(BaseModel):
    """Request to upload a document."""
    document_type: DocumentType = Field(..., description="Type of document")
    file_data: str = Field(..., description="Base64 encoded file data")
    filename: str = Field(..., description="Original filename")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('file_data')
    def validate_file_data(cls, v):
        if not v:
            raise ValueError('File data cannot be empty')
        return v

    @validator('filename')
    def validate_filename(cls, v):
        if not v:
            raise ValueError('Filename cannot be empty')
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError('File must be PDF, JPG, JPEG, or PNG')
        return v