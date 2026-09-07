"""
Anomaly Types, Domain Enums and Pydantic Models for JALDRISHTI AI Hydrometeorological Anomaly Detection (Phase 13).
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid

class AnomalyState(str, Enum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    ANOMALOUS = "ANOMALOUS"
    LIKELY_SENSOR_ERROR = "LIKELY_SENSOR_ERROR"

class AnomalyClassification(str, Enum):
    VALID_EXTREME = "VALID_EXTREME"
    POSSIBLE_ANOMALY = "POSSIBLE_ANOMALY"
    LIKELY_SENSOR_ERROR = "LIKELY_SENSOR_ERROR"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"
    TEMPORAL_JUMP = "TEMPORAL_JUMP"
    STATISTICAL_OUTLIER = "STATISTICAL_OUTLIER"

class AnomalyDomain(str, Enum):
    RAINFALL = "rainfall"
    RIVER_STAGE = "river_stage"
    DISCHARGE = "discharge"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    WIND = "wind"
    SOURCE_LATENCY = "source_latency"
    MISSINGNESS = "missingness"

class AnomalyRecord(BaseModel):
    anomaly_id: str = Field(default_factory=lambda: f"ANOM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}")
    station_id: str
    variable: str
    observed_value: Optional[float] = None
    expected_range: List[float] = Field(default_factory=list) # [min, max]
    baseline_value: Optional[float] = None
    anomaly_score: float = 0.0 # 0.0 to 1.0 (uncalibrated score, not raw probability)
    anomaly_state: AnomalyState = AnomalyState.NORMAL
    classification: AnomalyClassification = AnomalyClassification.INSUFFICIENT_CONTEXT
    reason: str = "Normal operating bounds"
    layers_triggered: List[str] = Field(default_factory=list) # ["LEVEL_0_PHYSICAL_BOUNDS", "LEVEL_1_TEMPORAL_JUMP", ...]
    neighbor_comparison: Dict[str, Any] = Field(default_factory=dict)
    source_agreement: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data_state: str = "LIVE"
    provider: str = "UNKNOWN"
