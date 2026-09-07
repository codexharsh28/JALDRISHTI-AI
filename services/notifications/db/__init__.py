"""
Database package for JALDRISHTI AI Public Notifications.
"""

from services.notifications.db.connection import db_manager, DatabaseManager
from services.notifications.db.migrations import migration_runner
from services.notifications.db.repositories import (
    UserRepository,
    VerificationRepository,
    SubscriptionRepository,
    NotificationRepository,
    AuditRepository
)

__all__ = [
    "db_manager",
    "DatabaseManager",
    "migration_runner",
    "UserRepository",
    "VerificationRepository",
    "SubscriptionRepository",
    "NotificationRepository",
    "AuditRepository"
]
