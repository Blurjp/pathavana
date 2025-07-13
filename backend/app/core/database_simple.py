"""
Simple database configuration for development using SQLite.
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from .config import settings

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)

# Create sync engine for SQLite
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    connect_args={"check_same_thread": False}  # SQLite specific
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)