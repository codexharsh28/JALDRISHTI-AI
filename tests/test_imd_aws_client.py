"""
Unit tests for IMDAWSClient.
Tests request construction, SSL context, timeout configuration, status classification, and retries.
"""

import pytest
from unittest.mock import patch, MagicMock
import urllib.error
from services.ingestion.providers.imd_aws_client import IMDAWSClient, IMDAWSClientError

def test_imd_aws_client_init_defaults():
    client = IMDAWSClient()
    assert client.base_url == "https://city.imd.gov.in/api/aws_data_api.php"
    assert client.timeout_seconds == 10.0
    assert client.is_configured() is True
    diag = client.get_status_diagnostics()
    assert diag["configured"] is True
    assert "https://city.imd.gov.in" in diag["endpoint"]

def test_imd_aws_client_custom_params():
    client = IMDAWSClient(
        base_url="https://city.imd.gov.in/api/aws_data_api.php",
        state_id="ODISHA",
        public_ip="203.0.113.10",
        timeout_seconds=5.0
    )
    assert client.state_id == "ODISHA"
    assert client.public_ip == "203.0.113.10"
    assert client.timeout_seconds == 5.0
    diag = client.get_status_diagnostics()
    assert diag["state_id"] == "ODISHA"
    assert diag["public_ip_configured"] is True

def test_status_code_classification():
    client = IMDAWSClient()
    assert client._classify_status_code(200) == "SUCCESS"
    assert client._classify_status_code(400) == "CONFIGURATION_ERROR"
    assert client._classify_status_code(401) == "ACCESS_DENIED"
    assert client._classify_status_code(403) == "ACCESS_DENIED"
    assert client._classify_status_code(404) == "ENDPOINT_NOT_FOUND"
    assert client._classify_status_code(429) == "RATE_LIMITED"
    assert client._classify_status_code(500) == "PROVIDER_UNAVAILABLE"
    assert client._classify_status_code(503) == "PROVIDER_UNAVAILABLE"

@patch("urllib.request.urlopen")
def test_fetch_raw_data_success(mock_urlopen):
    sample_json = b'[{"CALL_SIGN":"42971","STATION":"BHUBANESWAR","CURR_TEMP":"28.4","RH":"92","Latitude":"20.296","Longitude":"85.824"}]'
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = sample_json
    mock_urlopen.return_value.__enter__.return_value = mock_response

    client = IMDAWSClient()
    records, meta = client.fetch_raw_data(force=True)
    assert len(records) == 1
    assert records[0]["CALL_SIGN"] == "42971"
    assert meta["http_status"] == 200
    assert meta["record_count"] == 1

@patch("urllib.request.urlopen")
def test_fetch_raw_data_401_access_denied(mock_urlopen):
    http_error = urllib.error.HTTPError(
        url="https://city.imd.gov.in/api/aws_data_api.php",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=None
    )
    mock_urlopen.side_effect = http_error

    client = IMDAWSClient()
    with pytest.raises(IMDAWSClientError) as exc_info:
        client.fetch_raw_data(force=True)
    assert exc_info.value.category == "ACCESS_DENIED"
    assert exc_info.value.status_code == 401
