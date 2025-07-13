#!/usr/bin/env python3
"""
Initialize the Pathavana database by running migrations and seeding initial data.
"""

import asyncio
import sys
import os
from pathlib import Path
import subprocess
from datetime import datetime, timedelta
import uuid

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import get_db_context, engine, Base
from app.models import (
    User, UserProfile, TravelPreferences,
    UnifiedTravelSession, SessionStatus,
    Traveler, TravelerType,
    UserStatus, AuthProvider
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def run_migrations():
    """Run Alembic migrations to create/update database schema."""
    print("Running Alembic migrations...")
    
    try:
        # Run alembic upgrade head
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error running migrations: {result.stderr}")
            return False
        
        print("Migrations completed successfully!")
        print(result.stdout)
        return True
        
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False


async def seed_development_data(session: AsyncSession):
    """Seed the database with development/test data."""
    print("\nSeeding development data...")
    
    try:
        # Check if we already have data
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        
        if user_count > 0:
            print(f"Database already has {user_count} users. Skipping seed data.")
            return
        
        # Create test users
        users_data = [
            {
                "email": "demo@pathavana.com",
                "username": "demo_user",
                "full_name": "Demo User",
                "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH4RSJDjE2",  # password: demo123
                "phone_number": "+1234567890",
                "email_verified": True,
                "status": UserStatus.ACTIVE,
            },
            {
                "email": "test@pathavana.com",
                "username": "test_user",
                "full_name": "Test User",
                "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH4RSJDjE2",  # password: demo123
                "phone_number": "+0987654321",
                "email_verified": True,
                "status": UserStatus.ACTIVE,
            },
            {
                "email": "admin@pathavana.com",
                "username": "admin_user",
                "full_name": "Admin User",
                "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH4RSJDjE2",  # password: demo123
                "phone_number": "+1122334455",
                "email_verified": True,
                "status": UserStatus.ACTIVE,
            }
        ]
        
        created_users = []
        for user_data in users_data:
            user = User(**user_data)
            session.add(user)
            created_users.append(user)
        
        await session.flush()
        
        # Create user profiles and preferences
        for i, user in enumerate(created_users):
            # Create profile
            profile = UserProfile(
                user_id=user.id,
                bio=f"I love traveling and exploring new places!",
                date_of_birth=datetime(1990 + i * 5, 1, 1).date(),
                nationality="US",
                preferred_language="en",
                preferred_currency="USD",
                timezone="America/New_York",
                dietary_restrictions=["vegetarian"] if i == 1 else None,
                gdpr_consent=True,
                gdpr_consent_date=datetime.utcnow(),
                notification_preferences={
                    "email": True,
                    "sms": True,
                    "push": True,
                    "marketing": i != 2  # Admin doesn't want marketing
                }
            )
            session.add(profile)
            
            # Create travel preferences
            preferences = TravelPreferences(
                user_id=user.id,
                preferred_airlines=["AA", "DL", "UA"] if i == 0 else ["BA", "LH"],
                preferred_cabin_class="business" if i == 2 else "economy",
                preferred_seat_type="aisle" if i == 0 else "window",
                hotel_star_rating_min=4 if i == 2 else 3,
                budget_range_min=1000,
                budget_range_max=5000 if i < 2 else 10000,
                preferred_activities=["sightseeing", "museums", "food tours"],
                travel_pace="moderate",
                interests=["culture", "history", "gastronomy"] if i == 0 else ["adventure", "nature", "photography"],
                travel_style=["comfort", "authentic"] if i == 2 else ["budget", "backpacking"]
            )
            session.add(preferences)
            
            # Create travelers (companions)
            if i == 0:  # Demo user has family
                # Spouse
                spouse = Traveler(
                    user_id=user.id,
                    traveler_type=TravelerType.ADULT,
                    first_name="Jane",
                    last_name="Doe",
                    date_of_birth=datetime(1992, 6, 15).date(),
                    gender="female",
                    email="jane.doe@example.com",
                    is_primary=False,
                    relationship_to_primary="spouse"
                )
                session.add(spouse)
                
                # Child
                child = Traveler(
                    user_id=user.id,
                    traveler_type=TravelerType.CHILD,
                    first_name="Johnny",
                    last_name="Doe",
                    date_of_birth=datetime(2015, 3, 20).date(),
                    gender="male",
                    is_primary=False,
                    relationship_to_primary="child",
                    requires_guardian_consent=True,
                    guardian_name="Demo User",
                    guardian_relationship="parent"
                )
                session.add(child)
        
        await session.flush()
        
        # Create sample travel sessions
        sessions_data = [
            {
                "user": created_users[0],
                "status": SessionStatus.PLANNING,
                "session_data": {
                    "chat_messages": [
                        {
                            "role": "user",
                            "content": "I want to plan a family trip to Paris for next summer",
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        {
                            "role": "assistant",
                            "content": "I'd be happy to help you plan a family trip to Paris! Let me gather some information to create the perfect itinerary for you.",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    ],
                    "parsed_intent": {
                        "destination": "Paris",
                        "travel_type": "family",
                        "season": "summer",
                        "interests": ["sightseeing", "culture", "family-friendly"]
                    }
                },
                "plan_data": {
                    "title": "Family Summer in Paris",
                    "destination_city": "Paris",
                    "destination_country": "FR",
                    "start_date": "2024-07-15",
                    "end_date": "2024-07-22",
                    "travelers_count": 3,
                    "estimated_budget": {
                        "total": 4500,
                        "currency": "USD",
                        "breakdown": {
                            "flights": 2100,
                            "accommodation": 1400,
                            "activities": 600,
                            "meals": 400
                        }
                    }
                }
            },
            {
                "user": created_users[1],
                "status": SessionStatus.ACTIVE,
                "session_data": {
                    "chat_messages": [
                        {
                            "role": "user",
                            "content": "Looking for a weekend getaway to somewhere warm",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    ],
                    "ui_state": {
                        "current_step": "destination_selection",
                        "filters": {
                            "max_flight_duration": 4,
                            "preferred_temperature": "warm"
                        }
                    }
                }
            },
            {
                "user": created_users[0],
                "status": SessionStatus.COMPLETED,
                "session_data": {
                    "chat_messages": [
                        {
                            "role": "user",
                            "content": "Book a business trip to London next week",
                            "timestamp": (datetime.utcnow() - timedelta(days=30)).isoformat()
                        }
                    ]
                },
                "plan_data": {
                    "title": "London Business Trip",
                    "destination_city": "London",
                    "destination_country": "GB",
                    "start_date": "2024-02-20",
                    "end_date": "2024-02-23",
                    "travelers_count": 1,
                    "trip_completed": True
                }
            }
        ]
        
        for session_data in sessions_data:
            user = session_data.pop("user")
            travel_session = UnifiedTravelSession(
                user_id=user.id,
                **session_data,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            session.add(travel_session)
        
        # Commit all changes
        await session.commit()
        
        print("Development data seeded successfully!")
        print(f"- Created {len(created_users)} users")
        print(f"- Created {len(sessions_data)} travel sessions")
        print("\nTest credentials:")
        print("  Email: demo@pathavana.com")
        print("  Password: demo123")
        
    except Exception as e:
        await session.rollback()
        print(f"Error seeding data: {e}")
        raise


async def verify_database():
    """Verify the database is properly set up."""
    print("\nVerifying database setup...")
    
    async with get_db_context() as session:
        try:
            # Check tables exist
            tables_to_check = [
                "users", "user_profiles", "travel_preferences",
                "unified_travel_sessions", "bookings", "travelers"
            ]
            
            for table in tables_to_check:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = :table"),
                    {"table": table}
                )
                exists = result.scalar() > 0
                print(f"  ✓ Table '{table}': {'exists' if exists else 'MISSING!'}")
                
                if not exists:
                    return False
            
            # Check extensions
            extensions_to_check = ["uuid-ossp", "pg_trgm"]
            for ext in extensions_to_check:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM pg_extension WHERE extname = :ext"),
                    {"ext": ext}
                )
                exists = result.scalar() > 0
                print(f"  ✓ Extension '{ext}': {'installed' if exists else 'MISSING!'}")
            
            # Check sample data
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"\n  ✓ Total users in database: {user_count}")
            
            result = await session.execute(text("SELECT COUNT(*) FROM unified_travel_sessions"))
            session_count = result.scalar()
            print(f"  ✓ Total travel sessions: {session_count}")
            
            return True
            
        except Exception as e:
            print(f"Verification error: {e}")
            return False


async def main():
    """Main initialization function."""
    print("Pathavana Database Initialization")
    print("=" * 50)
    
    # Run migrations
    if not await run_migrations():
        print("\nFailed to run migrations. Please check the error messages above.")
        sys.exit(1)
    
    # Seed development data
    if os.getenv("ENVIRONMENT", "development") == "development":
        response = input("\nSeed development data? (y/N): ")
        if response.lower() == 'y':
            async with get_db_context() as session:
                await seed_development_data(session)
    
    # Verify setup
    if await verify_database():
        print("\n✅ Database initialization completed successfully!")
    else:
        print("\n❌ Database verification failed. Please check the setup.")
        sys.exit(1)
    
    # Close connections
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())