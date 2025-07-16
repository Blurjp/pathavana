"""
Adapter to make DatabaseTravelSessionManager compatible with UnifiedOrchestrator expectations.
"""

import uuid
from typing import Any, Dict, Optional
from datetime import datetime

from ..schemas.travel import ChatRequest, TravelSessionCreate, MessageRole
from ..core.logger import logger


class OrchestratorTravelServiceAdapter:
    """
    Adapter that wraps DatabaseTravelSessionManager to provide the interface
    expected by UnifiedOrchestrator.
    """
    
    def __init__(self, db_travel_service):
        self.db_service = db_travel_service
        logger.debug("OrchestratorTravelServiceAdapter initialized")
    
    async def create_session(
        self, 
        user_id: Optional[int] = None, 
        initial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new session and return the session ID."""
        try:
            # Create a session using the database service
            request = TravelSessionCreate(
                message="Starting a new travel planning session",
                source="orchestrator",
                metadata={"initial_context": initial_context or {}}
            )
            
            # Get user object if user_id is provided
            user = None
            if user_id:
                from sqlalchemy import select
                from ..models import User
                result = await self.db_service.db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
            
            session = await self.db_service.create_session(user=user, request=request)
            logger.debug(f"Created session via adapter: {session.session_id}")
            return str(session.session_id)
            
        except Exception as e:
            logger.error(f"Error creating session in adapter: {e}")
            raise
    
    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get the current state of a session."""
        try:
            session = await self.db_service.get_session(session_id)
            if not session:
                return {"travel_context": {}}
            
            # Extract travel context from plan_data
            travel_context = {}
            if session.plan_data and "trip_context" in session.plan_data:
                travel_context = session.plan_data["trip_context"]
            
            return {
                "travel_context": travel_context,
                "session_data": session.session_data or {},
                "plan_data": session.plan_data or {}
            }
            
        except Exception as e:
            logger.error(f"Error getting session state in adapter: {e}")
            return {"travel_context": {}}
    
    async def add_conversation_message(
        self,
        session_id: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a message to the conversation history."""
        try:
            # Only add user messages through the normal flow
            # Assistant messages are added by the response generation process
            if message_type == "user":
                # This is already handled by the add_chat_message flow
                logger.debug(f"Skipping user message addition (handled by chat flow)")
                return
            elif message_type == "assistant":
                # Assistant messages are added automatically
                logger.debug(f"Skipping assistant message addition (handled by response generation)")
                return
                
        except Exception as e:
            logger.error(f"Error adding conversation message in adapter: {e}")
    
    async def update_session_context(
        self,
        session_id: str,
        context: Dict[str, Any]
    ) -> None:
        """Update the session's travel context."""
        try:
            session = await self.db_service.get_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found for context update")
                return
            
            # Update trip context in plan_data
            if not session.plan_data:
                session.plan_data = {}
            
            if "trip_context" not in session.plan_data:
                session.plan_data["trip_context"] = {}
            
            session.plan_data["trip_context"].update(context)
            
            # Mark as dirty for JSONB update
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(session, "plan_data")
            
            session.last_activity_at = datetime.utcnow()
            await self.db_service.db.commit()
            
            logger.debug(f"Updated session context via adapter for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error updating session context in adapter: {e}")
            await self.db_service.db.rollback()