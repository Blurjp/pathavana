"""
Unified Travel Service for managing travel sessions and operations.
"""

import uuid
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from ..models.unified_travel_session import UnifiedTravelSession
from ..models.user import User
from ..schemas.travel import (
    SessionStatus,
    MessageRole,
    TravelSessionCreate,
    TravelSessionResponse,
    ChatRequest,
    SearchRequest,
    SaveItemRequest,
    SessionUpdate,
    LocationUpdate,
    DateUpdate
)
from ..core.logger import logger


class UnifiedTravelService:
    """Service for managing unified travel sessions."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_session(
        self,
        user_id: Optional[int],
        request: TravelSessionCreate
    ) -> UnifiedTravelSession:
        """Create a new travel session."""
        try:
            # Create new session
            session = UnifiedTravelSession(
                user_id=user_id,
                status=SessionStatus.ACTIVE,
                trip_context={
                    "initial_message": request.message,
                    "source": request.source,
                    "metadata": request.metadata or {}
                },
                preferences={},
                conversation_history=[],
                search_results={},
                selected_items={}
            )
            
            # Add initial user message
            session.add_message(
                role=MessageRole.USER.value,
                content=request.message,
                metadata={"source": request.source}
            )
            
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
            
            logger.info(f"Created travel session {session.id} for user {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create travel session: {str(e)}")
            await self.db.rollback()
            raise