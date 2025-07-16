"""
Logging configuration for Pathavana backend application.
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Dict, Any


class NoiseFilter(logging.Filter):
    """Filter out noisy log messages for specific endpoints."""
    
    def __init__(self, excluded_paths=None):
        super().__init__()
        self.excluded_paths = excluded_paths or [
            "/api/v1/frontend-config",
            "/health",
            "/api/health",
            "/favicon.ico"
        ]
    
    def filter(self, record):
        """Return False to filter out the record, True to keep it."""
        # Check if the log message contains any of the excluded paths
        message = record.getMessage()
        for path in self.excluded_paths:
            if path in message:
                return False
        return True

def setup_logging(log_dir: str = "logs", log_level: str = "INFO") -> None:
    """
    Setup logging configuration for the application.
    
    Args:
        log_dir: Directory to store log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Define log files
    app_log_file = log_path / "app.log"
    error_log_file = log_path / "error.log"
    access_log_file = log_path / "access.log"
    
    # Logging configuration
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "noise_filter": {
                "()": NoiseFilter
            }
        },
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(levelname)s - %(message)s"
            },
            "console": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "console",
                "stream": "ext://sys.stdout"
            },
            "file_app": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": str(app_log_file),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(error_log_file),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "file_access": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": str(access_log_file),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": log_level,
                "handlers": ["console", "file_app", "file_error"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file_app"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file_access"],
                "propagate": False,
                "filters": ["noise_filter"]
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "file_error"],
                "propagate": False
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console", "file_app"],
                "propagate": False
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["console", "file_app"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["file_app"],
                "propagate": False
            },
            "pathavana": {
                "level": log_level,
                "handlers": ["console", "file_app"],
                "propagate": False
            },
            "app": {
                "level": log_level,
                "handlers": ["console", "file_app"],
                "propagate": False
            }
        }
    }
    
    # Apply logging configuration
    logging.config.dictConfig(config)
    
    # Log startup message
    logger = logging.getLogger("pathavana.logging")
    logger.info(f"Logging configured - Level: {log_level}, Directory: {log_dir}")
    logger.info(f"Log files: {app_log_file}, {error_log_file}, {access_log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)