"""
Database Connection & Transaction Manager for JALDRISHTI AI Public Notifications.
Supports thread-safe connection pooling, WAL mode, foreign keys, and transaction contexts.
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Generator
import threading
from pathlib import Path

DEFAULT_DB_PATH = os.getenv("NOTIFICATIONS_DB_PATH", "data/jaldrishti_notifications.db")

class DatabaseManager:
    """
    Manages SQLite database connections with strict foreign key constraints,
    WAL journaling for concurrent reads/writes, and automatic transaction rollback.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        Path(os.path.dirname(self.db_path) or ".").mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "connection") or self._local.connection is None:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            # Enable foreign key enforcement
            conn.execute("PRAGMA foreign_keys = ON;")
            # Enable WAL mode for high concurrency
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            self._local.connection = conn
        return self._local.connection

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def execute_script(self, sql_script: str) -> None:
        with self.transaction() as conn:
            conn.executescript(sql_script)

    def _init_db(self) -> None:
        schema_file = Path(__file__).parent / "schema.sql"
        if schema_file.exists():
            with open(schema_file, "r", encoding="utf-8") as f:
                self.execute_script(f.read())

# Global singleton instance
db_manager = DatabaseManager()
