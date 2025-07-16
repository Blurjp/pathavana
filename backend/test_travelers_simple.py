#!/usr/bin/env python
"""Simple test for traveler endpoints without auth"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_api_health():
    """Test if API is running"""
    print("🧪 Testing API Health")
    print("=" * 50)
    
    # Test root
    resp = requests.get(f"{BASE_URL}/")
    print(f"Root endpoint: {resp.status_code}")
    
    # Test docs
    resp = requests.get(f"{BASE_URL}/docs")
    print(f"Docs endpoint: {resp.status_code}")
    
    # Test health
    resp = requests.get(f"{BASE_URL}/health")
    print(f"Health endpoint: {resp.status_code}")
    print(f"Health response: {json.dumps(resp.json(), indent=2)}")

def test_traveler_endpoints():
    """Test traveler endpoints"""
    print("\n🧪 Testing Traveler Endpoints (No Auth)")
    print("=" * 50)
    
    # Test list travelers
    print("\n1. GET /api/v1/travelers/")
    resp = requests.get(f"{BASE_URL}/api/v1/travelers/")
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.text[:200]}...")
    
    # Test options
    print("\n2. OPTIONS /api/v1/travelers/")
    resp = requests.options(f"{BASE_URL}/api/v1/travelers/")
    print(f"   Status: {resp.status_code}")
    print(f"   Headers: {dict(resp.headers)}")

def test_user_profile():
    """Test user profile endpoint"""
    print("\n🧪 Testing User Profile Endpoint (No Auth)")
    print("=" * 50)
    
    print("\n1. GET /api/v1/users/profile")
    resp = requests.get(f"{BASE_URL}/api/v1/users/profile")
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.text[:200]}...")

if __name__ == "__main__":
    test_api_health()
    test_traveler_endpoints()
    test_user_profile()