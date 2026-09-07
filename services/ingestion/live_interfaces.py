"""
Live Data Ingestion Interfaces for JALDRISHTI AI.
Defines provider-neutral abstractions, ingestion modes, and provenance metadata.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class IngestionMode(str, Enum):
    POLL = "POLL"
    STREAM = "STREAM"
    SCHEDULED = "SCHEDULED"
    FILE = "FILE"
    MANUAL = "MANUAL"

class SourceState(str, Enum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    UNAUTHORIZED = "UNAUTHORIZED"
    UNAVAILABLE = "UNAVAILABLE"
    STALE = "STALE"
    RATE_LIMITED = "RATE_LIMITED"
    OFFLINE = "OFFLINE"

class IngestionRunRecord(BaseModel):
    ingestion_run_id: str
    source_id: str
    provider: str
    ingestion_mode: IngestionMode
    started_at: datetime
    completed_at: datetime
    status: str  # "SUCCESS", "PARTIAL", "FAILED", "SKIPPED"
    records_received: int
    records_accepted: int
    records_rejected: int
    latency_ms: float
    payload_hash: str
    data_state: str  # "LIVE_OPERATIONAL", "MOCK_LIVE", "DEGRADED", "SYNTHETIC"
    error_message: Optional[str] = None

class LiveProviderMetadata(BaseModel):
    provider_id: str
    product_id: str
    ingestion_mode: IngestionMode
    refresh_interval_seconds: int
    minimum_refresh_interval_seconds: int
    timeout_seconds: float
    retry_max_attempts: int
    retry_backoff_factor: float
    units: str
    crs: str
    native_resolution: str
    access_type: str
    license_metadata: str

class LiveObservationResult(BaseModel):
    ingestion_run: IngestionRunRecord
    observations: List[Dict[str, Any]]
    raw_payload_checksum: str
    observed_at: datetime
    received_at: datetime
    source_state: SourceState
    quality_score: float

class BaseLiveProvider:
    """Base interface for all live data ingestion providers."""

    def __init__(self, metadata: LiveProviderMetadata):
        self.meta = metadata
        self._last_success_time: Optional[datetime] = None
        self._last_failure_time: Optional[datetime] = None
        self._consecutive_failures: int = 0
        self._last_ingestion_run: Optional[IngestionRunRecord] = None

    def connect(self) -> bool:
        raise NotImplementedError

    def fetch(self) -> LiveObservationResult:
        raise NotImplementedError

    def validate(self, raw_data: Any) -> bool:
        raise NotImplementedError

    def health_check(self) -> Dict[str, Any]:
        return {
            "provider_id": self.meta.provider_id,
            "product_id": self.meta.product_id,
            "mode": self.meta.ingestion_mode.value,
            "last_success": self._last_success_time.isoformat() if self._last_success_time else None,
            "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None,
            "consecutive_failures": self._consecutive_failures,
            "status": "HEALTHY" if self._consecutive_failures == 0 and self._last_success_time else ("OFFLINE" if self._consecutive_failures > 3 else "DEGRADED")
        }

    def metadata(self) -> LiveProviderMetadata:
        return self.meta
