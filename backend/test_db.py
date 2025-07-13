#!/usr/bin/env python3
"""
Test database connectivity and operations
"""
import sys
sys.path.insert(0, '.')

from app.db.session import get_db
from sqlalchemy import text
import json

def test_database():
    """Test basic database operations"""
    print("Testing database connectivity...\n")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Test 1: Check tables exist
        print("1. Checking tables...")
        cursor = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in cursor.fetchall()]
        print(f"   Found {len(tables)} tables: {', '.join(tables)}")
        
        # Test 2: Insert test data
        print("\n2. Inserting test data...")
        
        # Insert a test user
        db.execute(text("""
            INSERT INTO users (email, password_hash, full_name, is_active, is_admin, created_at)
            VALUES ('test@example.com', 'hashed_password', 'Test User', 1, 0, datetime('now'))
        """))
        db.commit()
        print("   ✓ Created test user")
        
        # Insert a test trip
        db.execute(text("""
            INSERT INTO trips (user_id, title, destination, start_date, end_date, status, budget, created_at)
            VALUES (1, 'Test Trip to Paris', 'Paris, France', '2024-08-15', '2024-08-22', 'planning', 3000.0, datetime('now'))
        """))
        db.commit()
        print("   ✓ Created test trip")
        
        # Insert a test traveler
        db.execute(text("""
            INSERT INTO travelers (user_id, first_name, last_name, email, created_at)
            VALUES (1, 'John', 'Doe', 'john.doe@example.com', datetime('now'))
        """))
        db.commit()
        print("   ✓ Created test traveler")
        
        # Test 3: Query data
        print("\n3. Querying data...")
        
        # Query trips
        cursor = db.execute(text("SELECT * FROM trips"))
        trips = cursor.fetchall()
        print(f"   Found {len(trips)} trips")
        for trip in trips:
            print(f"     - {trip[2]} to {trip[3]}")
        
        # Query travelers
        cursor = db.execute(text("SELECT * FROM travelers"))
        travelers = cursor.fetchall()
        print(f"   Found {len(travelers)} travelers")
        for traveler in travelers:
            print(f"     - {traveler[2]} {traveler[3]}")
        
        # Test 4: Travel sessions
        print("\n4. Testing travel sessions...")
        session_data = {
            "messages": [{"role": "user", "content": "I want to plan a trip", "timestamp": "2024-07-12T00:00:00Z"}]
        }
        db.execute(text("""
            INSERT INTO travel_sessions (id, user_id, status, session_data, context_data, created_at)
            VALUES ('test-session-123', 'test-user', 'active', :session_data, '{}', datetime('now'))
        """), {"session_data": json.dumps(session_data)})
        db.commit()
        print("   ✓ Created test session")
        
        # Query session
        cursor = db.execute(text("SELECT * FROM travel_sessions WHERE id = 'test-session-123'"))
        session = cursor.fetchone()
        if session:
            print(f"   ✓ Retrieved session: {session[0]}")
            session_data = json.loads(session[3])
            print(f"     Messages: {len(session_data.get('messages', []))}")
        
        print("\n✅ All database tests passed!")
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_database()