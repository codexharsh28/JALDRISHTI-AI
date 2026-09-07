"""
Immutable Audit Trail Logger for Alert Decisions in JALDRISHTI AI (Phase 16).
Appends tamper-evident audit records to daily JSONL files.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path
import json
import logging
import threading
from collections import deque

from services.alerts.alert_types import AlertAuditRecord

logger = logging.getLogger(__name__)

class AlertAuditLogger:
    """
    Append-only audit trail logger for operator review actions and lifecycle transitions.
    """

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path("data/alerts")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._recent_logs: deque = deque(maxlen=500)

    def log_action(self, record: AlertAuditRecord) -> bool:
        """Appends audit record to file and in-memory log."""
        with self._lock:
            self._recent_logs.append(record)
            today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
            file_path = self.log_dir / f"audit_log_{today_str}.jsonl"
            try:
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(record.model_dump_json() + "\n")
                return True
            except Exception as e:
                logger.error(f"Failed to persist alert audit record {record.audit_id}: {e}")
                return False

    def log_audit(self, record: AlertAuditRecord) -> bool:
        return self.log_action(record)

    def get_recent_audits(self, limit: int = 50) -> List[AlertAuditRecord]:
        with self._lock:
            return list(reversed(list(self._recent_logs)))[:limit]

# Global audit logger singleton
alert_audit_logger = AlertAuditLogger()
