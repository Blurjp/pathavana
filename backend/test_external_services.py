#!/usr/bin/env python3
"""
Test script for external API service integrations.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.amadeus_service import AmadeusService, AmadeusEnvironment
from app.services.cache_service import CacheService, CacheType
from app.services.destination_resolver import DestinationResolver
from app.services.llm_service import LLMService
from app.core.config import settings


async def test_cache_service():
    """Test the cache service functionality."""
    print("\n=== Testing Cache Service ===")
    
    cache = CacheService()
    
    # Test basic set/get
    test_key = "test_key"
    test_value = {"data": "test_value", "timestamp": datetime.now().isoformat()}
    
    # Set value
    success = await cache.set(test_key, test_value, ttl=60)
    print(f"Set cache value: {success}")
    
    # Get value
    retrieved = await cache.get(test_key)
    print(f"Retrieved value matches: {retrieved == test_value}")
    
    # Test cache types
    await cache.cache_flight_search(
        {"origin": "LAX", "destination": "JFK", "date": "2024-06-01"},
        {"flights": [{"id": "test_flight"}]}
    )
    
    cached_flight = await cache.get_cached_flight_search(
        {"origin": "LAX", "destination": "JFK", "date": "2024-06-01"}
    )
    print(f"Flight search caching works: {cached_flight is not None}")
    
    # Get cache stats
    stats = await cache.get_cache_stats()
    print(f"Cache stats: {stats['total_entries']} entries, {stats['total_size_mb']:.2f} MB")
    
    # Clean up
    await cache.delete(test_key)
    
    return True


async def test_amadeus_service():
    """Test the Amadeus service functionality."""
    print("\n=== Testing Amadeus Service ===")
    
    if not settings.AMADEUS_API_KEY or not settings.AMADEUS_API_SECRET:
        print("⚠️  Amadeus API keys not configured - skipping tests")
        return False
    
    # Initialize service (use sandbox for testing)
    amadeus = AmadeusService(environment=AmadeusEnvironment.SANDBOX)
    
    # Test authentication
    try:
        token = await amadeus._get_access_token()
        print(f"✓ Authentication successful - token obtained")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return False
    
    # Test airport lookup
    try:
        airport_info = await amadeus.get_airport_info("LAX")
        if "error" not in airport_info:
            print(f"✓ Airport lookup: {airport_info['name']} in {airport_info['city']}")
        else:
            print(f"✗ Airport lookup failed: {airport_info['error']}")
    except Exception as e:
        print(f"✗ Airport lookup error: {e}")
    
    # Test city lookup
    try:
        city_info = await amadeus.get_city_info("PAR")
        if "error" not in city_info:
            print(f"✓ City lookup: {city_info['name']}, {city_info['country']}")
        else:
            print(f"✗ City lookup failed: {city_info['error']}")
    except Exception as e:
        print(f"✗ City lookup error: {e}")
    
    # Test location search
    try:
        locations = await amadeus.search_locations("New York")
        if locations.get("locations"):
            print(f"✓ Location search found {len(locations['locations'])} results")
            for loc in locations["locations"][:2]:
                print(f"  - {loc['name']} ({loc['code']}) - {loc['type']}")
        else:
            print("✗ No locations found")
    except Exception as e:
        print(f"✗ Location search error: {e}")
    
    # Test flight search (with future dates)
    try:
        departure_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        return_date = (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d")
        
        flights = await amadeus.search_flights(
            origin="LAX",
            destination="JFK",
            departure_date=departure_date,
            return_date=return_date,
            adults=1,
            max_results=5
        )
        
        if flights.get("flights"):
            print(f"✓ Flight search found {len(flights['flights'])} results")
            for flight in flights["flights"][:2]:
                print(f"  - Flight {flight['id']}: ${flight['price']['total']} {flight['price']['currency']}")
        else:
            print("✗ No flights found")
    except Exception as e:
        print(f"✗ Flight search error: {e}")
    
    return True


async def test_destination_resolver():
    """Test the destination resolver functionality."""
    print("\n=== Testing Destination Resolver ===")
    
    # Initialize with optional LLM service
    try:
        llm_service = LLMService()
    except:
        llm_service = None
        print("⚠️  LLM service not available - testing without Layer 5")
    
    resolver = DestinationResolver(llm_service=llm_service)
    
    # Test cases
    test_cases = [
        ("LAX", "Direct airport code"),
        ("New York", "City name"),
        ("nyc", "City alias"),
        ("Paris France", "City with country"),
        ("French Riviera", "Regional mapping"),
        ("Bay Area", "Regional mapping"),
        ("Tokyo Japan", "City with country"),
        ("Big Apple", "City nickname"),
    ]
    
    for destination, description in test_cases:
        try:
            result = await resolver.resolve_destination(destination)
            if result["resolved"]:
                print(f"✓ {description} '{destination}' -> {result['city_name']} ({result['airport_code']}) - Layer: {result['resolution_layer']}")
            else:
                print(f"✗ {description} '{destination}' -> Not resolved")
        except Exception as e:
            print(f"✗ {description} '{destination}' -> Error: {e}")
    
    # Test autocomplete suggestions
    try:
        suggestions = resolver.get_suggestions("san", limit=3)
        print(f"\n✓ Autocomplete for 'san': {len(suggestions)} suggestions")
        for suggestion in suggestions:
            print(f"  - {suggestion['text']}")
    except Exception as e:
        print(f"✗ Autocomplete error: {e}")
    
    return True


async def test_llm_service():
    """Test the LLM service functionality."""
    print("\n=== Testing LLM Service ===")
    
    try:
        llm = LLMService()
        print(f"✓ LLM service initialized with provider: {llm.provider}")
    except Exception as e:
        print(f"✗ LLM service initialization failed: {e}")
        return False
    
    # Test intent extraction
    try:
        intent = await llm.extract_travel_intent(
            "I want to fly from Los Angeles to Tokyo next month for 2 people",
            {}
        )
        print(f"✓ Intent extraction: {intent['intent']} (confidence: {intent['confidence']:.2f})")
        print(f"  Entities: {intent.get('entities', {})}")
    except Exception as e:
        print(f"✗ Intent extraction error: {e}")
    
    # Test travel query parsing
    try:
        parsed = await llm.parse_travel_query_to_json(
            "Planning a trip to Paris and Rome in June for my family of 4",
            {}
        )
        if "error" not in parsed:
            print(f"✓ Travel query parsed successfully")
            print(f"  Destinations: {parsed.get('destinations', [])}")
            print(f"  Travelers: {parsed.get('travelers', {})}")
        else:
            print(f"✗ Travel query parsing failed: {parsed['error']}")
    except Exception as e:
        print(f"✗ Travel query parsing error: {e}")
    
    # Test suggestion generation
    try:
        suggestions = await llm.generate_suggestions({
            "travel_context": {
                "destinations": ["Paris"],
                "dates": {"departure": "2024-06-01"},
                "travelers": {"adults": 2}
            }
        })
        print(f"✓ Generated {len(suggestions)} suggestions:")
        for i, suggestion in enumerate(suggestions[:2], 1):
            print(f"  {i}. {suggestion}")
    except Exception as e:
        print(f"✗ Suggestion generation error: {e}")
    
    return True


async def test_integration():
    """Test integration between services."""
    print("\n=== Testing Service Integration ===")
    
    # Initialize services
    cache = CacheService()
    resolver = DestinationResolver()
    
    # Test destination resolution with caching
    destination = "San Francisco"
    
    # First resolution (cache miss)
    start_time = datetime.now()
    result1 = await resolver.resolve_destination(destination)
    time1 = (datetime.now() - start_time).total_seconds()
    
    # Second resolution (cache hit)
    start_time = datetime.now()
    result2 = await resolver.resolve_destination(destination)
    time2 = (datetime.now() - start_time).total_seconds()
    
    print(f"✓ Destination resolution caching:")
    print(f"  First call: {time1:.3f}s")
    print(f"  Cached call: {time2:.3f}s")
    print(f"  Speed improvement: {time1/time2:.1f}x faster")
    
    return True


async def main():
    """Run all tests."""
    print("=== Pathavana External Services Test Suite ===")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run tests
    tests = [
        ("Cache Service", test_cache_service),
        ("Amadeus Service", test_amadeus_service),
        ("Destination Resolver", test_destination_resolver),
        ("LLM Service", test_llm_service),
        ("Service Integration", test_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n=== Test Summary ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)