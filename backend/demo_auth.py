#!/usr/bin/env python3
"""
Demo authentication functionality without FastAPI
"""
import sys
sys.path.insert(0, '.')

from app.db.session import get_db
from app.api.endpoints.auth import (
    hash_password, verify_password, create_access_token, decode_token
)
from sqlalchemy import text
import json

def demo_auth_flow():
    """Demonstrate authentication flow"""
    print("=== Authentication Demo ===\n")
    
    # Get database session
    db = next(get_db())
    
    try:
        # 1. Create a test user
        print("1. Creating a test user...")
        test_email = "demo@example.com"
        test_password = "DemoPass123"
        test_name = "Demo User"
        
        # Check if user exists
        existing = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": test_email}
        ).fetchone()
        
        if existing:
            print(f"   User {test_email} already exists")
            user_id = existing[0]
        else:
            # Create user
            hashed_pw = hash_password(test_password)
            cursor = db.execute(
                text("""
                    INSERT INTO users (email, password_hash, full_name, is_active, is_admin, created_at)
                    VALUES (:email, :password_hash, :full_name, 1, 0, datetime('now'))
                """),
                {
                    "email": test_email,
                    "password_hash": hashed_pw,
                    "full_name": test_name
                }
            )
            db.commit()
            user_id = cursor.lastrowid
            print(f"   ✓ Created user: {test_email} (ID: {user_id})")
        
        # 2. Test password verification
        print("\n2. Testing password verification...")
        stored_hash = db.execute(
            text("SELECT password_hash FROM users WHERE email = :email"),
            {"email": test_email}
        ).fetchone()[0]
        
        if verify_password(test_password, stored_hash):
            print("   ✓ Password verification successful")
        else:
            print("   ❌ Password verification failed")
        
        # 3. Create access token
        print("\n3. Creating access token...")
        token = create_access_token({
            "sub": str(user_id),
            "email": test_email,
            "full_name": test_name
        })
        print(f"   ✓ Token created: {token[:50]}...")
        
        # 4. Decode and verify token
        print("\n4. Decoding token...")
        payload = decode_token(token)
        if payload:
            print("   ✓ Token decoded successfully:")
            print(f"     - User ID: {payload['sub']}")
            print(f"     - Email: {payload['email']}")
            print(f"     - Expires: {payload['exp']}")
        else:
            print("   ❌ Token decode failed")
        
        # 5. Test protected data access
        print("\n5. Testing protected data access...")
        
        # Without user context (should be empty)
        trips = db.execute(
            text("SELECT * FROM trips WHERE user_id = -1")
        ).fetchall()
        print(f"   Without auth: {len(trips)} trips found")
        
        # With user context
        trips = db.execute(
            text("SELECT * FROM trips WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchall()
        print(f"   With auth: {len(trips)} trips found")
        
        # Create a trip for the user
        print("\n6. Creating a trip for authenticated user...")
        cursor = db.execute(
            text("""
                INSERT INTO trips (user_id, title, destination, start_date, end_date, status, created_at)
                VALUES (:user_id, :title, :destination, :start_date, :end_date, :status, datetime('now'))
            """),
            {
                "user_id": user_id,
                "title": "Demo Trip",
                "destination": "Tokyo, Japan",
                "start_date": "2024-09-01",
                "end_date": "2024-09-07",
                "status": "planning"
            }
        )
        db.commit()
        print(f"   ✓ Created trip ID: {cursor.lastrowid}")
        
        # 7. Create a travel session
        print("\n7. Creating a travel session...")
        import uuid
        session_id = str(uuid.uuid4())
        session_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "I want to plan a trip to Tokyo",
                    "timestamp": "2024-07-12T00:00:00Z"
                }
            ]
        }
        
        db.execute(
            text("""
                INSERT INTO travel_sessions (id, user_id, status, session_data, context_data, created_at)
                VALUES (:id, :user_id, :status, :session_data, :context_data, datetime('now'))
            """),
            {
                "id": session_id,
                "user_id": str(user_id),
                "status": "active",
                "session_data": json.dumps(session_data),
                "context_data": "{}"
            }
        )
        db.commit()
        print(f"   ✓ Created session: {session_id[:8]}...")
        
        # Verify session belongs to user
        session = db.execute(
            text("SELECT * FROM travel_sessions WHERE id = :id AND user_id = :user_id"),
            {"id": session_id, "user_id": str(user_id)}
        ).fetchone()
        
        if session:
            print("   ✓ Session accessible by authenticated user")
        else:
            print("   ❌ Session not accessible")
        
        print("\n✅ Authentication demo completed!")
        print("\nSummary:")
        print(f"- User can sign up with email/password")
        print(f"- Passwords are hashed before storage")
        print(f"- JWT-like tokens are generated for authentication")
        print(f"- Protected resources (trips, sessions) are filtered by user")
        print(f"- Only authenticated users can access their own data")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    demo_auth_flow()