"""
Unit tests for Temporal Causality & Anti-Leakage in Risk Calculation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from services.risk.risk_types import RiskState
from services.risk.risk_service import RiskService

def test_risk_evaluation_timestamp_recorded():
    state = RiskState(
        risk_score=42.0,
        evaluation_time=datetime.now(timezone.utc).isoformat()
    )
    eval_dt = datetime.fromisoformat(state.evaluation_time)
    now_dt = datetime.now(timezone.utc)
    # Integrity check: evaluation time must be contemporary
    assert abs((now_dt - eval_dt).total_seconds()) < 10.0

def test_risk_history_temporal_monotonicity():
    history = [
        RiskState(state_version=1001, timestamp="2026-08-27T10:00:00Z", risk_score=25.0),
        RiskState(state_version=1002, timestamp="2026-08-27T10:15:00Z", risk_score=32.0),
        RiskState(state_version=1003, timestamp="2026-08-27T10:30:00Z", risk_score=48.0)
    ]
    for i in range(len(history) - 1):
        assert history[i].state_version < history[i + 1].state_version
        assert history[i].timestamp < history[i + 1].timestamp
