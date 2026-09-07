"""
JALDRISHTI AI — Hydrometeorological Anomaly Detection Package.
"""

from services.anomaly.anomaly_types import (
    AnomalyState,
    AnomalyClassification,
    AnomalyDomain,
    AnomalyRecord
)
from services.anomaly.baselines import (
    PHYSICAL_BOUNDS,
    MAX_JUMP_RATES_1H,
    StationBaselineTracker,
    baseline_tracker
)
from services.anomaly.spatial_consistency import (
    SpatialConsistencyEngine,
    spatial_consistency_engine
)
from services.anomaly.detector import (
    HydrometAnomalyDetector,
    hydromet_anomaly_detector
)
from services.anomaly.store import (
    AnomalyStore,
    anomaly_store
)
from services.anomaly.service import (
    AnomalyService,
    anomaly_service
)

__all__ = [
    "AnomalyState",
    "AnomalyClassification",
    "AnomalyDomain",
    "AnomalyRecord",
    "PHYSICAL_BOUNDS",
    "MAX_JUMP_RATES_1H",
    "StationBaselineTracker",
    "baseline_tracker",
    "SpatialConsistencyEngine",
    "spatial_consistency_engine",
    "HydrometAnomalyDetector",
    "hydromet_anomaly_detector",
    "AnomalyStore",
    "anomaly_store",
    "AnomalyService",
    "anomaly_service"
]
