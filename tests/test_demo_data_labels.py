"""
Data Honesty & Synthetic Labeling Verification Tests.
Ensures demo artifacts and responses never masquerade as LIVE real operational data.
"""

import pytest
from services.demo.demo_scenario import DEMO_SCENARIO_STAGES

def test_demo_stages_labeled_as_simulation_or_synthetic():
    for stage in DEMO_SCENARIO_STAGES:
        # None of the stages should claim to be LIVE OPERATIONAL
        assert "LIVE_OPERATIONAL" not in stage.stage_id
        assert stage.top_causal_driver != ""
