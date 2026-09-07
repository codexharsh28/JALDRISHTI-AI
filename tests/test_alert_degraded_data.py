"""
Unit tests for Alert Degraded Data Gating & GloFAS Fallback Constraints (Phase 16).
"""

import pytest
from datetime import datetime, timezone
from services.alerts.alert_engine import AlertEngine
from services.models import ConfidenceLevel, AlertSeverity

def test_degraded_data_suppresses_red_escalation():
    engine = AlertEngine()
    
    # Critical river stage exceeding danger mark, but data confidence is DATA_DEGRADED
    item = engine.evaluate_alert(
        fused_rain_mm_hr=70.0,
        rain_24h_mm=240.0,
        river_stage_m=28.40,
        warning_stage_m=25.0,
        danger_stage_m=26.30,
        flood_prob=0.95,
        inundated_area_sqkm=410.0,
        data_confidence=ConfidenceLevel.DATA_DEGRADED,
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=4.0,
        forecast_run_id="FR-DEG-01",
        base_time=datetime.now(timezone.utc)
    )

    # Must NOT be RED
    assert item.severity == AlertSeverity.ORANGE
    assert "ESCALATION CONSTRAINED" in item.trigger_reason
    assert "DEGRADED/OFFLINE" in item.trigger_reason
    assert item.requires_human_review is True
