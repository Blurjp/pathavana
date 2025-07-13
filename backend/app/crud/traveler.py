"""
CRUD operations for Traveler
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.traveler import Traveler
from app.schemas.traveler import TravelerCreate, TravelerUpdate

class CRUDTraveler(CRUDBase[Traveler, TravelerCreate, TravelerUpdate]):
    async def get_by_user(
        self, db: AsyncSession, *, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[Traveler]:
        query = (
            select(Traveler)
            .where(Traveler.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_email(
        self, db: AsyncSession, *, email: str, user_id: str
    ) -> Optional[Traveler]:
        query = select(Traveler).where(
            Traveler.email == email,
            Traveler.user_id == user_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

traveler = CRUDTraveler(Traveler)