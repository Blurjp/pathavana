"""
Core configuration settings for Pathavana backend application.
"""

import os
from typing import Any, Dict, List, Optional, Union
from functools import lru_cache
from dotenv import load_dotenv

# Reload environment variables on import
load_dotenv(override=True)

# Try to import pydantic, fall back to basic config if not available
try:
    try:
        from pydantic_settings import BaseSettings
        from pydantic import field_validator
        PYDANTIC_AVAILABLE = True
    except ImportError:
        from pydantic import BaseSettings, validator as field_validator
        PYDANTIC_AVAILABLE = True
except ImportError:
    # Fallback for when pydantic is not available
    PYDANTIC_AVAILABLE = False
    
    class BaseSettings:
        def __init__(self):
            # Load from environment variables
            for key, default_value in self._get_defaults().items():
                env_value = os.getenv(key, default_value)
                # Convert string values to appropriate types
                if isinstance(default_value, bool):
                    if isinstance(env_value, str):
                        env_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif isinstance(env_value, bool):
                        pass  # Already a boolean, keep as is
                elif isinstance(default_value, int):
                    try:
                        env_value = int(env_value)
                    except (ValueError, TypeError):
                        env_value = default_value
                elif isinstance(default_value, list):
                    if isinstance(env_value, str):
                        env_value = [item.strip() for item in env_value.split(',')]
                setattr(self, key, env_value)
        
        def _get_defaults(self):
            return {}
    
    def field_validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    def _get_defaults(self):
        """Return default configuration values."""
        return {
            # App configuration
            'APP_NAME': "Pathavana Travel Planning API",
            'VERSION': "1.0.0", 
            'DEBUG': False,
            'API_V1_STR': "/api",
            
            # Server configuration
            'HOST': "0.0.0.0",
            'PORT': 8000,
            
            # CORS settings
            'BACKEND_CORS_ORIGINS': "http://localhost:3000,http://localhost:5173",
            
            # Database configuration
            'DATABASE_URL': "sqlite+aiosqlite:///./pathavana_dev.db",
            'DATABASE_ECHO': False,
            
            # Redis configuration
            'REDIS_URL': "redis://localhost:6379",
            'CACHE_TTL': 3600,
            
            # Security
            'SECRET_KEY': "your-secret-key-change-in-production",
            'ACCESS_TOKEN_EXPIRE_MINUTES': 30,
            'REFRESH_TOKEN_EXPIRE_DAYS': 7,
            'PASSWORD_RESET_TOKEN_EXPIRE_HOURS': 1,
            'EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS': 24,
            
            # External APIs
            'AMADEUS_API_KEY': None,
            'AMADEUS_API_SECRET': None,
            'AMADEUS_API_BASE_URL': "https://api.amadeus.com",
            'OPENAI_API_KEY': None,
            'AZURE_OPENAI_API_KEY': None,
            'AZURE_OPENAI_ENDPOINT': None,
            'AZURE_OPENAI_API_VERSION': "2024-02-01",
            'AZURE_OPENAI_DEPLOYMENT_NAME': None,
            'ANTHROPIC_API_KEY': None,
            'GOOGLE_MAPS_API_KEY': None,
            
            # OAuth
            'GOOGLE_CLIENT_ID': None,
            'GOOGLE_CLIENT_SECRET': None,
            'FACEBOOK_APP_ID': None,
            'FACEBOOK_APP_SECRET': None,
            'MICROSOFT_CLIENT_ID': None,
            'MICROSOFT_CLIENT_SECRET': None,
            
            # Email
            'SMTP_HOST': None,
            'SMTP_PORT': 587,
            'SMTP_USERNAME': None,
            'SMTP_PASSWORD': None,
            'SMTP_FROM_EMAIL': "noreply@pathavana.com",
            'SMTP_FROM_NAME': "Pathavana",
            'SMTP_TLS': True,
            'SMTP_SSL': False,
            'FRONTEND_URL': "http://localhost:3000",
            
            # LLM
            'LLM_PROVIDER': "azure_openai",
            'LLM_MODEL': "gpt-4",
            'LLM_TEMPERATURE': 0.7,
            'LLM_MAX_TOKENS': 2000,
            'LLM_STREAMING_ENABLED': True,
            'LLM_CACHE_TTL': 3600,
            
            # Other settings
            'RATE_LIMIT_PER_MINUTE': 60,
            'LOG_LEVEL': "INFO",
            'LOG_FORMAT': "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            'CACHE_DIR': "cache",
            'LOG_DIR': "logs",
        }
    
    def __init__(self):
        if PYDANTIC_AVAILABLE:
            super().__init__()
        else:
            # Use fallback initialization
            super().__init__()
            # Load from .env file if it exists
            env_file = os.path.join(os.getcwd(), '.env')
            if os.path.exists(env_file):
                self._load_env_file(env_file)
    
    def _load_env_file(self, env_file):
        """Load environment variables from .env file."""
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
                        
                        # Set attribute if it exists in defaults
                        if hasattr(self, key):
                            # Convert to appropriate type
                            default_value = getattr(self, key)
                            if isinstance(default_value, bool):
                                if isinstance(value, str):
                                    value = value.lower() in ('true', '1', 'yes', 'on')
                            elif isinstance(default_value, int):
                                try:
                                    value = int(value)
                                except (ValueError, TypeError):
                                    pass
                            setattr(self, key, value)
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}")
    
    # App configuration
    APP_NAME: str = "Pathavana Travel Planning API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_STR: str = "/api"
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS settings
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from string or return list."""
        cors_origins = getattr(self, 'BACKEND_CORS_ORIGINS', "http://localhost:3000,http://localhost:5173")
        if isinstance(cors_origins, str):
            return [origin.strip() for origin in cors_origins.split(",")]
        elif isinstance(cors_origins, list):
            return cors_origins
        return ["http://localhost:3000", "http://localhost:5173"]
    
    # Database configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/pathavana"
    DATABASE_ECHO: bool = False
    
    # Redis configuration (for caching)
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 3600  # 1 hour default
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    
    # External API Keys
    AMADEUS_API_KEY: Optional[str] = None
    AMADEUS_API_SECRET: Optional[str] = None
    AMADEUS_API_BASE_URL: str = "https://api.amadeus.com"
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = None
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Google Maps Configuration
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    
    # OAuth Providers
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    
    # Email Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@pathavana.com"
    SMTP_FROM_NAME: str = "Pathavana"
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    
    # Frontend URL for email links
    FRONTEND_URL: str = "http://localhost:3000"
    
    # LLM Configuration
    LLM_PROVIDER: str = "azure_openai"  # azure_openai, openai, anthropic
    LLM_MODEL: str = "gpt-4"  # Model name or deployment name
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000
    LLM_STREAMING_ENABLED: bool = True
    LLM_CACHE_TTL: int = 3600  # Cache LLM responses for 1 hour
    
    # Travel API Configuration  
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # File paths
    CACHE_DIR: str = "cache"
    LOG_DIR: str = "logs"
    
    # Additional fields from .env file (legacy compatibility)
    SERVER_HOST: Optional[str] = None
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    ALGORITHM: Optional[str] = None
    AMADEUS_HOSTNAME: Optional[str] = None
    AZURE_OPENAI_PARSER_DEPLOYMENT_NAME: Optional[str] = None
    AZURE_OPENAI_AGENT_DEPLOYMENT_NAME: Optional[str] = None
    AZURE_OPENAI_AGGREGATOR_DEPLOYMENT_NAME: Optional[str] = None
    PROJECT_NAME: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env


# Global settings instance
settings = Settings()