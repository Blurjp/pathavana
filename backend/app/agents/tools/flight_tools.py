"""
Flight search and booking tools for the AI agent.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ...services.amadeus_service import AmadeusService
from ...services.cache_service import CacheService

logger = logging.getLogger(__name__)


class FlightTools:
    """Tools for flight-related operations in the AI agent."""
    
    def __init__(self, amadeus_service: AmadeusService, cache_service: CacheService):
        self.amadeus_service = amadeus_service
        self.cache_service = cache_service
    
    async def search_flights(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for flights based on parameters.
        
        Args:
            search_params: Flight search parameters
            
        Returns:
            Flight search results
        """
        try:
            # Check cache first
            cached_results = await self.cache_service.get_cached_flight_search(search_params)
            if cached_results:
                logger.info("Returning cached flight search results")
                return {
                    "flights": cached_results["flights"],
                    "cached": True,
                    "search_params": search_params
                }
            
            # Validate required parameters
            required_params = ["destination", "departure_date"]
            missing_params = [param for param in required_params if not search_params.get(param)]
            
            if missing_params:
                return {
                    "error": f"Missing required parameters: {', '.join(missing_params)}",
                    "flights": []
                }
            
            # Prepare Amadeus API parameters
            amadeus_params = self._prepare_amadeus_flight_params(search_params)
            
            if not amadeus_params:
                return {
                    "error": "Invalid search parameters",
                    "flights": []
                }
            
            # Search flights using Amadeus
            amadeus_results = await self.amadeus_service.search_flights(**amadeus_params)
            
            if amadeus_results.get("error"):
                return {
                    "error": amadeus_results["error"],
                    "flights": []
                }
            
            # Process and enhance results
            processed_results = self._process_flight_results(
                amadeus_results, 
                search_params
            )
            
            # Cache the results
            await self.cache_service.cache_flight_search(search_params, processed_results)
            
            return {
                "flights": processed_results["flights"],
                "cached": False,
                "search_params": search_params,
                "total_results": len(processed_results["flights"])
            }
            
        except Exception as e:
            logger.error(f"Error searching flights: {e}")
            return {
                "error": f"Flight search failed: {str(e)}",
                "flights": []
            }
    
    async def get_flight_details(self, flight_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific flight."""
        try:
            # In a real implementation, this would fetch detailed flight information
            # For now, return a placeholder
            return {
                "flight_id": flight_id,
                "details": "Detailed flight information would be fetched here",
                "available": True
            }
            
        except Exception as e:
            logger.error(f"Error getting flight details: {e}")
            return {
                "error": f"Failed to get flight details: {str(e)}",
                "flight_id": flight_id
            }
    
    async def check_flight_availability(self, flight_id: str) -> bool:
        """Check if a flight is still available for booking."""
        try:
            # Implementation would check real-time availability
            return True  # Placeholder
            
        except Exception as e:
            logger.error(f"Error checking flight availability: {e}")
            return False
    
    async def get_price_alerts(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """Set up price alerts for flight searches."""
        try:
            # Implementation would set up price monitoring
            return {
                "alert_id": "alert_123",
                "message": "Price alert set up successfully",
                "search_params": search_params
            }
            
        except Exception as e:
            logger.error(f"Error setting up price alerts: {e}")
            return {
                "error": f"Failed to set up price alerts: {str(e)}"
            }
    
    async def compare_airlines(
        self, 
        search_params: Dict[str, Any],
        airlines: List[str]
    ) -> Dict[str, Any]:
        """Compare specific airlines for a route."""
        try:
            # Search for flights
            all_results = await self.search_flights(search_params)
            
            if all_results.get("error"):
                return all_results
            
            # Filter by airlines
            airline_comparison = {}
            
            for flight in all_results["flights"]:
                for itinerary in flight.get("itineraries", []):
                    for segment in itinerary.get("segments", []):
                        carrier = segment.get("carrier")
                        if carrier in airlines:
                            if carrier not in airline_comparison:
                                airline_comparison[carrier] = []
                            airline_comparison[carrier].append(flight)
            
            return {
                "comparison": airline_comparison,
                "airlines_found": list(airline_comparison.keys()),
                "search_params": search_params
            }
            
        except Exception as e:
            logger.error(f"Error comparing airlines: {e}")
            return {
                "error": f"Airline comparison failed: {str(e)}"
            }
    
    def _prepare_amadeus_flight_params(self, search_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Prepare parameters for Amadeus API call."""
        try:
            amadeus_params = {
                "destination": search_params["destination"],
                "departure_date": search_params["departure_date"],
                "adults": search_params.get("adults", 1),
                "children": search_params.get("children", 0),
                "infants": search_params.get("infants", 0),
                "travel_class": search_params.get("travel_class", "ECONOMY"),
                "max_results": search_params.get("max_results", 10)
            }
            
            # Add origin if provided
            if search_params.get("origin"):
                amadeus_params["origin"] = search_params["origin"]
            
            # Add return date if provided
            if search_params.get("return_date"):
                amadeus_params["return_date"] = search_params["return_date"]
            
            return amadeus_params
            
        except Exception as e:
            logger.error(f"Error preparing Amadeus parameters: {e}")
            return None
    
    def _process_flight_results(
        self, 
        amadeus_results: Dict[str, Any], 
        search_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process and enhance flight results."""
        try:
            flights = amadeus_results.get("flights", [])
            
            # Sort flights by price (lowest first)
            flights.sort(key=lambda x: float(x.get("price", {}).get("total", "999999")))
            
            # Add enhanced information
            for flight in flights:
                # Calculate total travel time
                flight["total_duration"] = self._calculate_total_duration(flight)
                
                # Categorize flight (direct, one-stop, multi-stop)
                flight["flight_type"] = self._categorize_flight(flight)
                
                # Add convenience score
                flight["convenience_score"] = self._calculate_convenience_score(flight)
                
                # Add airline information
                flight["airlines"] = self._extract_airlines(flight)
            
            # Add search metadata
            processed_results = {
                "flights": flights,
                "search_metadata": {
                    "search_params": search_params,
                    "result_count": len(flights),
                    "search_time": datetime.utcnow().isoformat(),
                    "cheapest_price": flights[0].get("price", {}).get("total") if flights else None,
                    "price_range": self._calculate_price_range(flights)
                }
            }
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error processing flight results: {e}")
            return {"flights": amadeus_results.get("flights", [])}
    
    def _calculate_total_duration(self, flight: Dict[str, Any]) -> Optional[str]:
        """Calculate total travel duration for a flight."""
        try:
            total_minutes = 0
            
            for itinerary in flight.get("itineraries", []):
                duration_str = itinerary.get("duration", "")
                if duration_str:
                    # Parse ISO 8601 duration format (PT1H30M)
                    # Simplified parsing - in production, use proper ISO duration parser
                    import re
                    hours_match = re.search(r'(\d+)H', duration_str)
                    minutes_match = re.search(r'(\d+)M', duration_str)
                    
                    hours = int(hours_match.group(1)) if hours_match else 0
                    minutes = int(minutes_match.group(1)) if minutes_match else 0
                    
                    total_minutes += (hours * 60) + minutes
            
            if total_minutes > 0:
                hours = total_minutes // 60
                minutes = total_minutes % 60
                return f"{hours}h {minutes}m"
            
            return None
            
        except Exception as e:
            logger.warning(f"Error calculating flight duration: {e}")
            return None
    
    def _categorize_flight(self, flight: Dict[str, Any]) -> str:
        """Categorize flight as direct, one-stop, or multi-stop."""
        try:
            max_segments = 0
            
            for itinerary in flight.get("itineraries", []):
                segments = itinerary.get("segments", [])
                max_segments = max(max_segments, len(segments))
            
            if max_segments == 1:
                return "direct"
            elif max_segments == 2:
                return "one-stop"
            else:
                return "multi-stop"
                
        except Exception:
            return "unknown"
    
    def _calculate_convenience_score(self, flight: Dict[str, Any]) -> float:
        """Calculate a convenience score for the flight (0-10)."""
        try:
            score = 5.0  # Base score
            
            # Bonus for direct flights
            if self._categorize_flight(flight) == "direct":
                score += 2.0
            elif self._categorize_flight(flight) == "one-stop":
                score += 1.0
            
            # Bonus for reasonable departure times (6 AM - 10 PM)
            for itinerary in flight.get("itineraries", []):
                for segment in itinerary.get("segments", []):
                    departure_time = segment.get("departure", {}).get("time", "")
                    if departure_time:
                        try:
                            # Extract hour from ISO timestamp
                            hour = int(departure_time.split("T")[1][:2])
                            if 6 <= hour <= 22:
                                score += 0.5
                        except:
                            pass
            
            # Cap at 10
            return min(10.0, score)
            
        except Exception:
            return 5.0  # Default score
    
    def _extract_airlines(self, flight: Dict[str, Any]) -> List[str]:
        """Extract unique airlines from flight segments."""
        airlines = set()
        
        try:
            for itinerary in flight.get("itineraries", []):
                for segment in itinerary.get("segments", []):
                    carrier = segment.get("carrier")
                    if carrier:
                        airlines.add(carrier)
            
            return list(airlines)
            
        except Exception:
            return []
    
    def _calculate_price_range(self, flights: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
        """Calculate price range for flights."""
        try:
            if not flights:
                return None
            
            prices = []
            for flight in flights:
                price_str = flight.get("price", {}).get("total")
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