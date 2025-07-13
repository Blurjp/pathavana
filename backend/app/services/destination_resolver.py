"""
Smart destination resolution service for converting natural language to airport/city codes.

Implements a 5-layer fallback strategy:
1. Direct IATA/city code match
2. Fuzzy string matching
3. Regional mapping (e.g., "French Riviera" → cities)
4. Geocoding via Google Maps API
5. LLM-based interpretation
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from fuzzywuzzy import fuzz
import json
import logging
import aiohttp
from datetime import datetime
import asyncio

from ..core.config import settings
from .cache_service import CacheService, CacheType
from .llm_service import LLMService

logger = logging.getLogger(__name__)


class DestinationResolver:
    """Service for resolving natural language destinations to airport/city codes."""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        # Common airport codes and cities mapping
        self.airport_data = self._load_airport_data()
        self.city_aliases = self._load_city_aliases()
        self.regional_mappings = self._load_regional_mappings()
        
        # Initialize services
        self.cache = CacheService()
        self.llm_service = llm_service
        
        # Google Maps API key
        self.google_maps_api_key = settings.GOOGLE_MAPS_API_KEY
        
        # Resolution confidence thresholds
        self.confidence_thresholds = {
            "direct_match": 0.95,
            "fuzzy_match": 0.80,
            "regional_mapping": 0.85,
            "geocoding": 0.75,
            "llm_interpretation": 0.70
        }
    
    async def resolve_destination(
        self, 
        destination_text: str,
        prefer_airports: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resolve a destination string to airport/city codes using 5-layer strategy.
        
        Args:
            destination_text: Natural language destination
            prefer_airports: Whether to prefer airport codes over city codes
            context: Optional context for better resolution (e.g., departure location)
            
        Returns:
            Dict with resolved destination info including codes, confidence, etc.
        """
        if not destination_text:
            return {
                "resolved": False,
                "error": "Empty destination text",
                "original_text": destination_text
            }
        
        # Check cache first
        cached_result = await self.cache.get_cached_destination_resolution(destination_text)
        if cached_result:
            logger.debug(f"Cache hit for destination: {destination_text}")
            return cached_result
        
        # Clean and normalize the input
        clean_text = self._clean_destination_text(destination_text)
        
        # Store all resolution attempts
        resolution_layers = []
        
        # Layer 1: Direct IATA/city code match
        direct_result = await self._layer1_direct_match(clean_text)
        if direct_result:
            resolution_layers.append(direct_result)
            if direct_result["confidence"] >= self.confidence_thresholds["direct_match"]:
                result = self._format_result(direct_result, destination_text, resolution_layers)
                await self.cache.cache_destination_resolution(destination_text, result)
                return result
        
        # Layer 2: Fuzzy string matching
        fuzzy_results = await self._layer2_fuzzy_matching(clean_text)
        resolution_layers.extend(fuzzy_results)
        if fuzzy_results and fuzzy_results[0]["confidence"] >= self.confidence_thresholds["fuzzy_match"]:
            result = self._format_result(fuzzy_results[0], destination_text, resolution_layers)
            await self.cache.cache_destination_resolution(destination_text, result)
            return result
        
        # Layer 3: Regional mapping
        regional_results = await self._layer3_regional_mapping(clean_text)
        resolution_layers.extend(regional_results)
        if regional_results and regional_results[0]["confidence"] >= self.confidence_thresholds["regional_mapping"]:
            result = self._format_result(regional_results[0], destination_text, resolution_layers)
            await self.cache.cache_destination_resolution(destination_text, result)
            return result
        
        # Layer 4: Geocoding via Google Maps API
        if self.google_maps_api_key:
            geocoding_result = await self._layer4_geocoding(destination_text, context)
            if geocoding_result:
                resolution_layers.append(geocoding_result)
                if geocoding_result["confidence"] >= self.confidence_thresholds["geocoding"]:
                    result = self._format_result(geocoding_result, destination_text, resolution_layers)
                    await self.cache.cache_destination_resolution(destination_text, result)
                    return result
        
        # Layer 5: LLM-based interpretation
        if self.llm_service:
            llm_result = await self._layer5_llm_interpretation(destination_text, context, resolution_layers)
            if llm_result:
                resolution_layers.append(llm_result)
                if llm_result["confidence"] >= self.confidence_thresholds["llm_interpretation"]:
                    result = self._format_result(llm_result, destination_text, resolution_layers)
                    await self.cache.cache_destination_resolution(destination_text, result)
                    return result
        
        # If we have any results, return the best one
        if resolution_layers:
            resolution_layers.sort(key=lambda x: x["confidence"], reverse=True)
            result = self._format_result(resolution_layers[0], destination_text, resolution_layers)
            await self.cache.cache_destination_resolution(destination_text, result)
            return result
        
        # No resolution found
        result = {
            "resolved": False,
            "original_text": destination_text,
            "error": "Could not resolve destination through any layer",
            "attempted_layers": [
                "direct_match", "fuzzy_matching", "regional_mapping",
                "geocoding" if self.google_maps_api_key else "geocoding_skipped",
                "llm_interpretation" if self.llm_service else "llm_skipped"
            ]
        }
        
        # Cache negative results for a shorter time
        await self.cache.set(
            destination_text.lower().replace(" ", "_"),
            result,
            ttl=3600,  # 1 hour for failed resolutions
            cache_type=CacheType.DESTINATION_RESOLUTION
        )
        
        return result
    
    def resolve_multiple_destinations(
        self, 
        destinations: List[str]
    ) -> List[Dict[str, Any]]:
        """Resolve multiple destinations at once."""
        return [self.resolve_destination(dest) for dest in destinations]
    
    def get_suggestions(
        self, 
        partial_text: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get destination suggestions for autocomplete."""
        if len(partial_text) < 2:
            return []
        
        suggestions = []
        clean_text = self._clean_destination_text(partial_text)
        
        # Search in cities
        for city_data in self.airport_data.values():
            city_name = city_data.get("city_name", "").lower()
            if clean_text in city_name:
                suggestions.append({
                    "text": f"{city_data['city_name']}, {city_data['country']}",
                    "airport_code": city_data["airport_code"],
                    "city_name": city_data["city_name"],
                    "country": city_data["country"],
                    "type": "city"
                })
        
        # Search in airport names
        for airport_code, airport_data in self.airport_data.items():
            airport_name = airport_data.get("airport_name", "").lower()
            if clean_text in airport_name:
                suggestions.append({
                    "text": f"{airport_data['airport_name']} ({airport_code})",
                    "airport_code": airport_code,
                    "city_name": airport_data["city_name"],
                    "country": airport_data["country"],
                    "type": "airport"
                })
        
        # Remove duplicates and limit results
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            key = (suggestion["airport_code"], suggestion["type"])
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:limit]
    
    def _clean_destination_text(self, text: str) -> str:
        """Clean and normalize destination text."""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove common prefixes/suffixes
        text = re.sub(r'\b(airport|international|city|to|from)\b', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def _layer1_direct_match(self, text: str) -> Optional[Dict[str, Any]]:
        """Layer 1: Direct IATA code match for airports and cities."""
        text_upper = text.upper()
        
        # Look for 3-letter codes
        code_match = re.search(r'\b([A-Z]{3})\b', text_upper)
        if code_match:
            code = code_match.group(1)
            
            # Check if it's an airport code
            if code in self.airport_data:
                return {
                    "layer": "direct_match",
                    "type": "airport",
                    "confidence": 0.95,
                    "airport_code": code,
                    "city_code": self.airport_data[code].get("city_code"),
                    "city_name": self.airport_data[code]["city_name"],
                    "country": self.airport_data[code]["country"],
                    "airport_name": self.airport_data[code].get("airport_name")
                }
            
            # Check if it's a city code
            for airport_code, data in self.airport_data.items():
                if data.get("city_code") == code:
                    return {
                        "layer": "direct_match",
                        "type": "city",
                        "confidence": 0.95,
                        "city_code": code,
                        "city_name": data["city_name"],
                        "country": data["country"],
                        "airport_code": airport_code,  # Primary airport
                        "airport_name": data.get("airport_name")
                    }
        
        return None
    
    async def _layer2_fuzzy_matching(self, text: str) -> List[Dict[str, Any]]:
        """Layer 2: Fuzzy string matching for cities and airports."""
        matches = []
        
        # Check city aliases first
        for city_key, aliases in self.city_aliases.items():
            for alias in aliases:
                similarity = fuzz.ratio(text, alias)
                if similarity >= 75:
                    # Find the city in airport data
                    for airport_code, data in self.airport_data.items():
                        if data["city_name"].lower().replace(" ", "_") == city_key:
                            matches.append({
                                "layer": "fuzzy_matching",
                                "type": "city_alias",
                                "confidence": similarity / 100.0,
                                "airport_code": airport_code,
                                "city_code": data.get("city_code"),
                                "city_name": data["city_name"],
                                "country": data["country"],
                                "airport_name": data.get("airport_name"),
                                "matched_alias": alias
                            })
                            break
        
        # Fuzzy match city names
        for airport_code, airport_data in self.airport_data.items():
            city_name = airport_data["city_name"].lower()
            
            # Try different matching strategies
            partial_ratio = fuzz.partial_ratio(text, city_name)
            token_sort_ratio = fuzz.token_sort_ratio(text, city_name)
            
            max_similarity = max(partial_ratio, token_sort_ratio)
            
            if max_similarity >= 80:
                matches.append({
                    "layer": "fuzzy_matching",
                    "type": "city",
                    "confidence": max_similarity / 100.0,
                    "airport_code": airport_code,
                    "city_code": airport_data.get("city_code"),
                    "city_name": airport_data["city_name"],
                    "country": airport_data["country"],
                    "airport_name": airport_data.get("airport_name")
                })
        
        # Fuzzy match airport names
        for airport_code, airport_data in self.airport_data.items():
            if "airport_name" in airport_data:
                airport_name = airport_data["airport_name"].lower()
                
                similarity = fuzz.partial_ratio(text, airport_name)
                
                if similarity >= 75:
                    matches.append({
                        "layer": "fuzzy_matching",
                        "type": "airport",
                        "confidence": similarity / 100.0,
                        "airport_code": airport_code,
                        "city_code": airport_data.get("city_code"),
                        "city_name": airport_data["city_name"],
                        "country": airport_data["country"],
                        "airport_name": airport_data["airport_name"]
                    })
        
        # Sort by confidence and return top matches
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        return matches[:5]
    
    async def _layer3_regional_mapping(self, text: str) -> List[Dict[str, Any]]:
        """Layer 3: Regional mapping for areas like 'French Riviera', 'Bay Area', etc."""
        matches = []
        
        for region_name, region_data in self.regional_mappings.items():
            # Check if the text mentions this region
            if any(alias.lower() in text for alias in region_data["aliases"]):
                # Return all cities in the region
                for city in region_data["cities"]:
                    # Find the airport for this city
                    for airport_code, airport_data in self.airport_data.items():
                        if airport_data["city_name"].lower() == city.lower():
                            matches.append({
                                "layer": "regional_mapping",
                                "type": "region",
                                "confidence": 0.85,
                                "airport_code": airport_code,
                                "city_code": airport_data.get("city_code"),
                                "city_name": airport_data["city_name"],
                                "country": airport_data["country"],
                                "airport_name": airport_data.get("airport_name"),
                                "region": region_data["name"],
                                "region_description": region_data.get("description")
                            })
                            break
        
        return matches[:5]
    
    async def _layer4_geocoding(self, text: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Layer 4: Geocoding via Google Maps API."""
        if not self.google_maps_api_key:
            return None
        
        try:
            # Prepare geocoding request
            params = {
                "address": text,
                "key": self.google_maps_api_key
            }
            
            # Add context if available (e.g., bias towards departure country)
            if context and "departure_country" in context:
                params["region"] = context["departure_country"][:2].lower()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data["status"] == "OK" and data["results"]:
                            result = data["results"][0]
                            
                            # Extract location details
                            location = result["geometry"]["location"]
                            address_components = result["address_components"]
                            
                            # Find city and country from components
                            city_name = None
                            country = None
                            
                            for component in address_components:
                                types = component["types"]
                                if "locality" in types:
                                    city_name = component["long_name"]
                                elif "country" in types:
                                    country = component["long_name"]
                            
                            if city_name:
                                # Find nearest airport
                                nearest_airport = await self._find_nearest_airport(
                                    location["lat"],
                                    location["lng"],
                                    city_name
                                )
                                
                                if nearest_airport:
                                    return {
                                        "layer": "geocoding",
                                        "type": "geocoded",
                                        "confidence": 0.75,
                                        "airport_code": nearest_airport["airport_code"],
                                        "city_code": nearest_airport.get("city_code"),
                                        "city_name": city_name,
                                        "country": country,
                                        "airport_name": nearest_airport.get("airport_name"),
                                        "latitude": location["lat"],
                                        "longitude": location["lng"],
                                        "formatted_address": result["formatted_address"]
                                    }
        
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
        
        return None
    
    def _load_airport_data(self) -> Dict[str, Dict[str, Any]]:
        """Load airport and city data. In production, this would come from a database or file."""
        # This is a sample dataset. In production, you'd load from a comprehensive database
        return {
            "LAX": {
                "airport_name": "Los Angeles International Airport",
                "city_name": "Los Angeles",
                "city_code": "LAX",
                "country": "United States",
                "state": "California"
            },
            "JFK": {
                "airport_name": "John F. Kennedy International Airport",
                "city_name": "New York",
                "city_code": "NYC",
                "country": "United States",
                "state": "New York"
            },
            "LGA": {
                "airport_name": "LaGuardia Airport",
                "city_name": "New York",
                "city_code": "NYC",
                "country": "United States",
                "state": "New York"
            },
            "CDG": {
                "airport_name": "Charles de Gaulle Airport",
                "city_name": "Paris",
                "city_code": "PAR",
                "country": "France"
            },
            "LHR": {
                "airport_name": "Heathrow Airport",
                "city_name": "London",
                "city_code": "LON",
                "country": "United Kingdom"
            },
            "NRT": {
                "airport_name": "Narita International Airport",
                "city_name": "Tokyo",
                "city_code": "TYO",
                "country": "Japan"
            },
            "SFO": {
                "airport_name": "San Francisco International Airport",
                "city_name": "San Francisco",
                "city_code": "SFO",
                "country": "United States",
                "state": "California"
            },
            "ORD": {
                "airport_name": "O'Hare International Airport",
                "city_name": "Chicago",
                "city_code": "CHI",
                "country": "United States",
                "state": "Illinois"
            }
        }
    
    async def _layer5_llm_interpretation(self, text: str, context: Optional[Dict[str, Any]], previous_attempts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Layer 5: LLM-based interpretation for complex or ambiguous destinations."""
        if not self.llm_service:
            return None
        
        try:
            # Prepare context for LLM
            llm_prompt = f"""
            Please help resolve this travel destination: "{text}"
            
            Context:
            - User is planning a trip
            {f"- Departure location: {context.get('departure_city')}" if context and 'departure_city' in context else ""}
            {f"- Travel dates: {context.get('travel_dates')}" if context and 'travel_dates' in context else ""}
            
            Previous resolution attempts found these possibilities:
            {json.dumps([{"city": r.get("city_name"), "country": r.get("country"), "confidence": r.get("confidence")} for r in previous_attempts[:3]], indent=2)}
            
            Please provide the most likely destination in this format:
            {{
                "city_name": "City Name",
                "country": "Country Name",
                "airport_code": "IATA code if known",
                "explanation": "Brief explanation of why this is the most likely destination"
            }}
            """
            
            response = await self.llm_service.generate_response(
                [{"role": "system", "content": "You are a travel destination expert."},
                 {"role": "user", "content": llm_prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            # Parse LLM response
            try:
                llm_data = json.loads(response)
                
                # Try to match with our airport database
                for airport_code, airport_data in self.airport_data.items():
                    if (airport_data["city_name"].lower() == llm_data["city_name"].lower() or
                        airport_code == llm_data.get("airport_code", "").upper()):
                        
                        return {
                            "layer": "llm_interpretation",
                            "type": "llm_resolved",
                            "confidence": 0.70,
                            "airport_code": airport_code,
                            "city_code": airport_data.get("city_code"),
                            "city_name": airport_data["city_name"],
                            "country": airport_data["country"],
                            "airport_name": airport_data.get("airport_name"),
                            "llm_explanation": llm_data.get("explanation")
                        }
                
                # If no exact match, return LLM suggestion for further processing
                return {
                    "layer": "llm_interpretation",
                    "type": "llm_suggestion",
                    "confidence": 0.65,
                    "city_name": llm_data["city_name"],
                    "country": llm_data["country"],
                    "llm_explanation": llm_data.get("explanation")
                }
            
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM response as JSON")
        
        except Exception as e:
            logger.error(f"LLM interpretation error: {e}")
        
        return None
    
    async def _find_nearest_airport(self, lat: float, lng: float, city_name: str) -> Optional[Dict[str, Any]]:
        """Find the nearest airport to given coordinates."""
        # In a real implementation, this would query a spatial database
        # For now, we'll do a simple city name match
        for airport_code, airport_data in self.airport_data.items():
            if airport_data["city_name"].lower() == city_name.lower():
                return {
                    "airport_code": airport_code,
                    "city_code": airport_data.get("city_code"),
                    "airport_name": airport_data.get("airport_name")
                }
        return None
    
    def _format_result(self, best_match: Dict[str, Any], original_text: str, all_matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format the final resolution result."""
        # Get alternatives from different layers
        alternatives = []
        seen_codes = {best_match.get("airport_code")}
        
        for match in all_matches:
            if match.get("airport_code") not in seen_codes and len(alternatives) < 4:
                alternatives.append({
                    "airport_code": match.get("airport_code"),
                    "city_name": match.get("city_name"),
                    "country": match.get("country"),
                    "confidence": match.get("confidence"),
                    "layer": match.get("layer")
                })
                seen_codes.add(match.get("airport_code"))
        
        return {
            "resolved": True,
            "original_text": original_text,
            "airport_code": best_match.get("airport_code"),
            "city_code": best_match.get("city_code"),
            "city_name": best_match.get("city_name"),
            "country": best_match.get("country"),
            "confidence": best_match["confidence"],
            "resolution_layer": best_match.get("layer"),
            "type": best_match.get("type"),
            "alternatives": alternatives,
            "metadata": {
                "latitude": best_match.get("latitude"),
                "longitude": best_match.get("longitude"),
                "region": best_match.get("region"),
                "llm_explanation": best_match.get("llm_explanation")
            }
        }
    
    def _load_regional_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Load regional mappings for popular travel regions."""
        return {
            "french_riviera": {
                "name": "French Riviera",
                "aliases": ["french riviera", "cote d'azur", "côte d'azur", "south of france"],
                "cities": ["nice", "cannes", "monaco", "antibes", "saint-tropez"],
                "description": "Mediterranean coastline in southeastern France"
            },
            "bay_area": {
                "name": "San Francisco Bay Area",
                "aliases": ["bay area", "sf bay area", "silicon valley"],
                "cities": ["san francisco", "san jose", "oakland", "palo alto"],
                "description": "Metropolitan area surrounding San Francisco Bay"
            },
            "swiss_alps": {
                "name": "Swiss Alps",
                "aliases": ["swiss alps", "alps switzerland", "alpine region"],
                "cities": ["zurich", "geneva", "interlaken", "zermatt"],
                "description": "Mountainous region in Switzerland"
            },
            "caribbean": {
                "name": "Caribbean",
                "aliases": ["caribbean", "caribbean islands", "west indies"],
                "cities": ["san juan", "kingston", "bridgetown", "nassau"],
                "description": "Tropical island region in the Americas"
            }
        }
    
    def _load_city_aliases(self) -> Dict[str, List[str]]:
        """Load city aliases and common variations."""
        return {
            "new_york": ["nyc", "ny", "new york city", "manhattan", "big apple"],
            "los_angeles": ["la", "los angeles", "city of angels", "l.a."],
            "san_francisco": ["sf", "san francisco", "frisco", "bay city"],
            "chicago": ["chi", "windy city", "chi-town"],
            "london": ["london uk", "london england", "london britain"],
            "paris": ["paris france", "city of light", "city of love"],
            "tokyo": ["tokyo japan", "東京"],
            "dubai": ["dubai uae", "dubai emirates"],
            "singapore": ["singapore city", "lion city"],
            "bangkok": ["bangkok thailand", "krung thep"],
            "istanbul": ["istanbul turkey", "constantinople"],
            "rome": ["rome italy", "roma", "eternal city"]
        }