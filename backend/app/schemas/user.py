"""
User schemas for request/response validation
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, EmailStr

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None

# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Additional properties to return via API
class User(UserInDBBase):
    pass

# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str


# Extended Profile Schemas
class ExtendedProfileBase(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    country_of_residence: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    preferred_language: Optional[str] = None
    preferred_currency: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None


class ExtendedProfileUpdate(ExtendedProfileBase):
    pass


class ExtendedProfileResponse(ExtendedProfileBase):
    class Config:
        from_attributes = True


# Travel Preferences Schemas
class TravelPreferencesBase(BaseModel):
    preferred_cabin_class: Optional[str] = None
    preferred_airlines: Optional[List[str]] = None
    avoided_airlines: Optional[List[str]] = None
    preferred_seat_type: Optional[str] = None
    preferred_hotel_class: Optional[int] = None
    preferred_hotel_chains: Optional[List[str]] = None
    activity_interests: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    mobility_requirements: Optional[List[str]] = None
    default_budget_range: Optional[Dict[str, Any]] = None
    budget_currency: Optional[str] = None


class TravelPreferencesUpdate(TravelPreferencesBase):
    pass


class TravelPreferencesResponse(TravelPreferencesBase):
    class Config:
        from_attributes = True


# User Profile Update Schema (combines all updates)
class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    profile: Optional[ExtendedProfileUpdate] = None
    preferences: Optional[TravelPreferencesUpdate] = None


# User Profile Response Schema
class UserProfileResponse(BaseModel):
    id: int
    email: str
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    profile_picture_url: Optional[str] = None
    created_at: Optional[str] = None
    profile: Optional[ExtendedProfileResponse] = None
    preferences: Optional[TravelPreferencesResponse] = None
    
    class Config:
        from_attributes = True