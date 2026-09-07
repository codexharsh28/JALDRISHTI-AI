"""
Unit tests for Alert Integration & Safety Gating (Requirement 11).
Risk state can create ALERT_CANDIDATE but cannot bypass the backend alert safety gate.
RED requires: high risk, sufficient data confidence, severe impact, and human review.
"""

import pytest
from datetime import datetime, timezone
from services.alerts.alert_engine import AlertEngine
from services.models import ConfidenceLevel, AlertSeverity
from services.risk.risk_types import RiskLevel

def test_critical_risk_alert_gating_high_confidence():
    alert_engine = AlertEngine()
    
    # 1. High risk with HIGH data confidence & severe inundation
    item = alert_engine.evaluate_alert(
        fused_rain_mm_hr=75.0,
        rain_24h_mm=260.0,
        river_stage_m=28.20,
        warning_stage_m=25.0,
        danger_stage_m=26.30,
        flood_prob=0.94,
        inundated_area_sqkm=480.0,
        data_confidence=ConfidenceLevel.HIGH,
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=4.0,
        forecast_run_id="FR-CRIT-RISK-01",
        base_time=datetime.now(timezone.utc)
    )
    assert item.severity == AlertSeverity.RED
    assert item.requires_human_review is True

def test_critical_risk_blocked_from_red_when_data_degraded():
    alert_engine = AlertEngine()

    # 2. Critical risk conditions but DATA_DEGRADED -> MUST NOT BE RED
    item = alert_engine.evaluate_alert(
        fused_rain_mm_hr=75.0,
        rain_24h_mm=260.0,
        river_stage_m=28.20,
        warning_stage_m=25.0,
        danger_stage_m=26.30,
        flood_prob=0.94,
        inundated_area_sqkm=480.0,
        data_confidence=ConfidenceLevel.DATA_DEGRADED,
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=4.0,
        forecast_run_id="FR-CRIT-DEGRADED-01",
        base_time=datetime.now(timezone.utc)
    )
    assert item.severity != AlertSeverity.RED
    assert item.severity == AlertSeverity.ORANGE
    assert item.requires_human_review is True
