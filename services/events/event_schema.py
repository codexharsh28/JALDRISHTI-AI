"""
Immutable Operational Event Schema for JALDRISHTI AI.
Enforces versioning, provenance, causal lineage, and data references.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
import hashlib
import json
import uuid

from services.events.event_types import EventType, EventPriority

def generate_event_id(prefix: str = "EVT") -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    rand = uuid.uuid4().hex[:6]
    return f"{prefix}-{ts}-{rand}"

def compute_payload_hash(data: Any) -> str:
    encoded = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

class OperationalEvent(BaseModel):
    """
    Immutable Operational Event.
    Represents an atomic, versioned state transition or validated observation in JALDRISHTI AI.
    """
    model_config = ConfigDict(frozen=True) # Enforces strict immutability

    event_id: str = Field(default_factory=lambda: generate_event_id("EVT"))
    event_type: EventType
    event_version: str = "1.0.0"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    occurred_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    source_id: str
    provider: str
    mode: str = "LIVE"
    data_state: str = "LIVE"
    
    correlation_id: str = Field(default_factory=lambda: generate_event_id("CORR"))
    causation_id: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL

    # Lineage and execution identifiers
    ingestion_run_id: Optional[str] = None
    forecast_run_id: Optional[str] = None
    inundation_run_id: Optional[str] = None
    state_version: Optional[int] = None

    # Spatial & operational scoping
    station_id: Optional[str] = None
    basin_id: Optional[str] = "mahanadi-delta"
    subbasin_id: Optional[str] = None
    severity: Optional[str] = None
    latency_ms: Optional[float] = None

    # Payload & references (Large rasters MUST use payload_ref instead of embedding)
    payload_ref: Optional[str] = None
    payload_hash: str = Field(default_factory=lambda: hashlib.sha256(b"").hexdigest())
    data: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(
        cls,
        event_type: EventType,
        source_id: str,
        provider: str,
        data: Dict[str, Any],
        occurred_at: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        mode: str = "LIVE",
        data_state: str = "LIVE",
        ingestion_run_id: Optional[str] = None,
        forecast_run_id: Optional[str] = None,
        inundation_run_id: Optional[str] = None,
        state_version: Optional[int] = None,
        station_id: Optional[str] = None,
        payload_ref: Optional[str] = None
    ) -> "OperationalEvent":
        now = datetime.now(timezone.utc)
        payload_hash = compute_payload_hash(data)
        return cls(
            event_id=generate_event_id("EVT"),
            event_type=event_type,
            event_version="1.0.0",
            created_at=now.isoformat(),
            occurred_at=(occurred_at or now).isoformat(),
            source_id=source_id,
            provider=provider,
            mode=mode,
            data_state=data_state,
            correlation_id=correlation_id or generate_event_id("CORR"),
            causation_id=causation_id,
            priority=priority,
            ingestion_run_id=ingestion_run_id,
            forecast_run_id=forecast_run_id,
            inundation_run_id=inundation_run_id,
            state_version=state_version,
            station_id=station_id,
            payload_ref=payload_ref,
            payload_hash=payload_hash,
            data=data
        )
