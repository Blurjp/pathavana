"""
Initialize the database using synchronous SQLAlchemy
This is a temporary solution for initial database creation
"""
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from app.models import Base, model_metadata  # Import Base from models
from app.models import *  # Import all models to register them
from app.core.config import settings

def init_db():
    """Initialize database with all tables"""
    # Create synchronous engine for initial setup
    # Remove the async driver prefix
    sync_db_url = settings.DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://")
    
    engine = create_engine(
        sync_db_url,
        echo=True,
        connect_args={"check_same_thread": False}  # For SQLite
    )
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    
    # Show created tables
    print("\nCreated tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

if __name__ == "__main__":
    init_db()