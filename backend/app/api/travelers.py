"""
Traveler profile management API endpoints for Pathavana.

This module handles traveler profile operations including:
- Creating and managing traveler profiles
- Document management (passport, visa, etc.)
- Travel preferences and special needs
- Emergency contact information
- Profile validation and verification

All endpoints follow REST principles and include proper validation.
"""

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, UploadFile, File
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.base import BaseResponse, ResponseMetadata, ErrorDetail, PaginationInfo
from ..schemas.traveler import (
    TravelerCreate,
    TravelerResponse,
    TravelerUpdate,
    TravelerSearchParams,
    TravelerSummary,
    TravelerDocument,
    DocumentUpload,
    DocumentType,
    TravelerPreferences
)

# Note: These imports would need to be implemented
# from ..core.database import get_db
# from ..core.security import get_current_user
# from ..models.user import User
# from ..services.traveler_service import TravelerService
# from ..services.document_service import DocumentService

router = APIRouter(prefix="/api/travelers", tags=["travelers"])
security = HTTPBearer()


# Dependency stubs - these would be implemented in the actual application
async def get_db() -> AsyncSession:
    """Get database session."""
    pass


async def get_current_user(token: str = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user."""
    return {"id": 1, "email": "user@example.com"}


async def get_traveler_service() -> Any:
    """Get traveler service instance."""
    pass


async def get_document_service() -> Any:
    """Get document service instance."""
    pass


def validate_traveler_id(traveler_id: str) -> str:
    """Validate and return traveler ID."""
    try:
        uuid.UUID(traveler_id)
        return traveler_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid traveler ID format"
        )


def create_error_response(error_code: str, message: str, field: Optional[str] = None) -> BaseResponse:
    """Create standardized error response."""
    return BaseResponse(
        success=False,
        errors=[ErrorDetail(code=error_code, message=message, field=field)],
        metadata=ResponseMetadata()
    )


def create_success_response(data: Dict[str, Any]) -> BaseResponse:
    """Create standardized success response."""
    return BaseResponse(
        success=True,
        data=data,
        metadata=ResponseMetadata()
    )


@router.get("", response_model=BaseResponse)
async def list_travelers(
    params: TravelerSearchParams = Depends(),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    traveler_service: Any = Depends(get_traveler_service)
) -> BaseResponse:
    """
    List user's traveler profiles with filtering and pagination.
    
    This endpoint supports filtering by:
    - Search query (name matching)
    - Nationality
    - Passport availability
    - Age range
    - Primary traveler status
    
    Args:
        params: Search and pagination parameters
        db: Database session
        user: Authenticated user
        traveler_service: Traveler service instance
    
    Returns:
        BaseResponse with:
        - travelers: List of traveler summaries
        - pagination: Pagination information
        - filters_applied: Active filters
        - total_count: Total number of travelers
    
    Raises:
        HTTPException: If search parameters are invalid
    """
    try:
        # Execute search with filters
        search_result = await traveler_service.search_travelers(
            user_id=user["id"],
            filters={
                "search_query": params.search_query,
                "nationality": params.nationality,
                "has_passport": params.has_passport,
                "age_min": params.age_min,
                "age_max": params.age_max,
                "is_primary": params.is_primary
            },
            pagination={
                "page": params.page,
                "limit": params.limit,
                "offset": params.offset
            }
        )
        
        # Calculate pagination info
        total = search_result["total"]
        total_pages = (total + params.limit - 1) // params.limit
        
        pagination_info = PaginationInfo(
            page=params.page,
            limit=params.limit,
            total=total,
            pages=total_pages,
            has_next=params.page < total_pages,
            has_prev=params.page > 1
        )
        
        return create_success_response(
            data={
                "travelers": search_result["travelers"],
                "pagination": pagination_info.dict(),
                "filters_applied": {
                    key: value for key, value in {
                        "search_query": params.search_query,
                        "nationality": params.nationality,
                        "has_passport": params.has_passport,
                        "age_min": params.age_min,
                        "age_max": params.age_max,
                        "is_primary": params.is_primary
                    }.items() if value is not None
                },
                "total_count": total,
                "primary_traveler": search_result.get("primary_traveler")
            }
        )
        
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        return create_error_response("SEARCH_ERROR", "Failed to search travelers")


@router.post("", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_traveler(
    request: TravelerCreate,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    traveler_service: Any = Depends(get_traveler_service)
) -> BaseResponse:
    """
    Create a new traveler profile.
    
    This endpoint:
    1. Validates traveler information
    2. Checks for duplicate profiles
    3. Validates travel documents
    4. Creates the traveler profile
    5. Sets up default preferences
    
    Args:
        request: Complete traveler information
        db: Database session
        user: Authenticated user
        traveler_service: Traveler service instance
    
    Returns:
        BaseResponse with:
        - traveler_id: Unique traveler identifier
        - full_name: Complete formatted name
        - document_status: Status of document validation
        - next_steps: Suggested next actions
    
    Raises:
        HTTPException: If traveler creation fails
    """
    try:
        # Check for existing primary traveler if this one is marked as primary
        if request.is_primary:
            existing_primary = await traveler_service.get_primary_traveler(user["id"])
            if existing_primary:
                return create_error_response(
                    "PRIMARY_TRAVELER_EXISTS",
                    "A primary traveler already exists. Please update the existing one or set this as non-primary.",
                    "is_primary"
                )
        
        # Validate documents if provided
        document_validation = {"valid": True, "errors": []}
        if request.documents:
            document_validation = await traveler_service.validate_documents(
                request.documents
            )
            if not document_validation["valid"]:
                return create_error_response(
                    "DOCUMENT_VALIDATION_ERROR",
                    f"Document validation failed: {', '.join(document_validation['errors'])}"
                )
        
        # Check for potential duplicates
        duplicate_check = await traveler_service.check_for_duplicates(
            user_id=user["id"],
            first_name=request.first_name,
            last_name=request.last_name,
            date_of_birth=request.date_of_birth
        )
        
        if duplicate_check["found"]:
            return create_error_response(
                "DUPLICATE_TRAVELER",
                f"A similar traveler profile already exists: {duplicate_check['existing_traveler']['full_name']}",
                "personal_info"
            )
        
        # Create traveler profile
        traveler_result = await traveler_service.create_traveler(
            user_id=user["id"],
            traveler_data=request,
            document_validation=document_validation
        )
        
        return create_success_response(
            data={
                "traveler_id": traveler_result["traveler_id"],
                "full_name": traveler_result["full_name"],
                "age": traveler_result["age"],
                "document_status": traveler_result.get("document_status", "pending"),
                "is_primary": traveler_result["is_primary"],
                "next_steps": traveler_result.get("next_steps", []),
                "created_at": traveler_result["created_at"]
            }
        )
        
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        return create_error_response("CREATION_ERROR", "Failed to create traveler profile")


@router.get("/{traveler_id}", response_model=BaseResponse)
async def get_traveler(
    traveler_id: str = Path(..., description="Traveler ID"),
    include_documents: bool = Query(default=True, description="Include document details"),
    include_preferences: bool = Query(default=True, description="Include travel preferences"),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    traveler_service: Any = Depends(get_traveler_service)
) -> BaseResponse:
    """
    Get detailed traveler profile information.
    
    This endpoint returns complete traveler details including:
    - Personal information
    - Travel documents
    - Preferences and special needs
    - Contact information
    - Usage statistics
    
    Args:
        traveler_id: Unique traveler identifier
        include_documents: Whether to include document details
        include_preferences: Whether to include preferences
        db: Database session
        user: Authenticated user
        traveler_service: Traveler service instance
    
    Returns:
        BaseResponse with complete TravelerResponse data
    
    Raises:
        HTTPException: If traveler not found or access denied
    """
    traveler_id = validate_traveler_id(traveler_id)
    
    try:
        traveler_data = await traveler_service.get_traveler(
            traveler_id=traveler_id,
            user_id=user["id"],
            include_documents=include_documents,
            include_preferences=include_preferences
        )
        
        if not traveler_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traveler not found"
            )
        
        # Calculate additional computed fields
        additional_info = await traveler_service.get_traveler_stats(
            traveler_id=traveler_id
        )
        
        traveler_data.update(additional_info)
        
        return create_success_response(
            data=traveler_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response("RETRIEVAL_ERROR", "Failed to retrieve traveler")


@router.put("/{traveler_id}", response_model=BaseResponse)
async def update_traveler(
    traveler_id: str = Path(..., description="Traveler ID"),
    request: TravelerUpdate = ...,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    traveler_service: Any = Depends(get_traveler_service)
) -> BaseResponse:
    """
    Update traveler profile information.
    
    This endpoint allows updates to:
    - Personal information
    - Contact details
    - Travel documents
    - Preferences and special needs
    - Emergency contacts
    
    Args:
        traveler_id: Unique traveler identifier
        request: Updated traveler information
        db: Database session
        user: Authenticated user
        traveler_service: Traveler service instance
    
    Returns:
        BaseResponse with updated traveler data
    
    Raises:
        HTTPException: If traveler not found or update fails
    """
    traveler_id = validate_traveler_id(traveler_id)
    
    try:
        # Get current traveler to validate ownership
        current_traveler = await traveler_service.get_traveler(
            traveler_id=traveler_id,
            user_id=user["id"]
        )
        
        if not current_traveler:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traveler not found"
            )
        
        # Validate document updates if provided
        document_validation = {"valid": True, "errors": []}
        if request.documents:
            document_validation = await traveler_service.validate_documents(
                request.documents
            )
            if not document_validation["valid"]:
                return create_error_response(
                    "DOCUMENT_VALIDATION_ERROR",
                    f"Document validation failed: {', '.join(document_validation['errors'])}"
                )
        
        # Apply updates
        updated_traveler = await traveler_service.update_traveler(
            traveler_id=traveler_id,
            update_data=request.dict(exclude_unset=True),
            document_validation=document_validation
        )
        
        return create_success_response(
            data=updated_traveler
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        return create_error_response("UPDATE_ERROR", "Failed to update traveler")


@router.delete("/{traveler_id}", response_model=BaseResponse)
async def delete_traveler(
    traveler_id: str = Path(..., description="Traveler ID"),
    confirm_deletion: bool = Query(default=False, description="Confirm deletion"),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    traveler_service: Any = Depends(get_traveler_service)
) -> BaseResponse:
    """
    Delete a traveler profile.
    
    This endpoint:
    1. Validates traveler ownership
    2. Checks for active bookings
    3. Performs soft deletion (preserves for compliance)
    4. Updates related records
    
    Args:
        traveler_id: Unique traveler identifier
        confirm_deletion: Explicit confirmation required
        db: Database session
        user: Authenticated user
        traveler_service: Traveler service instance
    
    Returns:
        BaseResponse with deletion confirmation
    
    Raises:
        HTTPException: If traveler cannot be deleted
    """
    traveler_id = validate_traveler_id(traveler_id)
    
    if not confirm_deletion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deletion must be explicitly confirmed"
        )
    
    try:
        # Get traveler and validate ownership
        traveler = await traveler_service.get_traveler(
            traveler_id=traveler_id,
            user_id=user["id"]
        )
        
        if not traveler:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traveler not found"
            )
        
        # Check for active bookings
        booking_check = await traveler_service.check_active_bookings(
            traveler_id=traveler_id
        )
        
        if booking_check["has_active_bookings"]:
            return create_error_response(
                "ACTIVE_BOOKINGS_EXIST",
                f"Cannot delete traveler with {booking_check['active_count']} active bookings"
            )
        
        # Check if this is the primary traveler
        if traveler["is_primary"]:
            other_travelers = await traveler_service.get_other_travelers(
                user_id=user["id"],
                exclude_traveler_id=traveler_id
            )
            
            if other_travelers:
                return create_error_response(
                    "PRIMARY_TRAVELER_DELETION",
                    "Cannot delete primary traveler. Please set another traveler as primary first."
                )
        
        # Perform soft deletion
        deletion_result = await traveler_service.delete_traveler(
            traveler_id=traveler_id,
            user_id=user["id"]
        )
        
        return create_success_response(
            data={
                "deleted": True,
                "traveler_id": traveler_id,
                "full_name": traveler["full_name"],
                "deleted_at": deletion_result["deleted_at"],
                "retention_period": deletion_result.get("retention_period", "5 years"),
                "affected_records": deletion_result.get("affected_records", 0)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response("DELETION_ERROR", "Failed to delete traveler")


@router.post("/{traveler_id}/documents", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    traveler_id: str = Path(..., description="Traveler ID"),
    document_type: DocumentType = Query(..., description="Type of document"),
    file: UploadFile = File(..., description="Document file"),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    traveler_service: Any = Depends(get_traveler_service),
    document_service: Any = Depends(get_document_service)
) -> BaseResponse:
    """
    Upload a travel document for a traveler.
    
    This endpoint:
    1. Validates file type and size
    2. Scans for sensitive information
    3. Stores document securely
    4. Updates traveler profile
    5. Returns document metadata
    
    Args:
        traveler_id: Unique traveler identifier
        document_type: Type of document being uploaded
        file: Document file (PDF, JPG, PNG)
        db: Database session
        user: Authenticated user
        traveler_service: Traveler service instance
        document_service: Document service instance
    
    Returns:
        BaseResponse with:
        - document_id: Unique document identifier
        - document_url: Secure access URL
        - verification_status: Document verification status
        - extracted_data: Any extracted document data
    
    Raises:
        HTTPException: If upload fails or validation errors
    """
    traveler_id = validate_traveler_id(traveler_id)
    
    try:
        # Validate traveler ownership
        traveler = await traveler_service.get_traveler(
            traveler_id=traveler_id,
            user_id=user["id"]
        )
        
        if not traveler:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traveler not found"
            )
        
        # Validate file
        file_validation = await document_service.validate_file(
            file=file,
            allowed_types=["pdf", "jpg", "jpeg", "png"],
            max_size_mb=10
        )
        
        if not file_validation["valid"]:
            return create_error_response(
                "FILE_VALIDATION_ERROR",
                file_validation["error"]
            )
        
        # Process and store document
        upload_result = await document_service.upload_document(
            traveler_id=traveler_id,
            document_type=document_type,
            file=file,
            user_id=user["id"]
        )
        
        # Update traveler profile with document info
        await traveler_service.update_document_status(
            traveler_id=traveler_id,
            document_type=document_type,
            document_id=upload_result["document_id"]
        )
        
        return create_success_response(
            data={
                "document_id": upload_result["document_id"],
                "document_url": upload_result["secure_url"],
                "verification_status": upload_result.get("verification_status", "pending"),
                "extracted_data": upload_result.get("extracted_data", {}),
                "expires_at": upload_result.get("expires_at"),
                "file_size": upload_result["file_size"],
                "upload_timestamp": upload_result["uploaded_at"]
            }
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        return create_error_response("UPLOAD_ERROR", "Failed to upload document")


@router.get("/{traveler_id}/documents", response_model=BaseResponse)
async def list_documents(
    traveler_id: str = Path(..., description="Traveler ID"),
    document_type: Optional[DocumentType] = Query(None, description="Filter by document type"),
    include_expired: bool = Query(default=False, description="Include expired documents"),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    traveler_service: Any = Depends(get_traveler_service)
) -> BaseResponse:
    """
    List documents for a traveler.
    
    Args:
        traveler_id: Unique traveler identifier
        document_type: Optional filter by document type
        include_expired: Whether to include expired documents
        db: Database session
        user: Authenticated user
        traveler_service: Traveler service instance
    
    Returns:
        BaseResponse with list of documents
    """
    traveler_id = validate_traveler_id(traveler_id)
    
    try:
        documents = await traveler_service.list_documents(
            traveler_id=traveler_id,
            user_id=user["id"],
            document_type=document_type,
            include_expired=include_expired
        )
        
        return create_success_response(
            data={
                "documents": documents,
                "total_count": len(documents),
                "expired_count": len([d for d in documents if d.get("is_expired", False)]),
                "verification_pending": len([d for d in documents if d.get("verification_status") == "pending"])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response("RETRIEVAL_ERROR", "Failed to retrieve documents")


@router.put("/{traveler_id}/primary", response_model=BaseResponse)
async def set_primary_traveler(
    traveler_id: str = Path(..., description="Traveler ID"),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    traveler_service: Any = Depends(get_traveler_service)
) -> BaseResponse:
    """
    Set a traveler as the primary traveler for the user.
    
    This will unset any existing primary traveler.
    
    Args:
        traveler_id: Unique traveler identifier
        db: Database session
        user: Authenticated user
        traveler_service: Traveler service instance
    
    Returns:
        BaseResponse with update confirmation
    """
    traveler_id = validate_traveler_id(traveler_id)
    
    try:
        result = await traveler_service.set_primary_traveler(
            traveler_id=traveler_id,
            user_id=user["id"]
        )
        
        return create_success_response(
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response("UPDATE_ERROR", "Failed to set primary traveler")


@router.get("/{traveler_id}/validation", response_model=BaseResponse)
async def validate_traveler_for_booking(
    traveler_id: str = Path(..., description="Traveler ID"),
    destination_country: str = Query(..., description="Destination country code"),
    travel_date: date = Query(..., description="Travel date"),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    traveler_service: Any = Depends(get_traveler_service)
) -> BaseResponse:
    """
    Validate traveler profile for a specific booking.
    
    This endpoint checks:
    - Document validity and expiration
    - Visa requirements
    - Age restrictions
    - Special travel requirements
    
    Args:
        traveler_id: Unique traveler identifier
        destination_country: ISO country code for destination
        travel_date: Planned travel date
        db: Database session
        user: Authenticated user
        traveler_service: Traveler service instance
    
    Returns:
        BaseResponse with validation results and requirements
    """
    traveler_id = validate_traveler_id(traveler_id)
    
    try:
        validation_result = await traveler_service.validate_for_booking(
            traveler_id=traveler_id,
            user_id=user["id"],
            destination_country=destination_country,
            travel_date=travel_date
        )
        
        return create_success_response(
            data=validation_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response("VALIDATION_ERROR", "Failed to validate traveler for booking")