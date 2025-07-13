"""
Authentication-related models for session management and security.

Includes user sessions, refresh tokens, blacklisted tokens, and authentication logs.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

# Use shared base - will be overridden by __init__.py import
Base = declarative_base()


class TokenType(str, Enum):
    """Token type enumeration"""
    ACCESS = "access"
    REFRESH = "refresh"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    MFA = "mfa"


class AuthEventType(str, Enum):
    """Authentication event types for audit logging"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    EMAIL_VERIFIED = "email_verified"
    OAUTH_LOGIN = "oauth_login"
    TOKEN_REFRESH = "token_refresh"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_CHALLENGE_SUCCESS = "mfa_challenge_success"
    MFA_CHALLENGE_FAILED = "mfa_challenge_failed"


class UserSession(Base):
    """
    Active user sessions tracking.
    
    Tracks all active sessions for users including device information,
    IP addresses, and session validity.
    """
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Session identification
    session_token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, nullable=False, index=True)
    
    # Device and location information
    device_id = Column(String(255), nullable=True)
    device_type = Column(String(50), nullable=True)  # web, mobile, tablet
    device_name = Column(String(255), nullable=True)
    browser = Column(String(100), nullable=True)
    browser_version = Column(String(50), nullable=True)
    os = Column(String(100), nullable=True)
    os_version = Column(String(50), nullable=True)
    
    # Network information
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    location_data = Column(JSONB, nullable=True, comment="Approximate location based on IP")
    
    # Session validity
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Security flags
    is_trusted_device = Column(Boolean, default=False, nullable=False)
    requires_mfa = Column(Boolean, default=False, nullable=False)
    mfa_completed = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_expires', 'expires_at', 'is_active'),
        Index('idx_session_device', 'device_id', 'user_id'),
        Index('idx_session_ip', 'ip_address'),
        Index('idx_session_location', location_data, postgresql_using='gin',
              postgresql_ops={'location_data': 'jsonb_path_ops'}),
    )

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, device={self.device_name})>"


class TokenBlacklist(Base):
    """
    Blacklisted tokens for logout and security.
    
    Stores invalidated tokens to prevent reuse after logout or
    security events.
    """
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True)
    token_jti = Column(String(255), unique=True, nullable=False, index=True)  # JWT ID
    token_type = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Blacklist reason
    reason = Column(String(255), nullable=True)
    blacklisted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Token metadata
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Timestamps
    blacklisted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_blacklist_expires', 'expires_at'),
        Index('idx_blacklist_user_type', 'user_id', 'token_type'),
    )

    def __repr__(self):
        return f"<TokenBlacklist(id={self.id}, jti={self.token_jti}, reason={self.reason})>"


class AuthenticationLog(Base):
    """
    Authentication event logging for security and audit.
    
    Comprehensive logging of all authentication-related events
    for security monitoring and compliance.
    """
    __tablename__ = "authentication_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Event information
    event_type = Column(String(50), nullable=False, index=True)
    success = Column(Boolean, default=True, nullable=False, index=True)
    failure_reason = Column(String(255), nullable=True)
    
    # Request information
    ip_address = Column(INET, nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # Additional context
    event_metadata = Column(JSONB, nullable=True, comment="Additional event-specific data")
    
    # Session reference
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="auth_logs")
    session = relationship("UserSession", backref="auth_logs")
    
    __table_args__ = (
        Index('idx_authlog_user_event', 'user_id', 'event_type', 'created_at'),
        Index('idx_authlog_ip_event', 'ip_address', 'event_type'),
        Index('idx_authlog_created', 'created_at'),
        Index('idx_authlog_event_metadata', event_metadata, postgresql_using='gin',
              postgresql_ops={'event_metadata': 'jsonb_path_ops'}),
    )

    def __repr__(self):
        return f"<AuthenticationLog(id={self.id}, user_id={self.user_id}, event={self.event_type})>"


class OAuthConnection(Base):
    """
    OAuth provider connections for users.
    
    Stores OAuth provider information and tokens for connected accounts.
    """
    __tablename__ = "oauth_connections"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Provider information
    provider = Column(String(50), nullable=False)  # google, facebook, microsoft
    provider_user_id = Column(String(255), nullable=False)
    provider_email = Column(String(255), nullable=True)
    
    # OAuth tokens (encrypted in production)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Provider data
    provider_data = Column(JSONB, nullable=True, comment="Additional provider-specific data")
    
    # Connection status
    is_active = Column(Boolean, default=True, nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="oauth_connections")
    
    __table_args__ = (
        Index('idx_oauth_provider_user', 'provider', 'provider_user_id', unique=True),
        Index('idx_oauth_user_provider', 'user_id', 'provider'),
        Index('idx_oauth_active', 'is_active', 'provider'),
    )

    def __repr__(self):
        return f"<OAuthConnection(id={self.id}, user_id={self.user_id}, provider={self.provider})>"


class PasswordResetToken(Base):
    """
    Password reset tokens for secure password recovery.
    """
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Token information
    token = Column(String(255), unique=True, nullable=False, index=True)
    token_hash = Column(String(255), nullable=False)  # For additional security
    
    # Validity
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Request information
    requested_ip = Column(INET, nullable=True)
    used_ip = Column(INET, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="password_reset_tokens")
    
    __table_args__ = (
        Index('idx_reset_token_expires', 'expires_at', 'used'),
    )

    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"