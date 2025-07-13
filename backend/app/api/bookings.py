"""
Booking management API endpoints for Pathavana.

This module handles all booking-related operations including:
- Creating new bookings
- Retrieving booking details
- Updating booking information
- Cancelling bookings
- Listing user bookings

All endpoints follow REST principles and the standard API response pattern.
"""

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.base import BaseResponse, ResponseMetadata, ErrorDetail, PaginationInfo
from ..schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingUpdate,
    BookingCancellation,
    BookingSearchParams,
    BookingSummary,
    BookingStatus,
    BookingType,
    PaymentStatus
)

# Note: These imports would need to be implemented
# from ..core.database import get_db
# from ..core.security import get_current_user
# from ..models.user import User
# from ..services.booking_service import BookingService
# from ..services.payment_service import PaymentService

router = APIRouter(prefix="/api/bookings", tags=["bookings"])
security = HTTPBearer()


# Dependency stubs - these would be implemented in the actual application
async def get_db() -> AsyncSession:
    """Get database session."""
    pass


async def get_current_user(token: str = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user."""
    return {"id": 1, "email": "user@example.com"}


async def get_booking_service() -> Any:
    """Get booking service instance."""
    pass


async def get_payment_service() -> Any:
    """Get payment service instance."""
    pass


def validate_booking_id(booking_id: str) -> str:
    """Validate and return booking ID."""
    try:
        uuid.UUID(booking_id)
        return booking_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid booking ID format"
        )


def create_error_response(error_code: str, message: str, field: Optional[str] = None) -> BaseResponse:
    """Create standardized error response."""
    return BaseResponse(
        success=False,
        errors=[ErrorDetail(code=error_code, message=message, field=field)],
        metadata=ResponseMetadata()
    )


def create_success_response(data: Dict[str, Any], session_id: Optional[str] = None) -> BaseResponse:
    """Create standardized success response."""
    metadata = ResponseMetadata()
    if session_id:
        metadata.session_id = session_id
    
    return BaseResponse(
        success=True,
        data=data,
        metadata=metadata
    )


@router.post("", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    request: BookingCreate,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    booking_service: Any = Depends(get_booking_service),
    payment_service: Any = Depends(get_payment_service)
) -> BaseResponse:
    """
    Create a new booking.
    
    This endpoint:
    1. Validates booking data and traveler information
    2. Checks availability with the provider
    3. Processes payment if required
    4. Creates booking record with confirmation
    5. Returns booking details and confirmation number
    
    Args:
        request: Complete booking information
        db: Database session
        user: Authenticated user
        booking_service: Booking service instance
        payment_service: Payment service instance
    
    Returns:
        BaseResponse with:
        - booking_id: Unique booking identifier
        - confirmation_number: Provider confirmation number
        - total_price: Final booking price
        - payment_status: Payment processing status
        - estimated_confirmation_time: When booking will be confirmed
    
    Raises:
        HTTPException: If booking validation or processing fails
    """
    try:
        # Validate session ownership if session_id provided
        if request.session_id:
            session_valid = await booking_service.validate_session_ownership(
                request.session_id, user["id"]
            )
            if not session_valid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid session or access denied"
                )
        
        # Validate booking availability
        availability_check = await booking_service.check_availability(
            booking_type=request.booking_type,
            provider=request.provider,
            booking_data=request.booking_data
        )
        
        if not availability_check.get("available"):
            return create_error_response(
                "AVAILABILITY_ERROR",
                "Selected option is no longer available",
                "booking_data"
            )
        
        # Process payment
        payment_result = await payment_service.process_payment(
            payment_method=request.payment_method,
            amount=availability_check["price"]["amount"],
            currency=availability_check["price"]["currency"],
            booking_reference=str(uuid.uuid4())
        )
        
        if payment_result["status"] != "success":
            return create_error_response(
                "PAYMENT_ERROR",
                payment_result.get("error_message", "Payment processing failed")
            )
        
        # Create booking
        booking_result = await booking_service.create_booking(
            user_id=user["id"],
            booking_data=request,
            payment_data=payment_result,
            availability_data=availability_check
        )
        
        return create_success_response(
            data={
                "booking_id": booking_result["booking_id"],
                "confirmation_number": booking_result.get("confirmation_number"),
                "provider_booking_id": booking_result.get("provider_booking_id"),
                "status": booking_result["status"],
                "total_price": booking_result["total_price"],
                "payment_status": payment_result["status"],
                "estimated_confirmation_time": booking_result.get("estimated_confirmation_time"),
                "cancellation_policy": booking_result.get("cancellation_policy"),
                "contact_info": booking_result.get("contact_info")
            },
            session_id=request.session_id
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        # Log error in production
        return create_error_response("BOOKING_ERROR", "Failed to create booking")


@router.get("/{booking_id}", response_model=BaseResponse)
async def get_booking(
    booking_id: str = Path(..., description="Booking ID"),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    booking_service: Any = Depends(get_booking_service)
) -> BaseResponse:
    """
    Get detailed booking information.
    
    This endpoint returns complete booking details including:
    - Booking status and confirmation details
    - Traveler information
    - Provider-specific booking data
    - Payment information
    - Cancellation policy
    - Contact information
    
    Args:
        booking_id: Unique booking identifier
        db: Database session
        user: Authenticated user
        booking_service: Booking service instance
    
    Returns:
        BaseResponse with complete BookingResponse data
    
    Raises:
        HTTPException: If booking not found or access denied
    """
    booking_id = validate_booking_id(booking_id)
    
    try:
        booking_data = await booking_service.get_booking(
            booking_id=booking_id,
            user_id=user["id"]
        )
        
        if not booking_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Get latest status from provider if needed
        if booking_data["status"] in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            updated_status = await booking_service.sync_booking_status(
                booking_id=booking_id,
                provider=booking_data["provider"]
            )
            if updated_status:
                booking_data.update(updated_status)
        
        return create_success_response(
            data=booking_data,
            session_id=booking_data.get("session_id")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response("RETRIEVAL_ERROR", "Failed to retrieve booking")


@router.put("/{booking_id}", response_model=BaseResponse)
async def update_booking(
    booking_id: str = Path(..., description="Booking ID"),
    request: BookingUpdate = ...,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    booking_service: Any = Depends(get_booking_service)
) -> BaseResponse:
    """
    Update booking information.
    
    This endpoint allows updates to:
    - Traveler information
    - Contact details
    - Special requests
    - Status changes (limited)
    
    Note: Not all booking changes are allowed depending on provider policies
    and booking status.
    
    Args:
        booking_id: Unique booking identifier
        request: Updated booking information
        db: Database session
        user: Authenticated user
        booking_service: Booking service instance
    
    Returns:
        BaseResponse with updated booking data
    
    Raises:
        HTTPException: If booking not found, access denied, or update not allowed
    """
    booking_id = validate_booking_id(booking_id)
    
    try:
        # Get current booking to validate ownership and status
        current_booking = await booking_service.get_booking(
            booking_id=booking_id,
            user_id=user["id"]
        )
        
        if not current_booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Check if updates are allowed
        if current_booking["status"] in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update cancelled or completed bookings"
            )
        
        # Validate update permissions
        update_validation = await booking_service.validate_update(
            booking_id=booking_id,
            current_booking=current_booking,
            update_data=request.dict(exclude_unset=True)
        )
        
        if not update_validation["allowed"]:
            return create_error_response(
                "UPDATE_NOT_ALLOWED",
                update_validation.get("reason", "Update not permitted")
            )
        
        # Apply updates
        updated_booking = await booking_service.update_booking(
            booking_id=booking_id,
            update_data=request.dict(exclude_unset=True),
            validation_data=update_validation
        )
        
        return create_success_response(
            data=updated_booking,
            session_id=updated_booking.get("session_id")
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        return create_error_response("UPDATE_ERROR", "Failed to update booking")


@router.delete("/{booking_id}", response_model=BaseResponse)
async def cancel_booking(
    booking_id: str = Path(..., description="Booking ID"),
    request: BookingCancellation = ...,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    booking_service: Any = Depends(get_booking_service),
    payment_service: Any = Depends(get_payment_service)
) -> BaseResponse:
    """
    Cancel a booking.
    
    This endpoint:
    1. Validates cancellation eligibility
    2. Cancels with the provider
    3. Processes refunds according to policy
    4. Updates booking status
    5. Sends cancellation confirmation
    
    Args:
        booking_id: Unique booking identifier
        request: Cancellation details and reason
        db: Database session
        user: Authenticated user
        booking_service: Booking service instance
        payment_service: Payment service instance
    
    Returns:
        BaseResponse with:
        - cancellation_confirmed: Whether cancellation was successful
        - refund_amount: Amount to be refunded
        - refund_timeline: Expected refund processing time
        - cancellation_reference: Provider cancellation reference
    
    Raises:
        HTTPException: If booking cannot be cancelled
    """
    booking_id = validate_booking_id(booking_id)
    
    try:
        # Get booking and validate cancellation eligibility
        booking = await booking_service.get_booking(
            booking_id=booking_id,
            user_id=user["id"]
        )
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        if booking["status"] == BookingStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking is already cancelled"
            )
        
        # Check cancellation policy
        cancellation_check = await booking_service.check_cancellation_policy(
            booking_id=booking_id,
            booking_data=booking,
            reason=request.reason
        )
        
        if not cancellation_check["allowed"]:
            return create_error_response(
                "CANCELLATION_NOT_ALLOWED",
                cancellation_check.get("reason", "Cancellation not permitted")
            )
        
        # Process cancellation with provider
        provider_cancellation = await booking_service.cancel_with_provider(
            booking_id=booking_id,
            provider=booking["provider"],
            reason=request.reason
        )
        
        # Process refund if applicable
        refund_result = None
        if request.refund_requested and cancellation_check.get("refund_amount", 0) > 0:
            refund_result = await payment_service.process_refund(
                booking_id=booking_id,
                original_payment=booking["payment_method"],
                refund_amount=cancellation_check["refund_amount"],
                reason=request.reason
            )
        
        # Update booking status
        await booking_service.update_booking_status(
            booking_id=booking_id,
            status=BookingStatus.CANCELLED,
            cancellation_data={
                "reason": request.reason,
                "cancelled_at": datetime.utcnow(),
                "provider_confirmation": provider_cancellation,
                "refund_data": refund_result
            }
        )
        
        return create_success_response(
            data={
                "cancellation_confirmed": provider_cancellation.get("confirmed", False),
                "cancellation_reference": provider_cancellation.get("reference"),
                "refund_amount": cancellation_check.get("refund_amount", 0),
                "refund_timeline": cancellation_check.get("refund_timeline"),
                "refund_reference": refund_result.get("reference") if refund_result else None,
                "cancellation_fees": cancellation_check.get("fees", 0),
                "cancelled_at": datetime.utcnow().isoformat()
            },
            session_id=booking.get("session_id")
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        return create_error_response("CANCELLATION_ERROR", "Failed to cancel booking")


@router.get("", response_model=BaseResponse)
async def list_bookings(
    params: BookingSearchParams = Depends(),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    booking_service: Any = Depends(get_booking_service)
) -> BaseResponse:
    """
    List user's bookings with filtering and pagination.
    
    This endpoint supports filtering by:
    - Booking status
    - Booking type
    - Provider
    - Date range
    - Search query
    
    Args:
        params: Search and pagination parameters
        db: Database session
        user: Authenticated user
        booking_service: Booking service instance
    
    Returns:
        BaseResponse with:
        - bookings: List of booking summaries
        - pagination: Pagination information
        - filters_applied: Active filters
        - total_value: Total value of all bookings
    
    Raises:
        HTTPException: If search parameters are invalid
    """
    try:
        # Execute search with filters
        search_result = await booking_service.search_bookings(
            user_id=user["id"],
            filters={
                "status": params.status,
                "booking_type": params.booking_type,
                "provider": params.provider,
                "date_from": params.date_from,
                "date_to": params.date_to,
                "search_query": params.search_query
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
                "bookings": search_result["bookings"],
                "pagination": pagination_info.dict(),
                "filters_applied": {
                    key: value for key, value in {
                        "status": params.status,
                        "booking_type": params.booking_type,
                        "provider": params.provider,
                        "date_from": params.date_from,
                        "date_to": params.date_to,
                        "search_query": params.search_query
                    }.items() if value is not None
                },
                "total_value": search_result.get("total_value"),
                "summary": search_result.get("summary", {})
            }
        )
        
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        return create_error_response("SEARCH_ERROR", "Failed to search bookings")


@router.get("/{booking_id}/status", response_model=BaseResponse)
async def get_booking_status(
    booking_id: str = Path(..., description="Booking ID"),
    sync_with_provider: bool = Query(default=False, description="Sync status with provider"),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    booking_service: Any = Depends(get_booking_service)
) -> BaseResponse:
    """
    Get current booking status with optional provider sync.
    
    Args:
        booking_id: Unique booking identifier
        sync_with_provider: Whether to check status with provider
        db: Database session
        user: Authenticated user
        booking_service: Booking service instance
    
    Returns:
        BaseResponse with current status information
    """
    booking_id = validate_booking_id(booking_id)
    
    try:
        status_info = await booking_service.get_booking_status(
            booking_id=booking_id,
            user_id=user["id"],
            sync_with_provider=sync_with_provider
        )
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        return create_success_response(
            data=status_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response("STATUS_ERROR", "Failed to get booking status")


@router.post("/{booking_id}/documents", response_model=BaseResponse)
async def generate_booking_documents(
    booking_id: str = Path(..., description="Booking ID"),
    document_types: List[str] = Query(..., description="Types of documents to generate"),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    booking_service: Any = Depends(get_booking_service)
) -> BaseResponse:
    """
    Generate booking documents (e-tickets, vouchers, etc.).
    
    Args:
        booking_id: Unique booking identifier
        document_types: List of document types to generate
        db: Database session
        user: Authenticated user
        booking_service: Booking service instance
    
    Returns:
        BaseResponse with document download URLs
    """
    booking_id = validate_booking_id(booking_id)
    
    try:
        documents = await booking_service.generate_documents(
            booking_id=booking_id,
            user_id=user["id"],
            document_types=document_types
        )
        
        return create_success_response(
            data={
                "documents": documents,
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response("DOCUMENT_ERROR", "Failed to generate documents")