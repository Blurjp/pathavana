#!/usr/bin/env python3
"""
Simplified test without loading travel_preferences
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def test_query():
    """Test querying user with only profile (not preferences)"""
    async with AsyncSession(engine) as db:
        try:
            # Get test user without travel_preferences
            result = await db.execute(
                select(User)
                .options(
                    selectinload(User.profile)
                    # Skip travel_preferences for now
                )
                .where(User.email == "test@example.com")
            )
            user = result.scalar_one_or_none()
            
            if user:
                print(f"✅ Found user: {user.email}")
                print(f"   ID: {user.id}")
                print(f"   Full name: {user.full_name}")
                print(f"   Has profile: {user.profile is not None}")
                # Don't check preferences
            else:
                print("❌ User not found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_query())