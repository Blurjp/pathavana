#!/usr/bin/env python3
"""
Comprehensive backend testing script for Pathavana travel planning API.
Tests all major endpoints and functionality.
"""

import asyncio
import aiohttp
import json
import sys
import time
from typing import Dict, Any, Optional

# Test configuration
BASE_URL = "http://localhost:8001"
API_V1_STR = "/api/v1"


class PathavanaBackendTester:
    """Comprehensive tester for Pathavana backend API."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.test_session_id: Optional[str] = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "total": 0,
            "details": []
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def run_all_tests(self):
        """Run all backend tests."""
        print("🚀 Starting Pathavana Backend Tests")
        print("=" * 50)
        
        # Basic connectivity tests
        await self.test_health_check()
        await self.test_root_endpoint()
        await self.test_api_documentation()
        
        # Travel unified API tests
        await self.test_create_travel_session()
        await self.test_travel_chat_basic()
        await self.test_travel_chat_flight_search()
        await self.test_travel_chat_hotel_search()
        await self.test_get_session_state()
        await self.test_end_session()
        
        # Print results summary
        self.print_test_summary()
    
    async def test_health_check(self):
        """Test health check endpoint."""
        await self.run_test(
            "Health Check",
            self._make_request("GET", "/health"),
            lambda r: r.get("status") == "healthy"
        )
    
    async def test_root_endpoint(self):
        """Test root endpoint."""
        await self.run_test(
            "Root Endpoint",
            self._make_request("GET", "/"),
            lambda r: "Welcome to Pathavana" in r.get("message", "")
        )
    
    async def test_api_documentation(self):
        """Test API documentation accessibility."""
        await self.run_test(
            "API Documentation",
            self._make_request("GET", f"{API_V1_STR}/docs"),
            lambda r: True,  # Just check if it responds
            expect_json=False
        )
    
    async def test_create_travel_session(self):
        """Test creating a new travel session."""
        payload = {
            "user_id": None,
            "context": {
                "test_session": True
            }
        }
        
        result = await self.run_test(
            "Create Travel Session",
            self._make_request("POST", f"{API_V1_STR}/travel/session", json=payload),
            lambda r: "session_id" in r
        )
        
        if result and result.get("success"):
            self.test_session_id = result["response"].get("session_id")
    
    async def test_travel_chat_basic(self):
        """Test basic travel chat functionality."""
        if not self.test_session_id:
            await self.fail_test("Travel Chat Basic", "No session ID available")
            return
        
        payload = {
            "message": "Hello, I want to plan a trip",
            "session_id": self.test_session_id
        }
        
        await self.run_test(
            "Travel Chat Basic",
            self._make_request("POST", f"{API_V1_STR}/travel/chat", json=payload),
            lambda r: "response" in r and len(r.get("response", "")) > 0
        )
    
    async def test_travel_chat_flight_search(self):
        """Test flight search through chat."""
        if not self.test_session_id:
            await self.fail_test("Travel Chat Flight Search", "No session ID available")
            return
        
        payload = {
            "message": "I want to fly from New York to Paris on December 15th",
            "session_id": self.test_session_id
        }
        
        await self.run_test(
            "Travel Chat Flight Search",
            self._make_request("POST", f"{API_V1_STR}/travel/chat", json=payload),
            lambda r: "response" in r and "intent" in r
        )
    
    async def test_travel_chat_hotel_search(self):
        """Test hotel search through chat."""
        if not self.test_session_id:
            await self.fail_test("Travel Chat Hotel Search", "No session ID available")
            return
        
        payload = {
            "message": "Find me a hotel in Paris for 3 nights",
            "session_id": self.test_session_id
        }
        
        await self.run_test(
            "Travel Chat Hotel Search",
            self._make_request("POST", f"{API_V1_STR}/travel/chat", json=payload),
            lambda r: "response" in r
        )
    
    async def test_get_session_state(self):
        """Test getting session state."""
        if not self.test_session_id:
            await self.fail_test("Get Session State", "No session ID available")
            return
        
        await self.run_test(
            "Get Session State",
            self._make_request("GET", f"{API_V1_STR}/travel/session/{self.test_session_id}"),
            lambda r: "session_id" in r and "state" in r
        )
    
    async def test_end_session(self):
        """Test ending a travel session."""
        if not self.test_session_id:
            await self.fail_test("End Session", "No session ID available")
            return
        
        await self.run_test(
            "End Session",
            self._make_request("DELETE", f"{API_V1_STR}/travel/session/{self.test_session_id}"),
            lambda r: r.get("status") == "ended"
        )
    
    async def run_test(
        self, 
        test_name: str, 
        test_coroutine, 
        validation_func,
        expect_json: bool = True
    ):
        """Run a single test with error handling."""
        self.test_results["total"] += 1
        
        try:
            print(f"🧪 Testing: {test_name}")
            
            start_time = time.time()
            response = await test_coroutine
            duration = time.time() - start_time
            
            if expect_json and response is None:
                await self.fail_test(test_name, "No response received", duration)
                return
            
            if expect_json and not validation_func(response):
                await self.fail_test(test_name, f"Validation failed. Response: {response}", duration)
                return
            
            await self.pass_test(test_name, duration)
            return {"success": True, "response": response}
            
        except Exception as e:
            await self.fail_test(test_name, str(e))
            return {"success": False, "error": str(e)}
    
    async def pass_test(self, test_name: str, duration: float):
        """Mark test as passed."""
        self.test_results["passed"] += 1
        self.test_results["details"].append({
            "name": test_name,
            "status": "PASSED",
            "duration": f"{duration:.3f}s"
        })
        print(f"  ✅ PASSED ({duration:.3f}s)")
    
    async def fail_test(self, test_name: str, error: str, duration: float = 0):
        """Mark test as failed."""
        self.test_results["failed"] += 1
        self.test_results["details"].append({
            "name": test_name,
            "status": "FAILED",
            "error": error,
            "duration": f"{duration:.3f}s" if duration > 0 else "N/A"
        })
        print(f"  ❌ FAILED: {error}")
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"
        
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if headers:
            default_headers.update(headers)
        
        try:
            async with self.session.request(
                method, 
                url, 
                json=json, 
                headers=default_headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status >= 400:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
                
                # Try to parse JSON response
                try:
                    return await response.json()
                except:
                    # If not JSON, return text response for documentation endpoints
                    return {"text": await response.text()}
                
        except Exception as e:
            print(f"    Request failed: {e}")
            raise
    
    def print_test_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        total = self.test_results["total"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "0%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.test_results["details"]:
                if test["status"] == "FAILED":
                    print(f"  - {test['name']}: {test.get('error', 'Unknown error')}")
        
        print("\n📋 DETAILED RESULTS:")
        for test in self.test_results["details"]:
            status_icon = "✅" if test["status"] == "PASSED" else "❌"
            print(f"  {status_icon} {test['name']} ({test['duration']})")


async def main():
    """Main test runner."""
    try:
        async with PathavanaBackendTester() as tester:
            await tester.run_all_tests()
            
            # Exit with appropriate code
            if tester.test_results["failed"] > 0:
                sys.exit(1)
            else:
                print("\n🎉 All tests passed!")
                sys.exit(0)
                
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("Pathavana Backend Tester v1.0")
    print("Make sure the backend server is running on http://localhost:8001")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye! 👋")
        sys.exit(0)