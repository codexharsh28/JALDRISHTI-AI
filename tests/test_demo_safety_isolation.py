"""
Safety Isolation & Human Operator Review Gate Tests during Demo.
"""

import pytest
from services.demo.demo_orchestrator import demo_orchestrator

def test_operator_gate_blocks_until_acknowledged():
    demo_orchestrator.start_demo()
    # Step to stage 10 (Critical Stage - Requires Review)
    for _ in range(10):
        demo_orchestrator.step_forward()

    status = demo_orchestrator.get_status()
    assert status["current_stage"]["requires_operator_review"] is True
    assert status["operator_review_acknowledged"] is False

    # Acknowledge
    ack_res = demo_orchestrator.acknowledge_operator_gate()
    assert ack_res["operator_review_acknowledged"] is True
    assert ack_res["current_stage"]["requires_operator_review"] is False
