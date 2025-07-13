# Pathavana Database Scripts

This directory contains database management utilities for the Pathavana backend.

## Prerequisites

- PostgreSQL 13+ installed
- Python 3.9+ with required dependencies
- PostgreSQL client tools (psql, pg_dump) for backup/restore operations
- Superuser access to PostgreSQL for database creation

## Available Scripts

### 1. create_database.py
Creates the Pathavana database and user with proper permissions.

```bash
# Run with PostgreSQL superuser privileges
./scripts/create_database.py
```

This script will:
- Create the `pathavana` database
- Create the database user with proper permissions
- Install required PostgreSQL extensions (uuid-ossp, pg_trgm, btree_gin)

### 2. init_database.py
Initialize the database by running migrations and optionally seeding development data.

```bash
./scripts/init_database.py
```

Features:
- Runs all Alembic migrations
- Optionally seeds development data
- Verifies database setup
- Creates sample users and travel sessions

### 3. reset_database.py
**WARNING: This will delete all data!**

```bash
./scripts/reset_database.py
```

This script:
- Drops all tables and types
- Resets Alembic migration history
- Recreates the schema from migrations
- Optionally seeds fresh development data

### 4. backup_database.py
Comprehensive backup and restore utilities.

```bash
# Interactive mode
./scripts/backup_database.py

# Create full backup (with compression)
./scripts/backup_database.py full

# Create schema-only backup
./scripts/backup_database.py schema

# Create data-only backup
./scripts/backup_database.py data

# List existing backups
./scripts/backup_database.py list

# Restore from backup
./scripts/backup_database.py restore backups/pathavana_full_20240712_120000.sql.gz

# Clean up old backups (older than 7 days)
./scripts/backup_database.py cleanup 7
```

### 5. database_health.py
Database health monitoring and performance checks.

```bash
# Interactive health report
./scripts/database_health.py

# JSON output for monitoring systems
./scripts/database_health.py --json
```

Checks include:
- Connection health
- Table sizes and row counts
- Index usage statistics
- Slow query detection
- Connection pool statistics
- Long-running queries
- Table bloat analysis
- Missing index suggestions

### 6. seed_data.py
Generate comprehensive test data for development and testing.

```bash
./scripts/seed_data.py
```

Generates:
- 20 test users with profiles and preferences
- Travel companions (travelers)
- Travel sessions in various states
- Bookings (flights, hotels, activities)
- Saved items and session data

### 7. manage_migrations.py
Simplified Alembic migration management.

```bash
# Create new auto-generated migration
./scripts/manage_migrations.py create "Add new feature"

# Create empty migration
./scripts/manage_migrations.py create "Custom migration" --empty

# List all migrations
./scripts/manage_migrations.py list

# Upgrade to latest
./scripts/manage_migrations.py upgrade

# Upgrade to specific revision
./scripts/manage_migrations.py upgrade abc123

# Downgrade to previous
./scripts/manage_migrations.py downgrade -1

# Check pending migrations
./scripts/manage_migrations.py check

# Show SQL without executing
./scripts/manage_migrations.py sql

# Validate migrations
./scripts/manage_migrations.py validate
```

## Development Workflow

### Initial Setup
```bash
# 1. Create database (run as PostgreSQL superuser)
./scripts/create_database.py

# 2. Initialize with migrations and seed data
./scripts/init_database.py
# Answer 'y' when prompted to seed development data
```

### Reset Database
```bash
# Complete reset with fresh data
./scripts/reset_database.py
# Answer 'yes' to confirm reset
# Answer 'y' to seed development data
```

### Create New Migration
```bash
# After modifying models
./scripts/manage_migrations.py create "Description of changes"

# Review the generated migration
# Then apply it
./scripts/manage_migrations.py upgrade
```

### Regular Maintenance
```bash
# Check database health
./scripts/database_health.py

# Create backup before major changes
./scripts/backup_database.py full

# Clean up old backups
./scripts/backup_database.py cleanup 30
```

## Environment Variables

The scripts respect the following environment variables:
- `ENVIRONMENT`: Set to 'production' for production safety checks
- `DATABASE_URL`: Override the default database connection string
- `EDITOR`: Preferred text editor for migration editing

## Test Credentials

After seeding development data:
- **Demo User**: demo@pathavana.com / demo123
- **Test User**: test@pathavana.com / demo123
- **Admin User**: admin@pathavana.com / demo123
- **Generated Users**: user1@pathavana.com to user20@pathavana.com / demo123

## Production Considerations

1. **Backups**: Set up automated daily backups using cron:
   ```bash
   0 2 * * * /path/to/backend/scripts/backup_database.py full
   ```

2. **Health Monitoring**: Run health checks regularly:
   ```bash
   */15 * * * * /path/to/backend/scripts/database_health.py --json > /var/log/pathavana/db_health.json
   ```

3. **Migration Safety**:
   - Always backup before migrations
   - Test migrations on staging first
   - Use `manage_migrations.py sql` to review SQL before applying

4. **Security**:
   - Store database credentials securely
   - Restrict access to these scripts
   - Use read-only credentials for health checks

## Troubleshooting

### "pg_dump not found"
Install PostgreSQL client tools:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-client

# macOS
brew install postgresql

# Or use Docker
docker run --rm postgres:15 pg_dump --help
```

### "Permission denied" errors
Ensure scripts are executable:
```bash
chmod +x scripts/*.py
```

### Database connection errors
Check your DATABASE_URL in .env:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/pathavana
```

### Migration conflicts
If migrations are out of sync:
```bash
# Check current state
./scripts/manage_migrations.py check

# Force stamp to current state (use cautiously)
./scripts/manage_migrations.py stamp head
```