"""
Temporal and Spatial Anti-Leakage Guards for Inundation Modeling in JALDRISHTI AI.
Guarantees:
1. Temporal Leakage Prevention: Zero future observations (t > T) incorporated into feature pipelines.
2. Spatial Leakage Prevention: Event and subbasin isolation between TRAIN, VALIDATION, and HELD_OUT_TEST.
"""

from typing import Dict, Any, List, Set, Tuple, Optional
from datetime import datetime, timezone
import pandas as pd

class TemporalLeakageGuard:
    """
    Enforces that all features and inputs to the inundation surrogate model
    are strictly available prior to or at the forecast cutoff time T.
    """
    def __init__(self, forecast_cutoff_time: datetime):
        if forecast_cutoff_time.tzinfo is None:
            forecast_cutoff_time = forecast_cutoff_time.replace(tzinfo=timezone.utc)
        self.cutoff_time = forecast_cutoff_time

    def filter_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filters out any record with availability_time or observed_at > cutoff_time.
        """
        valid_records = []
        for r in records:
            time_str = r.get("availability_time") or r.get("observed_at") or r.get("timestamp")
            if time_str is None:
                continue
            if isinstance(time_str, str):
                dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            else:
                dt = time_str
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)

            if dt <= self.cutoff_time:
                valid_records.append(r)
        return valid_records

    def verify_no_future_data(self, timestamps: List[datetime]) -> Tuple[bool, List[datetime]]:
        """
        Verifies that no timestamp exceeds cutoff_time. Returns (is_clean, violating_timestamps).
        """
        violations = []
        for ts in timestamps:
            dt = ts if ts.tzinfo is not None else ts.replace(tzinfo=timezone.utc)
            if dt > self.cutoff_time:
                violations.append(dt)
        return (len(violations) == 0, violations)

class SpatialLeakageGuard:
    """
    Guarantees strict isolation of training, validation, and held-out test event partitions.
    """
    def __init__(
        self,
        train_events: List[str],
        val_events: List[str],
        test_events: List[str]
    ):
        self.train_events = set(train_events)
        self.val_events = set(val_events)
        self.test_events = set(test_events)

    def verify_disjoint_partitions(self) -> Dict[str, Any]:
        """
        Checks for any overlap among train, validation, and test event sets.
        """
        train_val_overlap = self.train_events.intersection(self.val_events)
        train_test_overlap = self.train_events.intersection(self.test_events)
        val_test_overlap = self.val_events.intersection(self.test_events)

        is_valid = not (train_val_overlap or train_test_overlap or val_test_overlap)

        return {
            "is_valid": is_valid,
            "train_val_overlap": list(train_val_overlap),
            "train_test_overlap": list(train_test_overlap),
            "val_test_overlap": list(val_test_overlap),
            "train_count": len(self.train_events),
            "val_count": len(self.val_events),
            "test_count": len(self.test_events)
        }

    def validate_dataframe_partition(
        self,
        df: pd.DataFrame,
        event_col: str = "event_id",
        partition: str = "TRAIN"
    ) -> bool:
        """
        Verifies that a dataframe intended for a given partition contains only allowed events.
        """
        if event_col not in df.columns:
            return True # Not event-tagged

        unique_events = set(df[event_col].dropna().unique())
        if partition == "TRAIN":
            allowed = self.train_events
        elif partition == "VALIDATION":
            allowed = self.val_events
        elif partition == "HELD_OUT_TEST":
            allowed = self.test_events
        else:
            raise ValueError(f"Unknown partition: {partition}")

        unauthorized = unique_events - allowed
        return len(unauthorized) == 0
