"""
Pathavana Database Models

This module imports and exports all SQLAlchemy models for the Pathavana application.
Uses a unified architecture with JSONB storage for maximum flexibility while
maintaining proper relationships and performance through strategic indexing.

Key Design Principles:
1. UUID-based session management for consistency
2. JSONB storage for flexible schema evolution
3. Strategic indexing for performance
4. Proper relationships between models
5. Enum types for controlled vocabularies
6. Timezone-aware timestamps
7. GDPR compliance support

Models included:
- UnifiedTravelSession: Core session model with JSONB storage
- User, UserProfile, TravelPreferences, UserDocument: User management
- UserSession, TokenBlacklist, AuthenticationLog, OAuthConnection: Authentication & security
- UnifiedBooking, FlightBooking, HotelBooking, ActivityBooking: Booking management
- Traveler, TravelerDocument, TravelerPreference: Individual traveler profiles
"""

# Core imports for SQLAlchemy setup
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

# Create a single Base for all models to share
# This ensures all models use the same metadata and can reference each other
model_metadata = MetaData()
Base = declarative_base(metadata=model_metadata)

# Override Base in all model modules to ensure consistency
import sys
current_module = sys.modules[__name__]

# Import all models to register them with SQLAlchemy
# Order matters for foreign key relationships

# User models - base authentication and profiles
from . import user
user.Base = Base  # Override the Base in user module
from .user import (
    User,
    UserProfile, 
    TravelPreferences,
    UserDocument,
    UserStatus,
    AuthProvider,
    DocumentType
)

# Authentication models - security and session management
from . import auth
auth.Base = Base  # Override the Base in auth module
from .auth import (
    UserSession,
    TokenBlacklist,
    AuthenticationLog,
    OAuthConnection,
    PasswordResetToken,
    TokenType,
    AuthEventType
)

# Traveler models - individual traveler profiles for group bookings
from . import traveler
traveler.Base = Base  # Override the Base in traveler module
from .traveler import (
    Traveler,
    TravelerDocument,
    TravelerPreference,
    TravelerType,
    TravelerStatus,
    TravelerDocumentStatus
)

# Core session model - unified architecture with JSONB storage
from . import unified_travel_session
unified_travel_session.Base = Base  # Override the Base in unified_travel_session module
from .unified_travel_session import (
    UnifiedTravelSession,
    UnifiedSavedItem,
    UnifiedSessionBooking,
    SessionStatus
)

# Booking models - comprehensive booking management
from . import booking
booking.Base = Base  # Override the Base in booking module
from .booking import (
    UnifiedBooking,
    FlightBooking,
    HotelBooking,
    ActivityBooking,
    booking_travelers,  # Association table
    BookingStatus,
    PaymentStatus,
    BookingType
)

# Re-export Base for use in other modules
__all__ = [
    # SQLAlchemy base
    "Base",
    "model_metadata",
    
    # User models
    "User",
    "UserProfile",
    "TravelPreferences", 
    "UserDocument",
    "UserStatus",
    "AuthProvider",
    "DocumentType",
    
    # Authentication models
    "UserSession",
    "TokenBlacklist",
    "AuthenticationLog",
    "OAuthConnection",
    "PasswordResetToken",
    "TokenType",
    "AuthEventType",
    
    # Traveler models
    "Traveler",
    "TravelerDocument",
    "TravelerPreference",
    "TravelerType",
    "TravelerStatus", 
    "TravelerDocumentStatus",
    
    # Session models
    "UnifiedTravelSession",
    "UnifiedSavedItem",
    "UnifiedSessionBooking",
    "SessionStatus",
    
    # Booking models
    "UnifiedBooking",
    "FlightBooking",
    "HotelBooking",
    "ActivityBooking",
    "booking_travelers",
    "BookingStatus",
    "PaymentStatus",
    "BookingType",
]

# Model registry for dynamic access
MODEL_REGISTRY = {
    # User models
    'user': User,
    'user_profile': UserProfile,
    'travel_preferences': TravelPreferences,
    'user_document': UserDocument,
    
    # Authentication models
    'user_session': UserSession,
    'token_blacklist': TokenBlacklist,
    'authentication_log': AuthenticationLog,
    'oauth_connection': OAuthConnection,
    'password_reset_token': PasswordResetToken,
    
    # Traveler models
    'traveler': Traveler,
    'traveler_document': TravelerDocument,
    'traveler_preference': TravelerPreference,
    
    # Session models
    'unified_travel_session': UnifiedTravelSession,
    'unified_saved_item': UnifiedSavedItem,
    'unified_session_booking': UnifiedSessionBooking,
    
    # Booking models
    'unified_booking': UnifiedBooking,
    'flight_booking': FlightBooking,
    'hotel_booking': HotelBooking,
    'activity_booking': ActivityBooking,
}

# Enum registry for validation
ENUM_REGISTRY = {
    'user_status': UserStatus,
    'auth_provider': AuthProvider,
    'document_type': DocumentType,
    'token_type': TokenType,
    'auth_event_type': AuthEventType,
    'traveler_type': TravelerType,
    'traveler_status': TravelerStatus,
    'traveler_document_status': TravelerDocumentStatus,
    'session_status': SessionStatus,
    'booking_status': BookingStatus,
    'payment_status': PaymentStatus,
    'booking_type': BookingType,
}


def get_model(model_name: str):
    """
    Get a model class by name.
    
    Args:
        model_name: The name of the model to retrieve
        
    Returns:
        The model class or None if not found
    """
    return MODEL_REGISTRY.get(model_name)


def get_enum(enum_name: str):
    """
    Get an enum class by name.
    
    Args:
        enum_name: The name of the enum to retrieve
        
    Returns:
        The enum class or None if not found
    """
    return ENUM_REGISTRY.get(enum_name)


def list_models():
    """
    Get a list of all available model names.
    
    Returns:
        List of model names
    """
    return list(MODEL_REGISTRY.keys())


def list_enums():
    """
    Get a list of all available enum names.
    
    Returns:
        List of enum names
    """
    return list(ENUM_REGISTRY.keys())