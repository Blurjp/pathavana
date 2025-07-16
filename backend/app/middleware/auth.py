"""
Authentication middleware and rate limiting.

Provides security middleware for request validation, rate limiting,
CORS configuration, and security headers.
"""

from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
import time
import logging
from collections import defaultdict
from datetime import datetime, timedelta
import redis.asyncio as redis
import json
from ipaddress import ip_address, ip_network

from ..core.config import settings
from ..core.security import verify_token, ACCESS_TOKEN_TYPE

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.
    
    Supports both in-memory and Redis-based rate limiting.
    """
    
    def __init__(
        self,
        app,
        calls: int = 100,
        period: int = 60,
        redis_client: Optional[redis.Redis] = None
    ):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.redis_client = redis_client
        
        # In-memory storage fallback
        self.requests = defaultdict(list)
        
        # Rate limit exemptions
        self.exempt_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics"
        ]
        
        # Different rate limits for different endpoints
        self.endpoint_limits = {
            "/api/auth/login": {"calls": 5, "period": 300},  # 5 calls per 5 minutes
            "/api/auth/register": {"calls": 3, "period": 3600},  # 3 calls per hour
            "/api/auth/forgot-password": {"calls": 3, "period": 3600},  # 3 calls per hour
            "/api/auth/refresh": {"calls": 10, "period": 60},  # 10 calls per minute
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Get rate limit for endpoint
        limit_config = self._get_limit_config(request.url.path)
        
        # Check rate limit
        allowed = await self._check_rate_limit(
            client_id,
            request.url.path,
            limit_config["calls"],
            limit_config["period"]
        )
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_id} on {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "Retry-After": str(limit_config["period"]),
                    "X-RateLimit-Limit": str(limit_config["calls"]),
                    "X-RateLimit-Period": str(limit_config["period"])
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit_config["calls"])
        response.headers["X-RateLimit-Period"] = str(limit_config["period"])
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get authenticated user ID
        authorization = request.headers.get("Authorization")
        if authorization:
            scheme, token = get_authorization_scheme_param(authorization)
            if scheme.lower() == "bearer":
                try:
                    payload = verify_token(token, ACCESS_TOKEN_TYPE)
                    return f"user:{payload.get('sub')}"
                except:
                    pass
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        
        if request.client:
            return f"ip:{request.client.host}"
        
        return "ip:unknown"
    
    def _get_limit_config(self, path: str) -> Dict[str, int]:
        """Get rate limit configuration for endpoint."""
        # Check specific endpoint limits
        for endpoint, config in self.endpoint_limits.items():
            if path.startswith(endpoint):
                return config
        
        # Return default limits
        return {"calls": self.calls, "period": self.period}
    
    async def _check_rate_limit(
        self,
        client_id: str,
        endpoint: str,
        calls: int,
        period: int
    ) -> bool:
        """Check if request is within rate limit."""
        key = f"rate_limit:{client_id}:{endpoint}"
        now = time.time()
        
        if self.redis_client:
            # Redis-based rate limiting
            try:
                # Use sliding window algorithm
                pipeline = self.redis_client.pipeline()
                pipeline.zremrangebyscore(key, 0, now - period)
                pipeline.zadd(key, {str(now): now})
                pipeline.zcount(key, now - period, now)
                pipeline.expire(key, period)
                
                results = await pipeline.execute()
                request_count = results[2]
                
                return request_count <= calls
            except Exception as e:
                logger.error(f"Redis rate limit error: {str(e)}")
                # Fall back to in-memory
        
        # In-memory rate limiting
        requests = self.requests[key]
        # Remove old requests
        requests = [req_time for req_time in requests if req_time > now - period]
        
        if len(requests) >= calls:
            return False
        
        requests.append(now)
        self.requests[key] = requests
        
        return True


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Adjust as needed
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self'",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # HSTS (only for HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for protected routes.
    
    Validates JWT tokens and adds user context to requests.
    """
    
    def __init__(self, app, protected_prefixes: Optional[list] = None):
        super().__init__(app)
        self.protected_prefixes = protected_prefixes or [
            "/api/bookings",
            "/api/travelers",
            "/api/travel/save",
            "/api/compliance/export"
        ]
        
        # Public endpoints that don't require authentication
        self.public_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/google",
            "/api/v1/auth/google-login",
            "/api/v1/auth/facebook",
            "/api/v1/auth/microsoft",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
            "/api/v1/auth/verify-email",
            "/api/v1/auth/oauth-url",
            "/api/v1/health",
            "/health",
            "/",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with authentication check."""
        # Allow OPTIONS requests through for CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Check if path requires authentication
        if not self._requires_auth(request.url.path):
            return await call_next(request)
        
        # Get authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate token
        scheme, token = get_authorization_scheme_param(authorization)
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        try:
            # Verify token and add user context to request state
            payload = verify_token(token, ACCESS_TOKEN_TYPE)
            request.state.user_id = payload.get("sub")
            request.state.session_id = payload.get("session_id")
            request.state.token_jti = payload.get("jti")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return await call_next(request)
    
    def _requires_auth(self, path: str) -> bool:
        """Check if path requires authentication."""
        # Public endpoints don't require auth
        if any(path.startswith(endpoint) for endpoint in self.public_endpoints):
            return False
        
        # Check protected prefixes
        return any(path.startswith(prefix) for prefix in self.protected_prefixes)


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    IP whitelist middleware for admin endpoints.
    """
    
    def __init__(self, app, whitelist: Optional[list] = None, protected_paths: Optional[list] = None):
        super().__init__(app)
        self.whitelist = whitelist or []
        self.protected_paths = protected_paths or ["/api/admin", "/api/internal"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check IP whitelist for protected paths."""
        # Check if path needs IP validation
        if not any(request.url.path.startswith(path) for path in self.protected_paths):
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check whitelist
        if not self._is_ip_allowed(client_ip):
            logger.warning(f"Blocked access from {client_ip} to {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _is_ip_allowed(self, client_ip: str) -> bool:
        """Check if IP is in whitelist."""
        if not self.whitelist:
            return True  # No whitelist means allow all
        
        try:
            ip_obj = ip_address(client_ip)
            for allowed in self.whitelist:
                # Check if it's a network range
                if "/" in allowed:
                    if ip_obj in ip_network(allowed):
                        return True
                else:
                    if str(ip_obj) == allowed:
                        return True
            return False
        except ValueError:
            return False


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request logging middleware for debugging and monitoring.
    """
    
    def __init__(self, app):
        super().__init__(app)
        # Paths to skip logging for (too noisy)
        self.skip_logging_paths = [
            "/api/v1/frontend-config",
            "/health",
            "/api/health",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        start_time = time.time()
        
        # Check if we should skip logging for this path
        skip_logging = any(request.url.path == path for path in self.skip_logging_paths)
        
        # Log request (if not skipped)
        if not skip_logging:
            logger.info(
                f"Request: {request.method} {request.url.path} "
                f"from {request.client.host if request.client else 'unknown'}"
            )
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response (if not skipped)
        if not skip_logging:
            logger.info(
                f"Response: {response.status_code} for {request.method} {request.url.path} "
                f"({process_time:.3f}s)"
            )
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class SessionValidationMiddleware(BaseHTTPMiddleware):
    """
    Session validation middleware to check active sessions.
    """
    
    def __init__(self, app, db_session_factory):
        super().__init__(app)
        self.db_session_factory = db_session_factory
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate user session if authenticated."""
        # Only check if we have user context from auth middleware
        if not hasattr(request.state, "user_id") or not hasattr(request.state, "session_id"):
            return await call_next(request)
        
        # Validate session in database
        async with self.db_session_factory() as db:
            from ..models import UserSession
            from sqlalchemy import select, and_
            import uuid
            
            result = await db.execute(
                select(UserSession).where(
                    and_(
                        UserSession.id == uuid.UUID(request.state.session_id),
                        UserSession.user_id == int(request.state.user_id),
                        UserSession.is_active == True,
                        UserSession.expires_at > datetime.utcnow()
                    )
                )
            )
            session = result.scalar_one_or_none()
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            await db.commit()
        
        return await call_next(request)