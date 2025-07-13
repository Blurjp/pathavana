"""
Database session management for synchronous SQLite
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import os

# Get database URL from environment or use default
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./pathavana_dev.db')

# Convert async URL to sync if needed
if "sqlite+aiosqlite" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()