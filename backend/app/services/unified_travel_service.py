"""
Unified travel service for orchestrating travel planning operations.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from datetime import datetime, timedelta

from ..models.unified_travel_session import UnifiedTravelSession, SessionStatus
from ..models.user import User
from ..core.security import create_session_token


class UnifiedTravelService:
    """
    Main service class for unified travel planning operations.
    Handles session management, context tracking, and service coordination.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_session(
        self, 
        user_id: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new unified travel planning session.
        """
        session_id = str(uuid.uuid4())
        session_token = create_session_token(session_id)
        expires_at = datetime.utcnow() + timedelta(hours=24)  # 24-hour session
        
        session = UnifiedTravelSession(
            id=session_id,
            user_id=user_id,
            session_token=session_token,
            status=SessionStatus.ACTIVE,
            expires_at=expires_at,
            travel_context=initial_context or {},
            conversation_history=[],
            current_intent=None,
            active_searches={},
            pending_bookings={},
            user_preferences={},
            external_session_ids={}
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        return session_id
    
    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve current session state and context.
        """
        query = select(UnifiedTravelSession).where(
            UnifiedTravelSession.id == session_id
        )
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        return {
            "session_id": session.id,
            "status": session.status.value,
            "travel_context": session.travel_context,
            "conversation_history": session.conversation_history,
            "current_intent": session.current_intent,
            "active_searches": session.active_searches,
            "pending_bookings": session.pending_bookings,
            "user_preferences": session.user_preferences,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat() if session.updated_at else None
        }
    
    async def update_session_context(
        self, 
        session_id: str, 
        context_updates: Dict[str, Any]
    ) -> None:
        """
        Update session context with new information.
        """
        query = select(UnifiedTravelSession).where(
            UnifiedTravelSession.id == session_id
        )
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Merge context updates
        current_context = session.travel_context or {}
        current_context.update(context_updates)
        session.travel_context = current_context
        
        await self.db.commit()
    
    async def add_conversation_message(
        self,
        session_id: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to the conversation history.
        """
        query = select(UnifiedTravelSession).where(
            UnifiedTravelSession.id == session_id
        )
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        message = {
            "id": str(uuid.uuid4()),
            "type": message_type,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        conversation_history = session.conversation_history or []
        conversation_history.append(message)
        session.conversation_history = conversation_history
        
        await self.db.commit()
    
    async def update_intent(
        self, 
        session_id: str, 
        intent: str,
        intent_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update the current intent for the session.
        """
        query = select(UnifiedTravelSession).where(
            UnifiedTravelSession.id == session_id
        )
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.current_intent = intent
        
        # Update travel context with intent data if provided
        if intent_data:
            current_context = session.travel_context or {}
            current_context.update(intent_data)
            session.travel_context = current_context
        
        await self.db.commit()
    
    async def store_search_results(
        self,
        session_id: str,
        search_type: str,
        results: Dict[str, Any]
    ) -> None:
        """
        Store search results for the session.
        """
        query = select(UnifiedTravelSession).where(
            UnifiedTravelSession.id == session_id
        )
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        active_searches = session.active_searches or {}
        active_searches[search_type] = {
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        session.active_searches = active_searches
        
        await self.db.commit()
    
    async def end_session(self, session_id: str) -> None:
        """
        End a travel planning session.
        """
        query = select(UnifiedTravelSession).where(
            UnifiedTravelSession.id == session_id
        )
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.status = SessionStatus.COMPLETED
        await self.db.commit()
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all sessions for a specific user.
        """
        query = select(UnifiedTravelSession).where(
            UnifiedTravelSession.user_id == user_id
        ).order_by(UnifiedTravelSession.created_at.desc())
        
        result = await self.db.execute(query)
        sessions = result.scalars().all()
        
        return [
            {
                "session_id": session.id,
                "status": session.status.value,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                "travel_context": session.travel_context
            }
            for session in sessions
        ]