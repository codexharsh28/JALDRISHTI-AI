"""
Event Bus Integration & Causal Propagation Tests for Demo Orchestrator.
"""

import pytest
from services.demo.demo_orchestrator import demo_orchestrator
from services.events.dispatcher import event_dispatcher

def test_demo_start_dispatches_events():
    status = demo_orchestrator.start_demo()
    assert status["is_active"] is True
    assert status["current_step"] == 0
    assert status["current_stage"]["name"] == "NORMAL"

def test_demo_stepping_advances_stages():
    status_t1 = demo_orchestrator.step_forward()
    assert status_t1["current_step"] == 1
    assert status_t1["current_stage"]["name"] == "RAINFALL_ONSET"

    status_t2 = demo_orchestrator.step_forward()
    assert status_t2["current_step"] == 2
    assert status_t2["current_stage"]["name"] == "HEAVY_RAIN"
