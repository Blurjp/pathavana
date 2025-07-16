#!/usr/bin/env python3
"""
Check which columns exist in travel_preferences table
"""
import asyncio
from app.core.database import engine
from sqlalchemy import text

async def check_columns():
    """Check columns in travel_preferences table"""
    async with engine.begin() as conn:
        try:
            result = await conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name='travel_preferences'
                ORDER BY ordinal_position
            """))
            
            print("Columns in travel_preferences table:")
            print("-" * 40)
            for row in result:
                print(f"{row[0]:<30} {row[1]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_columns())