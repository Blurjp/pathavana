# External API Services Integration Guide

This guide documents the implementation of external API service integrations for Pathavana, including Amadeus API, Google Maps, caching strategies, and destination resolution.

## Table of Contents
1. [Overview](#overview)
2. [Amadeus Service](#amadeus-service)
3. [Cache Service](#cache-service)
4. [Destination Resolver](#destination-resolver)
5. [LLM Service Integration](#llm-service-integration)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Best Practices](#best-practices)

## Overview

The external services layer provides robust integration with third-party APIs while implementing:
- **Rate limiting** to respect API quotas
- **Circuit breaker** patterns for reliability
- **Multi-level caching** for performance
- **Fallback strategies** for high availability
- **5-layer destination resolution** for user-friendly input

## Amadeus Service

The `AmadeusService` provides comprehensive integration with Amadeus travel APIs.

### Features

1. **Authentication Management**
   - Automatic token refresh
   - Token caching with expiration handling
   - Support for both sandbox and production environments

2. **Flight Search**
   ```python
   flights = await amadeus.search_flights(
       origin="LAX",
       destination="JFK", 
       departure_date="2024-06-01",
       return_date="2024-06-08",
       adults=2,
       travel_class="ECONOMY",
       non_stop=True
   )
   ```

3. **Hotel Search**
   ```python
   hotels = await amadeus.search_hotels(
       city_code="PAR",
       check_in_date="2024-06-01",
       check_out_date="2024-06-05",
       adults=2,
       price_range=(100, 300),
       amenities=["WIFI", "PARKING"]
   )
   ```

4. **Activity Search**
   ```python
   activities = await amadeus.search_activities_by_city(
       city_code="NYC",
       max_results=20
   )
   ```

5. **Location Services**
   - Airport information lookup
   - City information lookup
   - Keyword-based location search
   - Airline information lookup

### Rate Limiting

The service implements decorator-based rate limiting:
```python
@rate_limit(calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)
async def search_flights(...):
    # Implementation
```

### Circuit Breaker

Automatic circuit breaker protects against cascading failures:
- Opens after 5 consecutive failures
- Resets after 5 minutes
- Returns cached results when available

### Error Handling

Comprehensive error handling with:
- Retry logic with exponential backoff
- Detailed error messages
- Automatic fallback to cached data

## Cache Service

The `CacheService` implements multi-level caching with automatic expiration.

### Cache Types and TTLs

| Cache Type | TTL | Use Case |
|------------|-----|----------|
| AI_RECOMMENDATIONS | 24 hours | AI-generated recommendations |
| AMADEUS_ACTIVITIES | 6 hours | Activity search results |
| AMADEUS_LOCATIONS | 12 hours | Location data |
| CHAT_RESPONSES | 2 hours | Chat conversation responses |
| AI_HINTS | 1 hour | AI-generated hints |
| FLIGHT_SEARCHES | 30 minutes | Flight search results |
| HOTEL_SEARCHES | 1 hour | Hotel search results |
| LLM_RESPONSES | 24 hours | LLM completions |
| DESTINATION_RESOLUTION | 12 hours | Resolved destinations |

### Usage Examples

```python
# Cache flight search
await cache.cache_flight_search(
    search_params={"origin": "LAX", "destination": "JFK"},
    results=flight_results
)

# Retrieve cached flight search
cached = await cache.get_cached_flight_search(
    search_params={"origin": "LAX", "destination": "JFK"}
)

# Cache with custom TTL
await cache.set("custom_key", data, ttl=3600)

# Get cache statistics
stats = await cache.get_cache_stats()
```

### Features

1. **Automatic Cleanup**
   - Background task clears expired entries hourly
   - Manual cleanup available via `clear_expired()`

2. **Performance Tracking**
   - Hit/miss rate statistics
   - Size tracking by cache type
   - Runtime performance metrics

3. **Type-Safe Caching**
   - Enum-based cache types
   - Automatic TTL assignment
   - Key prefixing for organization

## Destination Resolver

The `DestinationResolver` implements a 5-layer fallback strategy for resolving user input to airport/city codes.

### Resolution Layers

1. **Layer 1: Direct Match**
   - IATA airport codes (LAX, JFK)
   - IATA city codes (NYC, PAR)
   - Confidence: 0.95

2. **Layer 2: Fuzzy Matching**
   - City name variations
   - Airport name matching
   - Common aliases (NYC → New York)
   - Confidence: 0.80+

3. **Layer 3: Regional Mapping**
   - "French Riviera" → Nice, Cannes, Monaco
   - "Bay Area" → San Francisco, San Jose, Oakland
   - "Swiss Alps" → Zurich, Geneva, Interlaken
   - Confidence: 0.85

4. **Layer 4: Google Maps Geocoding**
   - Address-based lookup
   - Nearest airport finding
   - Country bias support
   - Confidence: 0.75

5. **Layer 5: LLM Interpretation**
   - Complex query understanding
   - Context-aware resolution
   - Ambiguity handling
   - Confidence: 0.70

### Usage Example

```python
# Basic resolution
result = await resolver.resolve_destination("Paris France")

# With context
result = await resolver.resolve_destination(
    "Big Apple",
    context={"departure_country": "US"}
)

# Response format
{
    "resolved": True,
    "airport_code": "JFK",
    "city_code": "NYC",
    "city_name": "New York",
    "country": "United States",
    "confidence": 0.85,
    "resolution_layer": "fuzzy_matching",
    "alternatives": [...]
}
```

### Features

1. **Caching**
   - Results cached for 12 hours
   - Negative results cached for 1 hour

2. **Autocomplete Support**
   ```python
   suggestions = resolver.get_suggestions("san", limit=5)
   ```

3. **Regional Awareness**
   - Handles regions like "Caribbean", "French Riviera"
   - Returns multiple city options for regions

## LLM Service Integration

The LLM service is enhanced to work with external APIs for travel-specific tasks.

### Key Features

1. **Intent Extraction**
   ```python
   intent = await llm.extract_travel_intent(
       "I want to fly to Paris next week",
       context={}
   )
   ```

2. **Travel Query Parsing**
   ```python
   parsed = await llm.parse_travel_query_to_json(
       "Trip to Tokyo and Kyoto in April for 2",
       context=travel_context
   )
   ```

3. **Conflict Resolution**
   ```python
   resolution = await llm.resolve_conflicts(
       conflicts=[...],
       context=conversation_context
   )
   ```

4. **Response Formatting**
   ```python
   formatted = await llm.format_response_for_chat(
       data=flight_results,
       response_type="flight_results"
   )
   ```

### Fallback Support

- Primary service (Azure OpenAI, OpenAI, or Anthropic)
- Automatic fallback to secondary service
- Graceful degradation on failures

## Configuration

### Required Environment Variables

```bash
# Amadeus API
AMADEUS_API_KEY=your_amadeus_key
AMADEUS_API_SECRET=your_amadeus_secret
AMADEUS_API_BASE_URL=https://api.amadeus.com  # or https://test.api.amadeus.com

# Google Maps
GOOGLE_MAPS_API_KEY=your_google_maps_key

# LLM Services (at least one required)
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Cache Settings
CACHE_DIR=cache
CACHE_TTL=3600

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

### Service Initialization

```python
# Initialize services
amadeus = AmadeusService(environment=AmadeusEnvironment.PRODUCTION)
cache = CacheService()
llm = LLMService()
resolver = DestinationResolver(llm_service=llm)
```

## Testing

### Running Tests

```bash
# Run the comprehensive test suite
python test_external_services.py

# Run specific service tests
pytest tests/test_amadeus_service.py
pytest tests/test_cache_service.py
pytest tests/test_destination_resolver.py
```

### Test Coverage

The test suite covers:
- Authentication flows
- API rate limiting
- Circuit breaker behavior
- Cache hit/miss scenarios
- All 5 destination resolution layers
- Error handling and retries
- Service integration

## Best Practices

### 1. Always Use Caching
```python
# Check cache first
cached = await cache.get_cached_flight_search(params)
if cached:
    return cached

# Make API call
results = await amadeus.search_flights(**params)

# Cache results
await cache.cache_flight_search(params, results)
```

### 2. Handle Errors Gracefully
```python
try:
    result = await amadeus.search_flights(...)
except RateLimitError:
    # Use cached data or queue for later
    return await get_cached_or_default()
except AmadeusAPIError as e:
    # Log and provide user-friendly message
    logger.error(f"Amadeus error: {e}")
    return {"error": "Travel search temporarily unavailable"}
```

### 3. Use Appropriate Environments
```python
# Development/Testing
amadeus = AmadeusService(environment=AmadeusEnvironment.SANDBOX)

# Production
amadeus = AmadeusService(environment=AmadeusEnvironment.PRODUCTION)
```

### 4. Monitor Performance
```python
# Get cache statistics
stats = await cache.get_cache_stats()
logger.info(f"Cache hit rate: {stats['hit_rate']:.2%}")

# Monitor API calls
logger.info(f"Amadeus API calls: {amadeus.api_call_count}")
```

### 5. Implement Timeouts
```python
# Use asyncio timeout for long operations
async with asyncio.timeout(30):
    results = await resolver.resolve_destination(complex_query)
```

## Troubleshooting

### Common Issues

1. **Rate Limit Errors**
   - Check API quota in provider dashboard
   - Increase cache TTLs
   - Implement request queuing

2. **Authentication Failures**
   - Verify API credentials
   - Check token expiration
   - Ensure correct environment (sandbox vs production)

3. **Cache Misses**
   - Verify cache directory permissions
   - Check disk space
   - Monitor cache statistics

4. **Destination Resolution Failures**
   - Add more aliases to city mappings
   - Verify Google Maps API key
   - Check LLM service availability

### Debug Mode

Enable debug logging for detailed information:
```python
import logging
logging.getLogger("app.services").setLevel(logging.DEBUG)
```

## Performance Optimization

1. **Batch Operations**
   ```python
   # Batch multiple destination resolutions
   destinations = ["Paris", "London", "Tokyo"]
   results = await asyncio.gather(*[
       resolver.resolve_destination(dest) 
       for dest in destinations
   ])
   ```

2. **Preload Common Data**
   ```python
   # Warm up cache with popular destinations
   popular_cities = ["NYC", "LAX", "PAR", "LON"]
   for city in popular_cities:
       await resolver.resolve_destination(city)
   ```

3. **Use Connection Pooling**
   ```python
   # Reuse HTTP connections
   connector = aiohttp.TCPConnector(limit=100)
   session = aiohttp.ClientSession(connector=connector)
   ```

## Future Enhancements

1. **Additional Providers**
   - Skyscanner API integration
   - Booking.com API integration
   - TripAdvisor API integration

2. **Advanced Features**
   - Multi-city trip optimization
   - Price prediction
   - Seasonal recommendation engine

3. **Performance Improvements**
   - Redis caching option
   - GraphQL API layer
   - WebSocket support for real-time updates