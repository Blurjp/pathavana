#!/usr/bin/env python3
"""
Initialize the Pathavana database synchronously
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from app.core.config import settings
from app.core.database import Base

# Import all models to register them with Base
from app.models import (
    User, UserProfile, TravelPreferences, UserDocument,
    UserSession, TokenBlacklist, AuthenticationLog, OAuthConnection, PasswordResetToken,
    Traveler, TravelerDocument, TravelerPreference,
    UnifiedTravelSession, UnifiedSavedItem, UnifiedSessionBooking,
    UnifiedBooking, FlightBooking, HotelBooking, ActivityBooking
)


def init_db_sync():
    """Initialize database synchronously"""
    # Convert async database URL to sync
    db_url = settings.DATABASE_URL
    if "sqlite+aiosqlite" in db_url:
        db_url = db_url.replace("sqlite+aiosqlite", "sqlite")
    elif "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "")
    
    print(f"Database URL: {db_url}")
    
    # Create synchronous engine
    if "sqlite" in db_url:
        engine = create_engine(
            db_url,
            echo=True,
            connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(db_url, echo=True)
    
    # Drop and recreate all tables
    print("\nDropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("\nCreating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Verify tables
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\nSuccessfully created {len(tables)} tables:")
    for table in tables:
        print(f"  ✓ {table}")
    
    print("\nDatabase initialization complete!")


async def init_db_async():
    """Initialize database asynchronously using the existing init_db function"""
    from app.core.database import init_db
    await init_db()
    print("Database initialized successfully!")


if __name__ == "__main__":
    # Try sync approach first
    try:
        init_db_sync()
    except Exception as e:
        print(f"Sync initialization failed: {e}")
        print("\nTrying async initialization...")
        asyncio.run(init_db_async())