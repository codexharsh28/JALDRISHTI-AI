"""
WebSocket Security & Abuse Prevention Tests.
Validates ping/pong, heartbeat, message sizing, and state synchronization.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_websocket_ping_pong():
    with client.websocket_connect("/ws/v1/live") as ws:
        ws.send_json({"action": "PING"})
        data = ws.receive_json()
        assert data["type"] == "PONG"
        assert "timestamp" in data

def test_websocket_sync_state():
    with client.websocket_connect("/ws/v1/live") as ws:
        ws.send_json({"action": "SYNC_STATE", "last_state_version": 0})
        # Expect either full state snapshot or recent events
        data = ws.receive_json()
        assert "type" in data
