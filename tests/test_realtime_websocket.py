"""
Integration tests for WebSocket Event Distribution and Reconnect Sync.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from services.runtime.current_state import current_state_manager
from services.events.event_types import EventType
from services.events.event_schema import OperationalEvent
from services.events.event_store import event_store

def test_websocket_ping_pong_heartbeat():
    client = TestClient(app)
    with client.websocket_connect("/ws/v1/live") as websocket:
        websocket.send_json({"action": "PING"})
        data = websocket.receive_json()
        assert data["type"] == "PONG"
        assert "state_version" in data

def test_websocket_reconnect_missed_events_sync():
    """Verifies that client requesting SYNC_STATE receives missed event delta."""
    client = TestClient(app)
    v1 = current_state_manager.state_version

    # Insert an event with higher state version
    ev = OperationalEvent.create(
        event_type=EventType.HYDROLOGY_UPDATED,
        source_id="HYDRO_TEST",
        provider="Streamflow",
        state_version=v1 + 1,
        data={"stage_m": 26.9}
    )
    event_store.append(ev)

    with client.websocket_connect("/ws/v1/live") as websocket:
        websocket.send_json({"action": "SYNC_STATE", "last_state_version": v1})
        msg = websocket.receive_json()
        assert msg["type"] == "HYDROLOGY_UPDATED"
        assert msg["state_version"] == v1 + 1
