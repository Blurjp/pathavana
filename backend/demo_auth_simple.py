#!/usr/bin/env python3
"""
Demo authentication functionality - simplified version
"""
import sys
sys.path.insert(0, '.')

from app.db.session import get_db
from sqlalchemy import text
import json
import hashlib
import base64
from datetime import datetime, timedelta
import uuid

# Simple password hashing
def hash_password(password: str) -> str:
    """Simple password hashing"""
    salt = "pathavana_salt_2024"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict):
    """Create simple JWT-like token"""
    expire = datetime.utcnow() + timedelta(hours=24)
    
    token_data = {
        **data,
        "exp": expire.isoformat(),
        "iat": datetime.utcnow().isoformat()
    }
    
    # Simple token: base64 encode the JSON data
    token_json = json.dumps(token_data)
    token_bytes = token_json.encode('utf-8')
    token = base64.b64encode(token_bytes).decode('utf-8')
    
    # Add a simple signature
    secret = "your-secret-key-here"
    signature = hashlib.sha256(f"{token}{secret}".encode()).hexdigest()[:16]
    return f"{token}.{signature}"

def decode_token(token: str):
    """Decode and verify simple token"""
    try:
        # Split token and signature
        if "." not in token:
            return None
            
        token_part, signature = token.rsplit(".", 1)
        
        # Verify signature
        secret = "your-secret-key-here"
        expected_signature = hashlib.sha256(f"{token_part}{secret}".encode()).hexdigest()[:16]
        if signature != expected_signature:
            return None
        
        # Decode token
        token_json = base64.b64decode(token_part).decode('utf-8')
        token_data = json.loads(token_json)
        
        # Check expiration
        exp = datetime.fromisoformat(token_data.get("exp", ""))
        if datetime.utcnow() > exp:
            return None
        
        return token_data
    except Exception:
        return None

def demo_auth_flow():
    """Demonstrate authentication flow"""
    print("=== Authentication Demo ===\n")
    
    # Get database session
    db = next(get_db())
    
    try:
        # 1. Create a test user (signup)
        print("1. SIGNUP - Creating a new user...")
        test_email = "demo@example.com"
        test_password = "DemoPass123"
        test_name = "Demo User"
        
        # Check if user exists
        existing = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": test_email}
        ).fetchone()
        
        if existing:
            print(f"   User {test_email} already exists, deleting for fresh demo...")
            db.execute(text("DELETE FROM users WHERE email = :email"), {"email": test_email})
            db.commit()
        
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
        print(f"   ✓ User signed up successfully!")
        print(f"     Email: {test_email}")
        print(f"     Name: {test_name}")
        print(f"     User ID: {user_id}")
        
        # 2. Test signin
        print("\n2. SIGNIN - Authenticating user...")
        
        # Get user from database
        result = db.execute(
            text("SELECT id, email, password_hash, full_name FROM users WHERE email = :email"),
            {"email": test_email}
        ).fetchone()
        
        if result and verify_password(test_password, result[2]):
            print("   ✓ Password verified successfully!")
            
            # Create access token
            token = create_access_token({
                "sub": str(result[0]),
                "email": result[1],
                "full_name": result[3]
            })
            print(f"   ✓ Access token generated:")
            print(f"     {token[:50]}...")
        else:
            print("   ❌ Invalid credentials")
            return
        
        # 3. Use token to access protected resources
        print("\n3. ACCESSING PROTECTED RESOURCES...")
        
        # Decode token to get user info
        payload = decode_token(token)
        if not payload:
            print("   ❌ Invalid token")
            return
        
        auth_user_id = int(payload['sub'])
        print(f"   ✓ Token validated for user ID: {auth_user_id}")
        
        # Create some test data
        print("\n4. CREATING USER-SPECIFIC DATA...")
        
        # Create a trip
        cursor = db.execute(
            text("""
                INSERT INTO trips (user_id, title, destination, start_date, end_date, status, created_at)
                VALUES (:user_id, :title, :destination, :start_date, :end_date, :status, datetime('now'))
            """),
            {
                "user_id": auth_user_id,
                "title": "Tokyo Adventure",
                "destination": "Tokyo, Japan",
                "start_date": "2024-09-01",
                "end_date": "2024-09-07",
                "status": "planning"
            }
        )
        db.commit()
        trip_id = cursor.lastrowid
        print(f"   ✓ Created trip: Tokyo Adventure (ID: {trip_id})")
        
        # Create a traveler
        cursor = db.execute(
            text("""
                INSERT INTO travelers (user_id, first_name, last_name, email, created_at)
                VALUES (:user_id, :first_name, :last_name, :email, datetime('now'))
            """),
            {
                "user_id": auth_user_id,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com"
            }
        )
        db.commit()
        traveler_id = cursor.lastrowid
        print(f"   ✓ Created traveler: John Doe (ID: {traveler_id})")
        
        # Create a travel session
        session_id = str(uuid.uuid4())
        session_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "I want to plan a trip to Tokyo",
                    "timestamp": datetime.utcnow().isoformat()
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
                "user_id": str(auth_user_id),
                "status": "active",
                "session_data": json.dumps(session_data),
                "context_data": "{}"
            }
        )
        db.commit()
        print(f"   ✓ Created travel session: {session_id[:8]}...")
        
        # 5. Demonstrate access control
        print("\n5. DEMONSTRATING ACCESS CONTROL...")
        
        # Try to access data without user filter (simulating no auth)
        all_trips = db.execute(text("SELECT COUNT(*) FROM trips")).fetchone()[0]
        print(f"   Total trips in database: {all_trips}")
        
        # Access data with user filter (simulating authenticated access)
        user_trips = db.execute(
            text("SELECT COUNT(*) FROM trips WHERE user_id = :user_id"),
            {"user_id": auth_user_id}
        ).fetchone()[0]
        print(f"   Trips accessible to authenticated user: {user_trips}")
        
        # Try to access another user's data
        other_user_trips = db.execute(
            text("SELECT COUNT(*) FROM trips WHERE user_id = :user_id"),
            {"user_id": 99999}  # Non-existent user
        ).fetchone()[0]
        print(f"   Trips accessible to other user: {other_user_trips}")
        
        print("\n✅ Authentication Demo Completed!")
        print("\nKey Features Demonstrated:")
        print("1. User signup with email/password")
        print("2. Password hashing for security")
        print("3. User signin with credential verification")
        print("4. JWT-like token generation")
        print("5. Token-based authentication")
        print("6. User-specific data isolation")
        print("7. Access control - users can only see their own data")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    demo_auth_flow()