"""
User Profile API endpoints - DEBUG VERSION
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.auth_v2 import get_current_user_safe
from app.models.user import User, UserProfile, TravelPreferences
from app.schemas.user import (
    UserProfileResponse,
    UserProfileUpdate,
    TravelPreferencesResponse,
    TravelPreferencesUpdate
)
from app.schemas.base import BaseResponse, ResponseMetadata
from app.core.logger import logger

router = APIRouter(prefix="/api/v1/debug", tags=["debug-profile"])


@router.put("/profile", response_model=BaseResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: Optional[User] = Depends(get_current_user_safe),
    db: AsyncSession = Depends(get_db)
) -> BaseResponse:
    """
    DEBUG: Update profile without try/except to see errors
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Get user with related data
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.profile)
            # Skip travel_preferences due to schema mismatch
        )
        .where(User.id == current_user.id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update basic user information
    if profile_update.first_name is not None:
        user.first_name = profile_update.first_name
    if profile_update.last_name is not None:
        user.last_name = profile_update.last_name
    if profile_update.phone is not None:
        user.phone = profile_update.phone
    
    # Update full name if first or last name changed
    if profile_update.first_name is not None or profile_update.last_name is not None:
        first = profile_update.first_name or user.first_name or ""
        last = profile_update.last_name or user.last_name or ""
        user.full_name = f"{first} {last}".strip()
    
    # Update or create extended profile
    if profile_update.profile:
        if not user.profile:
            # Create new profile
            user.profile = UserProfile(
                user_id=current_user.id,
                date_of_birth=profile_update.profile.date_of_birth,
                gender=profile_update.profile.gender,
                nationality=profile_update.profile.nationality,
                country_of_residence=profile_update.profile.country_of_residence,
                city=profile_update.profile.city,
                timezone=profile_update.profile.timezone or "UTC",
                preferred_language=profile_update.profile.preferred_language or "en",
                preferred_currency=profile_update.profile.preferred_currency or "USD",
                emergency_contact_name=profile_update.profile.emergency_contact_name,
                emergency_contact_phone=profile_update.profile.emergency_contact_phone,
                emergency_contact_relationship=profile_update.profile.emergency_contact_relationship
            )
            db.add(user.profile)
        else:
            # Update existing profile
            for field, value in profile_update.profile.dict(exclude_unset=True).items():
                setattr(user.profile, field, value)
    
    # Skip travel preferences update due to schema mismatch
    # TODO: Fix schema mismatch between model and database
    
    # Commit changes
    await db.commit()
    await db.refresh(user)
    
    # Build response with updated data
    profile_data = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "phone": user.phone or "",
        "profile_picture_url": user.profile_picture_url,
        "updated_at": datetime.utcnow().isoformat(),
        "profile": None,
        "preferences": None
    }
    
    # Add updated profile data
    if user.profile:
        profile_data["profile"] = {
            "date_of_birth": user.profile.date_of_birth.isoformat() if user.profile.date_of_birth else None,
            "gender": user.profile.gender,
            "nationality": user.profile.nationality,
            "country_of_residence": user.profile.country_of_residence,
            "city": user.profile.city,
            "timezone": user.profile.timezone,
            "preferred_language": user.profile.preferred_language,
            "preferred_currency": user.profile.preferred_currency,
            "emergency_contact_name": user.profile.emergency_contact_name,
            "emergency_contact_phone": user.profile.emergency_contact_phone,
            "emergency_contact_relationship": user.profile.emergency_contact_relationship
        }
    
    # Skip travel preferences due to schema mismatch
    profile_data["preferences"] = None
    
    return BaseResponse(
        success=True,
        data=profile_data,
        metadata=ResponseMetadata(
            timestamp=datetime.utcnow().isoformat(),
            version="2.0",
            message="Profile updated successfully"
        )
    )