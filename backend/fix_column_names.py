#!/usr/bin/env python3
"""
Fix column name mismatch in travel_preferences table
"""
import asyncio
from app.core.database import engine
from sqlalchemy import text

async def fix_columns():
    """Rename columns to match the model"""
    async with engine.begin() as conn:
        try:
            # Check if the column exists with the wrong name
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='travel_preferences' 
                AND column_name IN ('preferred_airline', 'preferred_airlines')
            """))
            columns = [row[0] for row in result]
            
            if 'preferred_airline' in columns and 'preferred_airlines' not in columns:
                print("Found 'preferred_airline', renaming to 'preferred_airlines'...")
                await conn.execute(text("""
                    ALTER TABLE travel_preferences 
                    RENAME COLUMN preferred_airline TO preferred_airlines
                """))
                print("✅ Column renamed successfully")
            elif 'preferred_airlines' in columns:
                print("✅ Column 'preferred_airlines' already exists")
            else:
                print("❌ Neither column exists, might need to create it")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_columns())