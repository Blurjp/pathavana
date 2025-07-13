"""
Activity and attraction recommendation tools for the AI agent.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ...services.cache_service import CacheService

logger = logging.getLogger(__name__)


class ActivityTools:
    """Tools for activity and attraction recommendations."""
    
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        # In production, you would integrate with activity APIs like TripAdvisor, Viator, etc.
        self.activity_database = self._load_activity_database()
    
    async def get_activity_recommendations(
        self, 
        destination: Dict[str, Any],
        preferences: List[str],
        duration_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get activity recommendations for a destination.
        
        Args:
            destination: Destination information
            preferences: User preferences
            duration_days: Trip duration in days
            
        Returns:
            Activity recommendations
        """
        try:
            # Create cache key
            cache_key = self._create_activity_cache_key(destination, preferences)
            
            # Check cache first
            cached_results = await self.cache_service.get(cache_key)
            if cached_results:
                logger.info("Returning cached activity recommendations")
                return {
                    "activities": cached_results,
                    "cached": True,
                    "destination": destination
                }
            
            # Get destination info
            resolved_dest = destination.get("resolved", {})
            city_name = resolved_dest.get("city_name", "").lower()
            country = resolved_dest.get("country", "").lower()
            
            if not city_name:
                return {
                    "error": "Invalid destination for activity search",
                    "activities": []
                }
            
            # Get activities for the destination
            destination_activities = self._get_activities_for_destination(
                city_name, 
                country
            )
            
            # Filter and score activities based on preferences
            scored_activities = self._score_activities_by_preferences(
                destination_activities, 
                preferences
            )
            
            # Create itinerary if duration is provided
            itinerary = None
            if duration_days and duration_days > 0:
                itinerary = self._create_activity_itinerary(
                    scored_activities, 
                    duration_days
                )
            
            # Prepare response
            recommendations = {
                "activities": scored_activities[:15],  # Top 15 activities
                "total_found": len(scored_activities),
                "destination": destination,
                "preferences_applied": preferences,
                "categories": self._categorize_activities(scored_activities),
                "itinerary": itinerary
            }
            
            # Cache the results
            await self.cache_service.set(
                cache_key, 
                recommendations["activities"], 
                ttl=86400  # 24 hours
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting activity recommendations: {e}")
            return {
                "error": f"Activity search failed: {str(e)}",
                "activities": []
            }
    
    async def get_activities_by_category(
        self, 
        destination: Dict[str, Any],
        category: str
    ) -> Dict[str, Any]:
        """Get activities filtered by category."""
        try:
            # Get all activities first
            all_activities = await self.get_activity_recommendations(
                destination, 
                []  # No preference filtering
            )
            
            if all_activities.get("error"):
                return all_activities
            
            # Filter by category
            category_activities = [
                activity for activity in all_activities["activities"]
                if activity.get("category", "").lower() == category.lower()
            ]
            
            return {
                "activities": category_activities,
                "category": category,
                "total_found": len(category_activities),
                "destination": destination
            }
            
        except Exception as e:
            logger.error(f"Error getting activities by category: {e}")
            return {
                "error": f"Category filtering failed: {str(e)}",
                "activities": []
            }
    
    async def get_activity_details(self, activity_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific activity."""
        try:
            # In production, this would fetch from an external API
            for city_activities in self.activity_database.values():
                for activity in city_activities:
                    if activity.get("id") == activity_id:
                        # Add additional details
                        detailed_activity = activity.copy()
                        detailed_activity.update({
                            "detailed_description": f"Detailed information about {activity['name']}",
                            "booking_info": {
                                "advance_booking_required": True,
                                "cancellation_policy": "Free cancellation up to 24 hours",
                                "payment_options": ["credit_card", "paypal"]
                            },
                            "reviews": {
                                "average_rating": 4.5,
                                "review_count": 1250,
                                "recent_reviews": [
                                    "Amazing experience!",
                                    "Great guide and beautiful sights",
                                    "Worth every penny"
                                ]
                            }
                        })
                        return detailed_activity
            
            return {
                "error": f"Activity {activity_id} not found"
            }
            
        except Exception as e:
            logger.error(f"Error getting activity details: {e}")
            return {
                "error": f"Failed to get activity details: {str(e)}"
            }
    
    async def search_activities_by_keywords(
        self, 
        destination: Dict[str, Any],
        keywords: List[str]
    ) -> Dict[str, Any]:
        """Search activities by keywords."""
        try:
            # Get all activities
            all_activities = await self.get_activity_recommendations(
                destination, 
                []
            )
            
            if all_activities.get("error"):
                return all_activities
            
            # Search by keywords
            matching_activities = []
            
            for activity in all_activities["activities"]:
                activity_text = (
                    f"{activity.get('name', '')} "
                    f"{activity.get('description', '')} "
                    f"{activity.get('category', '')} "
                    f"{' '.join(activity.get('tags', []))}"
                ).lower()
                
                # Check if any keyword matches
                if any(keyword.lower() in activity_text for keyword in keywords):
                    matching_activities.append(activity)
            
            return {
                "activities": matching_activities,
                "keywords": keywords,
                "total_found": len(matching_activities),
                "destination": destination
            }
            
        except Exception as e:
            logger.error(f"Error searching activities by keywords: {e}")
            return {
                "error": f"Keyword search failed: {str(e)}",
                "activities": []
            }
    
    async def get_family_friendly_activities(
        self, 
        destination: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get family-friendly activities."""
        return await self.get_activities_by_category(destination, "family")
    
    async def get_outdoor_activities(
        self, 
        destination: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get outdoor activities."""
        return await self.get_activities_by_category(destination, "outdoor")
    
    async def get_cultural_activities(
        self, 
        destination: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get cultural activities."""
        return await self.get_activities_by_category(destination, "cultural")
    
    def _create_activity_cache_key(
        self, 
        destination: Dict[str, Any], 
        preferences: List[str]
    ) -> str:
        """Create cache key for activity search."""
        resolved_dest = destination.get("resolved", {})
        city = resolved_dest.get("city_name", "")
        country = resolved_dest.get("country", "")
        prefs_str = "_".join(sorted(preferences))
        
        return f"activities:{city}_{country}_{prefs_str}"
    
    def _get_activities_for_destination(
        self, 
        city_name: str, 
        country: str
    ) -> List[Dict[str, Any]]:
        """Get activities for a specific destination."""
        # Normalize city name for lookup
        city_key = city_name.replace(" ", "_").lower()
        
        # First, try exact city match
        if city_key in self.activity_database:
            return self.activity_database[city_key].copy()
        
        # Then try partial matches
        for db_city, activities in self.activity_database.items():
            if city_key in db_city or db_city in city_key:
                return activities.copy()
        
        # If no specific data, return generic activities
        return self._get_generic_activities()
    
    def _score_activities_by_preferences(
        self, 
        activities: List[Dict[str, Any]], 
        preferences: List[str]
    ) -> List[Dict[str, Any]]:
        """Score and sort activities based on user preferences."""
        if not preferences:
            return activities
        
        scored_activities = []
        
        for activity in activities:
            score = self._calculate_activity_preference_score(activity, preferences)
            activity["preference_score"] = score
            scored_activities.append(activity)
        
        # Sort by score (highest first)
        scored_activities.sort(key=lambda x: x.get("preference_score", 0), reverse=True)
        
        return scored_activities
    
    def _calculate_activity_preference_score(
        self, 
        activity: Dict[str, Any], 
        preferences: List[str]
    ) -> float:
        """Calculate how well an activity matches preferences."""
        score = 0.0
        
        activity_category = activity.get("category", "").lower()
        activity_tags = [tag.lower() for tag in activity.get("tags", [])]
        activity_description = activity.get("description", "").lower()
        
        preference_weights = {
            "cultural": 2.0,
            "outdoor": 2.0,
            "adventure": 2.0,
            "family": 1.5,
            "budget": 1.0,
            "luxury": 1.5,
            "food": 1.5,
            "shopping": 1.0,
            "nightlife": 1.0,
            "relaxing": 1.0,
            "active": 1.5
        }
        
        for preference in preferences:
            pref_lower = preference.lower()
            weight = preference_weights.get(pref_lower, 1.0)
            
            # Check category match
            if pref_lower == activity_category:
                score += weight * 2.0
            
            # Check tags match
            if pref_lower in activity_tags:
                score += weight * 1.5
            
            # Check description match
            if pref_lower in activity_description:
                score += weight * 1.0
        
        # Add base popularity score
        score += activity.get("popularity", 5.0)
        
        return score
    
    def _create_activity_itinerary(
        self, 
        activities: List[Dict[str, Any]], 
        duration_days: int
    ) -> Dict[str, Any]:
        """Create a day-by-day activity itinerary."""
        try:
            itinerary = {}
            activities_per_day = 2  # Reasonable number of activities per day
            
            # Group activities by day
            for day in range(1, duration_days + 1):
                start_idx = (day - 1) * activities_per_day
                end_idx = start_idx + activities_per_day
                
                day_activities = activities[start_idx:end_idx]
                
                itinerary[f"day_{day}"] = {
                    "day": day,
                    "activities": day_activities,
                    "theme": self._determine_day_theme(day_activities)
                }
            
            return {
                "duration_days": duration_days,
                "daily_schedule": itinerary,
                "total_activities": len(activities),
                "notes": "This is a suggested itinerary. Feel free to adjust based on your preferences!"
            }
            
        except Exception as e:
            logger.error(f"Error creating itinerary: {e}")
            return {}
    
    def _determine_day_theme(self, activities: List[Dict[str, Any]]) -> str:
        """Determine the theme for a day based on activities."""
        if not activities:
            return "free_time"
        
        categories = [activity.get("category", "") for activity in activities]
        
        if "cultural" in categories:
            return "cultural_exploration"
        elif "outdoor" in categories:
            return "outdoor_adventure"
        elif "family" in categories:
            return "family_fun"
        else:
            return "mixed_activities"
    
    def _categorize_activities(self, activities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize activities and count by category."""
        categories = {}
        
        for activity in activities:
            category = activity.get("category", "other")
            categories[category] = categories.get(category, 0) + 1
        
        return categories
    
    def _get_generic_activities(self) -> List[Dict[str, Any]]:
        """Get generic activities when no specific data is available."""
        return [
            {
                "id": "generic_1",
                "name": "City Walking Tour",
                "category": "cultural",
                "description": "Explore the city's main attractions on foot",
                "duration_hours": 3,
                "price_range": "budget",
                "popularity": 8.0,
                "tags": ["walking", "sightseeing", "history"]
            },
            {
                "id": "generic_2", 
                "name": "Local Food Tour",
                "category": "food",
                "description": "Taste local cuisine and learn about culinary traditions",
                "duration_hours": 4,
                "price_range": "moderate",
                "popularity": 9.0,
                "tags": ["food", "culture", "local"]
            },
            {
                "id": "generic_3",
                "name": "Museum Visit",
                "category": "cultural",
                "description": "Visit the city's main museum",
                "duration_hours": 2,
                "price_range": "budget",
                "popularity": 7.0,
                "tags": ["museum", "art", "history"]
            }
        ]
    
    def _load_activity_database(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load activity database. In production, this would come from external APIs."""
        return {
            "new_york": [
                {
                    "id": "nyc_1",
                    "name": "Statue of Liberty Tour",
                    "category": "cultural",
                    "description": "Visit the iconic Statue of Liberty and Ellis Island",
                    "duration_hours": 4,
                    "price_range": "moderate",
                    "popularity": 9.5,
                    "tags": ["landmark", "history", "boat_tour"]
                },
                {
                    "id": "nyc_2",
                    "name": "Central Park Bike Ride",
                    "category": "outdoor",
                    "description": "Explore Central Park on a guided bike tour",
                    "duration_hours": 2,
                    "price_range": "budget",
                    "popularity": 8.5,
                    "tags": ["biking", "nature", "park"]
                },
                {
                    "id": "nyc_3",
                    "name": "Broadway Show",
                    "category": "entertainment",
                    "description": "Watch a world-class Broadway production",
                    "duration_hours": 3,
                    "price_range": "expensive",
                    "popularity": 9.8,
                    "tags": ["theater", "music", "entertainment"]
                }
            ],
            "paris": [
                {
                    "id": "par_1",
                    "name": "Eiffel Tower Visit",
                    "category": "cultural",
                    "description": "Visit the iconic Eiffel Tower and enjoy panoramic views",
                    "duration_hours": 2,
                    "price_range": "moderate",
                    "popularity": 9.7,
                    "tags": ["landmark", "views", "architecture"]
                },
                {
                    "id": "par_2",
                    "name": "Louvre Museum Tour",
                    "category": "cultural",
                    "description": "Explore the world's largest art museum",
                    "duration_hours": 4,
                    "price_range": "moderate",
                    "popularity": 9.2,
                    "tags": ["museum", "art", "history"]
                },
                {
                    "id": "par_3",
                    "name": "Seine River Cruise",
                    "category": "leisure",
                    "description": "Scenic boat cruise along the Seine River",
                    "duration_hours": 1.5,
                    "price_range": "moderate",
                    "popularity": 8.8,
                    "tags": ["boat", "sightseeing", "romantic"]
                }
            ],
            "london": [
                {
                    "id": "lon_1",
                    "name": "Tower of London Tour",
                    "category": "cultural",
                    "description": "Explore the historic Tower of London and Crown Jewels",
                    "duration_hours": 3,
                    "price_range": "moderate",
                    "popularity": 9.0,
                    "tags": ["history", "castle", "jewels"]
                },
                {
                    "id": "lon_2",
                    "name": "Thames River Cruise",
                    "category": "leisure",
                    "description": "Sightseeing cruise along the River Thames",
                    "duration_hours": 1,
                    "price_range": "budget",
                    "popularity": 8.5,
                    "tags": ["boat", "sightseeing", "river"]
                },
                {
                    "id": "lon_3",
                    "name": "British Museum Visit",
                    "category": "cultural",
                    "description": "Discover ancient artifacts at the British Museum",
                    "duration_hours": 3,
                    "price_range": "free",
                    "popularity": 9.3,
                    "tags": ["museum", "history", "artifacts"]
                }
            ]
        }