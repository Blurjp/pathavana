#!/usr/bin/env python3
"""
Test the backend API to verify the New Chat functionality
"""
import requests
import json
from datetime import datetime

def test_create_session():
    """Test creating a new session via the backend API"""
    print("Testing New Chat API Endpoint")
    print("=" * 50)
    
    url = "http://localhost:8001/api/v1/travel/sessions"
    payload = {
        "message": "Hello, I want to plan a trip",
        "source": "web"
    }
    
    print(f"\n1. Sending POST request to {url}")
    print(f"   Payload: {json.dumps(payload)}")
    
    try:
        response = requests.post(url, json=payload)
        
        print(f"\n2. Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                print("   ✅ Success!")
                
                session_data = data.get("data", {})
                print(f"\n3. Session Created:")
                print(f"   - Session ID: {session_data.get('session_id')}")
                print(f"   - Status: {session_data.get('status')}")
                print(f"   - Initial Response: {session_data.get('initial_response', '')[:100]}...")
                
                metadata = session_data.get("metadata", {})
                if metadata.get("hints"):
                    print(f"   - Hints: {len(metadata['hints'])} hints provided")
                    for i, hint in enumerate(metadata['hints'][:3]):
                        print(f"     {i+1}. {hint.get('text', '')}")
                
                print(f"\n4. Frontend Implementation:")
                print("   The frontend should:")
                print("   a) Save this session_id to localStorage")
                print("   b) Create initial messages array with:")
                print("      - User message: 'Hello, I want to plan a trip'")
                print(f"      - Assistant message: '{session_data.get('initial_response', '')[:60]}...'")
                print("   c) Save messages to localStorage with key: pathavana_messages_{session_id}")
                print("   d) Display these messages in the chat UI")
                
                return True
            else:
                print(f"   ❌ API returned success=false: {data}")
                return False
        else:
            print(f"   ❌ HTTP Error {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection Error")
        print("   - Is the backend server running?")
        print("   - Try: cd backend && source venv/bin/activate && uvicorn app.main:app --port 8001")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected Error: {type(e).__name__}: {e}")
        return False

def test_get_session(session_id):
    """Test retrieving a session"""
    print(f"\n5. Testing Session Retrieval")
    url = f"http://localhost:8001/api/v1/travel/sessions/{session_id}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("   ✅ Session retrieved successfully")
                session_data = data.get("data", {})
                messages = session_data.get("session_data", {}).get("conversation_history", [])
                print(f"   - Conversation history: {len(messages)} messages")
                return True
            else:
                print(f"   ❌ Failed to retrieve session: {data}")
                return False
        else:
            print(f"   ❌ HTTP Error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test session creation
    if test_create_session():
        print("\n✅ Backend API is working correctly!")
        print("\nNext steps:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Click the 'New Chat' button")
        print("3. You should see the initial conversation appear")
    else:
        print("\n❌ Backend API test failed")
        print("\nTroubleshooting:")
        print("1. Check if backend is running: ps aux | grep uvicorn")
        print("2. Check backend logs for errors")
        print("3. Verify the backend is on port 8001")