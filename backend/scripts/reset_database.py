#!/usr/bin/env python3
"""
Reset the Pathavana database - drops all tables and recreates them.
WARNING: This will delete all data!
"""

import asyncio
import sys
import os
from pathlib import Path
import subprocess

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import engine
from sqlalchemy import text
import asyncpg


async def drop_all_tables():
    """Drop all tables in the database."""
    print("Dropping all tables...")
    
    # Parse database connection details
    url_parts = settings.DATABASE_URL.replace("postgresql+asyncpg://", "").split("@")
    user_pass = url_parts[0].split(":")
    host_port_db = url_parts[1].split("/")
    host_port = host_port_db[0].split(":")
    
    db_user = user_pass[0]
    db_password = user_pass[1] if len(user_pass) > 1 else ""
    db_host = host_port[0]
    db_port = int(host_port[1]) if len(host_port) > 1 else 5432
    db_name = host_port_db[1]
    
    try:
        # Connect directly with asyncpg to avoid connection pool issues
        conn = await asyncpg.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        
        # Drop all tables in public schema
        await conn.execute("""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                -- Drop all tables
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
                
                -- Drop all types
                FOR r IN (SELECT typname FROM pg_type WHERE typtype = 'e' AND typnamespace = 'public'::regnamespace) LOOP
                    EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
                END LOOP;
                
                -- Drop all functions
                FOR r IN (SELECT proname FROM pg_proc WHERE pronamespace = 'public'::regnamespace) LOOP
                    EXECUTE 'DROP FUNCTION IF EXISTS ' || quote_ident(r.proname) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        
        await conn.close()
        print("All tables dropped successfully!")
        return True
        
    except Exception as e:
        print(f"Error dropping tables: {e}")
        return False


async def reset_alembic():
    """Reset Alembic migration history."""
    print("\nResetting Alembic migration history...")
    
    try:
        # Remove alembic_version table if it exists
        async with engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        
        print("Alembic history reset successfully!")
        return True
        
    except Exception as e:
        print(f"Error resetting Alembic: {e}")
        return False


def run_migrations():
    """Run Alembic migrations to recreate schema."""
    print("\nRunning migrations to recreate schema...")
    
    try:
        # Run alembic upgrade head
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error running migrations: {result.stderr}")
            return False
        
        print("Migrations completed successfully!")
        print(result.stdout)
        return True
        
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False


def seed_data():
    """Optionally seed development data."""
    response = input("\nSeed development data? (y/N): ")
    if response.lower() == 'y':
        try:
            # Run the init_database script with seed data
            result = subprocess.run(
                [sys.executable, "scripts/init_database.py"],
                cwd=Path(__file__).parent.parent,
                input="y\n",  # Answer yes to seed data prompt
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Error seeding data: {result.stderr}")
                return False
            
            print("Data seeded successfully!")
            return True
            
        except Exception as e:
            print(f"Error seeding data: {e}")
            return False
    
    return True


async def main():
    """Main reset function."""
    print("Pathavana Database Reset")
    print("=" * 50)
    print("\n⚠️  WARNING: This will DELETE ALL DATA in the database! ⚠️")
    
    response = input("\nAre you SURE you want to reset the database? Type 'yes' to confirm: ")
    if response.lower() != 'yes':
        print("Reset cancelled.")
        sys.exit(0)
    
    # Double confirmation for production
    if os.getenv("ENVIRONMENT") == "production":
        response = input("\n🚨 PRODUCTION ENVIRONMENT DETECTED! Type 'RESET PRODUCTION' to confirm: ")
        if response != 'RESET PRODUCTION':
            print("Reset cancelled.")
            sys.exit(0)
    
    # Drop all tables
    if not await drop_all_tables():
        print("\nFailed to drop tables. Please check the error messages above.")
        sys.exit(1)
    
    # Reset Alembic
    if not await reset_alembic():
        print("\nFailed to reset Alembic. Please check the error messages above.")
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        print("\nFailed to run migrations. Please check the error messages above.")
        sys.exit(1)
    
    # Optionally seed data
    if os.getenv("ENVIRONMENT", "development") == "development":
        seed_data()
    
    print("\n✅ Database reset completed successfully!")
    
    # Close connections
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())