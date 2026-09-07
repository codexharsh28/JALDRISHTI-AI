"""
Unit tests for Material Risk Change Gating & Numerical Noise Suppression.
"""

import pytest
from services.risk.risk_calculator import (
    RiskCalculator,
    MINIMUM_SCORE_CHANGE,
    MINIMUM_PROBABILITY_CHANGE,
    MINIMUM_AREA_CHANGE_SQKM,
    MINIMUM_STAGE_CHANGE_M
)

def test_sub_threshold_numerical_noise_rejected():
    # Minor jitter: +0.8 score, +0.01 prob, +1.2 sqkm area, +0.02m stage
    is_material = RiskCalculator.is_material_change(
        prev_score=34.0,
        new_score=34.8,
        prev_prob=0.45,
        new_prob=0.46,
        prev_area=210.0,
        new_area=211.2,
        prev_stage=24.10,
        new_stage=24.12
    )
    assert is_material is False

def test_score_material_change_triggered():
    # Delta score = +3.5 (>= 3.0)
    is_material = RiskCalculator.is_material_change(
        prev_score=30.0,
        new_score=33.5,
        prev_prob=0.40,
        new_prob=0.41,
        prev_area=200.0,
        new_area=202.0,
        prev_stage=24.0,
        new_stage=24.05
    )
    assert is_material is True

def test_probability_material_change_triggered():
    # Delta prob = +0.08 (>= 0.04)
    is_material = RiskCalculator.is_material_change(
        prev_score=30.0,
        new_score=31.0,
        prev_prob=0.40,
        new_prob=0.48,
        prev_area=200.0,
        new_area=202.0,
        prev_stage=24.0,
        new_stage=24.05
    )
    assert is_material is True

def test_area_material_change_triggered():
    # Delta area = +15.0 sqkm (>= 5.0)
    is_material = RiskCalculator.is_material_change(
        prev_score=30.0,
        new_score=31.0,
        prev_prob=0.40,
        new_prob=0.41,
        prev_area=200.0,
        new_area=215.0,
        prev_stage=24.0,
        new_stage=24.05
    )
    assert is_material is True

def test_stage_material_change_triggered():
    # Delta stage = +0.25 m (>= 0.15m)
    is_material = RiskCalculator.is_material_change(
        prev_score=30.0,
        new_score=31.0,
        prev_prob=0.40,
        new_prob=0.41,
        prev_area=200.0,
        new_area=202.0,
        prev_stage=24.0,
        new_stage=24.25
    )
    assert is_material is True
