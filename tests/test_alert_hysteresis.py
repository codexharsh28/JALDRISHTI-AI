"""
Unit tests for Alert Deadband Hysteresis & Numerical Flapping Suppression (Phase 16).
"""

import pytest
from datetime import datetime, timezone
from services.alerts.alert_engine import AlertEngine
from services.models import ConfidenceLevel, AlertSeverity

def test_alert_severity_history_buffered():
    engine = AlertEngine()
    
    # Send 6 consecutive evaluations
    for i in range(6):
        item = engine.evaluate_alert(
            fused_rain_mm_hr=20.0,
            rain_24h_mm=120.0,
            river_stage_m=25.20 + (i * 0.02),
            warning_stage_m=25.0,
            danger_stage_m=26.30,
            flood_prob=0.58,
            inundated_area_sqkm=80.0,
            data_confidence=ConfidenceLevel.HIGH,
            model_confidence=ConfidenceLevel.HIGH,
            lead_time_hours=12.0,
            forecast_run_id="FR-HYST-01",
            base_time=datetime.now(timezone.utc)
        )
        assert item.severity == AlertSeverity.ORANGE

    hist = engine._severity_history[item.alert_id]
    # Max length of hysteresis buffer should be 5
    assert len(hist) == 5
    assert all(s == AlertSeverity.ORANGE for s in hist)
