"""
Initialize SQLite database with proper type handling
"""
import sys
from pathlib import Path
import uuid

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, event, String
from sqlalchemy.dialects import sqlite
from sqlalchemy.types import TypeDecorator, CHAR

# Import models
from app.models import Base, model_metadata
from app.models import *  # Import all models to register them
from app.core.config import settings


# Custom UUID type for SQLite
class UUID(TypeDecorator):
    """Platform-independent UUID type for SQLite"""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(postgresql.UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


def init_db():
    """Initialize SQLite database with all tables"""
    # Create synchronous engine for initial setup
    sync_db_url = settings.DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://")
    
    engine = create_engine(
        sync_db_url,
        echo=True,
        connect_args={"check_same_thread": False}
    )
    
    # SQLite doesn't support JSONB, so we need to replace it with JSON
    # This is done automatically by SQLAlchemy when using JSONB on SQLite
    
    # Create all tables
    print("Creating database tables...")
    
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")
    
    # Show created tables
    print("\nCreated tables:")
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    for table in tables:
        print(f"  - {table}")
        
    # Show table counts
    with engine.connect() as conn:
        print("\nTable structure verification:")
        for table in tables:
            from sqlalchemy import text
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  - {table}: {count} rows")


if __name__ == "__main__":
    init_db()