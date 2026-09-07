"""
Unit tests for IMD AWS Security, Sanitization & Privacy.
"""

import pytest
from services.ingestion.providers.imd_aws_client import IMDAWSClient
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_diagnostics_never_leaks_api_keys_or_tokens():
    aws_client = IMDAWSClient(base_url="https://city.imd.gov.in/api/aws_data_api.php?secret_key=SUPER_SECRET")
    diag = aws_client.get_status_diagnostics()
    # Query parameters must be stripped from endpoint in diagnostics
    assert "SUPER_SECRET" not in diag["endpoint"]
    assert "secret_key" not in diag["endpoint"]

def test_api_status_endpoint_safe_payload():
    res = client.get("/api/v1/live/imd-aws/status")
    assert res.status_code == 200
    data = res.json()
    # No passwords, secrets, or keys in payload
    for key in data:
        assert "token" not in key.lower()
        assert "secret" not in key.lower()
        assert "password" not in key.lower()
