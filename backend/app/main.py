"""
Main FastAPI application entry point for Pathavana travel planning API.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import os
import redis.asyncio as redis
from datetime import datetime

from .core.config import settings
from .core.database import init_db, close_db, get_db
from .core.logging_config import setup_logging, get_logger
from .api import travel_unified, bookings, travelers, data_compliance, auth
from .middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    AuthenticationMiddleware,
    RequestLoggingMiddleware,
    SessionValidationMiddleware
)


# Setup logging
setup_logging(log_dir=settings.LOG_DIR, log_level=settings.LOG_LEVEL)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Pathavana backend application...")
    
    # Ensure directories exist
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    os.makedirs(settings.CACHE_DIR, exist_ok=True)
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Initialize Redis for rate limiting (optional)
    redis_client = None
    if settings.REDIS_URL:
        try:
            redis_client = await redis.from_url(settings.REDIS_URL)
            await redis_client.ping()
            logger.info("Redis connection established")
            app.state.redis = redis_client
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory rate limiting.")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Pathavana backend application...")
    
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    # Close Redis connection if exists
    if hasattr(app.state, "redis") and app.state.redis:
        await app.state.redis.close()
        logger.info("Redis connection closed")
    
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Add middleware (order matters - outermost middleware runs first)
# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# CORS - must be before authentication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Period", "X-Process-Time"]
)

# Trusted host
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure based on your deployment
)

# Request logging
if settings.DEBUG:
    app.add_middleware(RequestLoggingMiddleware)

# Session validation
app.add_middleware(SessionValidationMiddleware, db_session_factory=get_db)

# Authentication
app.add_middleware(
    AuthenticationMiddleware,
    protected_prefixes=[
        f"{settings.API_V1_STR}/bookings",
        f"{settings.API_V1_STR}/travelers",
        f"{settings.API_V1_STR}/travel/save",
        f"{settings.API_V1_STR}/compliance/export",
        f"{settings.API_V1_STR}/auth/me",
        f"{settings.API_V1_STR}/auth/logout",
        f"{settings.API_V1_STR}/auth/change-password",
        f"{settings.API_V1_STR}/auth/sessions"
    ]
)

# Rate limiting
@app.on_event("startup")
async def setup_rate_limiting():
    redis_client = getattr(app.state, "redis", None)
    app.add_middleware(
        RateLimitMiddleware,
        calls=100,
        period=60,
        redis_client=redis_client
    )

# Include API routers
# Authentication routes (public)
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["authentication"]
)

# Travel routes
app.include_router(
    travel_unified.router,
    prefix=f"{settings.API_V1_STR}/travel",
    tags=["travel"]
)

app.include_router(
    bookings.router,
    prefix=f"{settings.API_V1_STR}/bookings",
    tags=["bookings"]
)

app.include_router(
    travelers.router,
    prefix=f"{settings.API_V1_STR}/travelers",
    tags=["travelers"]
)

app.include_router(
    data_compliance.router,
    prefix=f"{settings.API_V1_STR}/compliance",
    tags=["data-compliance"]
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Pathavana Travel Planning API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check database connection
    db_status = "healthy"
    try:
        async with get_db() as db:
            await db.execute("SELECT 1")
    except Exception:
        db_status = "unhealthy"
    
    # Check Redis connection
    redis_status = "not_configured"
    if hasattr(app.state, "redis") and app.state.redis:
        try:
            await app.state.redis.ping()
            redis_status = "healthy"
        except Exception:
            redis_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": {
            "database": db_status,
            "redis": redis_status
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )