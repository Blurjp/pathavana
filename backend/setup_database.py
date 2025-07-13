#!/usr/bin/env python3
"""
Setup Pathavana database without async dependencies
"""
import os
import sys

# Override DATABASE_URL to use synchronous SQLite
os.environ['DATABASE_URL'] = 'sqlite:///./pathavana_dev.db'

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

# Create base with naming convention
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)

# Now we need to recreate the models using this Base
# Since the models use a different Base, we'll need to monkey-patch
import app.core.database
app.core.database.Base = Base

# Import all models - they will now use our Base
from app.models import user, unified_travel_session, booking, traveler, auth

# Now import the actual model classes
from app.models.user import User, UserProfile, TravelPreferences, UserDocument
from app.models.auth import UserSession, TokenBlacklist, AuthenticationLog, OAuthConnection, PasswordResetToken
from app.models.traveler import Traveler, TravelerDocument, TravelerPreference
from app.models.unified_travel_session import UnifiedTravelSession, UnifiedSavedItem, UnifiedSessionBooking
from app.models.booking import UnifiedBooking, FlightBooking, HotelBooking, ActivityBooking


def setup_database():
    """Setup database with all tables"""
    db_url = 'sqlite:///./pathavana_dev.db'
    
    print(f"Setting up database: {db_url}")
    
    # Create engine
    engine = create_engine(
        db_url,
        echo=False,  # Set to True for SQL debugging
        connect_args={"check_same_thread": False}
    )
    
    # Drop existing tables
    print("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Verify tables
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ))
        tables = [row[0] for row in result]
        
        print(f"\nSuccessfully created {len(tables)} tables:")
        for table in sorted(tables):
            print(f"  ✓ {table}")
    
    print("\nDatabase setup complete!")
    print(f"Database file created: {os.path.abspath(db_url.replace('sqlite:///', ''))}")


if __name__ == "__main__":
    setup_database()