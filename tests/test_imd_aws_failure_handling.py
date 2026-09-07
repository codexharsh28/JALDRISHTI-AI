"""
Unit tests for graceful failure handling and outage behavior.
"""

import pytest
from unittest.mock import patch
from services.ingestion.live_adapters import IMDLiveAdapter
from services.ingestion.providers.imd_aws_client import IMDAWSClientError
from services.ingestion.live_interfaces import SourceState

@patch("services.ingestion.providers.imd_aws_client.IMDAWSClient.fetch_raw_data")
def test_unauthorized_classified_as_not_configured(mock_fetch):
    mock_fetch.side_effect = IMDAWSClientError(
        "IMD AWS HTTP Error 401: Unauthorized",
        category="ACCESS_DENIED",
        status_code=401
    )

    adapter = IMDLiveAdapter()
    result = adapter.fetch(force=True)

    assert result.source_state == SourceState.NOT_CONFIGURED
    assert result.ingestion_run.data_state == "NOT_CONFIGURED"
    assert len(result.observations) == 0  # No fake data!

@patch("services.ingestion.providers.imd_aws_client.IMDAWSClient.fetch_raw_data")
def test_provider_500_classified_as_offline(mock_fetch):
    mock_fetch.side_effect = IMDAWSClientError(
        "IMD AWS HTTP Error 500: Server Error",
        category="PROVIDER_UNAVAILABLE",
        status_code=500
    )

    adapter = IMDLiveAdapter()
    result = adapter.fetch(force=True)

    assert result.source_state == SourceState.OFFLINE
    assert result.ingestion_run.data_state == "OFFLINE"
    assert len(result.observations) == 0
