"""
Travelers API endpoints with full SQLAlchemy integration

Provides CRUD operations for traveler profiles with proper authentication
and database integration using SQLAlchemy ORM.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.auth_v2 import get_current_user_safe
from app.models.user import User
from app.models.traveler import Traveler, TravelerDocument, TravelerPreference
from app.schemas.traveler import (
    TravelerCreate,
    TravelerUpdate,
    TravelerResponse,
    TravelerListResponse
)
from app.schemas.base import BaseResponse, ResponseMetadata, ErrorDetail
from app.core.logger import logger

router = APIRouter(prefix="/api/v1/travelers", tags=["travelers"])


@router.get("/", response_model=BaseResponse)
async def get_travelers(
    skip: int = Query(0, ge=0, description="Number of travelers to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of travelers to return"),
    current_user: Optional[User] = Depends(get_current_user_safe),
    db: AsyncSession = Depends(get_db)
) -> BaseResponse:
    """
    Get all travelers for the current user.
    
    Returns a paginated list of traveler profiles associated with the authenticated user.
    """
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user_id = current_user.id
        
        # Query travelers for the user
        result = await db.execute(
            select(Traveler)
            .where(and_(
                Traveler.user_id == user_id,
                Traveler.status == "active"
            ))
            .offset(skip)
            .limit(limit)
            .order_by(Traveler.created_at.desc())
        )
        travelers = result.scalars().all()
        
        # Convert to response format
        travelers_data = []
        for traveler in travelers:
            travelers_data.append({
                "id": str(traveler.id),
                "first_name": traveler.first_name,
                "last_name": traveler.last_name,
                "full_name": traveler.full_name,
                "date_of_birth": traveler.date_of_birth.isoformat() if traveler.date_of_birth else None,
                "gender": traveler.gender,
                "nationality": traveler.nationality,
                "email": traveler.email,
                "phone": traveler.phone,
                "relationship_to_user": traveler.relationship_to_user,
                "dietary_restrictions": traveler.dietary_restrictions or [],
                "emergency_contact_name": traveler.emergency_contact_name,
                "emergency_contact_phone": traveler.emergency_contact_phone,
                "passport_verified": traveler.passport_verified,
                "created_at": traveler.created_at.isoformat() if traveler.created_at else None
            })
        
        return BaseResponse(
            success=True,
            data=travelers_data,
            metadata=ResponseMetadata(
                timestamp=datetime.utcnow().isoformat(),
                version="2.0",
                total_count=len(travelers_data)
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching travelers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch travelers"
        )


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_traveler(
    traveler_data: TravelerCreate,
    current_user: Optional[User] = Depends(get_current_user_safe),
    db: AsyncSession = Depends(get_db)
) -> BaseResponse:
    """
    Create a new traveler profile.
    
    Creates a new traveler associated with the authenticated user.
    """
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user_id = current_user.id
        
        # Create full name
        full_name = f"{traveler_data.first_name} {traveler_data.last_name}".strip()
        if traveler_data.middle_name:
            full_name = f"{traveler_data.first_name} {traveler_data.middle_name} {traveler_data.last_name}".strip()
        
        # Create new traveler
        new_traveler = Traveler(
            user_id=user_id,
            first_name=traveler_data.first_name,
            last_name=traveler_data.last_name,
            middle_name=traveler_data.middle_name,
            full_name=full_name,
            date_of_birth=traveler_data.date_of_birth,
            gender=traveler_data.gender,
            nationality=traveler_data.nationality,
            country_of_residence=traveler_data.country_of_residence,
            email=traveler_data.email,
            phone=traveler_data.phone,
            emergency_contact_name=traveler_data.emergency_contact_name,
            emergency_contact_phone=traveler_data.emergency_contact_phone,
            relationship_to_user=traveler_data.relationship_to_user,
            dietary_restrictions=traveler_data.dietary_restrictions,
            accessibility_needs=traveler_data.accessibility_needs,
            medical_conditions=traveler_data.medical_conditions,
            frequent_flyer_numbers=traveler_data.frequent_flyer_numbers,
            hotel_loyalty_numbers=traveler_data.hotel_loyalty_numbers,
            known_traveler_numbers=traveler_data.known_traveler_numbers,
            traveler_type="adult" if not traveler_data.date_of_birth else _determine_traveler_type(traveler_data.date_of_birth),
            status="active"
        )
        
        db.add(new_traveler)
        await db.commit()
        await db.refresh(new_traveler)
        
        # Return created traveler
        traveler_response = {
            "id": str(new_traveler.id),
            "first_name": new_traveler.first_name,
            "last_name": new_traveler.last_name,
            "full_name": new_traveler.full_name,
            "date_of_birth": new_traveler.date_of_birth.isoformat() if new_traveler.date_of_birth else None,
            "gender": new_traveler.gender,
            "nationality": new_traveler.nationality,
            "email": new_traveler.email,
            "phone": new_traveler.phone,
            "relationship_to_user": new_traveler.relationship_to_user,
            "dietary_restrictions": new_traveler.dietary_restrictions or [],
            "emergency_contact_name": new_traveler.emergency_contact_name,
            "emergency_contact_phone": new_traveler.emergency_contact_phone,
            "passport_verified": new_traveler.passport_verified,
            "created_at": new_traveler.created_at.isoformat() if new_traveler.created_at else None
        }
        
        return BaseResponse(
            success=True,
            data=traveler_response,
            metadata=ResponseMetadata(
                timestamp=datetime.utcnow().isoformat(),
                version="2.0",
                message="Traveler created successfully"
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating traveler: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create traveler"
        )


@router.get("/{traveler_id}", response_model=BaseResponse)
async def get_traveler(
    traveler_id: str,
    current_user: Optional[User] = Depends(get_current_user_safe),
    db: AsyncSession = Depends(get_db)
) -> BaseResponse:
    """
    Get a specific traveler by ID.
    
    Returns detailed information about a single traveler profile.
    """
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user_id = current_user.id
        
        # Query traveler with documents
        result = await db.execute(
            select(Traveler)
            .options(selectinload(Traveler.documents))
            .where(and_(
                Traveler.id == int(traveler_id),
                Traveler.user_id == user_id,
                Traveler.status == "active"
            ))
        )
        traveler = result.scalar_one_or_none()
        
        if not traveler:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traveler not found"
            )
        
        # Build detailed response
        traveler_data = {
            "id": str(traveler.id),
            "first_name": traveler.first_name,
            "last_name": traveler.last_name,
            "middle_name": traveler.middle_name,
            "full_name": traveler.full_name,
            "date_of_birth": traveler.date_of_birth.isoformat() if traveler.date_of_birth else None,
            "gender": traveler.gender,
            "nationality": traveler.nationality,
            "country_of_residence": traveler.country_of_residence,
            "email": traveler.email,
            "phone": traveler.phone,
            "emergency_contact_name": traveler.emergency_contact_name,
            "emergency_contact_phone": traveler.emergency_contact_phone,
            "relationship_to_user": traveler.relationship_to_user,
            "dietary_restrictions": traveler.dietary_restrictions or [],
            "accessibility_needs": traveler.accessibility_needs or [],
            "medical_conditions": traveler.medical_conditions or [],
            "frequent_flyer_numbers": traveler.frequent_flyer_numbers or {},
            "hotel_loyalty_numbers": traveler.hotel_loyalty_numbers or {},
            "known_traveler_numbers": traveler.known_traveler_numbers or {},
            "passport_verified": traveler.passport_verified,
            "document_status": traveler.document_status,
            "documents": [],
            "created_at": traveler.created_at.isoformat() if traveler.created_at else None,
            "updated_at": traveler.updated_at.isoformat() if traveler.updated_at else None
        }
        
        # Add document information
        for doc in traveler.documents:
            if doc.is_valid:
                traveler_data["documents"].append({
                    "id": str(doc.id),
                    "document_type": doc.document_type,
                    "document_number": doc.document_number[:4] + "****" if doc.document_number else None,  # Partially hide
                    "issuing_country": doc.issuing_country,
                    "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
                    "is_primary": doc.is_primary,
                    "verification_status": doc.verification_status
                })
        
        return BaseResponse(
            success=True,
            data=traveler_data,
            metadata=ResponseMetadata(
                timestamp=datetime.utcnow().isoformat(),
                version="2.0"
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching traveler: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch traveler"
        )


@router.put("/{traveler_id}", response_model=BaseResponse)
async def update_traveler(
    traveler_id: str,
    traveler_update: TravelerUpdate,
    current_user: Optional[User] = Depends(get_current_user_safe),
    db: AsyncSession = Depends(get_db)
) -> BaseResponse:
    """
    Update a traveler profile.
    
    Updates the specified traveler's information. Only the owner can update.
    """
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user_id = current_user.id
        
        # Get existing traveler
        result = await db.execute(
            select(Traveler)
            .where(and_(
                Traveler.id == int(traveler_id),
                Traveler.user_id == user_id,
                Traveler.status == "active"
            ))
        )
        traveler = result.scalar_one_or_none()
        
        if not traveler:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traveler not found"
            )
        
        # Update fields
        update_data = traveler_update.dict(exclude_unset=True)
        
        # Update full name if names changed
        if "first_name" in update_data or "last_name" in update_data or "middle_name" in update_data:
            first = update_data.get("first_name", traveler.first_name)
            middle = update_data.get("middle_name", traveler.middle_name)
            last = update_data.get("last_name", traveler.last_name)
            
            if middle:
                traveler.full_name = f"{first} {middle} {last}".strip()
            else:
                traveler.full_name = f"{first} {last}".strip()
        
        # Update other fields
        for field, value in update_data.items():
            if hasattr(traveler, field):
                setattr(traveler, field, value)
        
        # Update traveler type if date of birth changed
        if "date_of_birth" in update_data and update_data["date_of_birth"]:
            traveler.traveler_type = _determine_traveler_type(update_data["date_of_birth"])
        
        await db.commit()
        await db.refresh(traveler)
        
        # Return updated traveler
        traveler_response = {
            "id": str(traveler.id),
            "first_name": traveler.first_name,
            "last_name": traveler.last_name,
            "full_name": traveler.full_name,
            "date_of_birth": traveler.date_of_birth.isoformat() if traveler.date_of_birth else None,
            "gender": traveler.gender,
            "nationality": traveler.nationality,
            "email": traveler.email,
            "phone": traveler.phone,
            "relationship_to_user": traveler.relationship_to_user,
            "dietary_restrictions": traveler.dietary_restrictions or [],
            "emergency_contact_name": traveler.emergency_contact_name,
            "emergency_contact_phone": traveler.emergency_contact_phone,
            "passport_verified": traveler.passport_verified,
            "updated_at": traveler.updated_at.isoformat() if traveler.updated_at else None
        }
        
        return BaseResponse(
            success=True,
            data=traveler_response,
            metadata=ResponseMetadata(
                timestamp=datetime.utcnow().isoformat(),
                version="2.0",
                message="Traveler updated successfully"
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating traveler: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update traveler"
        )


@router.delete("/{traveler_id}", response_model=BaseResponse)
async def delete_traveler(
    traveler_id: str,
    current_user: Optional[User] = Depends(get_current_user_safe),
    db: AsyncSession = Depends(get_db)
) -> BaseResponse:
    """
    Delete a traveler profile.
    
    Soft deletes the traveler by setting status to 'archived'.
    The traveler data is retained for historical bookings.
    """
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user_id = current_user.id
        
        # Get existing traveler
        result = await db.execute(
            select(Traveler)
            .where(and_(
                Traveler.id == int(traveler_id),
                Traveler.user_id == user_id,
                Traveler.status == "active"
            ))
        )
        traveler = result.scalar_one_or_none()
        
        if not traveler:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traveler not found"
            )
        
        # Soft delete by setting status to archived
        traveler.status = "archived"
        await db.commit()
        
        return BaseResponse(
            success=True,
            data={"id": traveler_id, "status": "archived"},
            metadata=ResponseMetadata(
                timestamp=datetime.utcnow().isoformat(),
                version="2.0",
                message="Traveler deleted successfully"
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting traveler: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete traveler"
        )


def _determine_traveler_type(date_of_birth: date) -> str:
    """Determine traveler type based on age."""
    today = date.today()
    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    
    if age < 2:
        return "infant"
    elif age < 12:
        return "child"
    elif age >= 65:
        return "senior"
    else:
        return "adult"