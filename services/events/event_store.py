"""
Operational Event Store for JALDRISHTI AI.
Provides durable persistence, deduplication indexing, retention enforcement, and causal chain queries.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone, timedelta
import threading

from services.events.event_schema import OperationalEvent
from services.events.event_types import EventType

DEFAULT_EVENT_DIR = Path("data/events")
DEFAULT_EVENT_DIR.mkdir(parents=True, exist_ok=True)

class EventStore:
    """
    Append-only operational event log with in-memory indexes and deduplication.
    """

    def __init__(self, event_dir: Path = DEFAULT_EVENT_DIR, retention_hours: int = 72):
        self.event_dir = Path(event_dir)
        self.event_dir.mkdir(parents=True, exist_ok=True)
        self.retention_hours = retention_hours
        
        # In-memory indexes
        self._events_by_id: Dict[str, OperationalEvent] = {}
        self._events_by_correlation: Dict[str, List[str]] = {}
        self._dedup_keys: Set[str] = set()
        self._lock = threading.RLock()
        
        self._load_recent_events()

    def _dedup_fingerprint(self, event: OperationalEvent) -> str:
        return f"{event.source_id}|{event.occurred_at}|{event.payload_hash}"

    def is_duplicate(self, event: OperationalEvent) -> bool:
        """Check if identical observation has already been ingested."""
        with self._lock:
            if event.event_id in self._events_by_id:
                return True
            fp = self._dedup_fingerprint(event)
            return fp in self._dedup_keys

    def append(self, event: OperationalEvent) -> bool:
        """
        Store an event durably and update indexes.
        Returns False if duplicate, True if appended.
        """
        with self._lock:
            if self.is_duplicate(event):
                return False

            fp = self._dedup_fingerprint(event)
            self._dedup_keys.add(fp)
            self._events_by_id[event.event_id] = event

            if event.correlation_id not in self._events_by_correlation:
                self._events_by_correlation[event.correlation_id] = []
            self._events_by_correlation[event.correlation_id].append(event.event_id)

            # Persist to daily jsonl log
            day_str = datetime.now(timezone.utc).strftime("%Y%m%d")
            log_file = self.event_dir / f"events_{day_str}.jsonl"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")

            return True

    def get_event(self, event_id: str) -> Optional[OperationalEvent]:
        """Retrieve an event by ID."""
        with self._lock:
            return self._events_by_id.get(event_id)

    def query(
        self,
        event_type: Optional[EventType] = None,
        source_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        forecast_run_id: Optional[str] = None,
        since_version: Optional[int] = None,
        limit: int = 100
    ) -> List[OperationalEvent]:
        """Query stored events with forensic filters."""
        with self._lock:
            results = []
            for ev in reversed(list(self._events_by_id.values())):
                if event_type and ev.event_type != event_type:
                    continue
                if source_id and ev.source_id != source_id:
                    continue
                if correlation_id and ev.correlation_id != correlation_id:
                    continue
                if forecast_run_id and ev.forecast_run_id != forecast_run_id:
                    continue
                if since_version is not None and (ev.state_version is None or ev.state_version <= since_version):
                    continue
                results.append(ev)
                if len(results) >= limit:
                    break
            return results

    def get_causal_chain(self, event_id: str) -> List[OperationalEvent]:
        """Reconstruct the entire causal lineage for an event."""
        with self._lock:
            target = self._events_by_id.get(event_id)
            if not target:
                return []
            
            # Find all events sharing the same correlation_id
            corr_ids = self._events_by_correlation.get(target.correlation_id, [])
            chain = [self._events_by_id[eid] for eid in corr_ids if eid in self._events_by_id]
            chain.sort(key=lambda e: e.created_at)
            return chain

    def _load_recent_events(self):
        """Preload recent events from disk on startup for crash recovery."""
        try:
            today = datetime.now(timezone.utc)
            for i in range(2): # Load today and yesterday
                day_str = (today - timedelta(days=i)).strftime("%Y%m%d")
                log_file = self.event_dir / f"events_{day_str}.jsonl"
                if log_file.exists():
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                try:
                                    ev = OperationalEvent.model_validate_json(line)
                                    self._events_by_id[ev.event_id] = ev
                                    fp = self._dedup_fingerprint(ev)
                                    self._dedup_keys.add(fp)
                                    if ev.correlation_id not in self._events_by_correlation:
                                        self._events_by_correlation[ev.correlation_id] = []
                                    self._events_by_correlation[ev.correlation_id].append(ev.event_id)
                                except Exception:
                                    pass
        except Exception:
            pass

    def clear(self):
        """Clear memory indexes (used for test isolation)."""
        with self._lock:
            self._events_by_id.clear()
            self._events_by_correlation.clear()
            self._dedup_keys.clear()

# Global singleton
event_store = EventStore()
