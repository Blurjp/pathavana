"""
Authentication schemas for request/response validation.

Comprehensive schemas for authentication operations including login,
registration, OAuth, password reset, and session management.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class PasswordBase(BaseModel):
    """Base model for password validation."""
    password: str = Field(..., min_length=8)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserRegister(PasswordBase):
    """User registration request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    terms_accepted: bool = Field(..., description="User must accept terms and conditions")
    marketing_consent: Optional[bool] = Field(False, description="Marketing email consent")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecureP@ss123",
                "full_name": "John Doe",
                "phone": "+1234567890",
                "terms_accepted": True,
                "marketing_consent": True
            }
        }


class UserLogin(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str
    remember_me: Optional[bool] = Field(False, description="Extended session duration")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device information for session tracking")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecureP@ss123",
                "remember_me": True,
                "device_info": {
                    "device_id": "unique-device-id",
                    "device_type": "web",
                    "device_name": "Chrome on Windows",
                    "browser": "Chrome",
                    "browser_version": "91.0",
                    "os": "Windows",
                    "os_version": "10"
                }
            }
        }


class TokenRefresh(BaseModel):
    """Token refresh request schema."""
    refresh_token: str = Field(..., description="Valid refresh token")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class OAuthLogin(BaseModel):
    """OAuth login request schema."""
    provider: str = Field(..., pattern="^(google|facebook|microsoft)$")
    code: str = Field(..., description="OAuth authorization code")
    state: str = Field(..., description="OAuth state parameter for CSRF protection")
    redirect_uri: str = Field(..., description="OAuth redirect URI")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device information for session tracking")
    
    class Config:
        schema_extra = {
            "example": {
                "provider": "google",
                "code": "authorization-code-from-provider",
                "state": "random-state-string",
                "redirect_uri": "http://localhost:3000/auth/callback"
            }
        }


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: EmailStr
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str = Field(..., description="Password reset token from email")
    password: str = Field(..., min_length=8, description="New password")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token": "reset-token-from-email",
                "password": "NewSecureP@ss123"
            }
        }


class EmailVerification(BaseModel):
    """Email verification request schema."""
    token: str = Field(..., description="Email verification token")
    
    class Config:
        schema_extra = {
            "example": {
                "token": "verification-token-from-email"
            }
        }


class ChangePassword(BaseModel):
    """Change password request schema."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    logout_other_sessions: Optional[bool] = Field(False, description="Logout all other sessions")
    
    @field_validator("new_password")
    @classmethod  
    def validate_new_password(cls, v, info):
        # Password strength validation
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        
        # Check if different from current password
        if hasattr(info, 'data') and info.data.get("current_password") and v == info.data["current_password"]:
            raise ValueError("New password must be different from current password")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "OldP@ssword123",
                "new_password": "NewSecureP@ss123",
                "logout_other_sessions": True
            }
        }


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    email: str
    full_name: str
    first_name: Optional[str]
    last_name: Optional[str]
    profile_picture_url: Optional[str]
    phone: Optional[str]
    email_verified: bool
    phone_verified: bool
    is_admin: bool
    status: str
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True
        orm_mode = True  # For backward compatibility
        schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe",
                "first_name": "John",
                "last_name": "Doe",
                "profile_picture_url": "https://example.com/avatar.jpg",
                "phone": "+1234567890",
                "email_verified": True,
                "phone_verified": False,
                "is_admin": False,
                "status": "active",
                "created_at": "2023-01-01T00:00:00Z",
                "last_login_at": "2023-12-01T12:00:00Z"
            }
        }


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration in seconds")
    user: UserResponse
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "email_verified": True,
                    "is_admin": False,
                    "status": "active"
                }
            }
        }


class SessionResponse(BaseModel):
    """User session response schema."""
    id: str
    user_id: int
    device_type: Optional[str]
    device_name: Optional[str]
    browser: Optional[str]
    os: Optional[str]
    ip_address: Optional[str]
    location_data: Optional[Dict[str, Any]]
    is_current: bool
    is_active: bool
    last_activity: datetime
    created_at: datetime
    expires_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": 1,
                "device_type": "web",
                "device_name": "Chrome on Windows",
                "browser": "Chrome",
                "os": "Windows",
                "ip_address": "192.168.1.1",
                "location_data": {
                    "country": "US",
                    "city": "New York"
                },
                "is_current": True,
                "is_active": True,
                "last_activity": "2023-12-01T12:00:00Z",
                "created_at": "2023-12-01T10:00:00Z",
                "expires_at": "2023-12-01T13:00:00Z"
            }
        }


class MessageResponse(BaseModel):
    """Generic message response schema."""
    message: str
    success: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Operation completed successfully",
                "success": True
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
    code: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Invalid credentials",
                "code": "AUTH_001"
            }
        }


class UserUpdate(BaseModel):
    """User profile update schema."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    
    class Config:
        schema_extra = {
            "example": {
                "full_name": "Jane Doe",
                "first_name": "Jane",
                "last_name": "Doe",
                "phone": "+1987654321"
            }
        }


class MFASetup(BaseModel):
    """MFA setup request schema."""
    method: str = Field(..., pattern="^(totp|sms|email)$")
    phone_number: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    
    class Config:
        schema_extra = {
            "example": {
                "method": "totp",
                "phone_number": "+1234567890"
            }
        }


class MFAVerify(BaseModel):
    """MFA verification request schema."""
    code: str = Field(..., pattern=r"^\d{6}$", description="6-digit verification code")
    remember_device: Optional[bool] = Field(False, description="Remember this device")
    
    class Config:
        schema_extra = {
            "example": {
                "code": "123456",
                "remember_device": True
            }
        }


class SessionsListResponse(BaseModel):
    """List of user sessions response."""
    sessions: List[SessionResponse]
    total: int
    
    class Config:
        schema_extra = {
            "example": {
                "sessions": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "device_type": "web",
                        "is_current": True,
                        "is_active": True,
                        "last_activity": "2023-12-01T12:00:00Z"
                    }
                ],
                "total": 1
            }
        }