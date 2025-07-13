#!/usr/bin/env python3
"""
Create Pathavana database schema directly
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Table, Text, Float, Date, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import os

# Create base
Base = declarative_base()

# Define core tables needed for the application
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class TravelSession(Base):
    __tablename__ = 'travel_sessions'
    
    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(255), nullable=False, index=True)
    status = Column(String(50), default='active', nullable=False)
    session_data = Column(Text, nullable=True)  # JSON data
    context_data = Column(Text, nullable=True)  # JSON data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Traveler(Base):
    __tablename__ = 'travelers'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    passport_number = Column(String(50), nullable=True)
    nationality = Column(String(2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Trip(Base):
    __tablename__ = 'trips'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(50), default='planning', nullable=False)
    budget = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

def create_database():
    """Create the database and all tables"""
    db_path = './pathavana_dev.db'
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    # Create engine
    engine = create_engine(
        f'sqlite:///{db_path}',
        echo=True,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    print("\nCreating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Verify tables
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ))
        tables = [row[0] for row in result]
        
        print(f"\nSuccessfully created {len(tables)} tables:")
        for table in tables:
            print(f"  ✓ {table}")
            
            # Show table structure
            result = conn.execute(text(f"PRAGMA table_info({table})"))
            columns = result.fetchall()
            for col in columns:
                print(f"    - {col[1]} ({col[2]})")
    
    print(f"\nDatabase created successfully at: {os.path.abspath(db_path)}")

if __name__ == "__main__":
    create_database()