#!/usr/bin/env python3
"""
Backup the Pathavana database using pg_dump.
Creates timestamped backups with optional compression.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import subprocess
import gzip
import shutil

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings


def parse_database_url():
    """Parse the database URL to extract connection parameters."""
    url_parts = settings.DATABASE_URL.replace("postgresql+asyncpg://", "").split("@")
    user_pass = url_parts[0].split(":")
    host_port_db = url_parts[1].split("/")
    host_port = host_port_db[0].split(":")
    
    return {
        "user": user_pass[0],
        "password": user_pass[1] if len(user_pass) > 1 else "",
        "host": host_port[0],
        "port": int(host_port[1]) if len(host_port) > 1 else 5432,
        "database": host_port_db[1]
    }


def create_backup(backup_type="full", compress=True):
    """Create a database backup using pg_dump."""
    db_params = parse_database_url()
    
    # Create backups directory
    backup_dir = Path(__file__).parent.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    # Generate backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"pathavana_{backup_type}_{timestamp}.sql"
    
    print(f"Creating {backup_type} backup: {backup_file}")
    
    # Build pg_dump command
    env = os.environ.copy()
    env["PGPASSWORD"] = db_params["password"]
    
    cmd = [
        "pg_dump",
        "-h", db_params["host"],
        "-p", str(db_params["port"]),
        "-U", db_params["user"],
        "-d", db_params["database"],
        "-f", str(backup_file),
        "--verbose"
    ]
    
    # Add options based on backup type
    if backup_type == "full":
        cmd.extend(["--create", "--clean", "--if-exists"])
    elif backup_type == "schema":
        cmd.append("--schema-only")
    elif backup_type == "data":
        cmd.append("--data-only")
    
    try:
        # Run pg_dump
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error creating backup: {result.stderr}")
            return None
        
        print(f"Backup created successfully: {backup_file}")
        
        # Compress if requested
        if compress:
            compressed_file = Path(str(backup_file) + ".gz")
            print(f"Compressing backup to: {compressed_file}")
            
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed file
            backup_file.unlink()
            print(f"Backup compressed successfully!")
            return compressed_file
        
        return backup_file
        
    except FileNotFoundError:
        print("Error: pg_dump not found. Please ensure PostgreSQL client tools are installed.")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def list_backups():
    """List all existing backups."""
    backup_dir = Path(__file__).parent.parent / "backups"
    
    if not backup_dir.exists():
        print("No backups directory found.")
        return []
    
    backups = sorted(backup_dir.glob("pathavana_*.sql*"), reverse=True)
    
    if not backups:
        print("No backups found.")
        return []
    
    print("\nExisting backups:")
    print("-" * 60)
    
    for i, backup in enumerate(backups, 1):
        size = backup.stat().st_size / (1024 * 1024)  # Convert to MB
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"{i}. {backup.name} ({size:.2f} MB) - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return backups


def restore_backup(backup_file):
    """Restore a database backup using psql."""
    db_params = parse_database_url()
    
    if not Path(backup_file).exists():
        print(f"Backup file not found: {backup_file}")
        return False
    
    print(f"Restoring backup: {backup_file}")
    
    # Check if file is compressed
    is_compressed = backup_file.endswith('.gz')
    
    env = os.environ.copy()
    env["PGPASSWORD"] = db_params["password"]
    
    try:
        if is_compressed:
            # Decompress and pipe to psql
            print("Decompressing and restoring backup...")
            
            with gzip.open(backup_file, 'rb') as f:
                cmd = [
                    "psql",
                    "-h", db_params["host"],
                    "-p", str(db_params["port"]),
                    "-U", db_params["user"],
                    "-d", db_params["database"]
                ]
                
                result = subprocess.run(
                    cmd,
                    env=env,
                    input=f.read(),
                    capture_output=True
                )
        else:
            # Direct restore
            cmd = [
                "psql",
                "-h", db_params["host"],
                "-p", str(db_params["port"]),
                "-U", db_params["user"],
                "-d", db_params["database"],
                "-f", backup_file
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error restoring backup: {result.stderr}")
            return False
        
        print("Backup restored successfully!")
        return True
        
    except FileNotFoundError:
        print("Error: psql not found. Please ensure PostgreSQL client tools are installed.")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def cleanup_old_backups(days=7):
    """Remove backups older than specified days."""
    backup_dir = Path(__file__).parent.parent / "backups"
    
    if not backup_dir.exists():
        return
    
    cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
    removed_count = 0
    
    for backup in backup_dir.glob("pathavana_*.sql*"):
        if backup.stat().st_mtime < cutoff_time:
            print(f"Removing old backup: {backup.name}")
            backup.unlink()
            removed_count += 1
    
    if removed_count > 0:
        print(f"Removed {removed_count} old backup(s).")


def main():
    """Main backup function."""
    print("Pathavana Database Backup Utility")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list":
            list_backups()
        
        elif command == "restore":
            if len(sys.argv) < 3:
                print("Usage: backup_database.py restore <backup_file>")
                sys.exit(1)
            
            backup_file = sys.argv[2]
            if restore_backup(backup_file):
                print("\n✅ Restore completed successfully!")
            else:
                print("\n❌ Restore failed!")
                sys.exit(1)
        
        elif command == "cleanup":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            cleanup_old_backups(days)
        
        elif command in ["full", "schema", "data"]:
            compress = "--no-compress" not in sys.argv
            backup_file = create_backup(command, compress)
            
            if backup_file:
                print(f"\n✅ Backup completed successfully!")
                print(f"Backup file: {backup_file}")
            else:
                print("\n❌ Backup failed!")
                sys.exit(1)
        
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  backup_database.py [full|schema|data] [--no-compress]")
            print("  backup_database.py list")
            print("  backup_database.py restore <backup_file>")
            print("  backup_database.py cleanup [days]")
            sys.exit(1)
    
    else:
        # Interactive mode
        print("\nBackup options:")
        print("1. Full backup (schema + data)")
        print("2. Schema only")
        print("3. Data only")
        print("4. List existing backups")
        print("5. Restore from backup")
        print("6. Cleanup old backups")
        print("0. Exit")
        
        choice = input("\nSelect option: ")
        
        if choice == "1":
            create_backup("full")
        elif choice == "2":
            create_backup("schema")
        elif choice == "3":
            create_backup("data")
        elif choice == "4":
            list_backups()
        elif choice == "5":
            backups = list_backups()
            if backups:
                backup_idx = input("\nSelect backup number to restore (or 0 to cancel): ")
                if backup_idx.isdigit() and 0 < int(backup_idx) <= len(backups):
                    backup_file = backups[int(backup_idx) - 1]
                    
                    print(f"\n⚠️  WARNING: This will restore: {backup_file.name}")
                    confirm = input("Are you sure? (yes/N): ")
                    
                    if confirm.lower() == 'yes':
                        restore_backup(str(backup_file))
        elif choice == "6":
            days = input("Remove backups older than how many days? (default: 7): ")
            days = int(days) if days.isdigit() else 7
            cleanup_old_backups(days)
        elif choice == "0":
            print("Exiting.")
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()