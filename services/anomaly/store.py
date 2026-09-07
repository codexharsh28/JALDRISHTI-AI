"""
Persistent Anomaly Record Store for JALDRISHTI AI.
Appends validated anomaly events to daily JSONL audit logs and provides indexed, filterable querying.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path
import json
import logging
import threading
from collections import deque

from services.anomaly.anomaly_types import AnomalyRecord, AnomalyState, AnomalyClassification

logger = logging.getLogger(__name__)

class AnomalyStore:
    """
    Thread-safe append-only persistent store for hydrometeorological anomaly events.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("data/anomalies")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._recent_records: deque = deque(maxlen=1000)
        self._records_by_id: Dict[str, AnomalyRecord] = {}

    def append(self, record: AnomalyRecord) -> bool:
        """Appends an anomaly record to storage and in-memory cache."""
        with self._lock:
            self._recent_records.append(record)
            self._records_by_id[record.anomaly_id] = record

            # Daily JSONL archive
            today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
            file_path = self.storage_dir / f"anomalies_{today_str}.jsonl"
            try:
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(record.model_dump_json() + "\n")
                return True
            except Exception as e:
                logger.error(f"Failed to persist anomaly record {record.anomaly_id}: {e}")
                return False

    def get_by_id(self, anomaly_id: str) -> Optional[AnomalyRecord]:
        """Retrieves a single anomaly record by ID."""
        with self._lock:
            return self._records_by_id.get(anomaly_id)

    def query(
        self,
        station_id: Optional[str] = None,
        variable: Optional[str] = None,
        anomaly_state: Optional[AnomalyState] = None,
        classification: Optional[AnomalyClassification] = None,
        provider: Optional[str] = None,
        since_timestamp: Optional[str] = None,
        limit: int = 50
    ) -> List[AnomalyRecord]:
        """Query recent anomaly records with multi-criteria filtering."""
        with self._lock:
            results = []
            for rec in reversed(self._recent_records):
                if station_id and rec.station_id != station_id:
                    continue
                if variable and rec.variable != variable:
                    continue
                if anomaly_state and rec.anomaly_state != anomaly_state:
                    continue
                if classification and rec.classification != classification:
                    continue
                if provider and rec.provider != provider:
                    continue
                if since_timestamp and rec.timestamp < since_timestamp:
                    continue
                results.append(rec)
                if len(results) >= limit:
                    break
            return results

    def get_summary(self) -> Dict[str, Any]:
        """Generates high-level anomaly summary statistics."""
        with self._lock:
            counts_by_state = {s.value: 0 for s in AnomalyState}
            counts_by_station: Dict[str, int] = {}
            counts_by_classification: Dict[str, int] = {}
            
            for rec in self._recent_records:
                counts_by_state[rec.anomaly_state.value] = counts_by_state.get(rec.anomaly_state.value, 0) + 1
                counts_by_station[rec.station_id] = counts_by_station.get(rec.station_id, 0) + 1
                counts_by_classification[rec.classification.value] = counts_by_classification.get(rec.classification.value, 0) + 1

            return {
                "total_recent_anomalies": len(self._recent_records),
                "counts_by_state": counts_by_state,
                "counts_by_station": counts_by_station,
                "counts_by_classification": counts_by_classification
            }

    def clear(self):
        """Clears in-memory records (useful for test resets)."""
        with self._lock:
            self._recent_records.clear()
            self._records_by_id.clear()

# Global anomaly store singleton
anomaly_store = AnomalyStore()
