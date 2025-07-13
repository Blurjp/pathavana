"""
Hotel search and booking tools for the AI agent.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ...services.amadeus_service import AmadeusService
from ...services.cache_service import CacheService

logger = logging.getLogger(__name__)


class HotelTools:
    """Tools for hotel-related operations in the AI agent."""
    
    def __init__(self, amadeus_service: AmadeusService, cache_service: CacheService):
        self.amadeus_service = amadeus_service
        self.cache_service = cache_service
    
    async def search_hotels(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for hotels based on parameters.
        
        Args:
            search_params: Hotel search parameters
            
        Returns:
            Hotel search results
        """
        try:
            # Check cache first
            cached_results = await self.cache_service.get_cached_hotel_search(search_params)
            if cached_results:
                logger.info("Returning cached hotel search results")
                return {
                    "hotels": cached_results["hotels"],
                    "cached": True,
                    "search_params": search_params
                }
            
            # Validate required parameters
            required_params = ["city_code", "check_in_date", "check_out_date"]
            missing_params = [param for param in required_params if not search_params.get(param)]
            
            if missing_params:
                return {
                    "error": f"Missing required parameters: {', '.join(missing_params)}",
                    "hotels": []
                }
            
            # Prepare Amadeus API parameters
            amadeus_params = self._prepare_amadeus_hotel_params(search_params)
            
            if not amadeus_params:
                return {
                    "error": "Invalid search parameters",
                    "hotels": []
                }
            
            # Search hotels using Amadeus
            amadeus_results = await self.amadeus_service.search_hotels(**amadeus_params)
            
            if amadeus_results.get("error"):
                return {
                    "error": amadeus_results["error"],
                    "hotels": []
                }
            
            # Process and enhance results
            processed_results = self._process_hotel_results(
                amadeus_results, 
                search_params
            )
            
            # Cache the results
            await self.cache_service.cache_hotel_search(search_params, processed_results)
            
            return {
                "hotels": processed_results["hotels"],
                "cached": False,
                "search_params": search_params,
                "total_results": len(processed_results["hotels"])
            }
            
        except Exception as e:
            logger.error(f"Error searching hotels: {e}")
            return {
                "error": f"Hotel search failed: {str(e)}",
                "hotels": []
            }
    
    async def filter_hotels_by_amenities(
        self, 
        search_params: Dict[str, Any],
        required_amenities: List[str]
    ) -> Dict[str, Any]:
        """Filter hotels by required amenities."""
        try:
            # Get all hotels first
            all_results = await self.search_hotels(search_params)
            
            if all_results.get("error"):
                return all_results
            
            # Filter by amenities
            filtered_hotels = []
            
            for hotel in all_results["hotels"]:
                hotel_amenities = hotel.get("amenities", [])
                
                # Check if hotel has all required amenities
                has_all_amenities = all(
                    any(amenity.lower() in hotel_amenity.lower() 
                        for hotel_amenity in hotel_amenities)
                    for amenity in required_amenities
                )
                
                if has_all_amenities:
                    filtered_hotels.append(hotel)
            
            return {
                "hotels": filtered_hotels,
                "total_results": len(filtered_hotels),
                "filtered_by": required_amenities,
                "search_params": search_params
            }
            
        except Exception as e:
            logger.error(f"Error filtering hotels by amenities: {e}")
            return {
                "error": f"Amenity filtering failed: {str(e)}",
                "hotels": []
            }
    
    async def filter_hotels_by_price_range(
        self, 
        search_params: Dict[str, Any],
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Filter hotels by price range."""
        try:
            # Get all hotels first
            all_results = await self.search_hotels(search_params)
            
            if all_results.get("error"):
                return all_results
            
            # Filter by price range
            filtered_hotels = []
            
            for hotel in all_results["hotels"]:
                price_info = hotel.get("price", {})
                total_price_str = price_info.get("total")
                
                if total_price_str:
                    try:
                        total_price = float(total_price_str)
                        
                        # Check price range
                        if min_price is not None and total_price < min_price:
                            continue
                        if max_price is not None and total_price > max_price:
                            continue
                        
                        filtered_hotels.append(hotel)
                        
                    except ValueError:
                        continue
            
            return {
                "hotels": filtered_hotels,
                "total_results": len(filtered_hotels),
                "price_filter": {
                    "min_price": min_price,
                    "max_price": max_price
                },
                "search_params": search_params
            }
            
        except Exception as e:
            logger.error(f"Error filtering hotels by price: {e}")
            return {
                "error": f"Price filtering failed: {str(e)}",
                "hotels": []
            }
    
    async def filter_hotels_by_rating(
        self, 
        search_params: Dict[str, Any],
        min_rating: float
    ) -> Dict[str, Any]:
        """Filter hotels by minimum rating."""
        try:
            # Get all hotels first
            all_results = await self.search_hotels(search_params)
            
            if all_results.get("error"):
                return all_results
            
            # Filter by rating
            filtered_hotels = []
            
            for hotel in all_results["hotels"]:
                rating = hotel.get("rating")
                
                if rating:
                    try:
                        hotel_rating = float(rating)
                        if hotel_rating >= min_rating:
                            filtered_hotels.append(hotel)
                    except ValueError:
                        continue
            
            return {
                "hotels": filtered_hotels,
                "total_results": len(filtered_hotels),
                "min_rating": min_rating,
                "search_params": search_params
            }
            
        except Exception as e:
            logger.error(f"Error filtering hotels by rating: {e}")
            return {
                "error": f"Rating filtering failed: {str(e)}",
                "hotels": []
            }
    
    async def get_hotel_recommendations(
        self, 
        search_params: Dict[str, Any],
        preferences: List[str]
    ) -> Dict[str, Any]:
        """Get hotel recommendations based on preferences."""
        try:
            # Get all hotels first
            all_results = await self.search_hotels(search_params)
            
            if all_results.get("error"):
                return all_results
            
            # Score hotels based on preferences
            scored_hotels = []
            
            for hotel in all_results["hotels"]:
                score = self._calculate_preference_score(hotel, preferences)
                hotel["preference_score"] = score
                scored_hotels.append(hotel)
            
            # Sort by preference score (highest first)
            scored_hotels.sort(key=lambda x: x.get("preference_score", 0), reverse=True)
            
            return {
                "hotels": scored_hotels[:10],  # Top 10 recommendations
                "total_results": len(scored_hotels),
                "based_on_preferences": preferences,
                "search_params": search_params
            }
            
        except Exception as e:
            logger.error(f"Error getting hotel recommendations: {e}")
            return {
                "error": f"Recommendation failed: {str(e)}",
                "hotels": []
            }
    
    async def compare_hotels(
        self, 
        hotel_ids: List[str],
        search_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare specific hotels side by side."""
        try:
            # Get all hotels first
            all_results = await self.search_hotels(search_params)
            
            if all_results.get("error"):
                return all_results
            
            # Find the requested hotels
            comparison_hotels = []
            
            for hotel in all_results["hotels"]:
                if hotel.get("id") in hotel_ids:
                    comparison_hotels.append(hotel)
            
            # Create comparison matrix
            comparison = {
                "hotels": comparison_hotels,
                "comparison_matrix": self._create_comparison_matrix(comparison_hotels),
                "requested_ids": hotel_ids,
                "found_count": len(comparison_hotels)
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing hotels: {e}")
            return {
                "error": f"Hotel comparison failed: {str(e)}"
            }
    
    def _prepare_amadeus_hotel_params(self, search_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Prepare parameters for Amadeus API call."""
        try:
            amadeus_params = {
                "city_code": search_params["city_code"],
                "check_in_date": search_params["check_in_date"],
                "check_out_date": search_params["check_out_date"],
                "adults": search_params.get("adults", 1),
                "rooms": search_params.get("rooms", 1),
                "max_results": search_params.get("max_results", 10)
            }
            
            return amadeus_params
            
        except Exception as e:
            logger.error(f"Error preparing Amadeus hotel parameters: {e}")
            return None
    
    def _process_hotel_results(
        self, 
        amadeus_results: Dict[str, Any], 
        search_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process and enhance hotel results."""
        try:
            hotels = amadeus_results.get("hotels", [])
            
            # Sort hotels by rating (highest first), then by price (lowest first)
            hotels.sort(key=lambda x: (
                -float(x.get("rating", 0) or 0),
                float(x.get("price", {}).get("total", "999999"))
            ))
            
            # Add enhanced information
            for hotel in hotels:
                # Calculate value score
                hotel["value_score"] = self._calculate_value_score(hotel)
                
                # Categorize hotel type
                hotel["hotel_category"] = self._categorize_hotel(hotel)
                
                # Calculate distance to city center (if coordinates available)
                hotel["location_score"] = self._calculate_location_score(hotel)
                
                # Analyze amenities
                hotel["amenity_categories"] = self._categorize_amenities(
                    hotel.get("amenities", [])
                )
            
            # Add search metadata
            processed_results = {
                "hotels": hotels,
                "search_metadata": {
                    "search_params": search_params,
                    "result_count": len(hotels),
                    "search_time": datetime.utcnow().isoformat(),
                    "cheapest_price": self._get_cheapest_price(hotels),
                    "highest_rated": self._get_highest_rated(hotels),
                    "price_range": self._calculate_price_range(hotels)
                }
            }
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error processing hotel results: {e}")
            return {"hotels": amadeus_results.get("hotels", [])}
    
    def _calculate_preference_score(self, hotel: Dict[str, Any], preferences: List[str]) -> float:
        """Calculate how well a hotel matches user preferences."""
        score = 0.0
        
        try:
            hotel_amenities = [amenity.lower() for amenity in hotel.get("amenities", [])]
            
            # Score based on preference keywords
            preference_weights = {
                "budget": -1.0,  # Lower price = higher score for budget preference
                "luxury": 2.0,   # Higher rating = higher score for luxury
                "business": 1.5, # Business amenities
                "family": 1.5,   # Family-friendly amenities
                "romantic": 1.0, # Spa, fine dining, etc.
                "fitness": 1.0,  # Gym, pool, etc.
                "wifi": 0.5,     # Free wifi
                "parking": 0.5,  # Free parking
                "pool": 1.0,     # Swimming pool
                "spa": 1.5       # Spa services
            }
            
            for preference in preferences:
                weight = preference_weights.get(preference.lower(), 0.5)
                
                if preference.lower() == "budget":
                    # For budget preference, lower price = higher score
                    price = float(hotel.get("price", {}).get("total", "0"))
                    if price > 0:
                        score += weight * (1000 / price)  # Inverse relationship
                
                elif preference.lower() == "luxury":
                    # For luxury, higher rating = higher score
                    rating = float(hotel.get("rating", 0) or 0)
                    score += weight * rating
                
                else:
                    # Check if preference matches amenities
                    if any(preference.lower() in amenity for amenity in hotel_amenities):
                        score += weight
            
            # Normalize score
            return min(10.0, max(0.0, score))
            
        except Exception as e:
            logger.warning(f"Error calculating preference score: {e}")
            return 0.0
    
    def _calculate_value_score(self, hotel: Dict[str, Any]) -> float:
        """Calculate value score (rating vs price)."""
        try:
            rating = float(hotel.get("rating", 0) or 0)
            price = float(hotel.get("price", {}).get("total", "0"))
            
            if price > 0 and rating > 0:
                # Simple value calculation: rating per 100 currency units
                return (rating / (price / 100))
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _categorize_hotel(self, hotel: Dict[str, Any]) -> str:
        """Categorize hotel type based on amenities and rating."""
        try:
            rating = float(hotel.get("rating", 0) or 0)
            amenities = [amenity.lower() for amenity in hotel.get("amenities", [])]
            
            luxury_indicators = ["spa", "concierge", "valet", "butler", "suite"]
            business_indicators = ["business center", "meeting", "conference", "wifi"]
            family_indicators = ["kids", "family", "playground", "children"]
            
            if rating >= 4.5 and any(indicator in amenity for amenity in amenities for indicator in luxury_indicators):
                return "luxury"
            elif any(indicator in amenity for amenity in amenities for indicator in business_indicators):
                return "business"
            elif any(indicator in amenity for amenity in amenities for indicator in family_indicators):
                return "family"
            elif rating >= 4.0:
                return "upscale"
            elif rating >= 3.0:
                return "midscale"
            else:
                return "economy"
                
        except Exception:
            return "standard"
    
    def _calculate_location_score(self, hotel: Dict[str, Any]) -> float:
        """Calculate location convenience score."""
        # Simplified implementation - in production, calculate actual distance to POIs
        try:
            location = hotel.get("location", {})
            coordinates = location.get("coordinates", {})
            
            # For now, return a base score
            # In production, calculate distance to city center, attractions, etc.
            return 5.0
            
        except Exception:
            return 5.0
    
    def _categorize_amenities(self, amenities: List[str]) -> Dict[str, List[str]]:
        """Categorize amenities into functional groups."""
        categories = {
            "connectivity": [],
            "fitness": [],
            "dining": [],
            "business": [],
            "family": [],
            "luxury": [],
            "transportation": []
        }
        
        amenity_mapping = {
            "connectivity": ["wifi", "internet", "broadband"],
            "fitness": ["gym", "fitness", "pool", "spa", "sauna"],
            "dining": ["restaurant", "bar", "breakfast", "room service"],
            "business": ["business center", "meeting", "conference", "fax"],
            "family": ["kids", "children", "family", "playground", "babysitting"],
            "luxury": ["concierge", "valet", "butler", "limousine", "premium"],
            "transportation": ["parking", "shuttle", "airport", "transport"]
        }
        
        for amenity in amenities:
            amenity_lower = amenity.lower()
            for category, keywords in amenity_mapping.items():
                if any(keyword in amenity_lower for keyword in keywords):
                    categories[category].append(amenity)
                    break
        
        return categories
    
    def _get_cheapest_price(self, hotels: List[Dict[str, Any]]) -> Optional[float]:
        """Get the cheapest price from hotel list."""
        try:
            prices = []
            for hotel in hotels:
                price_str = hotel.get("price", {}).get("total")
                if price_str:
                    try:
                        prices.append(float(price_str))
                    except ValueError:
                        continue
            
            return min(prices) if prices else None
            
        except Exception:
            return None
    
    def _get_highest_rated(self, hotels: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get the highest rated hotel."""
        try:
            highest_rated = None
            highest_rating = 0
            
            for hotel in hotels:
                rating = float(hotel.get("rating", 0) or 0)
                if rating > highest_rating:
                    highest_rating = rating
                    highest_rated = hotel
            
            return highest_rated
            
        except Exception:
            return None
    
    def _calculate_price_range(self, hotels: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
        """Calculate price range for hotels."""
        try:
            prices = []
            for hotel in hotels:
                price_str = hotel.get("price", {}).get("total")
                if price_str:
                    try:
                        prices.append(float(price_str))
                    except ValueError:
                        continue
            
            if prices:
                return {
                    "min": min(prices),
                    "max": max(prices),
                    "average": sum(prices) / len(prices)
                }
            
            return None
            
        except Exception:
            return None
    
    def _create_comparison_matrix(self, hotels: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a comparison matrix for hotels."""
        try:
            if not hotels:
                return {}
            
            comparison_fields = ["name", "rating", "price", "amenities", "location"]
            matrix = {}
            
            for field in comparison_fields:
                matrix[field] = []
                for hotel in hotels:
                    if field == "price":
                        matrix[field].append(hotel.get("price", {}).get("total", "N/A"))
                    elif field == "amenities":
                        matrix[field].append(len(hotel.get("amenities", [])))
                    elif field == "location":
                        address = hotel.get("location", {}).get("address", {})
                        matrix[field].append(address.get("cityName", "N/A"))
                    else:
                        matrix[field].append(hotel.get(field, "N/A"))
            
            return matrix
            
        except Exception as e:
            logger.error(f"Error creating comparison matrix: {e}")
            return {}