"""
Unit tests for Alert Condition Fingerprint Deduplication (Phase 16).
"""

import pytest
from datetime import datetime, timezone
from services.alerts.alert_engine import AlertEngine
from services.models import ConfidenceLevel, AlertSeverity

def test_alert_condition_fingerprint_deduplication():
    engine = AlertEngine()

    # Evaluation 1: initial incident creation
    item1 = engine.evaluate_alert(
        fused_rain_mm_hr=22.0,
        rain_24h_mm=130.0,
        river_stage_m=25.40,
        warning_stage_m=25.0,
        danger_stage_m=26.30,
        flood_prob=0.62,
        inundated_area_sqkm=95.0,
        data_confidence=ConfidenceLevel.HIGH,
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=12.0,
        forecast_run_id="FR-DEDUP-01",
        base_time=datetime.now(timezone.utc)
    )

    incidents_count_1 = len(engine.get_all_incidents())
    assert incidents_count_1 == 1

    # Evaluation 2: same condition & stage window under another forecast run
    item2 = engine.evaluate_alert(
        fused_rain_mm_hr=23.0,
        rain_24h_mm=132.0,
        river_stage_m=25.42, # Same 25.4 bucket
        warning_stage_m=25.0,
        danger_stage_m=26.30,
        flood_prob=0.64,
        inundated_area_sqkm=98.0,
        data_confidence=ConfidenceLevel.HIGH,
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=12.0,
        forecast_run_id="FR-DEDUP-02",
        base_time=datetime.now(timezone.utc)
    )

    incidents_count_2 = len(engine.get_all_incidents())
    # Should update existing incident rather than duplicate
    assert incidents_count_2 == 1
    assert item2.alert_id == item1.alert_id
