"""Initial Pathavana schema with unified architecture

Revision ID: 001
Revises: 
Create Date: 2025-07-12 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables with proper indexes and constraints."""
    
    # Create enum types
    op.execute("CREATE TYPE userstatus AS ENUM ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'DELETED')")
    op.execute("CREATE TYPE authprovider AS ENUM ('LOCAL', 'GOOGLE', 'FACEBOOK', 'APPLE')")
    op.execute("CREATE TYPE documenttype AS ENUM ('PASSPORT', 'DRIVERS_LICENSE', 'NATIONAL_ID', 'VISA', 'OTHER')")
    op.execute("CREATE TYPE travelertype AS ENUM ('ADULT', 'CHILD', 'INFANT')")
    op.execute("CREATE TYPE travelerstatus AS ENUM ('ACTIVE', 'INACTIVE', 'DELETED')")
    op.execute("CREATE TYPE travelerdocumentstatus AS ENUM ('PENDING', 'VERIFIED', 'EXPIRED', 'REJECTED')")
    op.execute("CREATE TYPE sessionstatus AS ENUM ('ACTIVE', 'PLANNING', 'BOOKED', 'COMPLETED', 'CANCELLED')")
    op.execute("CREATE TYPE bookingstatus AS ENUM ('PENDING', 'CONFIRMED', 'CANCELLED', 'FAILED', 'REFUNDED')")
    op.execute("CREATE TYPE paymentstatus AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'REFUNDED', 'PARTIALLY_REFUNDED')")
    op.execute("CREATE TYPE bookingtype AS ENUM ('FLIGHT', 'HOTEL', 'ACTIVITY', 'PACKAGE')")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('phone_number', sa.String(50), nullable=True),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED', 'DELETED', name='userstatus'), nullable=False, server_default='ACTIVE'),
        sa.Column('auth_provider', postgresql.ENUM('LOCAL', 'GOOGLE', 'FACEBOOK', 'APPLE', name='authprovider'), nullable=False, server_default='LOCAL'),
        sa.Column('auth_provider_id', sa.String(255), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('phone_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('two_factor_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_ip', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for users table
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_auth_provider_id', 'users', ['auth_provider', 'auth_provider_id'])
    op.create_index('ix_users_status', 'users', ['status'])
    
    # Create user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('nationality', sa.String(2), nullable=True),
        sa.Column('preferred_language', sa.String(10), nullable=False, server_default='en'),
        sa.Column('preferred_currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='UTC'),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('emergency_contact_name', sa.String(255), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(50), nullable=True),
        sa.Column('emergency_contact_relationship', sa.String(100), nullable=True),
        sa.Column('loyalty_programs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('known_traveler_numbers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('medical_notes', sa.Text(), nullable=True),
        sa.Column('dietary_restrictions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('accessibility_needs', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('notification_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('privacy_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('gdpr_consent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('gdpr_consent_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('marketing_consent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('data_retention_consent', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for user_profiles
    op.create_index('ix_user_profiles_user_id', 'user_profiles', ['user_id'], unique=True)
    
    # Create travel_preferences table
    op.create_table(
        'travel_preferences',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('preferred_airlines', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('avoided_airlines', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('preferred_hotel_chains', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('preferred_cabin_class', sa.String(20), nullable=True),
        sa.Column('preferred_seat_type', sa.String(20), nullable=True),
        sa.Column('hotel_star_rating_min', sa.Integer(), nullable=True),
        sa.Column('budget_range_min', sa.Numeric(10, 2), nullable=True),
        sa.Column('budget_range_max', sa.Numeric(10, 2), nullable=True),
        sa.Column('preferred_activities', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('avoided_activities', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('travel_pace', sa.String(20), nullable=True),
        sa.Column('accommodation_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('transportation_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('meal_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('interests', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('travel_style', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for travel_preferences
    op.create_index('ix_travel_preferences_user_id', 'travel_preferences', ['user_id'], unique=True)
    
    # Create user_documents table
    op.create_table(
        'user_documents',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('document_type', postgresql.ENUM('PASSPORT', 'DRIVERS_LICENSE', 'NATIONAL_ID', 'VISA', 'OTHER', name='documenttype'), nullable=False),
        sa.Column('document_number', sa.String(100), nullable=False),
        sa.Column('issuing_country', sa.String(2), nullable=False),
        sa.Column('issue_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=False),
        sa.Column('document_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_method', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for user_documents
    op.create_index('ix_user_documents_user_id', 'user_documents', ['user_id'])
    op.create_index('ix_user_documents_document_type', 'user_documents', ['document_type'])
    op.create_index('ix_user_documents_expiry_date', 'user_documents', ['expiry_date'])
    
    # Create travelers table
    op.create_table(
        'travelers',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('traveler_type', postgresql.ENUM('ADULT', 'CHILD', 'INFANT', name='travelertype'), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('middle_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('gender', sa.String(10), nullable=True),
        sa.Column('nationality', sa.String(2), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone_number', sa.String(50), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('relationship_to_primary', sa.String(50), nullable=True),
        sa.Column('requires_guardian_consent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('guardian_name', sa.String(255), nullable=True),
        sa.Column('guardian_relationship', sa.String(50), nullable=True),
        sa.Column('special_needs', sa.Text(), nullable=True),
        sa.Column('dietary_restrictions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('medical_conditions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('accessibility_requirements', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('emergency_contact_name', sa.String(255), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(50), nullable=True),
        sa.Column('emergency_contact_relationship', sa.String(100), nullable=True),
        sa.Column('loyalty_programs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('known_traveler_numbers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('travel_history', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'INACTIVE', 'DELETED', name='travelerstatus'), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for travelers
    op.create_index('ix_travelers_user_id', 'travelers', ['user_id'])
    op.create_index('ix_travelers_email', 'travelers', ['email'])
    op.create_index('ix_travelers_status', 'travelers', ['status'])
    op.create_index('ix_travelers_is_primary', 'travelers', ['is_primary'])
    
    # Create traveler_documents table
    op.create_table(
        'traveler_documents',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('traveler_id', sa.UUID(), nullable=False),
        sa.Column('document_type', postgresql.ENUM('PASSPORT', 'DRIVERS_LICENSE', 'NATIONAL_ID', 'VISA', 'OTHER', name='documenttype'), nullable=False),
        sa.Column('document_number', sa.String(100), nullable=False),
        sa.Column('issuing_country', sa.String(2), nullable=False),
        sa.Column('issue_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=False),
        sa.Column('document_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'VERIFIED', 'EXPIRED', 'REJECTED', name='travelerdocumentstatus'), nullable=False, server_default='PENDING'),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['traveler_id'], ['travelers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for traveler_documents
    op.create_index('ix_traveler_documents_traveler_id', 'traveler_documents', ['traveler_id'])
    op.create_index('ix_traveler_documents_status', 'traveler_documents', ['status'])
    op.create_index('ix_traveler_documents_expiry_date', 'traveler_documents', ['expiry_date'])
    
    # Create traveler_preferences table
    op.create_table(
        'traveler_preferences',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('traveler_id', sa.UUID(), nullable=False),
        sa.Column('preferred_seat_type', sa.String(20), nullable=True),
        sa.Column('meal_preference', sa.String(50), nullable=True),
        sa.Column('special_meal_requirements', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('preferred_cabin_class', sa.String(20), nullable=True),
        sa.Column('bed_preference', sa.String(50), nullable=True),
        sa.Column('room_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('activity_preferences', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('accessibility_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('communication_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['traveler_id'], ['travelers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for traveler_preferences
    op.create_index('ix_traveler_preferences_traveler_id', 'traveler_preferences', ['traveler_id'], unique=True)
    
    # Create unified_travel_sessions table
    op.create_table(
        'unified_travel_sessions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('session_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('plan_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('search_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('session_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'PLANNING', 'BOOKED', 'COMPLETED', 'CANCELLED', name='sessionstatus'), nullable=False, server_default='ACTIVE'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for unified_travel_sessions
    op.create_index('ix_unified_travel_sessions_user_id', 'unified_travel_sessions', ['user_id'])
    op.create_index('ix_unified_travel_sessions_status', 'unified_travel_sessions', ['status'])
    op.create_index('ix_unified_travel_sessions_last_activity', 'unified_travel_sessions', ['last_activity_at'])
    op.create_index('ix_unified_travel_sessions_expires_at', 'unified_travel_sessions', ['expires_at'])
    
    # Create JSONB GIN indexes for unified_travel_sessions
    op.execute("""
        CREATE INDEX ix_unified_travel_sessions_session_data_gin 
        ON unified_travel_sessions USING GIN (session_data)
    """)
    op.execute("""
        CREATE INDEX ix_unified_travel_sessions_plan_data_gin 
        ON unified_travel_sessions USING GIN (plan_data)
    """)
    op.execute("""
        CREATE INDEX ix_unified_travel_sessions_search_params_gin 
        ON unified_travel_sessions USING GIN (search_parameters)
    """)
    
    # Create unified_saved_items table
    op.create_table(
        'unified_saved_items',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('item_type', sa.String(50), nullable=False),
        sa.Column('item_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('provider_reference', sa.String(255), nullable=True),
        sa.Column('price_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_selected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('selection_order', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['unified_travel_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for unified_saved_items
    op.create_index('ix_unified_saved_items_session_id', 'unified_saved_items', ['session_id'])
    op.create_index('ix_unified_saved_items_item_type', 'unified_saved_items', ['item_type'])
    op.create_index('ix_unified_saved_items_is_selected', 'unified_saved_items', ['is_selected'])
    op.create_index('ix_unified_saved_items_provider_reference', 'unified_saved_items', ['provider_reference'])
    
    # Create JSONB GIN index for unified_saved_items
    op.execute("""
        CREATE INDEX ix_unified_saved_items_item_data_gin 
        ON unified_saved_items USING GIN (item_data)
    """)
    
    # Create bookings table
    op.create_table(
        'bookings',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('booking_type', postgresql.ENUM('FLIGHT', 'HOTEL', 'ACTIVITY', 'PACKAGE', name='bookingtype'), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'CONFIRMED', 'CANCELLED', 'FAILED', 'REFUNDED', name='bookingstatus'), nullable=False, server_default='PENDING'),
        sa.Column('payment_status', postgresql.ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'REFUNDED', 'PARTIALLY_REFUNDED', name='paymentstatus'), nullable=False, server_default='PENDING'),
        sa.Column('provider_name', sa.String(100), nullable=False),
        sa.Column('provider_booking_reference', sa.String(255), nullable=True),
        sa.Column('internal_reference', sa.String(100), nullable=False),
        sa.Column('booking_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('provider_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('base_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('taxes', sa.Numeric(10, 2), nullable=True),
        sa.Column('fees', sa.Numeric(10, 2), nullable=True),
        sa.Column('commission_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('payment_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('cancellation_policy', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('refund_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('refund_processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('special_requests', sa.Text(), nullable=True),
        sa.Column('booking_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for bookings
    op.create_index('ix_bookings_user_id', 'bookings', ['user_id'])
    op.create_index('ix_bookings_booking_type', 'bookings', ['booking_type'])
    op.create_index('ix_bookings_status', 'bookings', ['status'])
    op.create_index('ix_bookings_payment_status', 'bookings', ['payment_status'])
    op.create_index('ix_bookings_internal_reference', 'bookings', ['internal_reference'], unique=True)
    op.create_index('ix_bookings_provider_reference', 'bookings', ['provider_booking_reference'])
    op.create_index('ix_bookings_created_at', 'bookings', ['created_at'])
    
    # Create flight_bookings table
    op.create_table(
        'flight_bookings',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('booking_id', sa.UUID(), nullable=False),
        sa.Column('departure_airport', sa.String(10), nullable=False),
        sa.Column('arrival_airport', sa.String(10), nullable=False),
        sa.Column('departure_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('arrival_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('airline_code', sa.String(10), nullable=False),
        sa.Column('flight_number', sa.String(20), nullable=False),
        sa.Column('cabin_class', sa.String(20), nullable=False),
        sa.Column('fare_basis', sa.String(50), nullable=True),
        sa.Column('is_refundable', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_changeable', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('baggage_allowance', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('seat_assignments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('meal_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('special_services', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('segments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for flight_bookings
    op.create_index('ix_flight_bookings_booking_id', 'flight_bookings', ['booking_id'])
    op.create_index('ix_flight_bookings_departure_datetime', 'flight_bookings', ['departure_datetime'])
    op.create_index('ix_flight_bookings_airports', 'flight_bookings', ['departure_airport', 'arrival_airport'])
    
    # Create hotel_bookings table
    op.create_table(
        'hotel_bookings',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('booking_id', sa.UUID(), nullable=False),
        sa.Column('hotel_name', sa.String(255), nullable=False),
        sa.Column('hotel_address', sa.Text(), nullable=False),
        sa.Column('hotel_city', sa.String(100), nullable=False),
        sa.Column('hotel_country', sa.String(2), nullable=False),
        sa.Column('check_in_date', sa.Date(), nullable=False),
        sa.Column('check_out_date', sa.Date(), nullable=False),
        sa.Column('room_type', sa.String(100), nullable=False),
        sa.Column('number_of_rooms', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('guests_per_room', sa.Integer(), nullable=False),
        sa.Column('bed_preference', sa.String(50), nullable=True),
        sa.Column('meal_plan', sa.String(50), nullable=True),
        sa.Column('special_amenities', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('cancellation_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('hotel_confirmation_number', sa.String(100), nullable=True),
        sa.Column('room_assignments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('hotel_policies', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for hotel_bookings
    op.create_index('ix_hotel_bookings_booking_id', 'hotel_bookings', ['booking_id'])
    op.create_index('ix_hotel_bookings_check_in_date', 'hotel_bookings', ['check_in_date'])
    op.create_index('ix_hotel_bookings_hotel_city', 'hotel_bookings', ['hotel_city'])
    
    # Create activity_bookings table
    op.create_table(
        'activity_bookings',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('booking_id', sa.UUID(), nullable=False),
        sa.Column('activity_name', sa.String(255), nullable=False),
        sa.Column('activity_description', sa.Text(), nullable=True),
        sa.Column('provider_name', sa.String(100), nullable=False),
        sa.Column('location_name', sa.String(255), nullable=False),
        sa.Column('location_address', sa.Text(), nullable=True),
        sa.Column('activity_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('number_of_participants', sa.Integer(), nullable=False),
        sa.Column('participant_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('includes', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('excludes', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('meeting_point', sa.Text(), nullable=True),
        sa.Column('important_info', sa.Text(), nullable=True),
        sa.Column('voucher_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for activity_bookings
    op.create_index('ix_activity_bookings_booking_id', 'activity_bookings', ['booking_id'])
    op.create_index('ix_activity_bookings_activity_date', 'activity_bookings', ['activity_date'])
    op.create_index('ix_activity_bookings_location_name', 'activity_bookings', ['location_name'])
    
    # Create booking_travelers association table
    op.create_table(
        'booking_travelers',
        sa.Column('booking_id', sa.UUID(), nullable=False),
        sa.Column('traveler_id', sa.UUID(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('traveler_reference', sa.String(100), nullable=True),
        sa.Column('special_requests', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['traveler_id'], ['travelers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('booking_id', 'traveler_id')
    )
    
    # Create indexes for booking_travelers
    op.create_index('ix_booking_travelers_booking_id', 'booking_travelers', ['booking_id'])
    op.create_index('ix_booking_travelers_traveler_id', 'booking_travelers', ['traveler_id'])
    
    # Create unified_session_bookings table
    op.create_table(
        'unified_session_bookings',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('booking_id', sa.UUID(), nullable=False),
        sa.Column('booking_order', sa.Integer(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('booking_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['unified_travel_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for unified_session_bookings
    op.create_index('ix_unified_session_bookings_session_id', 'unified_session_bookings', ['session_id'])
    op.create_index('ix_unified_session_bookings_booking_id', 'unified_session_bookings', ['booking_id'])
    op.create_index('ix_unified_session_bookings_unique', 'unified_session_bookings', ['session_id', 'booking_id'], unique=True)
    
    # Create update trigger for updated_at columns
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Apply the trigger to all tables with updated_at column
    tables_with_updated_at = [
        'users', 'user_profiles', 'travel_preferences', 'user_documents',
        'travelers', 'traveler_documents', 'traveler_preferences',
        'unified_travel_sessions', 'unified_saved_items', 'unified_session_bookings',
        'bookings', 'flight_bookings', 'hotel_bookings', 'activity_bookings'
    ]
    
    for table in tables_with_updated_at:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    """Drop all tables and types in reverse order."""
    
    # Drop triggers first
    tables_with_updated_at = [
        'users', 'user_profiles', 'travel_preferences', 'user_documents',
        'travelers', 'traveler_documents', 'traveler_preferences',
        'unified_travel_sessions', 'unified_saved_items', 'unified_session_bookings',
        'bookings', 'flight_bookings', 'hotel_bookings', 'activity_bookings'
    ]
    
    for table in tables_with_updated_at:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")
    
    # Drop the trigger function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop tables in reverse order of creation
    op.drop_table('unified_session_bookings')
    op.drop_table('booking_travelers')
    op.drop_table('activity_bookings')
    op.drop_table('hotel_bookings')
    op.drop_table('flight_bookings')
    op.drop_table('bookings')
    op.drop_table('unified_saved_items')
    op.drop_table('unified_travel_sessions')
    op.drop_table('traveler_preferences')
    op.drop_table('traveler_documents')
    op.drop_table('travelers')
    op.drop_table('user_documents')
    op.drop_table('travel_preferences')
    op.drop_table('user_profiles')
    op.drop_table('users')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS bookingtype")
    op.execute("DROP TYPE IF EXISTS paymentstatus")
    op.execute("DROP TYPE IF EXISTS bookingstatus")
    op.execute("DROP TYPE IF EXISTS sessionstatus")
    op.execute("DROP TYPE IF EXISTS travelerdocumentstatus")
    op.execute("DROP TYPE IF EXISTS travelerstatus")
    op.execute("DROP TYPE IF EXISTS travelertype")
    op.execute("DROP TYPE IF EXISTS documenttype")
    op.execute("DROP TYPE IF EXISTS authprovider")
    op.execute("DROP TYPE IF EXISTS userstatus")