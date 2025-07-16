#!/usr/bin/env python3
"""
Test direct database update
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine
from app.models.user import User
from sqlalchemy import select, update

async def test_update():
    """Test updating user directly"""
    async with AsyncSession(engine) as db:
        try:
            # Get test user
            result = await db.execute(
                select(User).where(User.email == "test@example.com")
            )
            user = result.scalar_one_or_none()
            
            if user:
                print(f"✅ Found user: {user.email}")
                print(f"   Current name: {user.full_name}")
                
                # Update name
                user.first_name = "Direct"
                user.last_name = "Update"
                user.full_name = "Direct Update"
                
                await db.commit()
                print("✅ Update committed")
                
                # Verify
                await db.refresh(user)
                print(f"   New name: {user.full_name}")
            else:
                print("❌ User not found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(test_update())