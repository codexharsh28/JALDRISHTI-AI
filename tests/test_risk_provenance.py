"""
Unit tests for Risk Provenance, Run ID Chaining & Store Querying.
"""

import pytest
from services.risk.risk_types import RiskState, RiskLevel
from services.risk.risk_store import risk_store

def test_risk_store_append_and_query():
    state = RiskState(
        risk_state_id="RSK-TEST-PROV-01",
        state_version=1050,
        risk_score=68.5,
        risk_level=RiskLevel.ALERT,
        forecast_run_id="FR-PROV-2026",
        inundation_run_id="INUN-PROV-2026",
        impact_run_id="IMP-PROV-2026",
        data_confidence="HIGH"
    )
    
    appended = risk_store.append(state)
    assert appended is True

    fetched = risk_store.get_by_id("RSK-TEST-PROV-01")
    assert fetched is not None
    assert fetched.risk_score == 68.5
    assert fetched.forecast_run_id == "FR-PROV-2026"
    assert fetched.inundation_run_id == "INUN-PROV-2026"

def test_risk_store_history_order():
    hist = risk_store.get_history(limit=5)
    assert len(hist) > 0
    # Most recent should be first
    assert hist[0].risk_state_id == "RSK-TEST-PROV-01"
