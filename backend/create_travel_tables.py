#!/usr/bin/env python3
"""
Create UnifiedTravelSession tables directly in the database.
"""
import asyncio
from sqlalchemy import text
from app.core.database import get_db_context, engine
from app.models import Base

async def create_tables():
    """Create the unified travel session tables."""
    async with get_db_context() as db:
        try:
            # Create unified_travel_sessions table
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS unified_travel_sessions (
                    session_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
                    user_id INTEGER REFERENCES users(id),
                    status VARCHAR(20) DEFAULT 'active' NOT NULL,
                    session_data JSONB DEFAULT '{}',
                    plan_data JSONB,
                    session_metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))
            print("✓ Created unified_travel_sessions table")
            
            # Create indexes
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_sessions_created 
                ON unified_travel_sessions(user_id, created_at)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_session_status_activity 
                ON unified_travel_sessions(status, last_activity_at)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_session_data_gin 
                ON unified_travel_sessions USING GIN (session_data)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_plan_data_gin 
                ON unified_travel_sessions USING GIN (plan_data)
            """))
            print("✓ Created indexes for unified_travel_sessions")
            
            # Create unified_saved_items table
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS unified_saved_items (
                    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                    session_id VARCHAR(36) REFERENCES unified_travel_sessions(session_id) ON DELETE CASCADE,
                    item_type VARCHAR(50) NOT NULL,
                    provider VARCHAR(100),
                    external_id VARCHAR(255),
                    item_data JSONB NOT NULL,
                    booking_data JSONB,
                    user_notes VARCHAR(1000),
                    assigned_day INTEGER,
                    sort_order INTEGER,
                    is_booked BOOLEAN DEFAULT FALSE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))
            print("✓ Created unified_saved_items table")
            
            # Create indexes for unified_saved_items
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_saved_items_session_type 
                ON unified_saved_items(session_id, item_type)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_saved_items_day_order 
                ON unified_saved_items(session_id, assigned_day, sort_order)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_saved_items_provider 
                ON unified_saved_items(provider, external_id)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_saved_items_data_gin 
                ON unified_saved_items USING GIN (item_data)
            """))
            print("✓ Created indexes for unified_saved_items")
            
            # Create unified_session_bookings table
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS unified_session_bookings (
                    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                    session_id VARCHAR(36) REFERENCES unified_travel_sessions(session_id) ON DELETE CASCADE,
                    booking_type VARCHAR(50) NOT NULL,
                    provider VARCHAR(100) NOT NULL,
                    provider_booking_id VARCHAR(255) NOT NULL,
                    confirmation_code VARCHAR(100),
                    booking_status VARCHAR(50) DEFAULT 'pending' NOT NULL,
                    total_amount INTEGER,
                    currency VARCHAR(3),
                    payment_status VARCHAR(50),
                    booking_data JSONB NOT NULL,
                    traveler_data JSONB,
                    payment_data JSONB,
                    booking_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    travel_date TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))
            print("✓ Created unified_session_bookings table")
            
            # Create indexes for unified_session_bookings
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bookings_session_type 
                ON unified_session_bookings(session_id, booking_type)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bookings_provider 
                ON unified_session_bookings(provider, provider_booking_id)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bookings_status 
                ON unified_session_bookings(booking_status, booking_date)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bookings_travel_date 
                ON unified_session_bookings(travel_date)
            """))
            
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bookings_data_gin 
                ON unified_session_bookings USING GIN (booking_data)
            """))
            print("✓ Created indexes for unified_session_bookings")
            
            await db.commit()
            print("\n✅ All travel session tables created successfully!")
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            await db.rollback()
            raise
    
    # Verify tables were created
    async with get_db_context() as db:
        result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('unified_travel_sessions', 'unified_saved_items', 'unified_session_bookings')
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        print(f"\nVerified tables exist: {tables}")

if __name__ == "__main__":
    asyncio.run(create_tables())