"""
Caching service for performance optimization.

Implements multi-level caching with automatic expiration:
- AI recommendations: 24 hours
- Amadeus activities: 6 hours
- Amadeus locations: 12 hours
- Chat responses: 2 hours
- AI hints: 1 hour
- Flight searches: 30 minutes
- Hotel searches: 1 hour
"""

import json
import hashlib
import os
import pickle
from typing import Any, Optional, Dict, Union, List
from datetime import datetime, timedelta
import aiofiles
import logging
from enum import Enum
import asyncio
from functools import wraps

from ..core.config import settings

logger = logging.getLogger(__name__)


class CacheType(Enum):
    """Cache types with predefined TTLs."""
    AI_RECOMMENDATIONS = ("ai_recommendations", 86400)  # 24 hours
    AMADEUS_ACTIVITIES = ("amadeus_activities", 21600)  # 6 hours
    AMADEUS_LOCATIONS = ("amadeus_locations", 43200)   # 12 hours
    CHAT_RESPONSES = ("chat_responses", 7200)           # 2 hours
    AI_HINTS = ("ai_hints", 3600)                      # 1 hour
    FLIGHT_SEARCHES = ("flight_searches", 1800)         # 30 minutes
    HOTEL_SEARCHES = ("hotel_searches", 3600)           # 1 hour
    LLM_RESPONSES = ("llm_responses", 86400)            # 24 hours
    DESTINATION_RESOLUTION = ("destination_resolution", 43200)  # 12 hours
    
    def __init__(self, prefix: str, ttl: int):
        self.prefix = prefix
        self.ttl = ttl


class CacheService:
    """Service for caching frequently accessed data and API responses."""
    
    def __init__(self):
        self.cache_dir = settings.CACHE_DIR
        self.default_ttl = settings.CACHE_TTL
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache statistics tracking
        self._stats = {
            "hits": 0,
            "misses": 0,
            "writes": 0,
            "errors": 0
        }
        
        # Background cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self) -> None:
        """Start background task for periodic cache cleanup."""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(3600)  # Run every hour
                    cleared = await self.clear_expired()
                    if cleared > 0:
                        logger.info(f"Cleared {cleared} expired cache entries")
                except Exception as e:
                    logger.error(f"Error in cache cleanup task: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
    
    async def get(self, key: str, cache_type: Optional[CacheType] = None) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            cache_type: Optional cache type for key prefixing
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            if cache_type:
                key = f"{cache_type.prefix}:{key}"
            
            cache_file = self._get_cache_file_path(key)
            
            if not os.path.exists(cache_file):
                self._stats["misses"] += 1
                return None
            
            async with aiofiles.open(cache_file, 'rb') as f:
                cache_data = pickle.loads(await f.read())
            
            # Check if expired
            if cache_data['expires_at'] < datetime.utcnow():
                await self._delete_cache_file(cache_file)
                self._stats["misses"] += 1
                return None
            
            self._stats["hits"] += 1
            return cache_data['value']
            
        except Exception as e:
            logger.warning(f"Error reading from cache: {e}")
            self._stats["errors"] += 1
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        cache_type: Optional[CacheType] = None
    ) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            cache_type: Optional cache type for automatic TTL and prefixing
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if cache_type:
                key = f"{cache_type.prefix}:{key}"
                ttl = ttl or cache_type.ttl
            else:
                ttl = ttl or self.default_ttl
            
            cache_file = self._get_cache_file_path(key)
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
            cache_data = {
                'value': value,
                'created_at': datetime.utcnow(),
                'expires_at': expires_at,
                'key': key,
                'ttl': ttl,
                'cache_type': cache_type.name if cache_type else None
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            
            async with aiofiles.open(cache_file, 'wb') as f:
                await f.write(pickle.dumps(cache_data))
            
            self._stats["writes"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error writing to cache: {e}")
            self._stats["errors"] += 1
            return False
    
    async def get_cached_response(self, key: str) -> Optional[Any]:
        """Get a cached response (alias for get)."""
        return await self.get(key, CacheType.LLM_RESPONSES)
    
    async def cache_response(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Cache a response (alias for set)."""
        return await self.set(key, value, ttl=ttl or CacheType.LLM_RESPONSES.ttl)
    
    async def delete(self, key: str, cache_type: Optional[CacheType] = None) -> bool:
        """
        Delete a value from cache.
        
        Args:
            key: Cache key to delete
            cache_type: Optional cache type for key prefixing
            
        Returns:
            True if deleted, False if not found
        """
        try:
            if cache_type:
                key = f"{cache_type.prefix}:{key}"
            
            cache_file = self._get_cache_file_path(key)
            return await self._delete_cache_file(cache_file)
            
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            self._stats["errors"] += 1
            return False
    
    async def clear_expired(self) -> int:
        """
        Clear all expired cache entries.
        
        Returns:
            Number of entries cleared
        """
        cleared_count = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    
                    try:
                        async with aiofiles.open(cache_file, 'rb') as f:
                            cache_data = pickle.loads(await f.read())
                        
                        if cache_data['expires_at'] < datetime.utcnow():
                            await self._delete_cache_file(cache_file)
                            cleared_count += 1
                            
                    except Exception:
                        # If we can't read the cache file, delete it
                        await self._delete_cache_file(cache_file)
                        cleared_count += 1
                        
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
        
        return cleared_count
    
    async def clear_all(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        cleared_count = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    await self._delete_cache_file(cache_file)
                    cleared_count += 1
                    
        except Exception as e:
            logger.error(f"Error clearing all cache: {e}")
        
        return cleared_count
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            'total_entries': 0,
            'expired_entries': 0,
            'valid_entries': 0,
            'total_size_mb': 0.0,
            'oldest_entry': None,
            'newest_entry': None,
            'hit_rate': 0.0,
            'runtime_stats': self._stats.copy(),
            'by_type': {}
        }
        
        try:
            oldest_time = None
            newest_time = None
            total_size = 0
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    stats['total_entries'] += 1
                    
                    # Get file size
                    file_size = os.path.getsize(cache_file)
                    total_size += file_size
                    
                    try:
                        async with aiofiles.open(cache_file, 'rb') as f:
                            cache_data = pickle.loads(await f.read())
                        
                        created_at = cache_data['created_at']
                        expires_at = cache_data['expires_at']
                        
                        # Track oldest and newest
                        if oldest_time is None or created_at < oldest_time:
                            oldest_time = created_at
                        if newest_time is None or created_at > newest_time:
                            newest_time = created_at
                        
                        # Check if expired
                        if expires_at < datetime.utcnow():
                            stats['expired_entries'] += 1
                        else:
                            stats['valid_entries'] += 1
                        
                        # Track by cache type
                        cache_type_name = cache_data.get('cache_type', 'unknown')
                        if cache_type_name not in stats['by_type']:
                            stats['by_type'][cache_type_name] = {
                                'count': 0,
                                'size_mb': 0.0,
                                'expired': 0
                            }
                        
                        stats['by_type'][cache_type_name]['count'] += 1
                        stats['by_type'][cache_type_name]['size_mb'] += file_size / (1024 * 1024)
                        
                        if expires_at < datetime.utcnow():
                            stats['by_type'][cache_type_name]['expired'] += 1
                            
                    except Exception:
                        stats['expired_entries'] += 1
            
            stats['total_size_mb'] = total_size / (1024 * 1024)
            stats['oldest_entry'] = oldest_time.isoformat() if oldest_time else None
            stats['newest_entry'] = newest_time.isoformat() if newest_time else None
            
            # Calculate hit rate
            total_requests = self._stats["hits"] + self._stats["misses"]
            if total_requests > 0:
                stats['hit_rate'] = self._stats["hits"] / total_requests
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
        
        return stats
    
    # Specialized caching methods for common use cases
    
    async def cache_flight_search(
        self, 
        search_params: Dict[str, Any], 
        results: Dict[str, Any]
    ) -> bool:
        """Cache flight search results."""
        key = self._generate_flight_search_key(search_params)
        return await self.set(key, results, cache_type=CacheType.FLIGHT_SEARCHES)
    
    async def get_cached_flight_search(
        self, 
        search_params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get cached flight search results."""
        key = self._generate_flight_search_key(search_params)
        return await self.get(key, cache_type=CacheType.FLIGHT_SEARCHES)
    
    async def cache_hotel_search(
        self, 
        search_params: Dict[str, Any], 
        results: Dict[str, Any]
    ) -> bool:
        """Cache hotel search results."""
        key = self._generate_hotel_search_key(search_params)
        return await self.set(key, results, cache_type=CacheType.HOTEL_SEARCHES)
    
    async def get_cached_hotel_search(
        self, 
        search_params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get cached hotel search results."""
        key = self._generate_hotel_search_key(search_params)
        return await self.get(key, cache_type=CacheType.HOTEL_SEARCHES)
    
    async def cache_llm_response(
        self, 
        prompt_hash: str, 
        response: str
    ) -> bool:
        """Cache LLM response."""
        return await self.set(prompt_hash, response, cache_type=CacheType.LLM_RESPONSES)
    
    async def get_cached_llm_response(self, prompt_hash: str) -> Optional[str]:
        """Get cached LLM response."""
        return await self.get(prompt_hash, cache_type=CacheType.LLM_RESPONSES)
    
    async def cache_ai_recommendation(
        self,
        recommendation_key: str,
        recommendation_data: Dict[str, Any]
    ) -> bool:
        """Cache AI recommendation."""
        return await self.set(recommendation_key, recommendation_data, cache_type=CacheType.AI_RECOMMENDATIONS)
    
    async def get_cached_ai_recommendation(
        self,
        recommendation_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached AI recommendation."""
        return await self.get(recommendation_key, cache_type=CacheType.AI_RECOMMENDATIONS)
    
    async def cache_activities(
        self,
        location_key: str,
        activities: List[Dict[str, Any]]
    ) -> bool:
        """Cache Amadeus activities."""
        return await self.set(location_key, activities, cache_type=CacheType.AMADEUS_ACTIVITIES)
    
    async def get_cached_activities(
        self,
        location_key: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached Amadeus activities."""
        return await self.get(location_key, cache_type=CacheType.AMADEUS_ACTIVITIES)
    
    async def cache_location(
        self,
        location_code: str,
        location_data: Dict[str, Any]
    ) -> bool:
        """Cache Amadeus location data."""
        return await self.set(location_code, location_data, cache_type=CacheType.AMADEUS_LOCATIONS)
    
    async def get_cached_location(
        self,
        location_code: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached Amadeus location data."""
        return await self.get(location_code, cache_type=CacheType.AMADEUS_LOCATIONS)
    
    async def cache_chat_response(
        self,
        session_id: str,
        message_hash: str,
        response: Dict[str, Any]
    ) -> bool:
        """Cache chat response."""
        key = f"{session_id}:{message_hash}"
        return await self.set(key, response, cache_type=CacheType.CHAT_RESPONSES)
    
    async def get_cached_chat_response(
        self,
        session_id: str,
        message_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached chat response."""
        key = f"{session_id}:{message_hash}"
        return await self.get(key, cache_type=CacheType.CHAT_RESPONSES)
    
    async def cache_ai_hint(
        self,
        hint_key: str,
        hint_data: Union[str, List[str]]
    ) -> bool:
        """Cache AI hint."""
        return await self.set(hint_key, hint_data, cache_type=CacheType.AI_HINTS)
    
    async def get_cached_ai_hint(
        self,
        hint_key: str
    ) -> Optional[Union[str, List[str]]]:
        """Get cached AI hint."""
        return await self.get(hint_key, cache_type=CacheType.AI_HINTS)
    
    async def cache_destination_resolution(
        self,
        destination_text: str,
        resolution_data: Dict[str, Any]
    ) -> bool:
        """Cache destination resolution result."""
        key = destination_text.lower().replace(" ", "_")
        return await self.set(key, resolution_data, cache_type=CacheType.DESTINATION_RESOLUTION)
    
    async def get_cached_destination_resolution(
        self,
        destination_text: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached destination resolution result."""
        key = destination_text.lower().replace(" ", "_")
        return await self.get(key, cache_type=CacheType.DESTINATION_RESOLUTION)
    
    def _get_cache_file_path(self, key: str) -> str:
        """Get the file path for a cache key."""
        # Hash the key to create a safe filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")
    
    async def _delete_cache_file(self, cache_file: str) -> bool:
        """Delete a cache file."""
        try:
            if os.path.exists(cache_file):
                os.remove(cache_file)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting cache file {cache_file}: {e}")
            return False
    
    def _generate_flight_search_key(self, search_params: Dict[str, Any]) -> str:
        """Generate a cache key for flight searches."""
        # Create a normalized key from search parameters
        key_data = {
            'type': 'flight_search',
            'origin': search_params.get('origin', '').upper(),
            'destination': search_params.get('destination', '').upper(),
            'departure_date': search_params.get('departure_date', ''),
            'return_date': search_params.get('return_date', ''),
            'adults': search_params.get('adults', 1),
            'children': search_params.get('children', 0),
            'infants': search_params.get('infants', 0),
            'travel_class': search_params.get('travel_class', 'ECONOMY').upper()
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _generate_hotel_search_key(self, search_params: Dict[str, Any]) -> str:
        """Generate a cache key for hotel searches."""
        key_data = {
            'type': 'hotel_search',
            'city_code': search_params.get('city_code', '').upper(),
            'check_in_date': search_params.get('check_in_date', ''),
            'check_out_date': search_params.get('check_out_date', ''),
            'adults': search_params.get('adults', 1),
            'rooms': search_params.get('rooms', 1)
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def cache_decorator(cache_type: CacheType, key_func=None):
        """
        Decorator for automatic caching of function results.
        
        Args:
            cache_type: Type of cache to use
            key_func: Optional function to generate cache key from args
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(self, *args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Default: use function name and all args
                    cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # Try to get from cache
                cache_service = getattr(self, 'cache', None)
                if cache_service:
                    cached = await cache_service.get(cache_key, cache_type)
                    if cached is not None:
                        logger.debug(f"Cache hit for {func.__name__}")
                        return cached
                
                # Execute function
                result = await func(self, *args, **kwargs)
                
                # Cache result
                if cache_service and result is not None:
                    await cache_service.set(cache_key, result, cache_type=cache_type)
                
                return result
            
            return wrapper
        return decorator