"""
Risk Types and Causal Attribution Schemas for JALDRISHTI AI Live Risk Evolution.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid

class RiskLevel(str, Enum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    WARNING = "WARNING"
    ALERT = "ALERT"
    CRITICAL = "CRITICAL"

class RiskContributor(BaseModel):
    factor_name: str
    delta_score: float # e.g. +10.5 or -2.0
    direction: str # "INCREASING_RISK", "DECREASING_RISK", "NEUTRAL"
    category: str # "PRECIPITATION", "HYDROLOGY", "INUNDATION", "IMPACT", "CONFIDENCE"
    evidence_value: Any
    baseline_value: Optional[Any] = None
    explanation: str

class RiskState(BaseModel):
    risk_state_id: str = Field(default_factory=lambda: f"RSK-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}")
    state_version: int = 1000
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    risk_score: float = 24.5 # Normalized 0.0 - 100.0
    previous_risk_score: float = 24.5
    risk_level: RiskLevel = RiskLevel.NORMAL
    risk_change: float = 0.0 # Delta
    is_material_change: bool = False
    contributors: List[RiskContributor] = Field(default_factory=list)
    top_causal_summary: str = "Baseline risk level"
    forecast_run_id: str = "FR-DEFAULT"
    inundation_run_id: Optional[str] = None
    impact_run_id: Optional[str] = None
    data_confidence: str = "HIGH"
    model_confidence: str = "HIGH"
    evaluation_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
