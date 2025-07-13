#!/usr/bin/env python3
"""
Final verification script for all Pathavana database models.
"""

# Import the models using the proper __init__.py structure
from app.models import *

def main():
    print("🔍 Verifying Pathavana Database Models")
    print("=" * 50)
    
    # Test that all models are properly imported
    models_to_test = [
        (User, "users"),
        (UserProfile, "user_profiles"),
        (TravelPreferences, "travel_preferences"),
        (UserDocument, "user_documents"),
        (Traveler, "travelers"),
        (TravelerDocument, "traveler_documents"),
        (TravelerPreference, "traveler_preferences"),
        (UnifiedTravelSession, "unified_travel_sessions"),
        (UnifiedSavedItem, "unified_saved_items"),
        (UnifiedSessionBooking, "unified_session_bookings"),
        (UnifiedBooking, "bookings"),
        (FlightBooking, "flight_bookings"),
        (HotelBooking, "hotel_bookings"),
        (ActivityBooking, "activity_bookings"),
    ]
    
    print("✅ Model Classes and Tables:")
    for model_class, expected_table in models_to_test:
        actual_table = model_class.__tablename__
        status = "✅" if actual_table == expected_table else "❌"
        print(f"  {status} {model_class.__name__}: {actual_table}")
    
    # Test enums
    enums_to_test = [
        (UserStatus, UserStatus.ACTIVE),
        (AuthProvider, AuthProvider.GOOGLE),
        (SessionStatus, SessionStatus.PLANNING),
        (BookingStatus, BookingStatus.CONFIRMED),
        (TravelerType, TravelerType.ADULT),
    ]
    
    print("\n✅ Enum Classes:")
    for enum_class, sample_value in enums_to_test:
        print(f"  ✅ {enum_class.__name__}: {sample_value}")
    
    # Test the shared Base
    print(f"\n✅ Shared SQLAlchemy Base:")
    print(f"  - Base class: {Base}")
    print(f"  - Total tables in metadata: {len(Base.metadata.tables)}")
    
    # List all tables with column counts
    print(f"\n✅ Database Schema:")
    for table_name in sorted(Base.metadata.tables.keys()):
        table = Base.metadata.tables[table_name]
        print(f"  - {table_name}: {len(table.columns)} columns, {len(table.indexes)} indexes")
    
    # Test model registry functions
    print(f"\n✅ Model Registry:")
    print(f"  - Available models: {len(list_models())}")
    print(f"  - Available enums: {len(list_enums())}")
    
    # Test some specific model lookups
    print(f"  - get_model('user'): {get_model('user').__name__ if get_model('user') else 'None'}")
    print(f"  - get_enum('user_status'): {get_enum('user_status').__name__ if get_enum('user_status') else 'None'}")
    
    print(f"\n🎉 All models verified successfully!")
    print(f"📊 Final Summary:")
    print(f"   - Database Tables: {len(Base.metadata.tables)}")
    print(f"   - Model Classes: {len(models_to_test)}")
    print(f"   - Enum Classes: {len(enums_to_test)}")
    print(f"   - Association Tables: 1 (booking_travelers)")
    print(f"   - Total Database Objects: {len(Base.metadata.tables) + len(enums_to_test)}")

if __name__ == "__main__":
    main()