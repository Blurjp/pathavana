#!/usr/bin/env python
"""Verify test user can log in"""

import requests
import json

BASE_URL = "http://localhost:8001"
TEST_USER = {
    "email": "selenium.test@example.com",
    "password": "SeleniumTest123!"
}

def test_login():
    """Test login with the test user"""
    print("🔐 Testing login with Selenium test user...")
    
    # Try login
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if "access_token" in data:
            print("✅ Login successful!")
            print(f"Token: {data['access_token'][:20]}...")
            return True
        else:
            print("❌ No access token in response")
            print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ Login failed")
        print(f"Response: {response.text}")
    
    return False

if __name__ == "__main__":
    success = test_login()
    print("\n" + "="*60)
    print("TEST USER CREDENTIALS:")
    print(f"Email:    {TEST_USER['email']}")
    print(f"Password: {TEST_USER['password']}")
    print("="*60)
    
    if success:
        print("\n✅ Test user is ready for Selenium tests!")
    else:
        print("\n⚠️  Test user created but login verification failed")
        print("Check your authentication configuration")