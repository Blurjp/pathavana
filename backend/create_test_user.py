#\!/usr/bin/env python
"""Create a test user for API testing"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select

async def create_test_user():
    """Create a test user"""
    async for db in get_db():
        try:
            # Check if user already exists
            result = await db.execute(
                select(User).where(User.email == "test@example.com")
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print("Test user already exists")
                return
            
            # Create new user
            user = User(
                email="test@example.com",
                username="testuser",
                full_name="Test User",
                hashed_password=get_password_hash("testpassword"),
                is_active=True,
                is_verified=True
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            print(f"Test user created successfully with ID: {user.id}")
            
        except Exception as e:
            print(f"Error creating test user: {e}")
            await db.rollback()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(create_test_user())