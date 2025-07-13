"""
Explicitly create database tables
"""
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
os.environ['DATABASE_URL'] = 'sqlite:///./pathavana_dev.db'

from sqlalchemy import create_engine, MetaData
import app.models  # Import models module to ensure all models are loaded

def create_tables():
    """Create all database tables"""
    # Get the database URL
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///./pathavana_dev.db')
    
    # Create engine
    engine = create_engine(
        database_url,
        echo=True,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
    )
    
    print(f"Using database: {database_url}")
    print(f"Base object: {app.models.Base}")
    print(f"Metadata tables before creation: {list(app.models.Base.metadata.tables.keys())}")
    
    # Create all tables
    print("\nCreating tables...")
    app.models.Base.metadata.create_all(bind=engine)
    
    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\nTables in database: {tables}")
    print(f"Number of tables created: {len(tables)}")
    
    return tables

if __name__ == "__main__":
    tables = create_tables()