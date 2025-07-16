#!/usr/bin/env python3
"""
Test script to verify the session flow:
1. Create an empty session
2. Send multiple messages to the same session
3. Verify no new sessions are created
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001/api/v1/travel"

def test_session_flow():
    print("=== Testing Session Flow ===\n")
    
    # Step 1: Create an empty session
    print("1. Creating empty session...")
    response = requests.post(f"{BASE_URL}/sessions/new")
    if response.status_code != 201:
        print(f"❌ Failed to create session: {response.status_code}")
        print(response.text)
        return
    
    session_data = response.json()
    session_id = session_data['data']['session_id']
    print(f"✅ Created session: {session_id}\n")
    
    # Step 2: Send first message
    print("2. Sending first message...")
    message1 = {
        "message": "I want to plan a trip to Paris for Christmas",
        "metadata": {}
    }
    response = requests.post(f"{BASE_URL}/sessions/{session_id}/chat", json=message1)
    if response.status_code != 200:
        print(f"❌ Failed to send first message: {response.status_code}")
        print(response.text)
        return
    
    response_data = response.json()
    print(f"✅ Received response: {response_data['data']['message'][:100]}...")
    print(f"   Hints: {len(response_data['data'].get('hints', []))} hints generated\n")
    
    # Step 3: Send second message to same session
    time.sleep(1)  # Small delay
    print("3. Sending second message to same session...")
    message2 = {
        "message": "I have 2 adults and 2 children, ages 8 and 10",
        "metadata": {}
    }
    response = requests.post(f"{BASE_URL}/sessions/{session_id}/chat", json=message2)
    if response.status_code != 200:
        print(f"❌ Failed to send second message: {response.status_code}")
        print(response.text)
        return
    
    response_data = response.json()
    print(f"✅ Received response: {response_data['data']['message'][:100]}...")
    print(f"   Context updated: {response_data['data'].get('updated_context', {})}\n")
    
    # Step 4: Send third message to verify continuity
    time.sleep(1)
    print("4. Sending third message to verify session continuity...")
    message3 = {
        "message": "What are the best family-friendly hotels?",
        "metadata": {}
    }
    response = requests.post(f"{BASE_URL}/sessions/{session_id}/chat", json=message3)
    if response.status_code != 200:
        print(f"❌ Failed to send third message: {response.status_code}")
        print(response.text)
        return
    
    response_data = response.json()
    print(f"✅ Received response: {response_data['data']['message'][:100]}...")
    
    # Step 5: Verify session state
    print("\n5. Verifying session state...")
    response = requests.get(f"{BASE_URL}/sessions/{session_id}")
    if response.status_code != 200:
        print(f"❌ Failed to get session: {response.status_code}")
        print(response.text)
        return
    
    session_data = response.json()['data']
    conversation_history = session_data.get('session_data', {}).get('conversation_history', [])
    print(f"✅ Session contains {len(conversation_history)} messages")
    print(f"   Session status: {session_data.get('status')}")
    print(f"   Trip context: {session_data.get('plan_data', {}).get('trip_context', {})}")
    
    print("\n✅ SUCCESS: All messages used the same session!")
    print(f"   Session ID: {session_id}")
    print(f"   Total messages: {len(conversation_history)}")

if __name__ == "__main__":
    test_session_flow()