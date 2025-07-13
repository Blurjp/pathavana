"""
Simplified authentication API using Google ID token verification.

This implementation uses Google's ID token verification instead of the 
OAuth authorization code flow, which is simpler and more suitable for SPAs.
"""

from datetime import datetime, timedelta
from typing import Optional, Any
import logging
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

# Google Auth imports
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_auth_requests

from ..core.database import get_db
from ..core.config import settings
from ..core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    get_current_user
)
from ..models import User, UserProfile, AuthProvider
from ..schemas.auth import TokenResponse, UserResponse, UserRegister

logger = logging.getLogger(__name__)
router = APIRouter(tags=["authentication"])


class GoogleLoginRequest(BaseModel):
    """Google login request with ID token from frontend."""
    id_token: Optional[str] = None
    access_token: Optional[str] = None
    user_info: Optional[dict] = None


class PasswordLoginRequest(BaseModel):
    """Email/password login request."""
    email: EmailStr
    password: str


@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user with email and password.
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        first_name=user_data.full_name.split(" ")[0],
        last_name=" ".join(user_data.full_name.split(" ")[1:]) or None,
        auth_provider=AuthProvider.LOCAL,
        status="active",
        email_verified=False,
        consent_data={
            "terms_accepted": True,
            "terms_accepted_at": datetime.utcnow().isoformat()
        }
    )
    
    db.add(user)
    await db.flush()
    
    # Create user profile
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
    
    logger.info(f"User {user.email} registered successfully")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.from_orm(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.
    """
    # Get user by email
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        user.failed_login_attempts += 1
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if account is active
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status}"
        )
    
    # Reset failed attempts and update last login
    user.failed_login_attempts = 0
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    # Create tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    
    logger.info(f"User {user.email} logged in successfully")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.from_orm(user)
    )


@router.post("/google-login", response_model=TokenResponse)
async def google_login(
    google_request: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Google Sign-In using either ID token or access token with user info.
    
    Supports both approaches for flexibility.
    """
    logger.info("Processing Google login request")
    
    if not settings.GOOGLE_CLIENT_ID:
        logger.error("Google Client ID not configured")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google login not configured"
        )
    
    try:
        # Option 1: ID token verification (preferred)
        if google_request.id_token:
            # Verify the Google ID token
            id_info = google_id_token.verify_oauth2_token(
                google_request.id_token,
                google_auth_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
            
            logger.info(f"Google ID token verified for email: {id_info.get('email')}")
            
            # Verify token issuer
            if id_info.get('iss') not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError("Invalid token issuer")
            
            user_email = id_info.get('email')
            email_verified = id_info.get('email_verified', False)
            
        # Option 2: Access token with user info (fallback)
        elif google_request.access_token and google_request.user_info:
            logger.info("Using access token with user info approach")
            id_info = google_request.user_info
            user_email = id_info.get('email')
            email_verified = id_info.get('verified_email', True)  # Google OAuth2 userinfo endpoint
            
        else:
            raise ValueError("Either id_token or (access_token + user_info) must be provided")
        
        # Extract user information
        if not user_email:
            raise ValueError("Email not found in Google data")
        
    except ValueError as e:
        logger.error(f"Invalid Google token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error verifying Google token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying Google token"
        )
    
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == user_email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user from Google data
        logger.info(f"Creating new user for Google email: {user_email}")
        
        full_name = id_info.get('name', '')
        given_name = id_info.get('given_name', '')
        family_name = id_info.get('family_name', '')
        picture_url = id_info.get('picture', '')
        google_id = id_info.get('sub')
        
        user = User(
            email=user_email,
            full_name=full_name or user_email.split('@')[0],
            first_name=given_name or full_name.split(' ')[0] if full_name else user_email.split('@')[0],
            last_name=family_name or ' '.join(full_name.split(' ')[1:]) if full_name and ' ' in full_name else None,
            profile_picture_url=picture_url,
            auth_provider=AuthProvider.GOOGLE,
            provider_user_id=google_id,
            email_verified=email_verified,
            status="active",
            consent_data={
                "terms_accepted": True,
                "terms_accepted_at": datetime.utcnow().isoformat(),
                "google_consent": True
            }
        )
        
        db.add(user)
        await db.flush()
        
        # Create user profile
        profile = UserProfile(
            user_id=user.id,
            preferred_language=id_info.get('locale', 'en').split('-')[0],
            preferred_currency="USD"
        )
        db.add(profile)
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"New user created: {user.email} (ID: {user.id})")
        
    else:
        # Update existing user
        logger.info(f"Existing user found: {user.email}")
        
        # Update profile picture if changed
        google_picture = id_info.get('picture')
        if google_picture and user.profile_picture_url != google_picture:
            user.profile_picture_url = google_picture
        
        # Verify email if not already verified
        if not user.email_verified and email_verified:
            user.email_verified = True
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
    
    # Check if account is active
    if user.status != "active":
        logger.warning(f"Inactive user attempted login: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )
    
    # Create application tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    
    logger.info(f"Tokens issued for user {user.email} via Google Sign-In")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.from_orm(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user information.
    """
    result = await db.execute(
        select(User).where(User.id == current_user["id"])
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)


@router.post("/logout")
async def logout():
    """
    Logout endpoint.
    
    For JWT-based auth, logout is handled client-side by removing the token.
    This endpoint is provided for compatibility.
    """
    return {"message": "Logged out successfully"}