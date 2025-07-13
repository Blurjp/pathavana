"""
Amadeus API service for flight, hotel, and activity data integration.

Provides comprehensive integration with Amadeus APIs including:
- Flight search with real-time pricing
- Hotel search and availability
- Activity and attraction recommendations
- Airport and city code lookup
- Authentication token management
- Rate limiting and error handling
- Response caching strategy
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
from functools import wraps
import time
from enum import Enum

from ..core.config import settings
from .cache_service import CacheService

logger = logging.getLogger(__name__)


class AmadeusEnvironment(Enum):
    """Amadeus API environments."""
    SANDBOX = "test"
    PRODUCTION = "production"


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass


class AmadeusAPIError(Exception):
    """General Amadeus API error."""
    pass


def rate_limit(calls_per_minute: int = 60):
    """Decorator for rate limiting API calls."""
    min_interval = 60.0 / calls_per_minute
    last_call_time = {}
    
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            current_time = time.time()
            func_name = func.__name__
            
            if func_name in last_call_time:
                elapsed = current_time - last_call_time[func_name]
                if elapsed < min_interval:
                    wait_time = min_interval - elapsed
                    logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
            
            last_call_time[func_name] = time.time()
            return await func(self, *args, **kwargs)
        
        return wrapper
    return decorator


class AmadeusService:
    """Service for integrating with Amadeus travel APIs."""
    
    def __init__(self, environment: AmadeusEnvironment = AmadeusEnvironment.PRODUCTION):
        self.environment = environment
        self.api_key = settings.AMADEUS_API_KEY
        self.api_secret = settings.AMADEUS_API_SECRET
        
        # Set base URL based on environment
        if environment == AmadeusEnvironment.SANDBOX:
            self.base_url = "https://test.api.amadeus.com"
        else:
            self.base_url = "https://api.amadeus.com"
        
        self.access_token = None
        self.token_expires_at = None
        
        # Initialize cache service
        self.cache = CacheService()
        
        # Circuit breaker state
        self.circuit_breaker_open = False
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_reset_time = None
        
        # Request retry settings
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
    
    async def _get_access_token(self) -> str:
        """Get or refresh the Amadeus API access token."""
        if (self.access_token and self.token_expires_at and 
            datetime.now() < self.token_expires_at):
            return self.access_token
        
        async with aiohttp.ClientSession() as session:
            auth_url = f"{self.base_url}/v1/security/oauth2/token"
            
            data = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.api_secret
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            try:
                async with session.post(auth_url, data=data, headers=headers) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data["access_token"]
                        
                        # Set expiration time (subtract 5 minutes for safety)
                        expires_in = token_data.get("expires_in", 3600)
                        self.token_expires_at = datetime.now() + timedelta(
                            seconds=expires_in - 300
                        )
                        
                        return self.access_token
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to get Amadeus token: {error_text}")
                        
            except Exception as e:
                logger.error(f"Error getting Amadeus access token: {e}")
                raise
    
    async def _check_circuit_breaker(self) -> None:
        """Check if circuit breaker is open and should be reset."""
        if self.circuit_breaker_open:
            if self.circuit_breaker_reset_time and datetime.now() > self.circuit_breaker_reset_time:
                logger.info("Circuit breaker reset")
                self.circuit_breaker_open = False
                self.circuit_breaker_failures = 0
                self.circuit_breaker_reset_time = None
            else:
                raise AmadeusAPIError("Circuit breaker is open - API temporarily unavailable")
    
    async def _handle_circuit_breaker_failure(self) -> None:
        """Handle a failure for circuit breaker logic."""
        self.circuit_breaker_failures += 1
        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            self.circuit_breaker_open = True
            self.circuit_breaker_reset_time = datetime.now() + timedelta(minutes=5)
            logger.error(f"Circuit breaker opened after {self.circuit_breaker_failures} failures")
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Dict[str, Any],
        method: str = "GET",
        use_cache: bool = True,
        cache_ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Amadeus API with retry logic."""
        # Check circuit breaker
        await self._check_circuit_breaker()
        
        # Generate cache key
        cache_key = None
        if use_cache and method.upper() == "GET":
            cache_key = f"amadeus:{endpoint}:{json.dumps(params, sort_keys=True)}"
            cached_response = await self.cache.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for {endpoint}")
                return cached_response
        
        # Retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                access_token = await self._get_access_token()
                
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                url = f"{self.base_url}{endpoint}"
                
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    if method.upper() == "GET":
                        async with session.get(url, params=params, headers=headers) as response:
                            result = await self._handle_response(response)
                    elif method.upper() == "POST":
                        async with session.post(url, json=params, headers=headers) as response:
                            result = await self._handle_response(response)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Reset circuit breaker on success
                if self.circuit_breaker_failures > 0:
                    self.circuit_breaker_failures = 0
                    logger.info("Circuit breaker failures reset after successful request")
                
                # Cache successful response
                if use_cache and cache_key and method.upper() == "GET":
                    ttl = cache_ttl or self._get_cache_ttl(endpoint)
                    await self.cache.set(cache_key, result, ttl)
                
                return result
                
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying after {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    await self._handle_circuit_breaker_failure()
                    
            except Exception as e:
                logger.error(f"Error making Amadeus API request: {e}")
                await self._handle_circuit_breaker_failure()
                raise
        
        raise AmadeusAPIError(f"Failed after {self.max_retries} attempts: {last_error}")
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle and parse API response with detailed error handling."""
        response_text = await response.text()
        
        if response.status == 200:
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response: {response_text[:200]}")
                raise AmadeusAPIError("Invalid JSON response from API")
        
        # Try to parse error response
        try:
            error_data = json.loads(response_text)
            error_detail = error_data.get("errors", [{}])[0]
            error_msg = error_detail.get("detail", "Unknown error")
            error_code = error_detail.get("code", "UNKNOWN")
        except:
            error_msg = response_text
            error_code = "PARSE_ERROR"
        
        if response.status == 400:
            raise AmadeusAPIError(f"Bad request [{error_code}]: {error_msg}")
        elif response.status == 401:
            # Clear token to force re-authentication
            self.access_token = None
            self.token_expires_at = None
            raise AmadeusAPIError("Authentication failed - invalid or expired credentials")
        elif response.status == 403:
            raise AmadeusAPIError("Forbidden - check API permissions")
        elif response.status == 404:
            raise AmadeusAPIError(f"Resource not found: {error_msg}")
        elif response.status == 429:
            # Extract rate limit headers if available
            retry_after = response.headers.get("Retry-After", "60")
            raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
        elif response.status >= 500:
            raise AmadeusAPIError(f"Server error {response.status}: {error_msg}")
        else:
            raise AmadeusAPIError(f"API error {response.status}: {error_msg}")
    
    def _get_cache_ttl(self, endpoint: str) -> int:
        """Get appropriate cache TTL for different endpoints."""
        # Cache TTLs based on data volatility
        ttl_map = {
            "/v2/shopping/flight-offers": 1800,  # 30 minutes for flight searches
            "/v3/shopping/hotel-offers": 3600,   # 1 hour for hotel searches
            "/v1/shopping/activities": 21600,    # 6 hours for activities
            "/v1/reference-data/locations": 43200,  # 12 hours for locations
            "/v1/reference-data/airlines": 86400,   # 24 hours for airline data
        }
        
        for pattern, ttl in ttl_map.items():
            if pattern in endpoint:
                return ttl
        
        return 3600  # Default 1 hour
    
    @rate_limit(calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        travel_class: str = "ECONOMY",
        max_results: int = 10,
        currency_code: str = "USD",
        non_stop: bool = False,
        include_airlines: Optional[List[str]] = None,
        exclude_airlines: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search for flights using Amadeus Flight Offers Search API.
        
        Args:
            origin: Origin airport code (e.g., 'LAX')
            destination: Destination airport code (e.g., 'JFK')
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date for round-trip (optional)
            adults: Number of adult passengers
            children: Number of child passengers
            infants: Number of infant passengers
            travel_class: Travel class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
            max_results: Maximum number of results to return
        """
        params = {
            "originLocationCode": origin.upper(),
            "destinationLocationCode": destination.upper(),
            "departureDate": departure_date,
            "adults": adults,
            "max": max_results,
            "travelClass": travel_class,
            "currencyCode": currency_code
        }
        
        if return_date:
            params["returnDate"] = return_date
        
        if children > 0:
            params["children"] = children
        
        if infants > 0:
            params["infants"] = infants
        
        if non_stop:
            params["nonStop"] = "true"
        
        if include_airlines:
            params["includedAirlineCodes"] = ",".join(include_airlines)
        
        if exclude_airlines:
            params["excludedAirlineCodes"] = ",".join(exclude_airlines)
        
        try:
            result = await self._make_request("/v2/shopping/flight-offers", params)
            return self._format_flight_results(result)
        
        except Exception as e:
            logger.error(f"Error searching flights: {e}")
            return {"flights": [], "error": str(e)}
    
    @rate_limit(calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)
    async def search_hotels(
        self,
        city_code: str,
        check_in_date: str,
        check_out_date: str,
        adults: int = 1,
        rooms: int = 1,
        max_results: int = 10,
        currency_code: str = "USD",
        price_range: Optional[Tuple[float, float]] = None,
        amenities: Optional[List[str]] = None,
        ratings: Optional[List[int]] = None,
        hotel_chains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search for hotels using Amadeus Hotel Search API.
        
        Args:
            city_code: City code (e.g., 'PAR' for Paris)
            check_in_date: Check-in date in YYYY-MM-DD format
            check_out_date: Check-out date in YYYY-MM-DD format
            adults: Number of adult guests
            rooms: Number of rooms
            max_results: Maximum number of results to return
        """
        # First, get hotel IDs for the city
        hotel_ids_params = {
            "cityCode": city_code.upper(),
            "radius": 20,  # 20 km radius
            "radiusUnit": "KM"
        }
        
        if ratings:
            hotel_ids_params["ratings"] = ",".join(map(str, ratings))
        
        if hotel_chains:
            hotel_ids_params["chainCodes"] = ",".join(hotel_chains)
        
        try:
            # Get hotel list
            hotels_response = await self._make_request(
                "/v1/reference-data/locations/hotels/by-city", 
                hotel_ids_params
            )
            
            if not hotels_response.get("data"):
                return {"hotels": [], "error": "No hotels found in this city"}
            
            # Extract hotel IDs (limit to max_results)
            hotel_ids = [
                hotel["hotelId"] 
                for hotel in hotels_response["data"][:max_results]
            ]
            
            # Search for hotel offers
            offers_params = {
                "hotelIds": ",".join(hotel_ids),
                "checkInDate": check_in_date,
                "checkOutDate": check_out_date,
                "adults": adults,
                "roomQuantity": rooms,
                "currency": currency_code
            }
            
            if price_range:
                offers_params["priceRange"] = f"{price_range[0]}-{price_range[1]}"
            
            if amenities:
                offers_params["amenities"] = ",".join(amenities)
            
            offers_response = await self._make_request(
                "/v3/shopping/hotel-offers",
                offers_params
            )
            
            return self._format_hotel_results(offers_response)
        
        except Exception as e:
            logger.error(f"Error searching hotels: {e}")
            return {"hotels": [], "error": str(e)}
    
    async def get_airport_info(self, airport_code: str) -> Dict[str, Any]:
        """Get airport information by IATA code."""
        params = {
            "keyword": airport_code,
            "subType": "AIRPORT"
        }
        
        try:
            result = await self._make_request(
                "/v1/reference-data/locations", 
                params
            )
            
            if result.get("data"):
                airport = result["data"][0]
                return {
                    "code": airport.get("iataCode"),
                    "name": airport.get("name"),
                    "city": airport.get("address", {}).get("cityName"),
                    "country": airport.get("address", {}).get("countryName")
                }
            else:
                return {"error": f"Airport {airport_code} not found"}
        
        except Exception as e:
            logger.error(f"Error getting airport info: {e}")
            return {"error": str(e)}
    
    def _format_flight_results(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """Format flight search results for consistent response."""
        if not raw_results.get("data"):
            return {"flights": []}
        
        flights = []
        for offer in raw_results["data"]:
            try:
                flight_data = {
                    "id": offer.get("id"),
                    "price": {
                        "total": offer.get("price", {}).get("total"),
                        "currency": offer.get("price", {}).get("currency")
                    },
                    "itineraries": []
                }
                
                for itinerary in offer.get("itineraries", []):
                    itinerary_data = {
                        "duration": itinerary.get("duration"),
                        "segments": []
                    }
                    
                    for segment in itinerary.get("segments", []):
                        segment_data = {
                            "departure": {
                                "airport": segment.get("departure", {}).get("iataCode"),
                                "time": segment.get("departure", {}).get("at")
                            },
                            "arrival": {
                                "airport": segment.get("arrival", {}).get("iataCode"),
                                "time": segment.get("arrival", {}).get("at")
                            },
                            "carrier": segment.get("carrierCode"),
                            "flight_number": segment.get("number"),
                            "aircraft": segment.get("aircraft", {}).get("code"),
                            "duration": segment.get("duration")
                        }
                        itinerary_data["segments"].append(segment_data)
                    
                    flight_data["itineraries"].append(itinerary_data)
                
                flights.append(flight_data)
                
            except Exception as e:
                logger.warning(f"Error formatting flight offer: {e}")
                continue
        
        return {"flights": flights}
    
    def _format_hotel_results(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """Format hotel search results for consistent response."""
        if not raw_results.get("data"):
            return {"hotels": []}
        
        hotels = []
        for hotel_data in raw_results["data"]:
            try:
                hotel = hotel_data.get("hotel", {})
                offers = hotel_data.get("offers", [])
                
                if offers:
                    best_offer = offers[0]  # Assuming first offer is best
                    
                    hotel_info = {
                        "id": hotel.get("hotelId"),
                        "name": hotel.get("name"),
                        "rating": hotel.get("rating"),
                        "location": {
                            "address": hotel.get("address", {}),
                            "coordinates": hotel.get("geoCode", {})
                        },
                        "amenities": hotel.get("amenities", []),
                        "price": {
                            "total": best_offer.get("price", {}).get("total"),
                            "currency": best_offer.get("price", {}).get("currency"),
                            "per_night": best_offer.get("price", {}).get("base")
                        },
                        "room": {
                            "type": best_offer.get("room", {}).get("type"),
                            "description": best_offer.get("room", {}).get("description")
                        },
                        "policies": best_offer.get("policies", {})
                    }
                    
                    hotels.append(hotel_info)
                    
            except Exception as e:
                logger.warning(f"Error formatting hotel offer: {e}")
                continue
        
        return {"hotels": hotels}
    
    @rate_limit(calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)
    async def search_activities(
        self,
        latitude: float,
        longitude: float,
        radius: int = 10,
        max_results: int = 20
    ) -> Dict[str, Any]:
        """
        Search for activities and attractions near a location.
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            radius: Search radius in kilometers
            max_results: Maximum number of results
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius,
            "limit": max_results
        }
        
        try:
            result = await self._make_request(
                "/v1/shopping/activities",
                params,
                cache_ttl=21600  # 6 hours
            )
            return self._format_activity_results(result)
        
        except Exception as e:
            logger.error(f"Error searching activities: {e}")
            return {"activities": [], "error": str(e)}
    
    @rate_limit(calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)
    async def search_activities_by_city(
        self,
        city_code: str,
        max_results: int = 20
    ) -> Dict[str, Any]:
        """
        Search for activities in a specific city.
        
        Args:
            city_code: IATA city code
            max_results: Maximum number of results
        """
        # First get city coordinates
        city_info = await self.get_city_info(city_code)
        if "error" in city_info:
            return {"activities": [], "error": city_info["error"]}
        
        if "latitude" in city_info and "longitude" in city_info:
            return await self.search_activities(
                latitude=city_info["latitude"],
                longitude=city_info["longitude"],
                radius=20,
                max_results=max_results
            )
        
        return {"activities": [], "error": "Could not determine city coordinates"}
    
    @rate_limit(calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)
    async def get_activity_details(
        self,
        activity_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific activity.
        
        Args:
            activity_id: Activity ID from search results
        """
        try:
            result = await self._make_request(
                f"/v1/shopping/activities/{activity_id}",
                {},
                cache_ttl=21600  # 6 hours
            )
            
            if result.get("data"):
                return self._format_single_activity(result["data"])
            else:
                return {"error": "Activity not found"}
        
        except Exception as e:
            logger.error(f"Error getting activity details: {e}")
            return {"error": str(e)}
    
    @rate_limit(calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)
    async def get_airport_info(self, airport_code: str) -> Dict[str, Any]:
        """Get detailed airport information by IATA code."""
        params = {
            "keyword": airport_code.upper(),
            "subType": "AIRPORT"
        }
        
        try:
            result = await self._make_request(
                "/v1/reference-data/locations",
                params,
                cache_ttl=43200  # 12 hours
            )
            
            if result.get("data"):
                airport = result["data"][0]
                return {
                    "code": airport.get("iataCode"),
                    "name": airport.get("name"),
                    "city": airport.get("address", {}).get("cityName"),
                    "city_code": airport.get("address", {}).get("cityCode"),
                    "country": airport.get("address", {}).get("countryName"),
                    "country_code": airport.get("address", {}).get("countryCode"),
                    "latitude": airport.get("geoCode", {}).get("latitude"),
                    "longitude": airport.get("geoCode", {}).get("longitude"),
                    "timezone": airport.get("timeZoneOffset")
                }
            else:
                return {"error": f"Airport {airport_code} not found"}
        
        except Exception as e:
            logger.error(f"Error getting airport info: {e}")
            return {"error": str(e)}
    
    @rate_limit(calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)
    async def get_city_info(self, city_code: str) -> Dict[str, Any]:
        """Get city information by IATA city code."""
        params = {
            "keyword": city_code.upper(),
            "subType": "CITY"
        }
        
        try:
            result = await self._make_request(
                "/v1/reference-data/locations",
                params,
                cache_ttl=43200  # 12 hours
            )
            
            if result.get("data"):
                city = result["data"][0]
                return {
                    "code": city.get("iataCode"),
                    "name": city.get("name"),
                    "country": city.get("address", {}).get("countryName"),
                    "country_code": city.get("address", {}).get("countryCode"),
                    "latitude": city.get("geoCode", {}).get("latitude"),
                    "longitude": city.get("geoCode", {}).get("longitude"),
                    "timezone": city.get("timeZoneOffset")
                }
            else:
                return {"error": f"City {city_code} not found"}
        
        except Exception as e:
            logger.error(f"Error getting city info: {e}")
            return {"error": str(e)}
    
    @rate_limit(calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)
    async def search_locations(
        self,
        keyword: str,
        sub_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search for locations (airports, cities) by keyword.
        
        Args:
            keyword: Search keyword
            sub_types: List of location types (AIRPORT, CITY)
        """
        params = {
            "keyword": keyword,
            "view": "FULL"
        }
        
        if sub_types:
            params["subType"] = ",".join(sub_types)
        else:
            params["subType"] = "AIRPORT,CITY"
        
        try:
            result = await self._make_request(
                "/v1/reference-data/locations",
                params,
                cache_ttl=43200  # 12 hours
            )
            
            locations = []
            for location in result.get("data", []):
                locations.append({
                    "type": location.get("subType"),
                    "code": location.get("iataCode"),
                    "name": location.get("name"),
                    "city": location.get("address", {}).get("cityName"),
                    "country": location.get("address", {}).get("countryName"),
                    "relevance": location.get("relevance", 0)
                })
            
            # Sort by relevance
            locations.sort(key=lambda x: x["relevance"], reverse=True)
            
            return {"locations": locations}
        
        except Exception as e:
            logger.error(f"Error searching locations: {e}")
            return {"locations": [], "error": str(e)}
    
    @rate_limit(calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)
    async def get_airline_info(self, airline_code: str) -> Dict[str, Any]:
        """Get airline information by IATA code."""
        params = {
            "airlineCodes": airline_code.upper()
        }
        
        try:
            result = await self._make_request(
                "/v1/reference-data/airlines",
                params,
                cache_ttl=86400  # 24 hours
            )
            
            if result.get("data"):
                airline = result["data"][0]
                return {
                    "code": airline.get("iataCode"),
                    "business_name": airline.get("businessName"),
                    "common_name": airline.get("commonName")
                }
            else:
                return {"error": f"Airline {airline_code} not found"}
        
        except Exception as e:
            logger.error(f"Error getting airline info: {e}")
            return {"error": str(e)}
    
    def _format_activity_results(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """Format activity search results."""
        if not raw_results.get("data"):
            return {"activities": []}
        
        activities = []
        for activity in raw_results["data"]:
            activities.append(self._format_single_activity(activity))
        
        return {"activities": activities}
    
    def _format_single_activity(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format a single activity."""
        try:
            return {
                "id": activity_data.get("id"),
                "name": activity_data.get("name"),
                "short_description": activity_data.get("shortDescription"),
                "description": activity_data.get("description"),
                "rating": activity_data.get("rating"),
                "price": {
                    "amount": activity_data.get("price", {}).get("amount"),
                    "currency": activity_data.get("price", {}).get("currencyCode")
                },
                "pictures": activity_data.get("pictures", []),
                "booking_link": activity_data.get("bookingLink"),
                "location": {
                    "latitude": activity_data.get("geoCode", {}).get("latitude"),
                    "longitude": activity_data.get("geoCode", {}).get("longitude")
                },
                "duration": activity_data.get("minimumDuration"),
                "categories": activity_data.get("categories", [])
            }
        except Exception as e:
            logger.warning(f"Error formatting activity: {e}")
            return None