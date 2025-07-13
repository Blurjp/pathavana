"""
Initialize database with tables and initial data
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import engine, Base, get_db
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_tables():
    """Create all tables in the database"""
    async with engine.begin() as conn:
        # Drop all tables for clean setup (remove in production!)
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created successfully")

async def init_db():
    """Initialize database with tables and initial data"""
    try:
        logger.info("🔧 Initializing database...")
        
        # Create tables
        await create_tables()
        
        # You can add initial data here if needed
        # async for session in get_db():
        #     # Create admin user, etc.
        #     pass
        
        logger.info("✅ Database initialization completed")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())