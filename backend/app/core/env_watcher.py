"""
Environment variable watcher for automatic reloading.
"""
import os
import time
from pathlib import Path
from typing import Dict, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

logger = logging.getLogger(__name__)

class EnvFileHandler(FileSystemEventHandler):
    """Handler for .env file changes."""
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.last_modified = None
        self._load_initial()
    
    def _load_initial(self):
        """Load initial modification time."""
        try:
            self.last_modified = os.path.getmtime(self.env_file)
        except FileNotFoundError:
            self.last_modified = None
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.src_path.endswith('.env'):
            current_modified = os.path.getmtime(self.env_file)
            if self.last_modified != current_modified:
                logger.info(f"Detected change in {self.env_file}, reloading environment variables...")
                self.last_modified = current_modified
                self._reload_env()
    
    def _reload_env(self):
        """Reload environment variables from .env file."""
        try:
            from dotenv import load_dotenv
            # Override existing environment variables
            load_dotenv(override=True)
            logger.info("Environment variables reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload environment variables: {e}")

def start_env_watcher(env_file: str = ".env"):
    """Start watching the .env file for changes."""
    path = Path(env_file).parent
    event_handler = EnvFileHandler(env_file)
    observer = Observer()
    observer.schedule(event_handler, path=str(path), recursive=False)
    observer.start()
    logger.info(f"Started watching {env_file} for changes")
    return observer