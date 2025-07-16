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
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json

from ..schemas.base import BaseResponse, ResponseMetadata, ErrorDetail
from ..core.logger import logger
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

router = APIRouter(tags=["travel"])
security = HTTPBearer(auto_error=False)


# Import actual database dependency
from ..core.database import get_db


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """Get current authenticated user."""
    # Import auth dependency
    from .auth_v2 import get_current_user_safe
    
    user = await get_current_user_safe(request, db)
    if user:
        return {"id": user.id, "email": user.email, "is_anonymous": False}
    
    # Allow anonymous access
    return None


async def get_travel_service(db: AsyncSession = Depends(get_db)) -> Any:
    """Get unified travel service instance."""
    from ..services.travel_session_db import DatabaseTravelSessionManager
    return DatabaseTravelSessionManager(db)


async def get_orchestrator(travel_service: Any = Depends(get_travel_service)) -> Any:
    """Get AI orchestrator instance."""
    logger.debug("=== ORCHESTRATOR INITIALIZATION ===")
    try:
        from ..agents.unified_orchestrator import UnifiedOrchestrator
        from ..services.orchestrator_adapter import OrchestratorTravelServiceAdapter
        from ..core.config import settings
        
        # Check if LLM credentials are configured
        if settings.LLM_PROVIDER == "openai" and not settings.OPENAI_API_KEY:
            logger.warning("❌ OpenAI API key not configured. AI agent will use template responses.")
            logger.info("ℹ️  To enable AI responses, set OPENAI_API_KEY in your .env file")
            return None
        elif settings.LLM_PROVIDER == "azure_openai":
            if not all([settings.AZURE_OPENAI_API_KEY, settings.AZURE_OPENAI_ENDPOINT, settings.AZURE_OPENAI_DEPLOYMENT_NAME]):
                logger.warning("❌ Azure OpenAI credentials not fully configured. AI agent will use template responses.")
                logger.info("ℹ️  To enable AI responses, set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT_NAME in your .env file")
                return None
        elif settings.LLM_PROVIDER == "anthropic" and not settings.ANTHROPIC_API_KEY:
            logger.warning("❌ Anthropic API key not configured. AI agent will use template responses.")
            logger.info("ℹ️  To enable AI responses, set ANTHROPIC_API_KEY in your .env file")
            return None
        
        logger.debug("Creating OrchestratorTravelServiceAdapter...")
        # Wrap the travel service with the adapter
        adapted_service = OrchestratorTravelServiceAdapter(travel_service)
        
        logger.debug("Creating UnifiedOrchestrator instance...")
        orchestrator = UnifiedOrchestrator(adapted_service)
        logger.info("✅ UnifiedOrchestrator initialized successfully")
        return orchestrator
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.info("ℹ️  Please check your LLM configuration in .env file")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to initialize UnifiedOrchestrator: {e}")
        logger.debug(f"Orchestrator initialization error details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return None


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


@router.post("/sessions/new", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_empty_travel_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(get_current_user),
    travel_service: Any = Depends(get_travel_service)
) -> BaseResponse:
    """
    Create a new empty travel session without an initial message.
    
    This endpoint is used when starting a new chat to get a session ID immediately.
    The first actual message will be sent via the chat endpoint.
    """
    try:
        # Get actual user object if authenticated
        user_obj = None
        if user and not user.get("is_anonymous"):
            from sqlalchemy import select
            from ..models import User
            result = await db.execute(select(User).where(User.id == user["id"]))
            user_obj = result.scalar_one_or_none()
        
        # Create empty session
        session = await travel_service.create_empty_session(user=user_obj)
        
        return create_success_response(
            data={
                "session_id": session.session_id,
                "status": session.status,
                "created_at": session.created_at.isoformat() if session.created_at else None
            },
            session_id=session.session_id
        )
        
    except Exception as e:
        logger.error(f"Failed to create empty session: {e}")
        return create_error_response("INTERNAL_ERROR", "Failed to create session")

@router.post("/sessions", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_travel_session(
    request_body: TravelSessionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(get_current_user),
    travel_service: Any = Depends(get_travel_service),
    orchestrator: Any = Depends(get_orchestrator)
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
        # Get actual user object if authenticated
        user_obj = None
        if user and not user.get("is_anonymous"):
            from sqlalchemy import select
            from ..models import User
            result = await db.execute(select(User).where(User.id == user["id"]))
            user_obj = result.scalar_one_or_none()
        
        # Create session using the implementation with orchestrator
        session = await travel_service.create_session(
            user=user_obj,
            request=request_body,
            orchestrator=orchestrator
        )
        
        # Extract initial response from conversation history
        conversation = session.session_data.get("conversation_history", [])
        ai_response = conversation[-1] if conversation else None
        
        # Include full metadata with hints
        response_data = {
            "session_id": session.session_id,
            "parsed_intent": session.session_data.get("parsed_intent", {
                "type": "travel_planning",
                "confidence": 0.9
            }),
            "suggestions": ai_response.get("metadata", {}).get("suggestions", []) if ai_response else [],
            "trip_context": session.plan_data.get("trip_context", {}) if session.plan_data else {},
            "status": session.status,
            "initial_response": ai_response.get("content", "") if ai_response else ""
        }
        
        # Add metadata with hints if available
        if ai_response and "metadata" in ai_response:
            response_data["metadata"] = ai_response["metadata"]
        
        return create_success_response(
            data=response_data,
            session_id=session.session_id
        )
        
    except ValueError as e:
        return create_error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        # Log the error in production
        return create_error_response("INTERNAL_ERROR", "Failed to create travel session")


@router.post("/sessions/{session_id}/chat", response_model=BaseResponse)
async def send_chat_message(
    request_body: ChatRequest,
    request: Request,
    session_id: str = Path(..., description="Travel session ID"),
    db: AsyncSession = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(get_current_user),
    travel_service: Any = Depends(get_travel_service),
    orchestrator: Any = Depends(get_orchestrator)
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
    
    logger.debug("\n" + "="*60)
    logger.debug(f"🗨️  PROCESSING CHAT MESSAGE")
    logger.debug(f"Session ID: {session_id}")
    logger.debug(f"User message: {request_body.message}")
    logger.debug(f"Orchestrator available: {orchestrator is not None}")
    logger.debug("="*60)
    
    # Log warning if orchestrator is not available
    if orchestrator is None:
        logger.warning("⚠️  AI Orchestrator not available - using template responses")
        logger.info("💡 TIP: Configure LLM credentials in .env to enable intelligent AI responses")
    
    try:
        # Process chat message
        result = await travel_service.add_chat_message(
            session_id=session_id,
            request=request_body,
            user_id=user.get("id") if user and not user.get("is_anonymous") else None,
            orchestrator=orchestrator
        )
        
        if not result:
            # Try to create a new session if not found
            logger.info(f"Session {session_id} not found, creating new session")
            
            # Get actual user object if authenticated
            user_obj = None
            if user and not user.get("is_anonymous"):
                from sqlalchemy import select
                from ..models import User
                result = await db.execute(select(User).where(User.id == user["id"]))
                user_obj = result.scalar_one_or_none()
            
            # Create new session with the message
            session = await travel_service.get_or_create_session(
                session_id=session_id,
                user=user_obj,
                initial_message=request_body.message
            )
            
            # Try adding the message again
            result = await travel_service.add_chat_message(
                session_id=session_id,
                request=request_body,
                user_id=user.get("id") if user and not user.get("is_anonymous") else None,
                orchestrator=orchestrator
            )
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to process message"
                )
        
        ai_response = result["ai_response"]
        session = result["session"]
        
        response_data = {
            "message": ai_response.get("content", ""),
            "updated_context": session.get("trip_context", {}),
            "suggestions": ai_response.get("metadata", {}).get("suggestions", []),
            "search_triggered": False,
            "conflicts": [],
            "chat_history": session.get("conversation_history", [])
        }
        
        # Include hints and other metadata
        if "metadata" in ai_response:
            metadata = ai_response["metadata"]
            if "hints" in metadata:
                response_data["hints"] = metadata["hints"]
            if "conversation_state" in metadata:
                response_data["conversation_state"] = metadata["conversation_state"]
            if "extracted_entities" in metadata:
                response_data["extracted_entities"] = metadata["extracted_entities"]
            if "next_steps" in metadata:
                response_data["next_steps"] = metadata["next_steps"]
        
        return create_success_response(
            data=response_data,
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
        # Get session
        session = await travel_service.get_session(
            session_id=session_id,
            user_id=user.get("id") if user and not user.get("is_anonymous") else None
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Eagerly load all attributes we need while in async context
        # Access attributes within the async context to avoid lazy loading issues
        session_id_str = str(session.session_id)
        user_id = session.user_id
        status = session.status
        created_at = session.created_at
        updated_at = session.updated_at
        last_activity_at = session.last_activity_at
        
        session_dict = {
            "session_id": session_id_str,
            "user_id": user_id,
            "status": status,
            "created_at": created_at,
            "updated_at": updated_at,
            "last_activity_at": last_activity_at
        }
        
        # Load JSONB fields - these might be lazy loaded
        session_data_dict = {}
        plan_data_dict = {}
        metadata_dict = {}
        
        if session.session_data is not None:
            session_data_dict = dict(session.session_data)
        if session.plan_data is not None:
            plan_data_dict = dict(session.plan_data)
        if session.session_metadata is not None:
            metadata_dict = dict(session.session_metadata)
        
        # Build final response
        session_data = {
            "session_id": session_dict["session_id"],
            "user_id": session_dict["user_id"],
            "status": session_dict["status"],
            "session_data": session_data_dict,
            "plan_data": plan_data_dict,
            "session_metadata": metadata_dict,
            "created_at": session_dict["created_at"].isoformat() if session_dict["created_at"] else None,
            "updated_at": session_dict["updated_at"].isoformat() if session_dict["updated_at"] else None,
            "last_activity_at": session_dict["last_activity_at"].isoformat() if session_dict["last_activity_at"] else None
        }
        
        return create_success_response(
            data=session_data,
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {e}", exc_info=True)
        return create_error_response("INTERNAL_ERROR", f"Failed to retrieve session: {str(e)}")


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
        # Execute search
        search_results = await travel_service.search(
            session_id=session_id,
            request=request,
            user_id=user.get("id") if user and not user.get("is_anonymous") else None
        )
        
        if not search_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return create_success_response(
            data={
                "results": search_results.get("results", []),
                "search_id": str(uuid.uuid4()),
                "cached": False,
                "errors": [],
                "context_used": search_results.get("context_used", {}),
                "result_counts": {"total": search_results.get("total_count", 0)}
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
        # Save item
        success = await travel_service.save_item(
            session_id=session_id,
            request=request,
            user_id=user.get("id") if user and not user.get("is_anonymous") else None
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return create_success_response(
            data={
                "item_id": request.item_id,
                "conflicts": [],
                "updated_plan": {},
                "suggestions": [],
                "total_items": 1
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
    
    async def generate_stream():
        """Generate streaming response."""
        try:
            # Simply use the streaming method from our implementation
            async for chunk in travel_service.stream_chat(
                session_id=session_id,
                request=request,
                user_id=user.get("id") if user and not user.get("is_anonymous") else None
            ):
                yield chunk
            
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
            "Access-Control-Allow-Origin": "*",  # Allow CORS for SSE
        }
    )