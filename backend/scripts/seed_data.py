#!/usr/bin/env python3
"""
Comprehensive seed data for Pathavana development and testing.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, date
import random
import uuid
from typing import List

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_db_context
from app.models import (
    User, UserProfile, TravelPreferences, UserDocument,
    UnifiedTravelSession, UnifiedSavedItem, UnifiedSessionBooking,
    UnifiedBooking, FlightBooking, HotelBooking, ActivityBooking,
    Traveler, TravelerDocument, TravelerPreference,
    UserStatus, AuthProvider, DocumentType,
    TravelerType, TravelerStatus, TravelerDocumentStatus,
    SessionStatus, BookingStatus, PaymentStatus, BookingType
)
from sqlalchemy import select


class SeedDataGenerator:
    """Generate comprehensive seed data for testing."""
    
    def __init__(self):
        self.users = []
        self.travelers = []
        self.sessions = []
        self.bookings = []
        
        # Sample data pools
        self.first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emma", "Robert", "Lisa", "William", "Maria"]
        self.last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        self.cities = ["Paris", "London", "Tokyo", "New York", "Barcelona", "Rome", "Sydney", "Dubai", "Singapore", "Amsterdam"]
        self.airlines = ["AA", "BA", "DL", "UA", "LH", "AF", "EK", "SQ", "QF", "KL"]
        self.hotels = ["Hilton", "Marriott", "Hyatt", "InterContinental", "Sheraton", "Westin", "Four Seasons", "Ritz-Carlton"]
        self.activities = ["City Tour", "Museum Visit", "Food Tour", "Boat Trip", "Walking Tour", "Cooking Class", "Wine Tasting", "Adventure Tour"]
    
    async def generate_users(self, session, count: int = 10) -> List[User]:
        """Generate test users with profiles and preferences."""
        print(f"Generating {count} users...")
        
        for i in range(count):
            # Create user
            user = User(
                email=f"user{i+1}@pathavana.com",
                username=f"user_{i+1}",
                full_name=f"{random.choice(self.first_names)} {random.choice(self.last_names)}",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH4RSJDjE2",  # demo123
                phone_number=f"+1{random.randint(2000000000, 9999999999)}",
                email_verified=True,
                status=UserStatus.ACTIVE,
                auth_provider=AuthProvider.LOCAL,
                last_login_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            session.add(user)
            self.users.append(user)
        
        await session.flush()
        
        # Create profiles and preferences
        for user in self.users:
            # Profile
            profile = UserProfile(
                user_id=user.id,
                bio=f"Travel enthusiast who loves exploring new places!",
                date_of_birth=date(1970 + random.randint(15, 40), random.randint(1, 12), random.randint(1, 28)),
                nationality=random.choice(["US", "GB", "CA", "AU", "FR", "DE", "JP", "IN"]),
                preferred_language=random.choice(["en", "es", "fr", "de", "ja"]),
                preferred_currency=random.choice(["USD", "EUR", "GBP", "JPY"]),
                timezone=random.choice(["America/New_York", "Europe/London", "Asia/Tokyo", "Australia/Sydney"]),
                dietary_restrictions=random.choice([None, ["vegetarian"], ["vegan"], ["gluten-free"], ["halal"]]),
                gdpr_consent=True,
                gdpr_consent_date=datetime.utcnow(),
                notification_preferences={
                    "email": True,
                    "sms": random.choice([True, False]),
                    "push": True,
                    "marketing": random.choice([True, False])
                }
            )
            session.add(profile)
            
            # Travel preferences
            preferences = TravelPreferences(
                user_id=user.id,
                preferred_airlines=random.sample(self.airlines, k=random.randint(1, 3)),
                preferred_cabin_class=random.choice(["economy", "premium_economy", "business", "first"]),
                preferred_seat_type=random.choice(["aisle", "window", "middle"]),
                hotel_star_rating_min=random.randint(3, 5),
                budget_range_min=random.randint(500, 2000),
                budget_range_max=random.randint(3000, 10000),
                preferred_activities=random.sample(["sightseeing", "museums", "food", "adventure", "relaxation", "nightlife", "shopping"], k=3),
                travel_pace=random.choice(["slow", "moderate", "fast"]),
                interests=random.sample(["culture", "history", "nature", "architecture", "photography", "sports", "music"], k=3),
                travel_style=random.sample(["luxury", "comfort", "budget", "adventure", "cultural", "relaxation"], k=2)
            )
            session.add(preferences)
            
            # Add travel documents
            if random.random() > 0.3:  # 70% have documents
                doc = UserDocument(
                    user_id=user.id,
                    document_type=DocumentType.PASSPORT,
                    document_number=f"P{random.randint(10000000, 99999999)}",
                    issuing_country=profile.nationality,
                    issue_date=date.today() - timedelta(days=random.randint(365, 3650)),
                    expiry_date=date.today() + timedelta(days=random.randint(365, 3650)),
                    verified=True,
                    verified_at=datetime.utcnow()
                )
                session.add(doc)
        
        await session.flush()
        return self.users
    
    async def generate_travelers(self, session) -> List[Traveler]:
        """Generate travelers (companions) for some users."""
        print("Generating travelers...")
        
        # Add travelers for 50% of users
        for user in random.sample(self.users, k=len(self.users) // 2):
            # Add 1-3 travelers per user
            num_travelers = random.randint(1, 3)
            
            for i in range(num_travelers):
                traveler_type = random.choice([TravelerType.ADULT, TravelerType.ADULT, TravelerType.CHILD])
                
                traveler = Traveler(
                    user_id=user.id,
                    traveler_type=traveler_type,
                    first_name=random.choice(self.first_names),
                    last_name=random.choice(self.last_names),
                    date_of_birth=date.today() - timedelta(
                        days=365 * (random.randint(5, 12) if traveler_type == TravelerType.CHILD else random.randint(25, 65))
                    ),
                    gender=random.choice(["male", "female", "other"]),
                    nationality=random.choice(["US", "GB", "CA", "AU"]),
                    email=f"traveler_{uuid.uuid4().hex[:8]}@example.com" if traveler_type == TravelerType.ADULT else None,
                    is_primary=False,
                    relationship_to_primary=random.choice(["spouse", "partner", "child", "parent", "friend"]),
                    dietary_restrictions=random.choice([None, ["vegetarian"], ["vegan"]]),
                    status=TravelerStatus.ACTIVE
                )
                
                if traveler_type == TravelerType.CHILD:
                    traveler.requires_guardian_consent = True
                    traveler.guardian_name = user.full_name
                    traveler.guardian_relationship = "parent"
                
                session.add(traveler)
                self.travelers.append(traveler)
                
                # Add travel document for traveler
                if random.random() > 0.4:  # 60% have documents
                    doc = TravelerDocument(
                        traveler_id=traveler.id,
                        document_type=DocumentType.PASSPORT,
                        document_number=f"P{random.randint(10000000, 99999999)}",
                        issuing_country=traveler.nationality or "US",
                        issue_date=date.today() - timedelta(days=random.randint(365, 3650)),
                        expiry_date=date.today() + timedelta(days=random.randint(365, 3650)),
                        status=TravelerDocumentStatus.VERIFIED,
                        verified_at=datetime.utcnow()
                    )
                    session.add(doc)
        
        await session.flush()
        return self.travelers
    
    async def generate_sessions(self, session) -> List[UnifiedTravelSession]:
        """Generate travel sessions with various states."""
        print("Generating travel sessions...")
        
        session_templates = [
            {
                "status": SessionStatus.ACTIVE,
                "chat_starter": "I want to plan a vacation to {destination}",
                "intent": {"type": "vacation", "flexible_dates": True}
            },
            {
                "status": SessionStatus.PLANNING,
                "chat_starter": "Looking for a romantic getaway to {destination} for our anniversary",
                "intent": {"type": "romantic", "occasion": "anniversary"}
            },
            {
                "status": SessionStatus.PLANNING,
                "chat_starter": "Need to book a business trip to {destination} next month",
                "intent": {"type": "business", "urgency": "high"}
            },
            {
                "status": SessionStatus.BOOKED,
                "chat_starter": "Family vacation to {destination} with kids",
                "intent": {"type": "family", "has_children": True}
            },
            {
                "status": SessionStatus.COMPLETED,
                "chat_starter": "Weekend trip to {destination}",
                "intent": {"type": "weekend", "duration": "short"}
            }
        ]
        
        # Create 2-5 sessions per user
        for user in self.users:
            num_sessions = random.randint(2, 5)
            
            for _ in range(num_sessions):
                template = random.choice(session_templates)
                destination = random.choice(self.cities)
                
                # Build session data
                session_data = {
                    "chat_messages": [
                        {
                            "role": "user",
                            "content": template["chat_starter"].format(destination=destination),
                            "timestamp": (datetime.utcnow() - timedelta(days=random.randint(0, 60))).isoformat()
                        },
                        {
                            "role": "assistant",
                            "content": f"I'd be happy to help you plan your trip to {destination}! Let me gather some information.",
                            "timestamp": (datetime.utcnow() - timedelta(days=random.randint(0, 60))).isoformat()
                        }
                    ],
                    "parsed_intent": {
                        "destination": destination,
                        **template["intent"]
                    },
                    "ui_state": {
                        "current_step": random.choice(["destination", "dates", "travelers", "preferences", "search", "results"])
                    }
                }
                
                # Add plan data for planning/booked/completed sessions
                plan_data = None
                if template["status"] in [SessionStatus.PLANNING, SessionStatus.BOOKED, SessionStatus.COMPLETED]:
                    start_date = date.today() + timedelta(days=random.randint(30, 180))
                    end_date = start_date + timedelta(days=random.randint(3, 14))
                    
                    plan_data = {
                        "title": f"{destination} {template['intent']['type'].title()} Trip",
                        "destination_city": destination,
                        "destination_country": "FR" if destination == "Paris" else "GB",
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "travelers_count": random.randint(1, 4),
                        "estimated_budget": {
                            "total": random.randint(2000, 10000),
                            "currency": "USD",
                            "breakdown": {
                                "flights": random.randint(800, 3000),
                                "accommodation": random.randint(600, 2000),
                                "activities": random.randint(300, 1000),
                                "meals": random.randint(200, 800)
                            }
                        }
                    }
                
                travel_session = UnifiedTravelSession(
                    user_id=user.id,
                    status=template["status"],
                    session_data=session_data,
                    plan_data=plan_data,
                    search_parameters={
                        "origin": "NYC",
                        "destination": destination,
                        "departure_date": start_date.isoformat() if plan_data else None,
                        "return_date": end_date.isoformat() if plan_data else None,
                        "adults": random.randint(1, 2),
                        "children": random.randint(0, 2)
                    } if plan_data else None,
                    expires_at=datetime.utcnow() + timedelta(days=90),
                    last_activity_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                )
                
                session.add(travel_session)
                self.sessions.append(travel_session)
        
        await session.flush()
        
        # Add saved items to some sessions
        for travel_session in random.sample(self.sessions, k=len(self.sessions) // 2):
            # Add 2-5 saved items
            num_items = random.randint(2, 5)
            
            for i in range(num_items):
                item_type = random.choice(["flight", "hotel", "activity"])
                
                if item_type == "flight":
                    item_data = {
                        "type": "flight",
                        "airline": random.choice(self.airlines),
                        "flight_number": f"{random.choice(self.airlines)}{random.randint(100, 999)}",
                        "departure": "JFK",
                        "arrival": random.choice(["CDG", "LHR", "NRT", "SYD"]),
                        "departure_time": (datetime.utcnow() + timedelta(days=random.randint(30, 90))).isoformat(),
                        "duration": random.randint(180, 720),
                        "price": random.randint(400, 2000)
                    }
                elif item_type == "hotel":
                    item_data = {
                        "type": "hotel",
                        "name": f"{random.choice(self.hotels)} {travel_session.plan_data['destination_city'] if travel_session.plan_data else 'City'}",
                        "rating": random.randint(3, 5),
                        "price_per_night": random.randint(100, 500),
                        "amenities": random.sample(["wifi", "pool", "gym", "spa", "restaurant", "bar"], k=3)
                    }
                else:  # activity
                    item_data = {
                        "type": "activity",
                        "name": random.choice(self.activities),
                        "duration": f"{random.randint(1, 8)} hours",
                        "price_per_person": random.randint(30, 200),
                        "rating": round(random.uniform(4.0, 5.0), 1)
                    }
                
                saved_item = UnifiedSavedItem(
                    session_id=travel_session.id,
                    item_type=item_type,
                    item_data=item_data,
                    provider_reference=f"{item_type.upper()}-{uuid.uuid4().hex[:8]}",
                    price_snapshot={
                        "amount": item_data.get("price", item_data.get("price_per_night", item_data.get("price_per_person", 0))),
                        "currency": "USD",
                        "captured_at": datetime.utcnow().isoformat()
                    },
                    is_selected=i == 0,  # Select first item
                    selection_order=i if i == 0 else None
                )
                
                session.add(saved_item)
        
        return self.sessions
    
    async def generate_bookings(self, session) -> List[UnifiedBooking]:
        """Generate bookings for booked/completed sessions."""
        print("Generating bookings...")
        
        booked_sessions = [s for s in self.sessions if s.status in [SessionStatus.BOOKED, SessionStatus.COMPLETED]]
        
        for travel_session in booked_sessions:
            # Create 1-3 bookings per session
            num_bookings = random.randint(1, 3)
            booking_types = random.sample([BookingType.FLIGHT, BookingType.HOTEL, BookingType.ACTIVITY], k=num_bookings)
            
            for booking_type in booking_types:
                # Create main booking
                booking = UnifiedBooking(
                    user_id=travel_session.user_id,
                    booking_type=booking_type,
                    status=BookingStatus.CONFIRMED if travel_session.status == SessionStatus.BOOKED else BookingStatus.COMPLETED,
                    payment_status=PaymentStatus.COMPLETED,
                    provider_name=random.choice(["Amadeus", "Booking.com", "Expedia", "Viator"]),
                    provider_booking_reference=f"PBR-{uuid.uuid4().hex[:8].upper()}",
                    internal_reference=f"PTH-{uuid.uuid4().hex[:8].upper()}",
                    booking_data={
                        "confirmation_email_sent": True,
                        "booking_date": datetime.utcnow().isoformat()
                    },
                    total_amount=random.randint(500, 5000),
                    currency="USD",
                    base_amount=random.randint(400, 4500),
                    taxes=random.randint(50, 300),
                    fees=random.randint(20, 100),
                    payment_method="credit_card",
                    payment_details={
                        "last_four": random.randint(1000, 9999),
                        "card_type": random.choice(["visa", "mastercard", "amex"])
                    }
                )
                
                session.add(booking)
                await session.flush()
                
                # Create specific booking details
                if booking_type == BookingType.FLIGHT:
                    flight = FlightBooking(
                        booking_id=booking.id,
                        departure_airport=random.choice(["JFK", "LAX", "ORD", "DFW"]),
                        arrival_airport=random.choice(["CDG", "LHR", "NRT", "SYD", "DXB"]),
                        departure_datetime=datetime.utcnow() + timedelta(days=random.randint(30, 180)),
                        arrival_datetime=datetime.utcnow() + timedelta(days=random.randint(30, 180), hours=random.randint(5, 15)),
                        airline_code=random.choice(self.airlines),
                        flight_number=f"{random.randint(100, 999)}",
                        cabin_class=random.choice(["economy", "premium_economy", "business"]),
                        is_refundable=random.choice([True, False]),
                        is_changeable=True,
                        baggage_allowance={
                            "cabin": "1x8kg",
                            "checked": "1x23kg"
                        }
                    )
                    session.add(flight)
                
                elif booking_type == BookingType.HOTEL:
                    hotel = HotelBooking(
                        booking_id=booking.id,
                        hotel_name=f"{random.choice(self.hotels)} {random.choice(self.cities)}",
                        hotel_address=f"{random.randint(1, 999)} {random.choice(['Main St', 'Park Ave', 'Broadway', 'Market St'])}",
                        hotel_city=random.choice(self.cities),
                        hotel_country=random.choice(["US", "FR", "GB", "JP"]),
                        check_in_date=date.today() + timedelta(days=random.randint(30, 180)),
                        check_out_date=date.today() + timedelta(days=random.randint(33, 190)),
                        room_type=random.choice(["Standard", "Deluxe", "Suite", "Executive"]),
                        number_of_rooms=random.randint(1, 2),
                        guests_per_room=random.randint(1, 4),
                        bed_preference=random.choice(["king", "queen", "twin"]),
                        meal_plan=random.choice(["room_only", "breakfast", "half_board", "full_board"]),
                        cancellation_deadline=datetime.utcnow() + timedelta(days=random.randint(20, 170))
                    )
                    session.add(hotel)
                
                else:  # ACTIVITY
                    activity = ActivityBooking(
                        booking_id=booking.id,
                        activity_name=random.choice(self.activities),
                        activity_description="An amazing experience you won't forget!",
                        provider_name=random.choice(["Viator", "GetYourGuide", "Local Provider"]),
                        location_name=random.choice(self.cities),
                        activity_date=date.today() + timedelta(days=random.randint(30, 180)),
                        start_time=datetime.strptime(f"{random.randint(8, 16)}:00", "%H:%M").time(),
                        duration_minutes=random.randint(60, 480),
                        number_of_participants=random.randint(1, 4),
                        includes=["Guide", "Transportation", "Entrance fees"],
                        meeting_point="Hotel lobby or designated meeting point"
                    )
                    session.add(activity)
                
                # Link booking to session
                session_booking = UnifiedSessionBooking(
                    session_id=travel_session.id,
                    booking_id=booking.id,
                    booking_order=1,
                    is_primary=True
                )
                session.add(session_booking)
                
                # Add travelers to booking (if any exist for this user)
                user_travelers = [t for t in self.travelers if t.user_id == travel_session.user_id]
                if user_travelers:
                    # Add the booking_travelers relationship
                    for traveler in random.sample(user_travelers, k=min(len(user_travelers), 2)):
                        await session.execute(
                            f"""
                            INSERT INTO booking_travelers (booking_id, traveler_id, is_primary, created_at)
                            VALUES ('{booking.id}', '{traveler.id}', false, CURRENT_TIMESTAMP)
                            """
                        )
                
                self.bookings.append(booking)
        
        return self.bookings
    
    async def generate_all(self, session):
        """Generate all seed data."""
        print("\nGenerating comprehensive seed data...")
        print("=" * 50)
        
        # Check if data already exists
        result = await session.execute(select(User).limit(1))
        if result.scalar():
            print("Database already contains data. Skipping seed generation.")
            return
        
        # Generate data in order
        await self.generate_users(session, count=20)
        await self.generate_travelers(session)
        await self.generate_sessions(session)
        await self.generate_bookings(session)
        
        # Commit all data
        await session.commit()
        
        print("\nSeed data generation completed!")
        print(f"  - Users: {len(self.users)}")
        print(f"  - Travelers: {len(self.travelers)}")
        print(f"  - Sessions: {len(self.sessions)}")
        print(f"  - Bookings: {len(self.bookings)}")
        print("\nSample login credentials:")
        print("  Email: user1@pathavana.com")
        print("  Password: demo123")


async def main():
    """Main function to run seed data generation."""
    generator = SeedDataGenerator()
    
    async with get_db_context() as session:
        await generator.generate_all(session)


if __name__ == "__main__":
    print("Pathavana Seed Data Generator")
    print("=" * 50)
    
    response = input("\nThis will generate comprehensive test data. Continue? (y/N): ")
    if response.lower() == 'y':
        asyncio.run(main())
    else:
        print("Seed data generation cancelled.")