#!/usr/bin/env python3
"""
Test creating traveler directly in database
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine
# Import all models to ensure they're registered
from app.models.user import User
from app.models.traveler import Traveler
from datetime import date

async def test_create():
    """Test creating traveler directly"""
    async with AsyncSession(engine) as db:
        try:
            # Create traveler
            traveler = Traveler(
                user_id=1,  # Test user ID
                first_name="Test",
                last_name="Traveler",
                full_name="Test Traveler",
                date_of_birth=date(1990, 1, 15),
                nationality="US",
                traveler_type="adult",
                status="active"
            )
            
            db.add(traveler)
            await db.commit()
            await db.refresh(traveler)
            
            print(f"✅ Traveler created successfully!")
            print(f"   ID: {traveler.id}")
            print(f"   Name: {traveler.full_name}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(test_create())