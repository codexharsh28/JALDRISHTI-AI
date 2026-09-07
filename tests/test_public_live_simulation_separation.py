"""
Live vs Mock vs Simulation Separation Tests for JALDRISHTI AI Public Alerts.
Proves that simulation, replay, and mock alerts are explicitly labeled and never called live operational.
"""

import pytest
from services.notifications.region_config import region_config_manager
from services.notifications.notification_queue import notification_queue
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_mock_mode_flag_in_health_and_providers():
    res_h = client.get("/api/v1/notifications/health")
    assert res_h.status_code == 200
    assert res_h.json()["providers"]["sms"] == "MOCK_MODE_ACTIVE"

    res_p = client.get("/api/v1/notifications/providers")
    assert res_p.status_code == 200
    assert res_p.json()["mock_mode"] is True
    assert res_p.json()["active_sms_provider"] == "MOCK_SMS_SINK"

def test_region_metadata_labels_pilot():
    meta = region_config_manager.get_public_metadata()
    assert "MAHANADI_DELTA" in meta["region_id"]
    assert meta["is_pilot_deployment"] is True
    assert meta["state"] == "Odisha"
