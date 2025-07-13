"""
CRUD operations for UnifiedTravelSession
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.crud.base import CRUDBase
from app.models.unified_travel_session import UnifiedTravelSession
from app.schemas.travel_session import TravelSessionCreate, TravelSessionUpdate

class CRUDTravelSession(CRUDBase[UnifiedTravelSession, TravelSessionCreate, TravelSessionUpdate]):
    async def get_by_user(
        self, db: AsyncSession, *, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[UnifiedTravelSession]:
        query = (
            select(UnifiedTravelSession)
            .where(UnifiedTravelSession.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(UnifiedTravelSession.updated_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_active_session(
        self, db: AsyncSession, *, user_id: str
    ) -> Optional[UnifiedTravelSession]:
        query = (
            select(UnifiedTravelSession)
            .where(
                and_(
                    UnifiedTravelSession.user_id == user_id,
                    UnifiedTravelSession.status == "active"
                )
            )
            .order_by(UnifiedTravelSession.updated_at.desc())
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update_session_data(
        self, db: AsyncSession, *, session_id: str, session_data: dict
    ) -> Optional[UnifiedTravelSession]:
        query = select(UnifiedTravelSession).where(UnifiedTravelSession.id == session_id)
        result = await db.execute(query)
        session = result.scalar_one_or_none()
        
        if session:
            session.session_data = session_data
            session.updated_at = datetime.utcnow()
            db.add(session)
            await db.commit()
            await db.refresh(session)
        
        return session

travel_session = CRUDTravelSession(UnifiedTravelSession)