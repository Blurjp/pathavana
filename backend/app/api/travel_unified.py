"""
Unified Travel API endpoints for Pathavana.

This module provides the main travel planning API endpoints that handle:
- Session creation and management
- Chat-based travel planning
- Search orchestration
- Item management
- Session data retrieval

All endpoints follow the standard API response pattern and use UUID-based session management.
"""

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.security import HTTPBearer
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json

from ..schemas.base import BaseResponse, ResponseMetadata, ErrorDetail
from ..schemas.travel import (
    TravelSessionCreate,
    TravelSessionResponse,
    ChatRequest,
    SearchRequest,
    SaveItemRequest,
    SessionUpdate,
    LocationUpdate,
    DateUpdate,
    SessionStatus,
    SearchType
)

# Note: These imports would need to be implemented
# from ..core.database import get_db
# from ..core.security import get_current_user
# from ..models.user import User
# from ..services.unified_travel_service import UnifiedTravelService
# from ..services.llm_service import LLMService

router = APIRouter(prefix="/api/travel", tags=["travel"])
security = HTTPBearer()


# Dependency stubs - these would be implemented in the actual application
async def get_db() -> AsyncSession:
    """Get database session."""
    # This would return an actual database session
    pass


async def get_current_user(token: str = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user."""
    # This would validate token and return user
    return {"id": 1, "email": "user@example.com"}


async def get_travel_service() -> Any:
    """Get unified travel service instance."""
    # This would return the actual service
    pass


async def get_orchestrator(travel_service: Any = Depends(get_travel_service)) -> Any:
    """Get AI orchestrator instance."""
    # This would return an actual orchestrator instance
    # In production:
    # from ..agents.unified_orchestrator import UnifiedOrchestrator
    # return UnifiedOrchestrator(travel_service)
    pass


def validate_session_id(session_id: str) -> str:
    """Validate and return session ID."""
    try:
        uuid.UUID(session_id)
        return session_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
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


@router.post("/sessions", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_travel_session(
    request: TravelSessionCreate,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    travel_service: Any = Depends(get_travel_service)
) -> BaseResponse:
    """
    Create a new travel session with initial message.
    
    This endpoint:
    1. Creates a new UUID-based session
    2. Processes the initial travel query using LLM
    3. Extracts travel intent and context
    4. Returns session ID and initial suggestions
    
    Args:
        request: Initial travel query and metadata
        db: Database session
        user: Authenticated user
        travel_service: Travel service instance
    
    Returns:
        BaseResponse with session data including:
        - session_id: UUID for the new session
        - parsed_intent: Extracted travel information
        - suggestions: AI-generated follow-up questions
        - trip_context: Initial trip context
    
    Raises:
        HTTPException: If session creation fails
    """
    try:
        # Generate new session ID
        session_id = str(uuid.uuid4())
        
        # Process initial message and create session
        session_data = await travel_service.create_session(
            session_id=session_id,
            user_id=user["id"],
            initial_message=request.message,
            source=request.source,
            metadata=request.metadata
        )
        
        return create_success_response(
            data={
                "session_id": session_id,
                "parsed_intent": session_data.get("parsed_intent"),
                "suggestions": session_data.get("suggestions", []),
                "trip_context": session_data.get("trip_context"),
                "status": SessionStatus.ACTIVE.value
            },
            session_id=session_id
        )
        
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        # Log the error in production
        return create_error_response("INTERNAL_ERROR", "Failed to create travel session")


@router.post("/sessions/{session_id}/chat", response_model=BaseResponse)
async def send_chat_message(
    session_id: str = Path(..., description="Travel session ID"),
    request: ChatRequest = ...,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    travel_service: Any = Depends(get_travel_service)
) -> BaseResponse:
    """
    Send a message to an existing travel session.
    
    This endpoint:
    1. Validates session ownership
    2. Processes the new message with conversation context
    3. Updates trip context if needed
    4. Triggers searches if appropriate
    5. Returns AI response and updated context
    
    Args:
        session_id: UUID of the travel session
        request: Chat message and metadata
        db: Database session
        user: Authenticated user
        travel_service: Travel service instance
    
    Returns:
        BaseResponse with:
        - message: AI assistant response
        - updated_context: Any changes to trip context
        - suggestions: Follow-up suggestions
        - search_triggered: Whether searches were initiated
        - conflicts: Any detected data conflicts
    
    Raises:
        HTTPException: If session not found or access denied
    """
    session_id = validate_session_id(session_id)
    
    try:
        # Verify session ownership
        session = await travel_service.get_session(session_id, user["id"])
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Process message with conversation context
        response_data = await travel_service.process_message(
            session_id=session_id,
            message=request.message,
            metadata=request.metadata
        )
        
        return create_success_response(
            data={
                "message": response_data.get("response_message"),
                "updated_context": response_data.get("updated_context"),
                "suggestions": response_data.get("suggestions", []),
                "search_triggered": response_data.get("search_triggered", False),
                "conflicts": response_data.get("conflicts", []),
                "chat_history": response_data.get("chat_history", [])
            },
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        return create_error_response("INTERNAL_ERROR", "Failed to process message")


@router.get("/sessions/{session_id}", response_model=BaseResponse)
async def get_travel_session(
    session_id: str = Path(..., description="Travel session ID"),
    include_history: bool = Query(default=True, description="Include chat history"),
    include_results: bool = Query(default=True, description="Include search results"),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    travel_service: Any = Depends(get_travel_service)
) -> BaseResponse:
    """
    Retrieve complete travel session data.
    
    This endpoint returns all session information including:
    - Chat history
    - Current trip context
    - Search results
    - Saved items
    - Session metadata
    
    Args:
        session_id: UUID of the travel session
        include_history: Whether to include chat history
        include_results: Whether to include search results
        db: Database session
        user: Authenticated user
        travel_service: Travel service instance
    
    Returns:
        BaseResponse with complete TravelSessionResponse data
    
    Raises:
        HTTPException: If session not found or access denied
    """
    session_id = validate_session_id(session_id)
    
    try:
        # Get session with optional inclusions
        session_data = await travel_service.get_session_data(
            session_id=session_id,
            user_id=user["id"],
            include_history=include_history,
            include_results=include_results
        )
        
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return create_success_response(
            data=session_data,
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response("INTERNAL_ERROR", "Failed to retrieve session")


@router.post("/sessions/{session_id}/search", response_model=BaseResponse)
async def trigger_search(
    session_id: str = Path(..., description="Travel session ID"),
    request: SearchRequest = ...,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    travel_service: Any = Depends(get_travel_service)
) -> BaseResponse:
    """
    Trigger searches based on current session context.
    
    This endpoint:
    1. Validates current trip context
    2. Executes searches for specified types (flights, hotels, activities)
    3. Caches results with appropriate TTL
    4. Returns search results and metadata
    
    Args:
        session_id: UUID of the travel session
        request: Search types and parameters
        db: Database session
        user: Authenticated user
        travel_service: Travel service instance
    
    Returns:
        BaseResponse with:
        - results: Search results by type
        - search_id: Unique search identifier
        - cached: Whether results were cached
        - errors: Any search failures
        - context_used: Trip context used for search
    
    Raises:
        HTTPException: If session not found or insufficient context
    """
    session_id = validate_session_id(session_id)
    
    try:
        # Verify session and get context
        session = await travel_service.get_session(session_id, user["id"])
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Execute searches
        search_results = await travel_service.execute_search(
            session_id=session_id,
            search_types=request.search_types,
            force_refresh=request.force_refresh,
            filters=request.filters,
            preferences=request.preferences
        )
        
        return create_success_response(
            data={
                "results": search_results.get("results", {}),
                "search_id": search_results.get("search_id"),
                "cached": search_results.get("cached", False),
                "errors": search_results.get("errors", []),
                "context_used": search_results.get("context_used"),
                "result_counts": search_results.get("result_counts", {})
            },
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        return create_error_response("SEARCH_ERROR", "Search execution failed")


@router.post("/sessions/{session_id}/items", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def save_item_to_trip(
    session_id: str = Path(..., description="Travel session ID"),
    request: SaveItemRequest = ...,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    travel_service: Any = Depends(get_travel_service)
) -> BaseResponse:
    """
    Save an item (flight, hotel, activity) to the trip plan.
    
    This endpoint:
    1. Validates the item data
    2. Checks for conflicts with existing items
    3. Adds item to the trip itinerary
    4. Updates trip context if needed
    5. Returns updated trip plan
    
    Args:
        session_id: UUID of the travel session
        request: Item data and placement information
        db: Database session
        user: Authenticated user
        travel_service: Travel service instance
    
    Returns:
        BaseResponse with:
        - item_id: Unique identifier for saved item
        - conflicts: Any conflicts detected
        - updated_plan: Updated trip plan
        - suggestions: Related suggestions
    
    Raises:
        HTTPException: If session not found or item validation fails
    """
    session_id = validate_session_id(session_id)
    
    try:
        # Save item to trip
        save_result = await travel_service.save_item_to_trip(
            session_id=session_id,
            user_id=user["id"],
            item_type=request.item_type,
            item_data=request.item_data,
            assigned_day=request.assigned_day,
            notes=request.notes,
            priority=request.priority
        )
        
        return create_success_response(
            data={
                "item_id": save_result.get("item_id"),
                "conflicts": save_result.get("conflicts", []),
                "updated_plan": save_result.get("updated_plan"),
                "suggestions": save_result.get("suggestions", []),
                "total_items": save_result.get("total_items", 0)
            },
            session_id=session_id
        )
        
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        return create_error_response("SAVE_ERROR", "Failed to save item to trip")


@router.put("/sessions/{session_id}", response_model=BaseResponse)
async def update_session(
    session_id: str = Path(..., description="Travel session ID"),
    request: SessionUpdate = ...,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    travel_service: Any = Depends(get_travel_service)
) -> BaseResponse:
    """
    Update session properties like status or trip context.
    
    Args:
        session_id: UUID of the travel session
        request: Session update data
        db: Database session
        user: Authenticated user
        travel_service: Travel service instance
    
    Returns:
        BaseResponse with updated session data
    """
    session_id = validate_session_id(session_id)
    
    try:
        updated_session = await travel_service.update_session(
            session_id=session_id,
            user_id=user["id"],
            update_data=request.dict(exclude_unset=True)
        )
        
        return create_success_response(
            data=updated_session,
            session_id=session_id
        )
        
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        return create_error_response("UPDATE_ERROR", "Failed to update session")


@router.put("/sessions/{session_id}/location", response_model=BaseResponse)
async def update_location(
    session_id: str = Path(..., description="Travel session ID"),
    request: LocationUpdate = ...,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    travel_service: Any = Depends(get_travel_service)
) -> BaseResponse:
    """
    Update location information for the trip.
    
    This endpoint handles location changes and may trigger new searches.
    """
    session_id = validate_session_id(session_id)
    
    try:
        result = await travel_service.update_location(
            session_id=session_id,
            user_id=user["id"],
            location_data=request.dict(exclude_unset=True)
        )
        
        return create_success_response(
            data=result,
            session_id=session_id
        )
        
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        return create_error_response("UPDATE_ERROR", "Failed to update location")


@router.put("/sessions/{session_id}/dates", response_model=BaseResponse)
async def update_dates(
    session_id: str = Path(..., description="Travel session ID"),
    request: DateUpdate = ...,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    travel_service: Any = Depends(get_travel_service)
) -> BaseResponse:
    """
    Update travel dates for the trip.
    
    This endpoint handles date changes and may trigger new searches.
    """
    session_id = validate_session_id(session_id)
    
    try:
        result = await travel_service.update_dates(
            session_id=session_id,
            user_id=user["id"],
            date_data=request.dict(exclude_unset=True)
        )
        
        return create_success_response(
            data=result,
            session_id=session_id
        )
        
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        return create_error_response("UPDATE_ERROR", "Failed to update dates")


@router.delete("/sessions/{session_id}", response_model=BaseResponse)
async def delete_session(
    session_id: str = Path(..., description="Travel session ID"),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    travel_service: Any = Depends(get_travel_service)
) -> BaseResponse:
    """
    Delete a travel session and all associated data.
    
    This is a soft delete that preserves data for compliance purposes.
    """
    session_id = validate_session_id(session_id)
    
    try:
        await travel_service.delete_session(
            session_id=session_id,
            user_id=user["id"]
        )
        
        return create_success_response(
            data={"deleted": True, "session_id": session_id},
            session_id=session_id
        )
        
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        return create_error_response("DELETE_ERROR", "Failed to delete session")


@router.get("/sessions", response_model=BaseResponse)
async def list_user_sessions(
    status: Optional[SessionStatus] = Query(None, description="Filter by session status"),
    limit: int = Query(default=20, ge=1, le=100, description="Number of sessions to return"),
    offset: int = Query(default=0, ge=0, description="Number of sessions to skip"),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    travel_service: Any = Depends(get_travel_service)
) -> BaseResponse:
    """
    List user's travel sessions with optional filtering.
    
    Returns a paginated list of sessions with summary information.
    """
    try:
        sessions = await travel_service.list_user_sessions(
            user_id=user["id"],
            status=status,
            limit=limit,
            offset=offset
        )
        
        return create_success_response(
            data={
                "sessions": sessions.get("sessions", []),
                "total": sessions.get("total", 0),
                "limit": limit,
                "offset": offset,
                "has_more": sessions.get("has_more", False)
            }
        )
        
    except Exception as e:
        return create_error_response("LIST_ERROR", "Failed to retrieve sessions")


@router.post("/sessions/{session_id}/chat/stream")
async def chat_stream(
    session_id: str = Path(..., description="Travel session ID"),
    request: ChatRequest = ...,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
    travel_service: Any = Depends(get_travel_service),
    orchestrator: Any = Depends(get_orchestrator)
) -> StreamingResponse:
    """
    Send a message to the AI assistant and stream the response.
    
    This endpoint provides real-time streaming of AI responses for a more
    interactive chat experience. The response is streamed as Server-Sent Events (SSE).
    
    Args:
        session_id: UUID of the travel session
        request: Chat message and metadata
        db: Database session
        user: Authenticated user
        travel_service: Travel service instance
        orchestrator: AI orchestrator instance
    
    Returns:
        StreamingResponse with Server-Sent Events containing:
        - message: Partial response text
        - suggestions: Follow-up suggestions (sent at the end)
        - done: Signal that streaming is complete
    """
    session_id = validate_session_id(session_id)
    
    # Verify session ownership
    session = await travel_service.get_session(session_id, user["id"])
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    async def generate_stream():
        """Generate streaming response."""
        try:
            # Add user message to history first
            await travel_service.add_conversation_message(
                session_id=session_id,
                message_type="user",
                content=request.message
            )
            
            # Initialize response parts
            full_response = ""
            response_chunks = []
            
            # Process message with streaming
            async for chunk in orchestrator.process_message_stream(
                message=request.message,
                session_id=session_id,
                user_id=user["id"]
            ):
                if chunk.get("type") == "response":
                    # Stream response text
                    text = chunk.get("text", "")
                    full_response += text
                    yield f"data: {{\"type\": \"message\", \"content\": {json.dumps(text)}}}\n\n"
                    
                elif chunk.get("type") == "tool_use":
                    # Notify about tool usage
                    tool_info = chunk.get("tool_info", {})
                    yield f"data: {{\"type\": \"tool_use\", \"tool\": {json.dumps(tool_info)}}}\n\n"
                    
                elif chunk.get("type") == "suggestions":
                    # Send suggestions
                    suggestions = chunk.get("suggestions", [])
                    yield f"data: {{\"type\": \"suggestions\", \"suggestions\": {json.dumps(suggestions)}}}\n\n"
                    
                elif chunk.get("type") == "context_update":
                    # Send context updates
                    context = chunk.get("context", {})
                    yield f"data: {{\"type\": \"context_update\", \"context\": {json.dumps(context)}}}\n\n"
                    
                elif chunk.get("type") == "error":
                    # Send error
                    error = chunk.get("error", "Unknown error")
                    yield f"data: {{\"type\": \"error\", \"error\": {json.dumps(error)}}}\n\n"
                    break
                    
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
            
            # Save complete AI response to history
            if full_response:
                await travel_service.add_conversation_message(
                    session_id=session_id,
                    message_type="assistant",
                    content=full_response
                )
            
            # Send completion signal
            yield f"data: {{\"type\": \"done\", \"message\": \"Stream complete\"}}\n\n"
            
        except Exception as e:
            # Send error event
            error_msg = str(e) if str(e) else "An error occurred during streaming"
            yield f"data: {{\"type\": \"error\", \"error\": {json.dumps(error_msg)}}}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )