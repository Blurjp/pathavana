"""
Improved authentication API with better error handling and CORS support.
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from ..core.database import get_db
from ..core.config import settings
from ..core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    ACCESS_TOKEN_TYPE
)
from ..models import User, UserProfile
from ..schemas.auth import TokenResponse, UserResponse, UserRegister

logger = logging.getLogger(__name__)
router = APIRouter()

# Security scheme
security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    """Email/password login request."""
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    """Google login request."""
    id_token: Optional[str] = None
    access_token: Optional[str] = None
    user_info: Optional[dict] = None


async def get_current_user_safe(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Safely get current user from JWT token without raising exceptions.
    Returns None if authentication fails.
    """
    try:
        # Get authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        
        # Parse bearer token
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        token = parts[1]
        
        # Verify token
        try:
            payload = verify_token(token, ACCESS_TOKEN_TYPE)
        except Exception as e:
            logger.debug(f"Token verification failed: {e}")
            return None
        
        # Get user ID
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Get user from database
        try:
            result = await db.execute(
                select(User).where(User.id == int(user_id))
            )
            user = result.scalar_one_or_none()
            
            if not user or user.status != "active":
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Database error fetching user: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user_safe: {e}")
        return None


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login with email and password."""
    try:
        # Find user
        result = await db.execute(
            select(User).where(User.email == login_data.email)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if account is active
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        await db.commit()
        
        # Create tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/google-login", response_model=TokenResponse)
async def google_login(
    google_data: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Google OAuth login."""
    try:
        logger.info(f"Google login request received: id_token={bool(google_data.id_token)}, user_info={bool(google_data.user_info)}")
        
        # Import Google auth libraries
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_auth_requests
        
        # Handle ID token verification
        if google_data.id_token:
            if not settings.GOOGLE_CLIENT_ID:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Google login not configured"
                )
            
            try:
                # Verify the Google ID token
                id_info = google_id_token.verify_oauth2_token(
                    google_data.id_token,
                    google_auth_requests.Request(),
                    settings.GOOGLE_CLIENT_ID
                )
                
                # Verify token issuer
                if id_info.get('iss') not in ['accounts.google.com', 'https://accounts.google.com']:
                    raise ValueError("Invalid token issuer")
                
                user_info = id_info
                
            except ValueError as e:
                logger.error(f"Invalid Google token: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid Google token: {str(e)}"
                )
                
        elif google_data.user_info:
            # Use provided user info (for testing/development)
            user_info = google_data.user_info
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either id_token or user_info must be provided"
            )
        
        # Extract email from user info
        email = user_info.get("email")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in Google data"
            )
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            user = User(
                email=email,
                full_name=user_info.get("name", email.split("@")[0]),
                first_name=user_info.get("given_name", ""),
                last_name=user_info.get("family_name", ""),
                profile_picture_url=user_info.get("picture", ""),
                auth_provider="google",
                provider_user_id=user_info.get("sub"),
                email_verified=user_info.get("verified_email", True),
                status="active",
                consent_data={
                    "terms_accepted": True,
                    "terms_accepted_at": datetime.utcnow().isoformat()
                }
            )
            db.add(user)
            await db.flush()
            
            # Create profile
            profile = UserProfile(
                user_id=user.id,
                preferred_language="en",
                preferred_currency="USD"
            )
            db.add(profile)
        else:
            # Update existing user
            if user_info.get("picture"):
                user.profile_picture_url = user_info["picture"]
            user.last_login_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
        
        # Create tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/me", response_model=UserResponse)
async def get_me(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get current user info."""
    try:
        user = await get_current_user_safe(request, db)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get me error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Logout current user."""
    try:
        user = await get_current_user_safe(request, db)
        
        if not user:
            # Already logged out
            return {"message": "Successfully logged out"}
        
        # In a real app, you might want to blacklist the token here
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        # Even on error, return success
        return {"message": "Successfully logged out"}


@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    try:
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            first_name=user_data.full_name.split(" ")[0],
            last_name=" ".join(user_data.full_name.split(" ")[1:]) or None,
            auth_provider="local",
            status="active",
            email_verified=False,
            consent_data={
                "terms_accepted": True,
                "terms_accepted_at": datetime.utcnow().isoformat()
            }
        )
        
        db.add(user)
        await db.flush()
        
        # Create profile
        profile = UserProfile(
            user_id=user.id,
            preferred_language="en",
            preferred_currency="USD"
        )
        db.add(profile)
        
        await db.commit()
        await db.refresh(user)
        
        # Create tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Register error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )