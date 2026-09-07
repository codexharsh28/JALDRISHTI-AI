"""
Anti-Leakage Gating & Informational Availability Integrity Tests for Hydrology.
Injects future stage, discharge, rainfall, and rating curve records to verify strict rejection.
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import List, Dict

def filter_observations_by_cutoff(
    records: List[Dict],
    cutoff_time: datetime
) -> List[Dict]:
    """Strict gating: Rejects any record with availability_time > cutoff_time."""
    valid = []
    for r in records:
        avail_str = r.get("availability_time") or r.get("observed_at")
        avail_dt = datetime.fromisoformat(avail_str.replace("Z", "+00:00"))
        if avail_dt <= cutoff_time:
            valid.append(r)
    return valid

def test_injected_future_stage_and_discharge_rejected():
    cutoff = datetime(2022, 8, 14, 12, 0, tzinfo=timezone.utc)

    records = [
        {"station_id": "CWC_MUNDALI", "observed_at": "2022-08-14T06:00:00Z", "availability_time": "2022-08-14T06:15:00Z", "stage_m": 25.4},
        {"station_id": "CWC_MUNDALI", "observed_at": "2022-08-14T11:00:00Z", "availability_time": "2022-08-14T11:20:00Z", "stage_m": 25.9},
        # Injected future observation
        {"station_id": "CWC_MUNDALI", "observed_at": "2022-08-14T18:00:00Z", "availability_time": "2022-08-14T18:15:00Z", "stage_m": 26.8}
    ]

    filtered = filter_observations_by_cutoff(records, cutoff)
    assert len(filtered) == 2
    assert all(r["stage_m"] < 26.5 for r in filtered)

def test_future_rating_curve_rejected_in_historical_hindcast():
    cutoff = datetime(2021, 9, 12, 0, 0, tzinfo=timezone.utc)
    
    rating_curves = [
        {"curve_id": "RC-2020", "valid_from": "2020-01-01T00:00:00Z", "valid_to": "2021-12-31T23:59:59Z", "availability_time": "2020-01-05T00:00:00Z"},
        # Post-event recalibrated curve
        {"curve_id": "RC-2024", "valid_from": "2024-01-01T00:00:00Z", "valid_to": "2024-12-31T23:59:59Z", "availability_time": "2024-01-10T00:00:00Z"}
    ]

    valid_curves = filter_observations_by_cutoff(rating_curves, cutoff)
    assert len(valid_curves) == 1
    assert valid_curves[0]["curve_id"] == "RC-2020"
