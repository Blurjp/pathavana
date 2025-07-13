#!/usr/bin/env python3
"""
Database health check and monitoring utilities for Pathavana.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_db_context, engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class DatabaseHealthChecker:
    """Comprehensive database health checking utilities."""
    
    async def check_connection(self, session: AsyncSession) -> Dict[str, Any]:
        """Check basic database connectivity."""
        try:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            
            # Get PostgreSQL version
            version_result = await session.execute(text("SELECT version()"))
            pg_version = version_result.scalar()
            
            return {
                "status": "healthy",
                "connected": True,
                "postgresql_version": pg_version.split(' ')[1] if pg_version else "unknown"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }
    
    async def check_table_sizes(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Get size information for all tables."""
        query = """
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
            pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
            pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS indexes_size,
            n_live_tup AS row_count
        FROM pg_stat_user_tables
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        """
        
        result = await session.execute(text(query))
        return [
            {
                "schema": row[0],
                "table": row[1],
                "total_size": row[2],
                "table_size": row[3],
                "indexes_size": row[4],
                "row_count": row[5]
            }
            for row in result
        ]
    
    async def check_index_usage(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Check index usage statistics."""
        query = """
        SELECT 
            schemaname,
            tablename,
            indexname,
            idx_scan AS index_scans,
            idx_tup_read AS tuples_read,
            idx_tup_fetch AS tuples_fetched,
            pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
        FROM pg_stat_user_indexes
        ORDER BY idx_scan DESC;
        """
        
        result = await session.execute(text(query))
        return [
            {
                "schema": row[0],
                "table": row[1],
                "index": row[2],
                "scans": row[3],
                "tuples_read": row[4],
                "tuples_fetched": row[5],
                "size": row[6]
            }
            for row in result
        ]
    
    async def check_slow_queries(self, session: AsyncSession, threshold_ms: int = 1000) -> List[Dict[str, Any]]:
        """Find slow queries."""
        query = """
        SELECT 
            query,
            calls,
            round(total_exec_time::numeric, 2) AS total_time_ms,
            round(mean_exec_time::numeric, 2) AS mean_time_ms,
            round(max_exec_time::numeric, 2) AS max_time_ms,
            round(stddev_exec_time::numeric, 2) AS stddev_time_ms
        FROM pg_stat_statements
        WHERE mean_exec_time > :threshold
        ORDER BY mean_exec_time DESC
        LIMIT 20;
        """
        
        try:
            result = await session.execute(text(query), {"threshold": threshold_ms})
            return [
                {
                    "query": row[0][:100] + "..." if len(row[0]) > 100 else row[0],
                    "calls": row[1],
                    "total_time_ms": row[2],
                    "mean_time_ms": row[3],
                    "max_time_ms": row[4],
                    "stddev_time_ms": row[5]
                }
                for row in result
            ]
        except Exception:
            # pg_stat_statements extension might not be installed
            return []
    
    async def check_connection_stats(self, session: AsyncSession) -> Dict[str, Any]:
        """Check database connection statistics."""
        query = """
        SELECT 
            COUNT(*) AS total_connections,
            COUNT(*) FILTER (WHERE state = 'active') AS active_connections,
            COUNT(*) FILTER (WHERE state = 'idle') AS idle_connections,
            COUNT(*) FILTER (WHERE state = 'idle in transaction') AS idle_in_transaction,
            COUNT(*) FILTER (WHERE wait_event IS NOT NULL) AS waiting_connections
        FROM pg_stat_activity
        WHERE datname = current_database();
        """
        
        result = await session.execute(text(query))
        row = result.one()
        
        return {
            "total": row[0],
            "active": row[1],
            "idle": row[2],
            "idle_in_transaction": row[3],
            "waiting": row[4]
        }
    
    async def check_long_running_queries(self, session: AsyncSession, threshold_minutes: int = 5) -> List[Dict[str, Any]]:
        """Find long-running queries."""
        query = """
        SELECT 
            pid,
            usename,
            application_name,
            state,
            query_start,
            state_change,
            wait_event,
            query
        FROM pg_stat_activity
        WHERE state != 'idle' 
        AND query_start < NOW() - INTERVAL ':threshold minutes'
        AND datname = current_database()
        ORDER BY query_start;
        """
        
        result = await session.execute(text(query.replace(':threshold', str(threshold_minutes))))
        return [
            {
                "pid": row[0],
                "username": row[1],
                "application": row[2],
                "state": row[3],
                "query_start": row[4].isoformat() if row[4] else None,
                "state_change": row[5].isoformat() if row[5] else None,
                "wait_event": row[6],
                "query": row[7][:100] + "..." if len(row[7]) > 100 else row[7]
            }
            for row in result
        ]
    
    async def check_table_bloat(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Check for table bloat."""
        query = """
        SELECT 
            schemaname,
            tablename,
            n_live_tup,
            n_dead_tup,
            CASE WHEN n_live_tup > 0 
                THEN round(100.0 * n_dead_tup / n_live_tup, 2) 
                ELSE 0 
            END AS dead_tuple_percent,
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze
        FROM pg_stat_user_tables
        WHERE n_dead_tup > 1000
        ORDER BY n_dead_tup DESC;
        """
        
        result = await session.execute(text(query))
        return [
            {
                "schema": row[0],
                "table": row[1],
                "live_tuples": row[2],
                "dead_tuples": row[3],
                "dead_percent": row[4],
                "last_vacuum": row[5].isoformat() if row[5] else None,
                "last_autovacuum": row[6].isoformat() if row[6] else None,
                "last_analyze": row[7].isoformat() if row[7] else None,
                "last_autoanalyze": row[8].isoformat() if row[8] else None
            }
            for row in result
        ]
    
    async def check_missing_indexes(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Suggest potentially missing indexes based on query patterns."""
        query = """
        SELECT 
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation,
            null_frac
        FROM pg_stats
        WHERE schemaname = 'public'
        AND n_distinct > 100
        AND correlation < 0.1
        AND null_frac < 0.5
        ORDER BY n_distinct DESC
        LIMIT 20;
        """
        
        result = await session.execute(text(query))
        return [
            {
                "schema": row[0],
                "table": row[1],
                "column": row[2],
                "distinct_values": row[3],
                "correlation": row[4],
                "null_fraction": row[5],
                "suggestion": f"Consider adding index on {row[1]}.{row[2]}"
            }
            for row in result
        ]
    
    async def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": "pathavana",
            "checks": {}
        }
        
        async with get_db_context() as session:
            # Connection check
            report["checks"]["connection"] = await self.check_connection(session)
            
            # Table sizes
            report["checks"]["table_sizes"] = await self.check_table_sizes(session)
            
            # Connection stats
            report["checks"]["connections"] = await self.check_connection_stats(session)
            
            # Long running queries
            report["checks"]["long_running_queries"] = await self.check_long_running_queries(session)
            
            # Table bloat
            report["checks"]["table_bloat"] = await self.check_table_bloat(session)
            
            # Index usage
            report["checks"]["index_usage"] = await self.check_index_usage(session)
            
            # Slow queries
            report["checks"]["slow_queries"] = await self.check_slow_queries(session)
            
            # Missing indexes
            report["checks"]["missing_indexes"] = await self.check_missing_indexes(session)
            
            # Overall health score
            report["health_score"] = self._calculate_health_score(report["checks"])
        
        return report
    
    def _calculate_health_score(self, checks: Dict[str, Any]) -> int:
        """Calculate overall health score (0-100)."""
        score = 100
        
        # Connection health
        if checks["connection"]["status"] != "healthy":
            score -= 50
        
        # Connection pool usage
        conn_stats = checks["connections"]
        if conn_stats["idle_in_transaction"] > 5:
            score -= 10
        if conn_stats["waiting"] > 10:
            score -= 10
        
        # Long running queries
        if len(checks["long_running_queries"]) > 0:
            score -= min(20, len(checks["long_running_queries"]) * 5)
        
        # Table bloat
        for table in checks["table_bloat"]:
            if table["dead_percent"] > 20:
                score -= 5
        
        # Slow queries
        if len(checks["slow_queries"]) > 5:
            score -= 10
        
        return max(0, score)


async def main():
    """Main health check function."""
    print("Pathavana Database Health Check")
    print("=" * 50)
    
    checker = DatabaseHealthChecker()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        # JSON output mode
        report = await checker.generate_health_report()
        print(json.dumps(report, indent=2))
    else:
        # Interactive mode
        print("\nGenerating health report...\n")
        
        report = await checker.generate_health_report()
        
        # Connection status
        conn = report["checks"]["connection"]
        print(f"Database Connection: {conn['status'].upper()}")
        if conn["connected"]:
            print(f"PostgreSQL Version: {conn['postgresql_version']}")
        print()
        
        # Health score
        score = report["health_score"]
        score_emoji = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
        print(f"Overall Health Score: {score}/100 {score_emoji}")
        print()
        
        # Connection statistics
        conn_stats = report["checks"]["connections"]
        print("Connection Statistics:")
        print(f"  Total: {conn_stats['total']}")
        print(f"  Active: {conn_stats['active']}")
        print(f"  Idle: {conn_stats['idle']}")
        print(f"  Idle in Transaction: {conn_stats['idle_in_transaction']}")
        print(f"  Waiting: {conn_stats['waiting']}")
        print()
        
        # Table sizes
        print("Largest Tables:")
        for table in report["checks"]["table_sizes"][:5]:
            print(f"  {table['table']}: {table['total_size']} ({table['row_count']} rows)")
        print()
        
        # Long running queries
        long_queries = report["checks"]["long_running_queries"]
        if long_queries:
            print(f"⚠️  Long Running Queries ({len(long_queries)}):")
            for query in long_queries[:3]:
                print(f"  PID {query['pid']}: {query['query']}")
            print()
        
        # Table bloat
        bloated = [t for t in report["checks"]["table_bloat"] if t["dead_percent"] > 10]
        if bloated:
            print(f"⚠️  Tables with High Dead Tuple Ratio ({len(bloated)}):")
            for table in bloated[:3]:
                print(f"  {table['table']}: {table['dead_percent']}% dead tuples")
            print()
        
        # Slow queries
        slow_queries = report["checks"]["slow_queries"]
        if slow_queries:
            print(f"Slowest Queries (avg time):")
            for query in slow_queries[:3]:
                print(f"  {query['mean_time_ms']}ms: {query['query']}")
            print()
        
        # Save full report
        report_file = Path(__file__).parent.parent / "logs" / f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nFull report saved to: {report_file}")
    
    # Close connections
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())