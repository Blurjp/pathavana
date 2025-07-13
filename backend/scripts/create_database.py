#!/usr/bin/env python3
"""
Create the Pathavana database and user with proper permissions.
This script should be run with PostgreSQL superuser privileges.
"""

import asyncio
import asyncpg
import sys
import os
from pathlib import Path

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings


async def create_database():
    """Create the Pathavana database and user."""
    
    # Parse the database URL to get connection details
    # Format: postgresql+asyncpg://user:password@host:port/database
    url_parts = settings.DATABASE_URL.replace("postgresql+asyncpg://", "").split("@")
    user_pass = url_parts[0].split(":")
    host_port_db = url_parts[1].split("/")
    host_port = host_port_db[0].split(":")
    
    db_user = user_pass[0]
    db_password = user_pass[1] if len(user_pass) > 1 else ""
    db_host = host_port[0]
    db_port = int(host_port[1]) if len(host_port) > 1 else 5432
    db_name = host_port_db[1]
    
    print(f"Creating database '{db_name}' on {db_host}:{db_port}")
    
    # Connect to PostgreSQL as superuser (to the postgres database)
    try:
        # Connect to the default postgres database
        conn = await asyncpg.connect(
            host=db_host,
            port=db_port,
            user="postgres",  # Assumes you have postgres superuser access
            database="postgres",
        )
        
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
            db_name
        )
        
        if exists:
            print(f"Database '{db_name}' already exists")
        else:
            # Create the database
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Database '{db_name}' created successfully")
        
        # Check if user exists
        user_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_user WHERE usename = $1)",
            db_user
        )
        
        if not user_exists:
            # Create the user
            await conn.execute(
                f"CREATE USER {db_user} WITH PASSWORD '{db_password}'"
            )
            print(f"User '{db_user}' created successfully")
        else:
            # Update password just in case
            await conn.execute(
                f"ALTER USER {db_user} WITH PASSWORD '{db_password}'"
            )
            print(f"User '{db_user}' password updated")
        
        # Grant all privileges on the database to the user
        await conn.execute(
            f'GRANT ALL PRIVILEGES ON DATABASE "{db_name}" TO {db_user}'
        )
        print(f"Granted all privileges on '{db_name}' to '{db_user}'")
        
        await conn.close()
        
        # Now connect to the new database to set up extensions
        conn = await asyncpg.connect(
            host=db_host,
            port=db_port,
            user="postgres",
            database=db_name,
        )
        
        # Create necessary extensions
        extensions = ["uuid-ossp", "pg_trgm", "btree_gin"]
        
        for ext in extensions:
            try:
                await conn.execute(f'CREATE EXTENSION IF NOT EXISTS "{ext}"')
                print(f"Extension '{ext}' created/verified")
            except asyncpg.InsufficientPrivilegeError:
                print(f"Warning: Could not create extension '{ext}'. You may need superuser privileges.")
            except Exception as e:
                print(f"Warning: Error creating extension '{ext}': {e}")
        
        # Grant schema permissions
        await conn.execute(f"GRANT ALL ON SCHEMA public TO {db_user}")
        print(f"Granted schema permissions to '{db_user}'")
        
        await conn.close()
        
        print("\nDatabase setup completed successfully!")
        print(f"Connection string: {settings.DATABASE_URL}")
        
    except asyncpg.PostgresError as e:
        print(f"PostgreSQL error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("Pathavana Database Setup")
    print("=" * 50)
    
    # Check if we should proceed
    response = input("\nThis will create the Pathavana database. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Aborted.")
        sys.exit(0)
    
    asyncio.run(create_database())