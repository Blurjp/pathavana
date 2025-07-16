#!/usr/bin/env python
"""
Create a test user for Selenium UI testing
This ensures consistent test credentials across all tests
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User, UserStatus
from app.core.security import get_password_hash
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test user credentials - consistent across all tests
TEST_USER = {
    "email": "selenium.test@example.com",
    "password": "SeleniumTest123!",
    "full_name": "Selenium Test User",
    "username": "seleniumtest"
}

async def create_test_user():
    """Create or update the Selenium test user"""
    async for db in get_db():
        try:
            # Check if user already exists
            result = await db.execute(
                select(User).where(User.email == TEST_USER["email"])
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                # Update the password to ensure it matches
                logger.info(f"Test user already exists with ID: {existing_user.id}")
                existing_user.password_hash = get_password_hash(TEST_USER["password"])
                existing_user.status = UserStatus.ACTIVE.value
                existing_user.email_verified = True
                existing_user.full_name = TEST_USER["full_name"]
                await db.commit()
                logger.info("Updated test user password and status")
            else:
                # Create new user
                user = User(
                    email=TEST_USER["email"],
                    full_name=TEST_USER["full_name"],
                    password_hash=get_password_hash(TEST_USER["password"]),
                    status=UserStatus.ACTIVE.value,
                    email_verified=True
                )
                
                db.add(user)
                await db.commit()
                await db.refresh(user)
                
                logger.info(f"Created new test user with ID: {user.id}")
            
            # Print credentials for reference
            print("\n" + "="*60)
            print("✅ SELENIUM TEST USER READY")
            print("="*60)
            print(f"Email:    {TEST_USER['email']}")
            print(f"Password: {TEST_USER['password']}")
            print(f"Name:     {TEST_USER['full_name']}")
            print("="*60)
            print("\nThese credentials are configured in all Selenium tests.")
            print("You can also use them to manually log in and test.\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating test user: {e}")
            await db.rollback()
            return False
        finally:
            await db.close()
            break

async def verify_login():
    """Verify that the test user can log in"""
    try:
        from app.api.auth_v2 import authenticate_user
        
        async for db in get_db():
            try:
                user = await authenticate_user(
                    db, 
                    TEST_USER["email"], 
                    TEST_USER["password"]
                )
                
                if user:
                    logger.info("✅ Login verification successful")
                    return True
                else:
                    logger.error("❌ Login verification failed")
                    return False
                    
            finally:
                await db.close()
                break
                
    except Exception as e:
        logger.error(f"Error verifying login: {e}")
        return False

async def main():
    """Main function"""
    print("🔧 Creating Selenium Test User")
    print("-" * 60)
    
    # Create user
    success = await create_test_user()
    
    if success:
        # Verify login works
        print("\n🔐 Verifying login...")
        login_ok = await verify_login()
        
        if login_ok:
            print("\n✅ Test user setup complete!")
            sys.exit(0)
        else:
            print("\n⚠️  User created but login verification failed")
            print("   Check your authentication configuration")
            sys.exit(1)
    else:
        print("\n❌ Failed to create test user")
        print("   Check your database connection and configuration")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())