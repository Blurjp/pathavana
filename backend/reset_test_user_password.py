#!/usr/bin/env python3
"""
Reset test user password
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select, update

async def reset_password():
    """Reset test user password"""
    async with AsyncSession(engine) as db:
        try:
            # Update password for test user
            result = await db.execute(
                update(User)
                .where(User.email == "test@example.com")
                .values(
                    password_hash=get_password_hash("testpass123"),
                    status="active"
                )
            )
            
            await db.commit()
            
            if result.rowcount > 0:
                print("✅ Test user password reset successfully")
            else:
                print("❌ Test user not found")
                
        except Exception as e:
            print(f"❌ Error resetting password: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(reset_password())