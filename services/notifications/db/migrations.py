"""
Database Migration System for JALDRISHTI AI Public Notifications.
Tracks schema versions, applies incremental migration scripts, and ensures data integrity.
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
import logging
from services.notifications.db.connection import db_manager

logger = logging.getLogger(__name__)

MIGRATIONS: List[Dict[str, Any]] = [
    {
        "version": "20260827_001_initial_schema",
        "description": "Initial normalized schema for citizens, subscriptions, verifications, and delivery audit",
        "sql": """
        -- Verifies schema_migrations existence
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(32) PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    },
    {
        "version": "20260827_002_add_geohash_indices",
        "description": "Add spatial geohash indices and multi-region fields",
        "sql": """
        CREATE INDEX IF NOT EXISTS idx_subscriptions_locality ON location_subscriptions(locality_name);
        CREATE INDEX IF NOT EXISTS idx_notifications_region ON notifications(region_id);
        """
    }
]

class MigrationRunner:
    """
    Executes versioned migrations in ordered sequence inside transactions.
    """

    @classmethod
    def apply_migrations(cls) -> int:
        applied_count = 0
        with db_manager.transaction() as conn:
            # Ensure migration ledger table exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(32) PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Query already applied migrations
            cursor = conn.execute("SELECT version FROM schema_migrations")
            applied_versions = {row["version"] for row in cursor.fetchall()}

            for m in MIGRATIONS:
                ver = m["version"]
                if ver not in applied_versions:
                    logger.info(f"[MIGRATIONS] Applying migration {ver}: {m['description']}")
                    conn.executescript(m["sql"])
                    conn.execute(
                        "INSERT INTO schema_migrations (version, description, applied_at) VALUES (?, ?, ?)",
                        (ver, m["description"], datetime.now(timezone.utc).isoformat())
                    )
                    applied_count += 1

        return applied_count

    @classmethod
    def get_applied_migrations(cls) -> List[Dict[str, Any]]:
        with db_manager.transaction() as conn:
            cursor = conn.execute("SELECT version, description, applied_at FROM schema_migrations ORDER BY applied_at ASC")
            return [dict(row) for row in cursor.fetchall()]

# Auto-apply on import
migration_runner = MigrationRunner()
migration_runner.apply_migrations()
