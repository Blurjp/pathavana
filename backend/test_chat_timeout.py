#!/usr/bin/env python3
"""Test chat endpoint to debug timeout issue."""

import asyncio
import requests
import json

def test_chat_endpoint():
    """Test the chat endpoint with a travel planning request."""
    print("🧪 Testing Chat Endpoint")
    print("=" * 60)
    
    # First, let's login with the test account
    print("\n1️⃣ Logging in...")
    login_url = "http://localhost:8001/api/v1/auth/login"
    login_data = {
        "email": "selenium.test@example.com",
        "password": "SeleniumTest123!"
    }
    
    login_response = requests.post(login_url, json=login_data)
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print(f"✅ Login successful, token: {token[:20]}...")
    
    # Create a new session
    print("\n2️⃣ Creating travel session...")
    session_url = "http://localhost:8001/api/v1/travel/sessions"
    session_data = {
        "message": "I want to plan a 5-day trip to Paris next month with flights, hotels, and activities",
        "source": "web",
        "metadata": {}
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    session_response = requests.post(session_url, json=session_data, headers=headers)
    
    if session_response.status_code != 201:
        print(f"❌ Session creation failed: {session_response.status_code}")
        print(f"Response: {session_response.text}")
        return
    
    session_id = session_response.json()["data"]["session_id"]
    print(f"✅ Session created: {session_id}")
    
    # Send a chat message
    print("\n3️⃣ Sending chat message...")
    chat_url = f"http://localhost:8001/api/v1/travel/sessions/{session_id}/chat"
    chat_data = {
        "message": "I want to plan a 5-day trip to Paris next month with flights, hotels, and activities",
        "metadata": {}
    }
    
    try:
        # Set a reasonable timeout
        chat_response = requests.post(chat_url, json=chat_data, headers=headers, timeout=30)
        
        if chat_response.status_code == 200:
            result = chat_response.json()
            print(f"✅ Chat response received!")
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('data', {}).get('message', '')[:100]}...")
            if "error" in result:
                print(f"⚠️  Error in response: {result['error']}")
        else:
            print(f"❌ Chat failed: {chat_response.status_code}")
            print(f"Response: {chat_response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
        print("This indicates the AI processing is taking too long or hanging")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print("\n" + "=" * 60)
    print("📋 Debug Summary:")
    print("- If timeout: Check LLM configuration and API keys")
    print("- If error: Check backend logs for detailed error messages")
    print("- Run: tail -f logs/app.log")

if __name__ == "__main__":
    test_chat_endpoint()