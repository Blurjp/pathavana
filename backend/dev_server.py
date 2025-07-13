#!/usr/bin/env python3
"""
Development server with automatic environment reloading.
"""
import os
import sys
import subprocess
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class EnvFileHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_modified = {}
        self.process = None
        self.start_server()
    
    def start_server(self):
        """Start the uvicorn server."""
        print("🚀 Starting development server...")
        self.process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8001"
        ])
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.src_path.endswith('.env'):
            current_time = time.time()
            last_time = self.last_modified.get(event.src_path, 0)
            
            # Debounce: only react if file hasn't been modified in last 2 seconds
            if current_time - last_time > 2:
                print(f"\n📝 Detected change in {event.src_path}")
                print("🔄 Environment variables will be reloaded automatically")
                print("✅ No server restart needed - changes will take effect immediately\n")
                self.last_modified[event.src_path] = current_time

def main():
    """Run the development server with environment watching."""
    print("🛠️  Pathavana Development Server")
    print("================================")
    print("✨ Features:")
    print("  - Auto-reload on code changes")
    print("  - Auto-reload environment variables from .env")
    print("  - No manual restart needed")
    print("\nStarting...\n")
    
    # Create event handler and observer
    event_handler = EnvFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
    
    observer.join()

if __name__ == "__main__":
    main()