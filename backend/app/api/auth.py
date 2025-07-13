"""
Authentication API endpoints.

Comprehensive authentication endpoints including login, registration,
OAuth, password reset, session management, and MFA support.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update
from sqlalchemy.exc import IntegrityError
import logging
import secrets
import httpx
from urllib.parse import urlencode
import uuid

from ..core.database import get_db
from ..core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    create_email_verification_token,
    create_password_reset_token,
    verify_token,
    get_current_user,
    create_user_session,
    refresh_access_token,
    revoke_token,
    revoke_all_user_sessions,
    log_auth_event,
    SecurityUtils,
    get_client_ip,
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    EMAIL_VERIFICATION_TYPE,
    PASSWORD_RESET_TYPE,
    MAX_LOGIN_ATTEMPTS,
    LOCKOUT_DURATION_MINUTES
)
from ..core.config import settings
from ..models import (
    User,
    UserProfile,
    UserSession,
    TokenBlacklist,
    AuthenticationLog,
    OAuthConnection,
    PasswordResetToken,
    AuthEventType,
    AuthProvider
)
from ..schemas.auth import (
    UserRegister,
    UserLogin,
    TokenRefresh,
    OAuthLogin,
    PasswordResetRequest,
    PasswordResetConfirm,
    EmailVerification,
    ChangePassword,
    UserResponse,
    TokenResponse,
    SessionResponse,
    MessageResponse,
    ErrorResponse,
    UserUpdate,
    MFASetup,
    MFAVerify,
    SessionsListResponse
)
from ..services.email_service import email_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["authentication"])


class OAuthProviderConfig:
    """OAuth provider configuration."""
    
    GOOGLE = {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scopes": ["openid", "email", "profile"]
    }
    
    FACEBOOK = {
        "auth_url": "https://www.facebook.com/v12.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v12.0/oauth/access_token",
        "user_info_url": "https://graph.facebook.com/v12.0/me",
        "scopes": ["email", "public_profile"]
    }
    
    MICROSOFT = {
        "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "user_info_url": "https://graph.microsoft.com/v1.0/me",
        "scopes": ["openid", "email", "profile", "User.Read"]
    }


@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Register a new user account.
    
    Creates a new user account with email/password authentication.
    Sends email verification link to the provided email address.
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
        phone=user_data.phone,
        auth_provider=AuthProvider.LOCAL,
        status="pending_verification",
        consent_data={
            "terms_accepted": user_data.terms_accepted,
            "terms_accepted_at": datetime.utcnow().isoformat(),
            "marketing_consent": user_data.marketing_consent,
            "marketing_consent_at": datetime.utcnow().isoformat() if user_data.marketing_consent else None
        }
    )
    
    # Split full name into first and last
    name_parts = user_data.full_name.split(" ", 1)
    user.first_name = name_parts[0]
    user.last_name = name_parts[1] if len(name_parts) > 1 else None
    
    db.add(user)
    
    # Create user profile
    profile = UserProfile(
        user=user,
        preferred_language="en",
        preferred_currency="USD"
    )
    db.add(profile)
    
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed"
        )
    
    # Create session and tokens
    session_id, access_token, refresh_token = await create_user_session(
        user.id,
        request,
        db,
        user_data.device_info
    )
    
    # Create email verification token
    verification_token = create_email_verification_token(user.id, user.email)
    user.email_verification_token = SecurityUtils.hash_token(verification_token)
    await db.commit()
    
    # Send verification email in background
    background_tasks.add_task(
        send_verification_email,
        user.email,
        user.full_name,
        verification_token
    )
    
    # Log registration event
    await log_auth_event(
        AuthEventType.REGISTER,
        user.id,
        request,
        db,
        metadata={"email": user.email},
        session_id=session_id
    )
    
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
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.
    
    Authenticates user with email/password and returns JWT tokens.
    Implements account lockout after failed attempts.
    """
    # Get user by email
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        await log_auth_event(
            AuthEventType.LOGIN_FAILED,
            None,
            request,
            db,
            success=False,
            failure_reason="User not found",
            metadata={"email": form_data.username}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        await log_auth_event(
            AuthEventType.LOGIN_FAILED,
            user.id,
            request,
            db,
            success=False,
            failure_reason="Account locked",
            metadata={"locked_until": user.locked_until.isoformat()}
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked. Try again after {user.locked_until}"
        )
    
    # Verify password
    if not user.password_hash or not verify_password(form_data.password, user.password_hash):
        # Increment failed attempts
        user.failed_login_attempts += 1
        
        # Lock account if too many attempts
        if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            await log_auth_event(
                AuthEventType.ACCOUNT_LOCKED,
                user.id,
                request,
                db,
                metadata={"attempts": user.failed_login_attempts}
            )
        
        await db.commit()
        
        await log_auth_event(
            AuthEventType.LOGIN_FAILED,
            user.id,
            request,
            db,
            success=False,
            failure_reason="Invalid password",
            metadata={"attempts": user.failed_login_attempts}
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check account status
    if user.status != "active" and user.status != "pending_verification":
        await log_auth_event(
            AuthEventType.LOGIN_FAILED,
            user.id,
            request,
            db,
            success=False,
            failure_reason=f"Account {user.status}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status}"
        )
    
    # Reset failed attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()
    
    # Create session and tokens
    device_info = None  # Could be extracted from user agent
    session_id, access_token, refresh_token = await create_user_session(
        user.id,
        request,
        db,
        device_info
    )
    
    await db.commit()
    
    # Log successful login
    await log_auth_event(
        AuthEventType.LOGIN_SUCCESS,
        user.id,
        request,
        db,
        session_id=session_id
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.from_orm(user)
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout current session.
    
    Invalidates the current session and blacklists tokens.
    """
    user_id = current_user["id"]
    session_id = current_user.get("session_id")
    token_jti = current_user.get("token_jti")
    
    # Deactivate current session
    if session_id:
        result = await db.execute(
            select(UserSession).where(
                and_(
                    UserSession.id == uuid.UUID(session_id),
                    UserSession.user_id == user_id
                )
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.is_active = False
    
    # Blacklist current token
    if token_jti:
        await revoke_token(
            token_jti,
            ACCESS_TOKEN_TYPE,
            user_id,
            "User logout",
            db
        )
    
    await db.commit()
    
    # Log logout event
    await log_auth_event(
        AuthEventType.LOGOUT,
        user_id,
        request,
        db,
        session_id=session_id
    )
    
    return MessageResponse(message="Logged out successfully")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all_sessions(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout all user sessions.
    
    Invalidates all sessions except the current one (optional).
    """
    user_id = current_user["id"]
    
    # Revoke all sessions
    await revoke_all_user_sessions(user_id, db)
    
    # Log event
    await log_auth_event(
        AuthEventType.LOGOUT,
        user_id,
        request,
        db,
        metadata={"logout_type": "all_sessions"}
    )
    
    return MessageResponse(message="All sessions logged out successfully")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token.
    
    Uses refresh token to generate new access and refresh tokens.
    Implements token rotation for security.
    """
    try:
        # Refresh tokens
        new_access_token, new_refresh_token = await refresh_access_token(
            token_data.refresh_token,
            db
        )
        
        # Get user info from new token
        payload = verify_token(new_access_token, ACCESS_TOKEN_TYPE)
        user_id = int(payload["sub"])
        
        # Get user
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Log token refresh
        await log_auth_event(
            AuthEventType.TOKEN_REFRESH,
            user_id,
            request,
            db,
            session_id=payload.get("session_id")
        )
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/google", response_model=TokenResponse)
async def google_oauth(
    oauth_data: OAuthLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login/register with Google OAuth.
    
    Exchanges Google authorization code for user tokens.
    Creates new account if user doesn't exist.
    """
    try:
        return await oauth_login(
            "google",
            oauth_data,
            request,
            db,
            settings.GOOGLE_CLIENT_ID,
            settings.GOOGLE_CLIENT_SECRET,
            OAuthProviderConfig.GOOGLE
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )


@router.post("/facebook", response_model=TokenResponse)
async def facebook_oauth(
    oauth_data: OAuthLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login/register with Facebook OAuth.
    
    Exchanges Facebook authorization code for user tokens.
    Creates new account if user doesn't exist.
    """
    return await oauth_login(
        "facebook",
        oauth_data,
        request,
        db,
        settings.FACEBOOK_APP_ID,
        settings.FACEBOOK_APP_SECRET,
        OAuthProviderConfig.FACEBOOK
    )


@router.post("/microsoft", response_model=TokenResponse)
async def microsoft_oauth(
    oauth_data: OAuthLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login/register with Microsoft OAuth.
    
    Exchanges Microsoft authorization code for user tokens.
    Creates new account if user doesn't exist.
    """
    return await oauth_login(
        "microsoft",
        oauth_data,
        request,
        db,
        settings.MICROSOFT_CLIENT_ID,
        settings.MICROSOFT_CLIENT_SECRET,
        OAuthProviderConfig.MICROSOFT
    )


async def oauth_login(
    provider: str,
    oauth_data: OAuthLogin,
    request: Request,
    db: AsyncSession,
    client_id: str,
    client_secret: str,
    provider_config: dict
) -> TokenResponse:
    """
    Common OAuth login logic for all providers.
    """
    # Dynamically reload credentials
    import os
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    # Get fresh credentials
    if provider == "google":
        client_id = os.getenv('GOOGLE_CLIENT_ID', client_id)
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET', client_secret)
    elif provider == "facebook":
        client_id = os.getenv('FACEBOOK_APP_ID', client_id)
        client_secret = os.getenv('FACEBOOK_APP_SECRET', client_secret)
    
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"{provider.capitalize()} OAuth not configured"
        )
    
    # Verify state parameter (CSRF protection)
    # In production, verify against stored state
    
    logger.info(f"OAuth {provider} login attempt - code: {oauth_data.code[:20]}..., redirect_uri: {oauth_data.redirect_uri}")
    
    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_data = {
            "grant_type": "authorization_code",
            "code": oauth_data.code,
            "redirect_uri": oauth_data.redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        logger.debug(f"Token exchange request to {provider_config['token_url']}")
        
        token_response = await client.post(
            provider_config["token_url"],
            data=token_data
        )
        
        if token_response.status_code != 200:
            logger.error(f"OAuth token exchange failed: {token_response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth authentication failed"
            )
        
        tokens = token_response.json()
        oauth_access_token = tokens.get("access_token")
        
        # Get user info
        headers = {"Authorization": f"Bearer {oauth_access_token}"}
        user_response = await client.get(
            provider_config["user_info_url"],
            headers=headers,
            params={"fields": "id,email,name,picture"} if provider == "facebook" else None
        )
        
        if user_response.status_code != 200:
            logger.error(f"OAuth user info failed: {user_response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information"
            )
        
        user_info = user_response.json()
    
    # Extract user data based on provider
    provider_user_id = str(user_info.get("id") or user_info.get("sub"))
    email = user_info.get("email")
    full_name = user_info.get("name") or f"{user_info.get('given_name', '')} {user_info.get('family_name', '')}".strip()
    picture_url = user_info.get("picture")
    
    if isinstance(picture_url, dict):  # Facebook returns object
        picture_url = picture_url.get("data", {}).get("url")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided by OAuth provider"
        )
    
    # Check if OAuth connection exists
    result = await db.execute(
        select(OAuthConnection).where(
            and_(
                OAuthConnection.provider == provider,
                OAuthConnection.provider_user_id == provider_user_id
            )
        )
    )
    oauth_connection = result.scalar_one_or_none()
    
    if oauth_connection:
        # Existing OAuth user
        user = oauth_connection.user
        
        # Update OAuth tokens
        oauth_connection.access_token = oauth_access_token
        oauth_connection.refresh_token = tokens.get("refresh_token")
        oauth_connection.last_used = datetime.utcnow()
        
    else:
        # Check if user exists with this email
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Link existing account
            oauth_connection = OAuthConnection(
                user_id=user.id,
                provider=provider,
                provider_user_id=provider_user_id,
                provider_email=email,
                access_token=oauth_access_token,
                refresh_token=tokens.get("refresh_token"),
                provider_data=user_info
            )
            db.add(oauth_connection)
        else:
            # Create new user
            user = User(
                email=email,
                full_name=full_name or email,
                auth_provider=provider,
                provider_user_id=provider_user_id,
                profile_picture_url=picture_url,
                email_verified=True,  # OAuth providers verify email
                status="active"
            )
            
            # Split name
            name_parts = full_name.split(" ", 1) if full_name else [email.split("@")[0]]
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else None
            
            db.add(user)
            await db.flush()
            
            # Create profile
            profile = UserProfile(
                user_id=user.id,
                preferred_language="en",
                preferred_currency="USD"
            )
            db.add(profile)
            
            # Create OAuth connection
            oauth_connection = OAuthConnection(
                user_id=user.id,
                provider=provider,
                provider_user_id=provider_user_id,
                provider_email=email,
                access_token=oauth_access_token,
                refresh_token=tokens.get("refresh_token"),
                provider_data=user_info
            )
            db.add(oauth_connection)
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    
    try:
        # Create session
        session_id, access_token, refresh_token = await create_user_session(
            user.id,
            request,
            db,
            oauth_data.device_info
        )
        
        await db.commit()
        
        # Log OAuth login
        await log_auth_event(
            AuthEventType.OAUTH_LOGIN,
            user.id,
            request,
            db,
            metadata={"provider": provider},
            session_id=session_id
        )
        
        logger.info(f"OAuth {provider} login successful for user {user.id}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
    except Exception as e:
        logger.error(f"OAuth {provider} session/token creation failed: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user session"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user information.
    
    Returns the authenticated user's profile information.
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


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user profile.
    
    Updates the authenticated user's profile information.
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
    
    # Update fields if provided
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
        name_parts = user_update.full_name.split(" ", 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else None
    
    if user_update.first_name is not None:
        user.first_name = user_update.first_name
    
    if user_update.last_name is not None:
        user.last_name = user_update.last_name
    
    if user_update.phone is not None:
        user.phone = user_update.phone
        user.phone_verified = False  # Reset verification
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.from_orm(user)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    data: PasswordResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Request password reset.
    
    Sends password reset link to user's email address.
    """
    # Get user by email
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()
    
    # Always return success to prevent email enumeration
    if not user:
        return MessageResponse(
            message="If the email exists, a password reset link has been sent"
        )
    
    # Check if user can reset password (OAuth users might not have passwords)
    if user.auth_provider != AuthProvider.LOCAL and not user.password_hash:
        return MessageResponse(
            message="Password reset not available for OAuth accounts"
        )
    
    # Create reset token
    reset_token = SecurityUtils.generate_token()
    jwt_token = create_password_reset_token(user.id, user.email)
    
    # Store reset token
    reset_record = PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        token_hash=SecurityUtils.hash_token(jwt_token),
        expires_at=datetime.utcnow() + timedelta(hours=1),
        requested_ip=get_client_ip(request)
    )
    db.add(reset_record)
    await db.commit()
    
    # Send reset email in background
    background_tasks.add_task(
        send_password_reset_email,
        user.email,
        user.full_name,
        reset_token
    )
    
    # Log event
    await log_auth_event(
        AuthEventType.PASSWORD_RESET_REQUEST,
        user.id,
        request,
        db,
        metadata={"email": user.email}
    )
    
    return MessageResponse(
        message="If the email exists, a password reset link has been sent"
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: PasswordResetConfirm,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password with token.
    
    Completes password reset using token from email.
    """
    # Get reset token record
    result = await db.execute(
        select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token == data.token,
                PasswordResetToken.used == False,
                PasswordResetToken.expires_at > datetime.utcnow()
            )
        )
    )
    reset_record = result.scalar_one_or_none()
    
    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get user
    user = reset_record.user
    
    # Update password
    user.password_hash = get_password_hash(data.password)
    user.failed_login_attempts = 0
    user.locked_until = None
    
    # Mark token as used
    reset_record.used = True
    reset_record.used_at = datetime.utcnow()
    reset_record.used_ip = get_client_ip(request)
    
    # Revoke all sessions for security
    await revoke_all_user_sessions(user.id, db)
    
    await db.commit()
    
    # Log event
    await log_auth_event(
        AuthEventType.PASSWORD_RESET_COMPLETE,
        user.id,
        request,
        db
    )
    
    return MessageResponse(message="Password reset successfully")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    data: EmailVerification,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify email address.
    
    Completes email verification using token from email.
    """
    try:
        # Verify token
        payload = verify_token(data.token, EMAIL_VERIFICATION_TYPE)
        user_id = int(payload["sub"])
        email = payload["email"]
        
        # Get user
        result = await db.execute(
            select(User).where(
                and_(
                    User.id == user_id,
                    User.email == email
                )
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if already verified
        if user.email_verified:
            return MessageResponse(message="Email already verified")
        
        # Verify email
        user.email_verified = True
        user.email_verification_token = None
        
        # Activate account if pending
        if user.status == "pending_verification":
            user.status = "active"
        
        await db.commit()
        
        # Log event
        await log_auth_event(
            AuthEventType.EMAIL_VERIFIED,
            user.id,
            request,
            db,
            metadata={"email": email}
        )
        
        return MessageResponse(message="Email verified successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePassword,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password.
    
    Allows authenticated users to change their password.
    """
    # Get user
    result = await db.execute(
        select(User).where(User.id == current_user["id"])
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not user.password_hash or not verify_password(data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    user.password_hash = get_password_hash(data.new_password)
    
    # Optionally logout other sessions
    if data.logout_other_sessions:
        await revoke_all_user_sessions(
            user.id,
            db,
            except_session_id=current_user.get("session_id")
        )
    
    await db.commit()
    
    return MessageResponse(message="Password changed successfully")


@router.get("/sessions", response_model=SessionsListResponse)
async def get_user_sessions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all user sessions.
    
    Returns list of all active sessions for the authenticated user.
    """
    current_session_id = current_user.get("session_id")
    
    # Get all active sessions
    result = await db.execute(
        select(UserSession).where(
            and_(
                UserSession.user_id == current_user["id"],
                UserSession.is_active == True
            )
        ).order_by(UserSession.last_activity.desc())
    )
    sessions = result.scalars().all()
    
    # Convert to response format
    session_responses = []
    for session in sessions:
        session_response = SessionResponse(
            id=str(session.id),
            user_id=session.user_id,
            device_type=session.device_type,
            device_name=session.device_name,
            browser=session.browser,
            os=session.os,
            ip_address=str(session.ip_address) if session.ip_address else None,
            location_data=session.location_data,
            is_current=str(session.id) == current_session_id,
            is_active=session.is_active,
            last_activity=session.last_activity,
            created_at=session.created_at,
            expires_at=session.expires_at
        )
        session_responses.append(session_response)
    
    return SessionsListResponse(
        sessions=session_responses,
        total=len(session_responses)
    )


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def revoke_session(
    session_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke a specific session.
    
    Allows users to logout specific sessions/devices.
    """
    # Verify session belongs to user
    result = await db.execute(
        select(UserSession).where(
            and_(
                UserSession.id == uuid.UUID(session_id),
                UserSession.user_id == current_user["id"]
            )
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Don't allow revoking current session through this endpoint
    if str(session.id) == current_user.get("session_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke current session. Use logout instead."
        )
    
    # Deactivate session
    session.is_active = False
    await db.commit()
    
    return MessageResponse(message="Session revoked successfully")


# Email sending functions
async def send_verification_email(email: str, name: str, token: str):
    """Send email verification link."""
    await email_service.send_verification_email(email, name, token)


async def send_password_reset_email(email: str, name: str, token: str):
    """Send password reset link."""
    await email_service.send_password_reset_email(email, name, token)


# OAuth URL generators for frontend
@router.get("/oauth-url/{provider}")
async def get_oauth_url(
    provider: str,
    redirect_uri: str,
    state: Optional[str] = None
):
    """
    Generate OAuth authorization URL.
    
    Returns the OAuth provider's authorization URL for frontend redirect.
    """
    if provider not in ["google", "facebook", "microsoft"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth provider"
        )
    
    # Generate state if not provided
    if not state:
        state = secrets.token_urlsafe(32)
    
    # Get provider config
    provider_config = getattr(OAuthProviderConfig, provider.upper())
    
    # Dynamically load environment variables
    import os
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    # Get client ID from environment
    client_ids = {
        "google": os.getenv('GOOGLE_CLIENT_ID'),
        "facebook": os.getenv('FACEBOOK_APP_ID'),
        "microsoft": os.getenv('MICROSOFT_CLIENT_ID')
    }
    
    client_id = client_ids.get(provider)
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"{provider.capitalize()} OAuth not configured"
        )
    
    # Build authorization URL
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(provider_config["scopes"]),
        "state": state,
        "access_type": "offline",  # For Google refresh tokens
        "prompt": "consent"  # Force consent screen
    }
    
    auth_url = f"{provider_config['auth_url']}?{urlencode(params)}"
    
    return {
        "auth_url": auth_url,
        "state": state
    }