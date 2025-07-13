"""
Security utilities for authentication and authorization.

Comprehensive security module with JWT tokens, refresh tokens, OAuth support,
session management, and security best practices.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union, Tuple, List
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import secrets
import hashlib
import base64
import uuid
from ipaddress import ip_address, ip_network
import re

from .config import settings
from .database import get_db

# Password hashing context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer token
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Token types
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
EMAIL_VERIFICATION_TYPE = "email_verification"
PASSWORD_RESET_TYPE = "password_reset"

# Security constants
MIN_PASSWORD_LENGTH = 8
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30
TOKEN_BYTE_SIZE = 32
SALT_SIZE = 32


class SecurityUtils:
    """Utility class for security operations."""
    
    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(TOKEN_BYTE_SIZE)
    
    @staticmethod
    def generate_jti() -> str:
        """Generate a unique JWT ID."""
        return str(uuid.uuid4())
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Create a SHA256 hash of a token."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def verify_token_hash(token: str, token_hash: str) -> bool:
        """Verify a token against its hash."""
        return SecurityUtils.hash_token(token) == token_hash
    
    @staticmethod
    def generate_salt() -> str:
        """Generate a random salt."""
        return base64.b64encode(secrets.token_bytes(SALT_SIZE)).decode()
    
    @staticmethod
    def is_strong_password(password: str) -> Tuple[bool, Optional[str]]:
        """
        Check if password meets security requirements.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
        
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r"\d", password):
            return False, "Password must contain at least one number"
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"
        
        return True, None


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create access token with optional additional claims.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "iat": datetime.utcnow(),
        "sub": str(subject),
        "type": ACCESS_TOKEN_TYPE,
        "jti": SecurityUtils.generate_jti()
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    session_id: Optional[str] = None
) -> str:
    """
    Create refresh token for token rotation.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)  # 7 days default
    
    to_encode = {
        "exp": expire,
        "iat": datetime.utcnow(),
        "sub": str(subject),
        "type": REFRESH_TOKEN_TYPE,
        "jti": SecurityUtils.generate_jti()
    }
    
    if session_id:
        to_encode["session_id"] = session_id
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def create_email_verification_token(user_id: int, email: str) -> str:
    """
    Create email verification token.
    """
    expire = datetime.utcnow() + timedelta(hours=24)  # 24 hours validity
    
    to_encode = {
        "exp": expire,
        "iat": datetime.utcnow(),
        "sub": str(user_id),
        "email": email,
        "type": EMAIL_VERIFICATION_TYPE,
        "jti": SecurityUtils.generate_jti()
    }
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def create_password_reset_token(user_id: int, email: str) -> str:
    """
    Create password reset token.
    """
    expire = datetime.utcnow() + timedelta(hours=1)  # 1 hour validity
    
    to_encode = {
        "exp": expire,
        "iat": datetime.utcnow(),
        "sub": str(user_id),
        "email": email,
        "type": PASSWORD_RESET_TYPE,
        "jti": SecurityUtils.generate_jti()
    }
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def verify_token(token: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify and decode JWT token with optional type checking.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        
        # Check token type if specified
        if expected_type and payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_token_blacklist(
    token_jti: str,
    db: AsyncSession
) -> bool:
    """
    Check if token is blacklisted.
    """
    from ..models import TokenBlacklist
    
    result = await db.execute(
        select(TokenBlacklist).where(
            TokenBlacklist.token_jti == token_jti
        )
    )
    return result.scalar_one_or_none() is not None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    return pwd_context.hash(password)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current user from JWT token.
    """
    token = credentials.credentials
    payload = verify_token(token, ACCESS_TOKEN_TYPE)
    
    # Check if token is blacklisted
    token_jti = payload.get("jti")
    if token_jti and await verify_token_blacklist(token_jti, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    # Get user from database
    from ..models import User
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_admin": user.is_admin,
        "token_jti": token_jti,
        "session_id": payload.get("session_id")
    }


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current active user.
    """
    return current_user


async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current admin user.
    """
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def create_session_token(session_id: str) -> str:
    """
    Create a session token for anonymous users.
    """
    expire = datetime.utcnow() + timedelta(hours=24)  # 24 hour session
    to_encode = {
        "exp": expire,
        "iat": datetime.utcnow(),
        "session_id": session_id,
        "type": "session",
        "jti": SecurityUtils.generate_jti()
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def verify_session_token(token: str) -> str:
    """
    Verify session token and return session ID.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        session_id = payload.get("session_id")
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session token",
            )
        return session_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate session",
        )


async def create_user_session(
    user_id: int,
    request: Request,
    db: AsyncSession,
    device_info: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, str]:
    """
    Create a new user session and return tokens.
    
    Returns:
        Tuple of (session_id, access_token, refresh_token)
    """
    from ..models import UserSession
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Create tokens
    access_token = create_access_token(
        subject=user_id,
        additional_claims={"session_id": session_id}
    )
    refresh_token = create_refresh_token(
        subject=user_id,
        session_id=session_id
    )
    
    # Extract client information
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent", "")
    
    # Create session record
    session = UserSession(
        user_id=user_id,
        session_token=SecurityUtils.hash_token(access_token),
        refresh_token=SecurityUtils.hash_token(refresh_token),
        ip_address=client_ip,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        refresh_token_expires_at=datetime.utcnow() + timedelta(days=7)
    )
    
    # Add device info if provided
    if device_info:
        session.device_id = device_info.get("device_id")
        session.device_type = device_info.get("device_type")
        session.device_name = device_info.get("device_name")
        session.browser = device_info.get("browser")
        session.browser_version = device_info.get("browser_version")
        session.os = device_info.get("os")
        session.os_version = device_info.get("os_version")
    
    db.add(session)
    await db.commit()
    
    return str(session.id), access_token, refresh_token


async def refresh_access_token(
    refresh_token: str,
    db: AsyncSession
) -> Tuple[str, str]:
    """
    Refresh access token using refresh token.
    
    Returns:
        Tuple of (new_access_token, new_refresh_token)
    """
    # Verify refresh token
    payload = verify_token(refresh_token, REFRESH_TOKEN_TYPE)
    
    # Check if token is blacklisted
    token_jti = payload.get("jti")
    if token_jti and await verify_token_blacklist(token_jti, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )
    
    user_id = payload.get("sub")
    session_id = payload.get("session_id")
    
    # Verify session exists and is active
    from ..models import UserSession
    result = await db.execute(
        select(UserSession).where(
            and_(
                UserSession.id == uuid.UUID(session_id),
                UserSession.user_id == int(user_id),
                UserSession.is_active == True
            )
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )
    
    # Check if refresh token matches
    if not SecurityUtils.verify_token_hash(refresh_token, session.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Create new tokens
    new_access_token = create_access_token(
        subject=user_id,
        additional_claims={"session_id": session_id}
    )
    new_refresh_token = create_refresh_token(
        subject=user_id,
        session_id=session_id
    )
    
    # Update session with new tokens
    session.session_token = SecurityUtils.hash_token(new_access_token)
    session.refresh_token = SecurityUtils.hash_token(new_refresh_token)
    session.last_activity = datetime.utcnow()
    session.expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    session.refresh_token_expires_at = datetime.utcnow() + timedelta(days=7)
    
    # Blacklist old refresh token
    from ..models import TokenBlacklist
    blacklist_entry = TokenBlacklist(
        token_jti=token_jti,
        token_type=REFRESH_TOKEN_TYPE,
        user_id=int(user_id),
        reason="Token refreshed",
        expires_at=payload.get("exp", datetime.utcnow())
    )
    db.add(blacklist_entry)
    
    await db.commit()
    
    return new_access_token, new_refresh_token


async def revoke_token(
    token_jti: str,
    token_type: str,
    user_id: int,
    reason: str,
    db: AsyncSession,
    expires_at: Optional[datetime] = None
) -> None:
    """
    Revoke a token by adding it to blacklist.
    """
    from ..models import TokenBlacklist
    
    blacklist_entry = TokenBlacklist(
        token_jti=token_jti,
        token_type=token_type,
        user_id=user_id,
        reason=reason,
        expires_at=expires_at or datetime.utcnow() + timedelta(hours=1)
    )
    db.add(blacklist_entry)
    await db.commit()


async def revoke_all_user_sessions(
    user_id: int,
    db: AsyncSession,
    except_session_id: Optional[str] = None
) -> None:
    """
    Revoke all user sessions except optionally one.
    """
    from ..models import UserSession
    
    # Get all active sessions
    query = select(UserSession).where(
        and_(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        )
    )
    
    if except_session_id:
        query = query.where(UserSession.id != uuid.UUID(except_session_id))
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    # Deactivate all sessions
    for session in sessions:
        session.is_active = False
    
    await db.commit()


def get_client_ip(request: Request) -> Optional[str]:
    """
    Get client IP address from request, handling proxies.
    """
    # Check X-Forwarded-For header for proxy situations
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # Get the first IP in the chain
        return x_forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP header
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip
    
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    
    return None


def is_ip_allowed(ip: str, allowed_networks: List[str]) -> bool:
    """
    Check if IP is in allowed networks.
    """
    try:
        ip_obj = ip_address(ip)
        for network_str in allowed_networks:
            network = ip_network(network_str)
            if ip_obj in network:
                return True
        return False
    except ValueError:
        return False


async def log_auth_event(
    event_type: str,
    user_id: Optional[int],
    request: Request,
    db: AsyncSession,
    success: bool = True,
    failure_reason: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
) -> None:
    """
    Log authentication event for audit trail.
    """
    from ..models import AuthenticationLog
    
    log_entry = AuthenticationLog(
        user_id=user_id,
        event_type=event_type,
        success=success,
        failure_reason=failure_reason,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent", ""),
        metadata=metadata or {},
        session_id=uuid.UUID(session_id) if session_id else None
    )
    
    db.add(log_entry)
    await db.commit()