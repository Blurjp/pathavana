#!/usr/bin/env python3
"""
Test direct database query to see if the issue is with the database
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def test_query():
    """Test querying user with profile and preferences"""
    async with AsyncSession(engine) as db:
        try:
            # Get test user
            result = await db.execute(
                select(User)
                .options(
                    selectinload(User.profile),
                    selectinload(User.travel_preferences)
                )
                .where(User.email == "test@example.com")
            )
            user = result.scalar_one_or_none()
            
            if user:
                print(f"✅ Found user: {user.email}")
                print(f"   ID: {user.id}")
                print(f"   Full name: {user.full_name}")
                print(f"   Has profile: {user.profile is not None}")
                print(f"   Has preferences: {user.travel_preferences is not None}")
            else:
                print("❌ User not found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_query())