"""
Demo Scenario State Reset & Clean Cleanup Tests.
"""

import pytest
from services.demo.demo_orchestrator import demo_orchestrator

def test_demo_reset_clears_active_state():
    demo_orchestrator.start_demo()
    demo_orchestrator.step_forward()
    demo_orchestrator.step_forward()

    status = demo_orchestrator.reset_demo()
    assert status["is_active"] is False
    assert status["is_playing"] is False
    assert status["current_step"] == 0
    assert status["current_stage"]["index"] == 0
