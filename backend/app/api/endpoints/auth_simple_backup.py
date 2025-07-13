"""
Simple authentication endpoints without external dependencies
"""
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import secrets
import json
import base64
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session
from sqlalchemy import text

try:
    from fastapi import APIRouter, Depends, HTTPException, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from app.db.session import get_db
    from app.core.config import settings
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = None
    Depends = None
    HTTPException = None
    status = None
    HTTPBearer = None


# Security
security = HTTPBearer() if FASTAPI_AVAILABLE else None


# Pydantic models
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserSignin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


# Simple password hashing (in production, use bcrypt)
def hash_password(password: str) -> str:
    """Simple password hashing"""
    salt = "pathavana_salt_2024"  # In production, use random salt per user
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create simple JWT-like token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    token_data = {
        **data,
        "exp": expire.isoformat(),
        "iat": datetime.utcnow().isoformat()
    }
    
    # Simple token: base64 encode the JSON data
    token_json = json.dumps(token_data)
    token_bytes = token_json.encode('utf-8')
    token = base64.b64encode(token_bytes).decode('utf-8')
    
    # Add a simple signature
    signature = hashlib.sha256(f"{token}{settings.SECRET_KEY}".encode()).hexdigest()[:16]
    return f"{token}.{signature}"


def decode_token(token: str):
    """Decode and verify simple token"""
    try:
        # Split token and signature
        if "." not in token:
            return None
            
        token_part, signature = token.rsplit(".", 1)
        
        # Verify signature
        expected_signature = hashlib.sha256(f"{token_part}{settings.SECRET_KEY}".encode()).hexdigest()[:16]
        if signature != expected_signature:
            return None
        
        # Decode token
        token_json = base64.b64decode(token_part).decode('utf-8')
        token_data = json.loads(token_json)
        
        # Check expiration
        exp = datetime.fromisoformat(token_data.get("exp", ""))
        if datetime.utcnow() > exp:
            return None
        
        return token_data
    except Exception:
        return None


# Create router only if FastAPI is available
if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/auth", tags=["authentication"])
    
    @router.post("/signup", response_model=Token)
    def signup(user_data: UserSignup, db: Session = Depends(get_db)):
        """Create a new user account"""
        # Check if user already exists
        result = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": user_data.email}
        ).fetchone()
        
        if result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = hash_password(user_data.password)
        
        cursor = db.execute(
            text("""
                INSERT INTO users (email, password_hash, full_name, is_active, is_admin, created_at)
                VALUES (:email, :password_hash, :full_name, 1, 0, datetime('now'))
            """),
            {
                "email": user_data.email,
                "password_hash": hashed_password,
                "full_name": user_data.full_name
            }
        )
        db.commit()
        
        user_id = cursor.lastrowid
        
        # Create access token
        access_token = create_access_token(
            data={
                "sub": str(user_id),
                "email": user_data.email,
                "full_name": user_data.full_name
            }
        )
        
        return Token(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": user_id,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "is_active": True
            }
        )
    
    @router.post("/signin", response_model=Token)
    def signin(credentials: UserSignin, db: Session = Depends(get_db)):
        """Sign in with email and password"""
        # Get user by email
        result = db.execute(
            text("SELECT id, email, password_hash, full_name, is_active FROM users WHERE email = :email"),
            {"email": credentials.email}
        ).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user_id, email, password_hash, full_name, is_active = result
        
        # Verify password
        if not verify_password(credentials.password, password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Create access token
        access_token = create_access_token(
            data={
                "sub": str(user_id),
                "email": email,
                "full_name": full_name
            }
        )
        
        return Token(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "is_active": is_active
            }
        )
    
    @router.get("/me", response_model=UserResponse)
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ):
        """Get current authenticated user"""
        token = credentials.credentials
        
        # Decode token
        payload = decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user from database
        result = db.execute(
            text("SELECT id, email, full_name, is_active, created_at FROM users WHERE id = :id"),
            {"id": int(user_id)}
        ).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=result[0],
            email=result[1],
            full_name=result[2],
            is_active=result[3],
            created_at=result[4]
        )
    
    @router.post("/signout")
    async def signout():
        """Sign out the current user"""
        # In a real application, you might want to blacklist the token
        # For now, just return success (client should remove token)
        return {"message": "Successfully signed out"}
    
    
    # Helper function to get current user for dependency injection
    async def get_current_active_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> dict:
        """Dependency to get current authenticated user"""
        token = credentials.credentials
        
        # Decode token
        payload = decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        result = db.execute(
            text("SELECT id, email, full_name, is_active FROM users WHERE id = :id"),
            {"id": int(user_id)}
        ).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not result[3]:  # is_active
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        return {
            "id": result[0],
            "email": result[1],
            "full_name": result[2],
            "is_active": result[3]
        }
else:
    router = None
    get_current_active_user = None