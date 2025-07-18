#!/usr/bin/env python3
"""Test trip plan creation through chat API."""

import asyncio
import requests
import json

def test_trip_plan_creation():
    """Test creating a trip plan through the chat API."""
    print("🧪 Testing Trip Plan Creation")
    print("=" * 60)
    
    # Login first
    print("\n1️⃣ Logging in...")
    login_url = "http://localhost:8001/api/v1/auth/login"
    login_data = {
        "email": "selenium.test@example.com",
        "password": "SeleniumTest123!"
    }
    
    login_response = requests.post(login_url, json=login_data)
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Logged in successfully")
    
    # Create session with travel request
    print("\n2️⃣ Creating session with travel request...")
    session_url = "http://localhost:8001/api/v1/travel/sessions"
    session_data = {
        "message": "I want to travel to Tokyo for 5 days next month. My budget is $3000. Please create a trip plan with flights from San Francisco, hotels in Shibuya, and daily activities.",
        "source": "web",
        "metadata": {}
    }
    
    session_response = requests.post(session_url, json=session_data, headers=headers)
    if session_response.status_code != 201:
        print(f"❌ Session creation failed: {session_response.status_code}")
        print(f"Response: {session_response.text}")
        return
    
    result = session_response.json()
    session_id = result["data"]["session_id"]
    print(f"✅ Session created: {session_id}")
    
    # Check the response
    print("\n3️⃣ Checking initial response...")
    print(f"Initial message: {result['data'].get('initial_response', 'No response')[:200]}...")
    print(f"Trip context: {result['data'].get('trip_context', {})}")
    
    # Wait a bit for processing
    import time
    time.sleep(2)
    
    # Get session details
    print("\n4️⃣ Getting session details...")
    get_url = f"http://localhost:8001/api/v1/travel/sessions/{session_id}"
    get_response = requests.get(get_url, headers=headers)
    
    if get_response.status_code == 200:
        response_json = get_response.json()
        session_data = response_json.get("data")
        if session_data:
            print(f"Session status: {session_data.get('status')}")
            print(f"Plan data: {json.dumps(session_data.get('plan_data', {}), indent=2)}")
            print(f"Session data: {json.dumps(session_data.get('session_data', {}), indent=2)}")
        else:
            print(f"Response: {response_json}")
        
        # Check if trip plan exists
        if session_data and session_data.get('plan_data', {}).get('trip_context'):
            print("\n✅ Trip context found in plan_data!")
            trip_context = session_data['plan_data']['trip_context']
            print(f"Destination: {trip_context.get('destination')}")
            print(f"Duration: {trip_context.get('duration')}")
            print(f"Budget: {trip_context.get('budget')}")
        else:
            print("\n❌ No trip context found in plan_data!")
    else:
        print(f"❌ Failed to get session: {get_response.status_code}")
    
    print("\n" + "=" * 60)
    print("📋 Summary:")
    print("- If trip context is empty, the AI is not extracting trip details")
    print("- If initial response is generic, the orchestrator might not be processing correctly")
    print("- Check backend logs for more details")

if __name__ == "__main__":
    test_trip_plan_creation()