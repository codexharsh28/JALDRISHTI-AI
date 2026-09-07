"""
Unit tests for Alert Event-Specific Lead Time & Threshold Crossing Calculations (Phase 16).
"""

import pytest
from datetime import datetime, timezone, timedelta
from services.alerts.alert_engine import AlertEngine
from services.models import ConfidenceLevel, AlertSeverity

def test_alert_event_specific_lead_time_tracking():
    engine = AlertEngine()
    base_t = datetime(2026, 8, 27, 12, 0, 0, tzinfo=timezone.utc)
    
    item = engine.evaluate_alert(
        fused_rain_mm_hr=35.0,
        rain_24h_mm=140.0,
        river_stage_m=25.80,
        warning_stage_m=25.0,
        danger_stage_m=26.30,
        flood_prob=0.74,
        inundated_area_sqkm=110.0,
        data_confidence=ConfidenceLevel.HIGH,
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=8.5,
        forecast_run_id="FR-LEAD-01",
        base_time=base_t
    )

    assert item.lead_time_hours == 8.5
    inc = engine.get_incident_by_id(item.alert_id)
    assert inc is not None
    assert inc.lead_time_hours == 8.5
    assert inc.threshold_crossing_time == (base_t + timedelta(hours=8.5)).isoformat()
