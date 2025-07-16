#!/usr/bin/env python3
"""
Create travelers table
"""
import asyncio
from app.core.database import engine
from sqlalchemy import text

async def create_table():
    """Create travelers table"""
    async with engine.begin() as conn:
        try:
            # Create travelers table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS travelers (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    middle_name VARCHAR(100),
                    full_name VARCHAR(300),
                    date_of_birth DATE,
                    gender VARCHAR(20),
                    nationality VARCHAR(2),
                    country_of_residence VARCHAR(2),
                    email VARCHAR(255),
                    phone VARCHAR(50),
                    emergency_contact_name VARCHAR(200),
                    emergency_contact_phone VARCHAR(50),
                    relationship_to_user VARCHAR(50),
                    traveler_type VARCHAR(20),
                    passport_verified BOOLEAN DEFAULT FALSE,
                    document_status VARCHAR(50),
                    dietary_restrictions JSONB,
                    accessibility_needs JSONB,
                    medical_conditions JSONB,
                    frequent_flyer_numbers JSONB,
                    hotel_loyalty_numbers JSONB,
                    known_traveler_numbers JSONB,
                    preferences JSONB,
                    notes TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """))
            
            # Create indexes
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_travelers_user_id ON travelers(user_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_travelers_is_active ON travelers(is_active)"))
            
            print("✅ Travelers table created successfully")
            
        except Exception as e:
            print(f"❌ Error creating table: {e}")

if __name__ == "__main__":
    asyncio.run(create_table())