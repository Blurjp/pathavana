"""
Advanced database configuration for Pathavana.
Includes connection pooling, performance settings, and monitoring.
"""

from typing import Dict, Any
from sqlalchemy.pool import NullPool, QueuePool, StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager
import logging

from .config import settings

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration with environment-specific settings."""
    
    @staticmethod
    def get_pool_config() -> Dict[str, Any]:
        """Get connection pool configuration based on environment."""
        
        if settings.DEBUG:
            # Development: Smaller pool, echo SQL
            return {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 1800,  # 30 minutes
                "echo": True,
                "echo_pool": True,
            }
        else:
            # Production: Larger pool, no echo
            return {
                "pool_size": 20,
                "max_overflow": 40,
                "pool_timeout": 30,
                "pool_recycle": 3600,  # 1 hour
                "echo": False,
                "echo_pool": False,
                "pool_pre_ping": True,  # Verify connections
            }
    
    @staticmethod
    def get_engine_config() -> Dict[str, Any]:
        """Get engine configuration with performance settings."""
        
        return {
            "connect_args": {
                "server_settings": {
                    "application_name": "pathavana_backend",
                    "jit": "off",  # Disable JIT for more predictable performance
                },
                "command_timeout": 60,
                "prepared_statement_cache_size": 0,  # Disable for asyncpg
                "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
            },
            "execution_options": {
                "isolation_level": "READ COMMITTED",
            },
        }
    
    @staticmethod
    def create_engine(database_url: str = None):
        """Create async engine with proper configuration."""
        
        url = database_url or settings.DATABASE_URL
        pool_config = DatabaseConfig.get_pool_config()
        engine_config = DatabaseConfig.get_engine_config()
        
        # Merge configurations
        config = {**pool_config, **engine_config}
        
        # Create engine with appropriate pool class
        if settings.DEBUG and settings.DATABASE_URL.startswith("sqlite"):
            # SQLite for testing
            config["poolclass"] = StaticPool
            config["connect_args"] = {"check_same_thread": False}
        elif "poolclass" not in config:
            config["poolclass"] = QueuePool
        
        engine = create_async_engine(url, **config)
        
        # Set up event listeners
        DatabaseConfig._setup_event_listeners(engine)
        
        return engine
    
    @staticmethod
    def _setup_event_listeners(engine):
        """Set up engine event listeners for monitoring."""
        
        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            """Set SQLite pragmas for better performance."""
            if "sqlite" in str(engine.url):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.close()
        
        @event.listens_for(engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log slow queries in production."""
            if not settings.DEBUG:
                conn.info.setdefault("query_start_time", []).append(time.time())
        
        @event.listens_for(engine.sync_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log slow queries in production."""
            if not settings.DEBUG:
                total_time = time.time() - conn.info["query_start_time"].pop(-1)
                if total_time > 1.0:  # Log queries slower than 1 second
                    logger.warning(
                        f"Slow query detected ({total_time:.2f}s): {statement[:100]}..."
                    )


class DatabaseSession:
    """Enhanced database session management."""
    
    def __init__(self, engine=None):
        self.engine = engine or DatabaseConfig.create_engine()
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """Get a database session with automatic transaction management."""
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def execute_read(self, query, params=None):
        """Execute a read-only query."""
        async with self.async_session_maker() as session:
            result = await session.execute(query, params or {})
            return result
    
    async def execute_write(self, query, params=None):
        """Execute a write query with automatic commit."""
        async with self.get_session() as session:
            result = await session.execute(query, params or {})
            return result
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.async_session_maker() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def close(self):
        """Close all database connections."""
        await self.engine.dispose()


# Performance monitoring queries
MONITORING_QUERIES = {
    "active_connections": """
        SELECT count(*) 
        FROM pg_stat_activity 
        WHERE state = 'active' 
        AND datname = current_database()
    """,
    
    "connection_stats": """
        SELECT 
            state,
            count(*) as count,
            max(now() - query_start) as max_duration
        FROM pg_stat_activity
        WHERE datname = current_database()
        GROUP BY state
    """,
    
    "table_sizes": """
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
            n_live_tup as row_count
        FROM pg_stat_user_tables
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        LIMIT 10
    """,
    
    "index_usage": """
        SELECT 
            schemaname,
            tablename,
            indexname,
            idx_scan as index_scans,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size
        FROM pg_stat_user_indexes
        WHERE idx_scan = 0
        AND indexrelname NOT LIKE 'pg_toast%'
        ORDER BY pg_relation_size(indexrelid) DESC
        LIMIT 10
    """,
    
    "cache_hit_ratio": """
        SELECT 
            'index hit rate' AS name,
            (sum(idx_blks_hit)) / nullif(sum(idx_blks_hit + idx_blks_read),0) AS ratio
        FROM pg_statio_user_indexes
        UNION ALL
        SELECT 
            'table hit rate' AS name,
            sum(heap_blks_hit) / nullif(sum(heap_blks_hit) + sum(heap_blks_read),0) AS ratio
        FROM pg_statio_user_tables
    """,
}


async def get_database_metrics(session: AsyncSession) -> Dict[str, Any]:
    """Get current database performance metrics."""
    metrics = {}
    
    for metric_name, query in MONITORING_QUERIES.items():
        try:
            result = await session.execute(text(query))
            rows = result.fetchall()
            
            if metric_name in ["active_connections"]:
                metrics[metric_name] = rows[0][0] if rows else 0
            else:
                metrics[metric_name] = [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get metric {metric_name}: {e}")
            metrics[metric_name] = None
    
    return metrics


# Import prevention for circular dependencies
if __name__ == "__main__":
    import time
    import uuid
    from sqlalchemy import event, text