"""
Trip context service for managing conversation context and travel state.
Includes conflict detection, smart resolution strategies, and multi-city support.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import re
import logging

from .destination_resolver import DestinationResolver
from .llm_service import LLMService

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts that can occur in trip planning."""
    DATE_CONFLICT = "date_conflict"
    DESTINATION_CONFLICT = "destination_conflict"
    TRAVELER_CONFLICT = "traveler_conflict"
    BUDGET_CONFLICT = "budget_conflict"
    DURATION_CONFLICT = "duration_conflict"
    PREFERENCE_CONFLICT = "preference_conflict"


class ResolutionStrategy(Enum):
    """Strategies for resolving conflicts."""
    MOST_RECENT = "most_recent"  # Use the most recently provided information
    MOST_SPECIFIC = "most_specific"  # Use the most specific/detailed information
    USER_CONFIRMATION = "user_confirmation"  # Ask user to confirm
    AI_RESOLUTION = "ai_resolution"  # Use AI to resolve based on context
    MERGE = "merge"  # Merge conflicting information


@dataclass
class TripContext:
    """Comprehensive trip context with conflict tracking."""
    # Core trip information
    departure_city: Optional[str] = None
    destination_city: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    travelers: Dict[str, int] = field(default_factory=lambda: {"adults": 1, "children": 0, "infants": 0})
    
    # Multi-city support
    destinations: List[Dict[str, Any]] = field(default_factory=list)
    city_durations: Dict[str, int] = field(default_factory=dict)
    
    # Trip details
    budget: Optional[Dict[str, Any]] = None
    preferences: List[str] = field(default_factory=list)
    trip_type: Optional[str] = None
    trip_purpose: Optional[str] = None
    
    # Conflict tracking
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    conflicts_resolved: List[str] = field(default_factory=list)
    confidence: float = 1.0
    
    # Metadata
    last_updated: Optional[str] = None
    created_at: Optional[str] = None
    
    def detect_conflicts(self, new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify conflicts between existing context and new data."""
        detected_conflicts = []
        
        # Date conflicts
        if new_data.get("start_date") and self.start_date:
            if new_data["start_date"] != self.start_date:
                detected_conflicts.append({
                    "type": ConflictType.DATE_CONFLICT,
                    "field": "start_date",
                    "existing": self.start_date,
                    "new": new_data["start_date"],
                    "severity": "high"
                })
        
        if new_data.get("end_date") and self.end_date:
            if new_data["end_date"] != self.end_date:
                detected_conflicts.append({
                    "type": ConflictType.DATE_CONFLICT,
                    "field": "end_date",
                    "existing": self.end_date,
                    "new": new_data["end_date"],
                    "severity": "high"
                })
        
        # Destination conflicts
        if new_data.get("destination_city") and self.destination_city:
            if new_data["destination_city"].lower() != self.destination_city.lower():
                detected_conflicts.append({
                    "type": ConflictType.DESTINATION_CONFLICT,
                    "field": "destination_city",
                    "existing": self.destination_city,
                    "new": new_data["destination_city"],
                    "severity": "medium"
                })
        
        # Traveler count conflicts
        new_travelers = new_data.get("travelers", {})
        for traveler_type in ["adults", "children", "infants"]:
            if new_travelers.get(traveler_type) is not None:
                if new_travelers[traveler_type] != self.travelers.get(traveler_type, 0):
                    detected_conflicts.append({
                        "type": ConflictType.TRAVELER_CONFLICT,
                        "field": f"travelers.{traveler_type}",
                        "existing": self.travelers.get(traveler_type, 0),
                        "new": new_travelers[traveler_type],
                        "severity": "medium"
                    })
        
        # Budget conflicts
        if new_data.get("budget") and self.budget:
            new_budget = new_data["budget"]
            if new_budget.get("amount") != self.budget.get("amount"):
                detected_conflicts.append({
                    "type": ConflictType.BUDGET_CONFLICT,
                    "field": "budget.amount",
                    "existing": self.budget.get("amount"),
                    "new": new_budget.get("amount"),
                    "severity": "low"
                })
        
        return detected_conflicts
    
    def resolve_conflicts(
        self, 
        conflicts: List[Dict[str, Any]], 
        strategy: ResolutionStrategy = ResolutionStrategy.MOST_RECENT
    ) -> None:
        """Apply conflict resolution strategy."""
        for conflict in conflicts:
            conflict_id = f"{conflict['field']}_{conflict['new']}"
            
            if strategy == ResolutionStrategy.MOST_RECENT:
                # Use the new value
                self._apply_resolution(conflict["field"], conflict["new"])
                self.conflicts_resolved.append(conflict_id)
            
            elif strategy == ResolutionStrategy.MOST_SPECIFIC:
                # Use the more specific value
                if self._is_more_specific(conflict["new"], conflict["existing"]):
                    self._apply_resolution(conflict["field"], conflict["new"])
                    self.conflicts_resolved.append(conflict_id)
            
            elif strategy == ResolutionStrategy.MERGE:
                # Merge values if possible
                merged = self._merge_values(
                    conflict["existing"], 
                    conflict["new"], 
                    conflict["field"]
                )
                if merged:
                    self._apply_resolution(conflict["field"], merged)
                    self.conflicts_resolved.append(conflict_id)
        
        # Update confidence based on conflicts
        self.confidence = max(0.5, self.confidence - (len(conflicts) * 0.1))
    
    def _apply_resolution(self, field: str, value: Any) -> None:
        """Apply resolved value to the appropriate field."""
        if "." in field:
            # Handle nested fields
            parts = field.split(".")
            if parts[0] == "travelers":
                self.travelers[parts[1]] = value
            elif parts[0] == "budget":
                if not self.budget:
                    self.budget = {}
                self.budget[parts[1]] = value
        else:
            # Handle top-level fields
            setattr(self, field, value)
    
    def _is_more_specific(self, new_value: Any, existing_value: Any) -> bool:
        """Determine if new value is more specific than existing."""
        # Date specificity (exact date > month > year)
        if isinstance(new_value, str) and isinstance(existing_value, str):
            new_parts = new_value.count("-")
            existing_parts = existing_value.count("-")
            return new_parts > existing_parts
        
        # Numeric specificity (non-zero > zero)
        if isinstance(new_value, (int, float)) and isinstance(existing_value, (int, float)):
            return abs(new_value) > abs(existing_value)
        
        # String specificity (longer > shorter)
        if isinstance(new_value, str) and isinstance(existing_value, str):
            return len(new_value) > len(existing_value)
        
        return False
    
    def _merge_values(self, existing: Any, new: Any, field: str) -> Optional[Any]:
        """Merge two conflicting values if possible."""
        if field == "preferences":
            # Merge preference lists
            if isinstance(existing, list) and isinstance(new, list):
                return list(set(existing + new))
        
        elif field.startswith("destinations"):
            # Merge destination lists
            if isinstance(existing, list) and isinstance(new, list):
                merged = existing.copy()
                for dest in new:
                    if dest not in merged:
                        merged.append(dest)
                return merged
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "departure_city": self.departure_city,
            "destination_city": self.destination_city,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "travelers": self.travelers,
            "destinations": self.destinations,
            "city_durations": self.city_durations,
            "budget": self.budget,
            "preferences": self.preferences,
            "trip_type": self.trip_type,
            "trip_purpose": self.trip_purpose,
            "conflicts": self.conflicts,
            "conflicts_resolved": self.conflicts_resolved,
            "confidence": self.confidence,
            "last_updated": self.last_updated,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TripContext":
        """Create TripContext from dictionary."""
        return cls(
            departure_city=data.get("departure_city"),
            destination_city=data.get("destination_city"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            travelers=data.get("travelers", {"adults": 1, "children": 0, "infants": 0}),
            destinations=data.get("destinations", []),
            city_durations=data.get("city_durations", {}),
            budget=data.get("budget"),
            preferences=data.get("preferences", []),
            trip_type=data.get("trip_type"),
            trip_purpose=data.get("trip_purpose"),
            conflicts=data.get("conflicts", []),
            conflicts_resolved=data.get("conflicts_resolved", []),
            confidence=data.get("confidence", 1.0),
            last_updated=data.get("last_updated"),
            created_at=data.get("created_at")
        )


class TripContextService:
    """Service for managing and interpreting travel conversation context."""
    
    def __init__(self):
        self.destination_resolver = DestinationResolver()
        self.llm_service = None  # Lazy initialization to avoid circular imports
    
    def _get_llm_service(self):
        """Lazy initialization of LLM service."""
        if not self.llm_service:
            self.llm_service = LLMService()
        return self.llm_service
    
    async def create_context(self, initial_data: Dict[str, Any] = None) -> TripContext:
        """Create a new trip context."""
        context = TripContext(
            created_at=datetime.utcnow().isoformat(),
            last_updated=datetime.utcnow().isoformat()
        )
        
        if initial_data:
            extracted = await self.extract_travel_entities(
                initial_data.get("message", ""), 
                {}
            )
            context = await self.update_context(context, extracted)
        
        return context
    
    async def update_context(
        self, 
        context: TripContext, 
        new_data: Dict[str, Any],
        resolution_strategy: ResolutionStrategy = ResolutionStrategy.AI_RESOLUTION
    ) -> TripContext:
        """Update context with new data, handling conflicts."""
        # Detect conflicts
        conflicts = context.detect_conflicts(new_data)
        
        if conflicts:
            # Handle conflicts based on strategy
            if resolution_strategy == ResolutionStrategy.AI_RESOLUTION:
                # Use AI to resolve conflicts
                resolved_data = await self._ai_resolve_conflicts(
                    context, 
                    new_data, 
                    conflicts
                )
                # Apply resolved data
                for key, value in resolved_data.items():
                    if value is not None:
                        context._apply_resolution(key, value)
            else:
                # Use specified strategy
                context.resolve_conflicts(conflicts, resolution_strategy)
        
        # Apply non-conflicting updates
        for key, value in new_data.items():
            if value is not None and not any(c["field"] == key for c in conflicts):
                if hasattr(context, key):
                    setattr(context, key, value)
        
        # Update metadata
        context.last_updated = datetime.utcnow().isoformat()
        
        return context
    
    async def _ai_resolve_conflicts(
        self, 
        context: TripContext, 
        new_data: Dict[str, Any], 
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use AI to intelligently resolve conflicts."""
        llm_service = self._get_llm_service()
        
        conflict_data = {
            "conflicts": conflicts,
            "existing_context": context.to_dict(),
            "new_data": new_data
        }
        
        resolution = await llm_service.resolve_conflicts(
            conflicts, 
            context.to_dict()
        )
        
        if resolution.get("resolved"):
            return resolution.get("resolution", {}).get("resolutions", {})
        
        # Fallback to most recent strategy
        resolved = {}
        for conflict in conflicts:
            resolved[conflict["field"]] = conflict["new"]
        
        return resolved
    
    async def extract_travel_entities(
        self, 
        message: str, 
        existing_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract travel entities from a user message using both rules and AI.
        
        Args:
            message: User's message text
            existing_context: Existing conversation context
            
        Returns:
            Dictionary of extracted entities
        """
        # First, use rule-based extraction
        rule_based = self._extract_entities_rule_based(message)
        
        # Then, enhance with AI extraction
        llm_service = self._get_llm_service()
        ai_extracted = await llm_service.parse_travel_query_to_json(
            message, 
            existing_context
        )
        
        # Merge results, preferring AI extraction for ambiguous cases
        merged = self._merge_extraction_results(rule_based, ai_extracted)
        
        return merged
    
    def _extract_entities_rule_based(self, message: str) -> Dict[str, Any]:
        """Rule-based entity extraction."""
        entities = {}
        
        # Extract destinations
        destinations = self._extract_destinations(message)
        if destinations:
            entities["destinations"] = destinations
            # Set primary destination
            if len(destinations) == 1:
                entities["destination_city"] = destinations[0].get("resolved", {}).get("city_name")
            elif len(destinations) >= 2:
                # Assume first is departure, second is destination
                entities["departure_city"] = destinations[0].get("resolved", {}).get("city_name")
                entities["destination_city"] = destinations[1].get("resolved", {}).get("city_name")
        
        # Extract dates
        dates = self._extract_dates(message)
        if dates:
            entities["start_date"] = dates.get("departure")
            entities["end_date"] = dates.get("return")
        
        # Extract passenger information
        passengers = self._extract_passengers(message)
        if passengers:
            entities["travelers"] = passengers
        
        # Extract preferences
        preferences = self._extract_preferences(message)
        if preferences:
            entities["preferences"] = preferences
        
        # Extract budget information
        budget = self._extract_budget(message)
        if budget:
            entities["budget"] = budget
        
        # Extract trip duration
        duration = self._extract_duration(message)
        if duration:
            entities["duration"] = duration
        
        # Determine trip type
        trip_type = self._determine_trip_type(message, entities)
        if trip_type:
            entities["trip_type"] = trip_type
        
        return entities
    
    def _merge_extraction_results(
        self, 
        rule_based: Dict[str, Any], 
        ai_based: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge rule-based and AI-based extraction results."""
        merged = {}
        
        # For each field, prefer AI if available and valid
        for key in set(list(rule_based.keys()) + list(ai_based.keys())):
            ai_value = ai_based.get(key)
            rule_value = rule_based.get(key)
            
            if ai_value and not ai_based.get("error"):
                merged[key] = ai_value
            elif rule_value:
                merged[key] = rule_value
        
        return merged
    
    def merge_context(
        self, 
        existing_context: Dict[str, Any], 
        new_entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge new entities with existing context intelligently.
        
        Args:
            existing_context: Current travel context
            new_entities: Newly extracted entities
            
        Returns:
            Merged context
        """
        # Convert to TripContext for advanced handling
        context = TripContext.from_dict(existing_context) if existing_context else TripContext()
        
        # Detect and handle conflicts
        conflicts = context.detect_conflicts(new_entities)
        
        if conflicts:
            # Use most recent strategy by default for synchronous method
            context.resolve_conflicts(conflicts, ResolutionStrategy.MOST_RECENT)
        
        # Apply updates
        merged = existing_context.copy() if existing_context else {}
        
        # Merge destinations
        if new_entities.get("destinations"):
            existing_destinations = merged.get("destinations", [])
            for dest in new_entities["destinations"]:
                if dest not in existing_destinations:
                    existing_destinations.append(dest)
            merged["destinations"] = existing_destinations
        
        # Merge dates (new dates override existing ones if more specific)
        if new_entities.get("start_date"):
            merged["start_date"] = new_entities["start_date"]
        if new_entities.get("end_date"):
            merged["end_date"] = new_entities["end_date"]
        
        # Merge passengers (new info overrides existing)
        if new_entities.get("travelers"):
            merged["travelers"] = {
                **merged.get("travelers", {}),
                **new_entities["travelers"]
            }
        
        # Merge preferences (accumulate)
        if new_entities.get("preferences"):
            existing_prefs = merged.get("preferences", [])
            for pref in new_entities["preferences"]:
                if pref not in existing_prefs:
                    existing_prefs.append(pref)
            merged["preferences"] = existing_prefs
        
        # Update other fields if new values exist
        for key in ["departure_city", "destination_city", "budget", "duration", "trip_type", "trip_purpose"]:
            if new_entities.get(key):
                merged[key] = new_entities[key]
        
        # Add conflict tracking
        merged["conflicts"] = context.conflicts
        merged["conflicts_resolved"] = context.conflicts_resolved
        merged["confidence"] = context.confidence
        
        # Add timestamp for context freshness
        merged["last_updated"] = datetime.utcnow().isoformat()
        
        return merged
    
    def validate_trip_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate trip context and identify missing information.
        
        Args:
            context: Travel context to validate
            
        Returns:
            Validation result with missing fields and suggestions
        """
        validation = {
            "is_complete": True,
            "missing_fields": [],
            "suggestions": [],
            "confidence": 1.0,
            "warnings": []
        }
        
        # Check for date conflicts
        start_date = context.get("start_date")
        end_date = context.get("end_date")
        
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                
                if start > end:
                    validation["warnings"].append("Return date is before departure date")
                    validation["confidence"] *= 0.5
                
                if start < datetime.now():
                    validation["warnings"].append("Departure date is in the past")
                    validation["confidence"] *= 0.8
                    
            except:
                pass
        
        # Required fields for different trip types
        trip_type = context.get("trip_type", "general")
        
        # Check destinations
        if not context.get("destination_city") and not context.get("destinations"):
            validation["missing_fields"].append("destination")
            validation["suggestions"].append("Where would you like to travel?")
        
        # Check departure location for flights
        if trip_type == "flight_search" and not context.get("departure_city"):
            validation["missing_fields"].append("departure_city")
            validation["suggestions"].append("Where will you be departing from?")
        
        # Check dates
        if not context.get("start_date"):
            validation["missing_fields"].append("start_date")
            validation["suggestions"].append("When would you like to depart?")
        
        # Check travelers
        if not context.get("travelers", {}).get("adults"):
            validation["suggestions"].append("How many travelers will be going?")
        
        # Multi-city validation
        destinations = context.get("destinations", [])
        if len(destinations) > 1 and not context.get("city_durations"):
            validation["suggestions"].append("How many days would you like to spend in each city?")
        
        # Update completion status
        validation["is_complete"] = len(validation["missing_fields"]) == 0
        validation["confidence"] = max(0.1, validation["confidence"] - (len(validation["missing_fields"]) * 0.2))
        
        return validation
    
    def generate_clarifying_questions(self, context: Dict[str, Any]) -> List[str]:
        """Generate clarifying questions based on context gaps."""
        questions = []
        validation = self.validate_trip_context(context)
        
        # Add validation suggestions
        questions.extend(validation.get("suggestions", []))
        
        # Add context-specific questions
        destinations = context.get("destinations", [])
        dates = context.get("dates", {})
        travelers = context.get("travelers", {})
        
        # Budget questions
        if not context.get("budget"):
            questions.append("What's your approximate budget for this trip?")
        
        # Preference questions
        if not context.get("preferences"):
            questions.append("Do you have any specific preferences for your trip (e.g., direct flights, luxury hotels)?")
        
        # Trip purpose
        if not context.get("trip_purpose"):
            questions.append("Is this trip for business or leisure?")
        
        # Hotel requirements
        if context.get("trip_type") in ["hotel_search", "trip_planning"]:
            if not context.get("hotel_preferences"):
                questions.append("What type of accommodation are you looking for?")
        
        # Activity interests
        if destinations and not context.get("activity_preferences"):
            questions.append("What types of activities interest you at your destination?")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_questions = []
        for q in questions:
            if q not in seen:
                seen.add(q)
                unique_questions.append(q)
        
        return unique_questions[:3]  # Limit to 3 questions
    
    def _extract_destinations(self, message: str) -> List[Dict[str, Any]]:
        """Extract destination information from message."""
        destinations = []
        
        # Common destination patterns
        patterns = [
            r'(?:to|fly to|going to|visit|travel to)\s+([^,\n\.]+)',
            r'(?:from|departing from|leaving from)\s+([^,\n\.]+)\s+to\s+([^,\n\.]+)',
            r'([A-Z]{3})\s*(?:to|->)\s*([A-Z]{3})',  # Airport codes
            r'in\s+([^,\n\.]+?)(?:\s+for|\s+from|\s+on|$)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z]{2})?)'  # City names
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                # Handle from-to patterns
                if len(match.groups()) == 2 and "from" in pattern:
                    # Extract both departure and destination
                    from_text = match.group(1).strip()
                    to_text = match.group(2).strip()
                    
                    from_resolved = self.destination_resolver.resolve_destination(from_text)
                    if from_resolved.get("resolved"):
                        destinations.append({
                            "original_text": from_text,
                            "resolved": from_resolved,
                            "type": "departure"
                        })
                    
                    to_resolved = self.destination_resolver.resolve_destination(to_text)
                    if to_resolved.get("resolved"):
                        destinations.append({
                            "original_text": to_text,
                            "resolved": to_resolved,
                            "type": "destination"
                        })
                else:
                    dest_text = match.group(1).strip()
                    
                    # Skip common false positives
                    if dest_text.lower() in ["the", "a", "an", "my", "our", "your"]:
                        continue
                    
                    # Resolve destination
                    resolved = self.destination_resolver.resolve_destination(dest_text)
                    if resolved.get("resolved"):
                        destinations.append({
                            "original_text": dest_text,
                            "resolved": resolved,
                            "type": "destination"
                        })
        
        return destinations
    
    def _extract_dates(self, message: str) -> Dict[str, Any]:
        """Extract date information from message."""
        dates = {}
        
        # Date patterns
        date_patterns = [
            (r'(?:on|for)\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?)', 'specific'),
            (r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'numeric'),
            (r'(?:next|this)\s+(\w+)', 'relative'),
            (r'(?:in|after)\s+(\d+)\s*(?:days?|weeks?|months?)', 'duration'),
            (r'(?:tomorrow|today|yesterday)', 'relative'),
            (r'(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}', 'month')
        ]
        
        for pattern, date_type in date_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                date_text = match.group(0)
                
                # Basic date parsing (in production, use a proper date parser)
                parsed_date = self._parse_date_text(date_text, date_type)
                if parsed_date:
                    # Determine if it's departure or return based on context
                    if any(word in message.lower()[:match.start()] for word in ["return", "back", "come back"]):
                        dates["return"] = parsed_date
                    else:
                        if "departure" not in dates:
                            dates["departure"] = parsed_date
                        elif "return" not in dates:
                            dates["return"] = parsed_date
        
        return dates
    
    def _extract_passengers(self, message: str) -> Dict[str, Any]:
        """Extract passenger information from message."""
        passengers = {}
        
        # Passenger patterns
        patterns = [
            (r'(\d+)\s*(?:adult|adults|person|people|passenger|passengers)', 'adults'),
            (r'(\d+)\s*(?:child|children|kids?)', 'children'),
            (r'(\d+)\s*(?:infant|infants|baby|babies)', 'infants'),
            (r'for\s+(\d+)(?!\s*(?:days?|nights?|weeks?))', 'adults'),  # "for 2" but not "for 2 days"
            (r'(\d+)\s*travelers?', 'adults'),
            (r'(?:solo|alone|myself|just me)', 'solo'),
            (r'(?:couple|two of us|both of us)', 'couple'),
            (r'family of\s*(\d+)', 'family')
        ]
        
        for pattern, passenger_type in patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                if passenger_type in ['adults', 'children', 'infants']:
                    count = int(match.group(1))
                    passengers[passenger_type] = count
                elif passenger_type == 'solo':
                    passengers['adults'] = 1
                elif passenger_type == 'couple':
                    passengers['adults'] = 2
                elif passenger_type == 'family':
                    family_size = int(match.group(1))
                    # Assume 2 adults and rest children for family
                    passengers['adults'] = 2
                    if family_size > 2:
                        passengers['children'] = family_size - 2
        
        return passengers
    
    def _extract_preferences(self, message: str) -> List[str]:
        """Extract travel preferences from message."""
        preferences = []
        
        # Preference patterns
        preference_map = {
            "budget": ["cheap", "budget", "affordable", "low cost", "economy", "save money"],
            "luxury": ["luxury", "premium", "first class", "business class", "expensive", "high-end", "5 star"],
            "direct": ["direct", "nonstop", "no stops", "non-stop"],
            "flexible": ["flexible", "any time", "open dates", "whenever"],
            "window": ["window seat"],
            "aisle": ["aisle seat"],
            "vegetarian": ["vegetarian", "vegan", "plant-based"],
            "wifi": ["wifi", "internet", "wi-fi"],
            "pool": ["pool", "swimming"],
            "spa": ["spa", "wellness", "massage"],
            "gym": ["gym", "fitness", "workout"],
            "parking": ["parking", "car park"],
            "pet_friendly": ["pet", "dog", "cat", "pet-friendly"],
            "family": ["family", "kids", "children", "family-friendly"],
            "romantic": ["romantic", "honeymoon", "couple", "romance"],
            "business": ["business", "work", "conference", "meeting"],
            "adventure": ["adventure", "hiking", "outdoor", "active"],
            "cultural": ["cultural", "museum", "history", "art"],
            "beach": ["beach", "seaside", "ocean", "coastal"],
            "mountain": ["mountain", "ski", "alpine", "hiking"]
        }
        
        message_lower = message.lower()
        for pref_type, keywords in preference_map.items():
            for keyword in keywords:
                if keyword in message_lower:
                    preferences.append(pref_type)
                    break
        
        return list(set(preferences))  # Remove duplicates
    
    def _extract_budget(self, message: str) -> Optional[Dict[str, Any]]:
        """Extract budget information from message."""
        budget_patterns = [
            (r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', 'USD', 'exact'),
            (r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|usd)', 'USD', 'exact'),
            (r'€(\d+(?:,\d{3})*(?:\.\d{2})?)', 'EUR', 'exact'),
            (r'£(\d+(?:,\d{3})*(?:\.\d{2})?)', 'GBP', 'exact'),
            (r'under\s+\$?(\d+(?:,\d{3})*)', 'USD', 'maximum'),
            (r'less than\s+\$?(\d+(?:,\d{3})*)', 'USD', 'maximum'),
            (r'around\s+\$?(\d+(?:,\d{3})*)', 'USD', 'approximate'),
            (r'about\s+\$?(\d+(?:,\d{3})*)', 'USD', 'approximate'),
            (r'between\s+\$?(\d+(?:,\d{3})*)\s*(?:and|to)\s*\$?(\d+(?:,\d{3})*)', 'USD', 'range')
        ]
        
        for pattern, currency, budget_type in budget_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                if budget_type == 'range':
                    min_amount = float(match.group(1).replace(",", ""))
                    max_amount = float(match.group(2).replace(",", ""))
                    return {
                        "min_amount": min_amount,
                        "max_amount": max_amount,
                        "currency": currency,
                        "type": budget_type
                    }
                else:
                    amount = float(match.group(1).replace(",", ""))
                    budget = {
                        "amount": amount,
                        "currency": currency,
                        "type": budget_type
                    }
                    
                    # Check if per person
                    if "per person" in message.lower() or "each" in message.lower():
                        budget["per_person"] = True
                    else:
                        budget["per_person"] = False
                    
                    return budget
        
        return None
    
    def _extract_duration(self, message: str) -> Optional[Dict[str, Any]]:
        """Extract trip duration from message."""
        duration_patterns = [
            (r'(\d+)\s*(?:day|days)', 'days'),
            (r'(\d+)\s*(?:week|weeks)', 'weeks'),
            (r'(\d+)\s*(?:night|nights)', 'nights'),
            (r'(?:weekend|long weekend)', 'weekend'),
            (r'(?:month|months)', 'month')
        ]
        
        for pattern, unit in duration_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                if unit in ['weekend', 'month']:
                    if unit == 'weekend':
                        return {"value": 2, "unit": "days", "type": "weekend"}
                    else:
                        return {"value": 30, "unit": "days", "type": "month"}
                else:
                    value = int(match.group(1))
                    return {"value": value, "unit": unit}
        
        return None
    
    def _determine_trip_type(
        self, 
        message: str, 
        entities: Dict[str, Any]
    ) -> Optional[str]:
        """Determine the type of trip based on message and entities."""
        message_lower = message.lower()
        
        # Flight-related keywords
        flight_keywords = ["flight", "fly", "plane", "airline", "book a flight", "airfare"]
        if any(keyword in message_lower for keyword in flight_keywords):
            return "flight_search"
        
        # Hotel-related keywords
        hotel_keywords = ["hotel", "accommodation", "stay", "room", "book a hotel", "lodging"]
        if any(keyword in message_lower for keyword in hotel_keywords):
            return "hotel_search"
        
        # Activity-related keywords
        activity_keywords = ["activity", "activities", "things to do", "attractions", "tour", "experience"]
        if any(keyword in message_lower for keyword in activity_keywords):
            return "activity_search"
        
        # Booking-related keywords
        booking_keywords = ["book", "reserve", "purchase", "buy"]
        if any(keyword in message_lower for keyword in booking_keywords):
            return "booking_assistance"
        
        # General trip planning
        planning_keywords = ["trip", "vacation", "travel", "plan", "itinerary", "journey", "holiday"]
        if any(keyword in message_lower for keyword in planning_keywords):
            return "trip_planning"
        
        # Default based on entities
        if entities.get("destinations") and entities.get("dates"):
            return "trip_planning"
        
        return "general_travel_info"
    
    def _parse_date_text(self, date_text: str, date_type: str) -> Optional[str]:
        """Parse date text to ISO format. Simplified implementation."""
        date_text = date_text.lower().strip()
        
        # Handle relative dates
        if date_text == "tomorrow":
            return (datetime.now() + timedelta(days=1)).date().isoformat()
        elif date_text == "today":
            return datetime.now().date().isoformat()
        elif date_text.startswith("next week"):
            return (datetime.now() + timedelta(days=7)).date().isoformat()
        elif date_text.startswith("next month"):
            return (datetime.now() + timedelta(days=30)).date().isoformat()
        
        # Handle duration-based dates
        duration_match = re.search(r'in\s+(\d+)\s*days?', date_text)
        if duration_match:
            days = int(duration_match.group(1))
            return (datetime.now() + timedelta(days=days)).date().isoformat()
        
        # For more complex dates, return a descriptive string
        # In production, use dateutil.parser or similar
        return date_text