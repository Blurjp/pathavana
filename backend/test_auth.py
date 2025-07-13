#!/usr/bin/env python3
"""
Test authentication flow - signup, signin, and protected endpoints
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def test_auth_flow():
    """Test complete authentication flow"""
    print("Testing Authentication Flow\n")
    
    # Test data
    test_user = {
        "email": "testuser@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    
    # 1. Test signup
    print("1. Testing Signup...")
    response = requests.post(f"{BASE_URL}/auth/signup", json=test_user)
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        print(f"   ✓ Signup successful")
        print(f"   ✓ Token received: {token[:20]}...")
        print(f"   ✓ User ID: {data['user']['id']}")
    elif response.status_code == 400:
        print("   ℹ️  User already exists, trying signin...")
        token = None
    else:
        print(f"   ❌ Signup failed: {response.status_code} - {response.text}")
        return
    
    # 2. Test signin
    print("\n2. Testing Signin...")
    signin_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    response = requests.post(f"{BASE_URL}/auth/signin", json=signin_data)
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        user_id = data["user"]["id"]
        print(f"   ✓ Signin successful")
        print(f"   ✓ Token received: {token[:20]}...")
        print(f"   ✓ User: {data['user']['full_name']} ({data['user']['email']})")
    else:
        print(f"   ❌ Signin failed: {response.status_code} - {response.text}")
        return
    
    # Create headers with auth token
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Test get current user
    print("\n3. Testing Get Current User...")
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Current user retrieved")
        print(f"   ✓ User: {data['full_name']} (ID: {data['id']})")
    else:
        print(f"   ❌ Get user failed: {response.status_code} - {response.text}")
    
    # 4. Test accessing protected endpoints without token
    print("\n4. Testing Protected Endpoints Without Token...")
    response = requests.get(f"{BASE_URL}/trips")
    if response.status_code == 403 or response.status_code == 401:
        print(f"   ✓ Correctly blocked unauthorized access (status: {response.status_code})")
    else:
        print(f"   ❌ Security issue - endpoint accessible without auth: {response.status_code}")
    
    # 5. Test accessing protected endpoints with token
    print("\n5. Testing Protected Endpoints With Token...")
    
    # Test trips
    response = requests.get(f"{BASE_URL}/trips", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Trips endpoint accessible with auth")
        print(f"   ✓ Found {len(data)} trips")
    else:
        print(f"   ❌ Trips access failed: {response.status_code} - {response.text}")
    
    # Test travelers
    response = requests.get(f"{BASE_URL}/travelers", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Travelers endpoint accessible with auth")
        print(f"   ✓ Found {len(data)} travelers")
    else:
        print(f"   ❌ Travelers access failed: {response.status_code} - {response.text}")
    
    # 6. Test creating a travel session
    print("\n6. Testing Travel Session Creation...")
    session_data = {
        "message": "I want to plan a trip to Paris",
        "source": "test"
    }
    response = requests.post(f"{BASE_URL}/travel/sessions", json=session_data, headers=headers)
    if response.status_code == 200:
        data = response.json()
        session_id = data["data"]["session_id"]
        print(f"   ✓ Travel session created")
        print(f"   ✓ Session ID: {session_id}")
        
        # Test updating session
        update_data = {
            "message": "I want to go in August",
            "source": "test"
        }
        response = requests.put(f"{BASE_URL}/travel/sessions/{session_id}", json=update_data, headers=headers)
        if response.status_code == 200:
            print(f"   ✓ Travel session updated successfully")
        else:
            print(f"   ❌ Session update failed: {response.status_code}")
    else:
        print(f"   ❌ Session creation failed: {response.status_code} - {response.text}")
    
    # 7. Test creating a trip
    print("\n7. Testing Trip Creation...")
    trip_data = {
        "title": "Summer Vacation",
        "destination": "Paris, France",
        "start_date": "2024-08-15",
        "end_date": "2024-08-22",
        "status": "planning",
        "budget": 3000.0,
        "notes": "Family trip to Paris"
    }
    response = requests.post(f"{BASE_URL}/trips", json=trip_data, headers=headers)
    if response.status_code == 200:
        data = response.json()
        trip_id = data["id"]
        print(f"   ✓ Trip created successfully")
        print(f"   ✓ Trip ID: {trip_id}")
        
        # Test getting the trip
        response = requests.get(f"{BASE_URL}/trips/{trip_id}", headers=headers)
        if response.status_code == 200:
            print(f"   ✓ Trip retrieved successfully")
        else:
            print(f"   ❌ Trip retrieval failed: {response.status_code}")
    else:
        print(f"   ❌ Trip creation failed: {response.status_code} - {response.text}")
    
    print("\n✅ Authentication flow test completed!")

if __name__ == "__main__":
    try:
        test_auth_flow()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the backend is running on http://localhost:8000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)