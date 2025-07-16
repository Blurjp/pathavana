#!/usr/bin/env python3
"""
Check which tables exist
"""
import asyncio
from app.core.database import engine
from sqlalchemy import text

async def check_tables():
    """Check tables in database"""
    async with engine.begin() as conn:
        try:
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            
            print("Tables in database:")
            print("-" * 40)
            for row in result:
                print(row[0])
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_tables())