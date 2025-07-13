#!/usr/bin/env python3
"""
Initialize the Pathavana database
"""
import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Set environment variable for database URL
os.environ['DATABASE_URL'] = 'sqlite:///./pathavana_dev.db'

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool


def init_database():
    """Initialize the database with all tables"""
    # Import settings after setting env var
    from app.core.config import settings
    
    # Import all models - this registers them with Base.metadata
    print("Importing models...")
    from app.models import (
        Base,
        User, UserProfile, TravelPreferences, UserDocument,
        UserSession, TokenBlacklist, AuthenticationLog, OAuthConnection, PasswordResetToken,
        Traveler, TravelerDocument, TravelerPreference,
        UnifiedTravelSession, UnifiedSavedItem, UnifiedSessionBooking,
        UnifiedBooking, FlightBooking, HotelBooking, ActivityBooking
    )
    
    # Get database URL and ensure it's using synchronous SQLite
    db_url = settings.DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://")
    print(f"Database URL: {db_url}")
    
    # Create engine with SQLite-specific settings
    if "sqlite" in db_url:
        engine = create_engine(
            db_url,
            echo=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool  # Better for SQLite
        )
    else:
        engine = create_engine(db_url, echo=True)
    
    # Drop all existing tables
    print("\nDropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    
    # Create all tables
    print("\nCreating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Verify tables were created
    with engine.connect() as conn:
        if "sqlite" in db_url:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ))
        else:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            ))
        
        tables = [row[0] for row in result]
        
        print(f"\nSuccessfully created {len(tables)} tables:")
        for table in tables:
            print(f"  ✓ {table}")
    
    print("\nDatabase initialization complete!")
    return engine


if __name__ == "__main__":
    init_database()