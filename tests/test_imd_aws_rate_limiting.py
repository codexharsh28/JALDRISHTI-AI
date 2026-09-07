"""
Unit tests for IMD AWS provider rate limiting and request cooldown.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from services.ingestion.providers.imd_aws_client import IMDAWSClient

@patch("urllib.request.urlopen")
def test_client_cooldown_delays_rapid_requests(mock_urlopen):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b'[]'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    client = IMDAWSClient()
    client._min_cooldown_seconds = 0.1  # Fast cooldown for test

    # First call
    client.fetch_raw_data(force=True)
    t0 = time.monotonic()

    # Second call without force -> should sleep for cooldown
    client.fetch_raw_data(force=False)
    t1 = time.monotonic()

    assert (t1 - t0) >= 0.05
