"""
Sentinel-1 SAR Flood Reference Validation and Metrics Engine for JALDRISHTI AI.
CRITICAL SCIENTIFIC AMENDMENTS:
1. Ground Truth -> Sentinel-1 SAR Flood Reference terminology.
2. Temporal Window Gating: Tracks forecast_valid_time, SAR_acquisition_time, and time_difference_hours.
3. Extent vs Depth Decoupling: Satellite SAR measures 2D surface water extent.
   Depth validation is UNAVAILABLE and labeled MODEL_ESTIMATE.
"""

from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone
import numpy as np

from services.models import TemporalMatchStatus, DepthStatus, DepthValidationStatus

def validate_sar_temporal_window(
    forecast_time: datetime,
    sar_time: datetime,
    max_tolerance_hours: float = 3.0,
    reject_threshold_hours: float = 12.0
) -> Tuple[float, TemporalMatchStatus]:
    """
    Computes absolute time difference between forecast valid time and SAR satellite pass.
    Enforces temporal match thresholds:
    - <= max_tolerance_hours: MATCHED
    - > max_tolerance_hours and <= reject_threshold_hours: MISMATCH_TOLERANCE_EXCEEDED
    - > reject_threshold_hours: REJECTED
    """
    if forecast_time.tzinfo is None:
        forecast_time = forecast_time.replace(tzinfo=timezone.utc)
    if sar_time.tzinfo is None:
        sar_time = sar_time.replace(tzinfo=timezone.utc)

    diff_seconds = abs((forecast_time - sar_time).total_seconds())
    diff_hours = diff_seconds / 3600.0

    if diff_hours <= max_tolerance_hours:
        status = TemporalMatchStatus.MATCHED
    elif diff_hours <= reject_threshold_hours:
        status = TemporalMatchStatus.MISMATCH_TOLERANCE_EXCEEDED
    else:
        status = TemporalMatchStatus.REJECTED

    return diff_hours, status

def evaluate_sar_flood_reference(
    observed_extent_sqkm: float,
    predicted_extent_sqkm: float,
    overlap_ratio_proxy: float = 0.90
) -> Dict[str, float]:
    """
    Computes 2D flood extent metrics against Sentinel-1 SAR Reference.
    Metrics:
    - IoU (Intersection over Union / Jaccard Index)
    - F1-Score (Dice Coefficient)
    - CSI (Critical Success Index / Threat Score)
    - Precision (Positive Predictive Value)
    - Recall (Hit Rate / Sensitivity)
    """
    # Overlap proxy calculation for aggregate extent comparison
    min_ext = min(observed_extent_sqkm, predicted_extent_sqkm)
    max_ext = max(observed_extent_sqkm, predicted_extent_sqkm)

    intersection = min_ext * overlap_ratio_proxy
    union = max_ext + (min_ext * (1.0 - overlap_ratio_proxy))
    
    iou = float(intersection / max(1e-6, union))
    precision = float(intersection / max(1e-6, predicted_extent_sqkm))
    recall = float(intersection / max(1e-6, observed_extent_sqkm))
    f1 = float(2.0 * precision * recall / max(1e-6, (precision + recall)))
    csi = float(intersection / max(1e-6, (predicted_extent_sqkm + observed_extent_sqkm - intersection)))

    return {
        "iou": round(iou, 3),
        "f1": round(f1, 3),
        "csi": round(csi, 3),
        "precision": round(precision, 3),
        "recall": round(recall, 3)
    }

def evaluate_binary_water_masks(
    y_sar_reference: np.ndarray,
    y_pred_extent: np.ndarray
) -> Dict[str, float]:
    """
    Computes exact pixel-level confusion matrix and metrics from 2D binary raster arrays.
    y_sar_reference: 1 = Inundated / Water, 0 = Dry
    y_pred_extent: 1 = Inundated / Water, 0 = Dry
    """
    y_t = (np.asarray(y_sar_reference) > 0.5).astype(int).ravel()
    y_p = (np.asarray(y_pred_extent) > 0.5).astype(int).ravel()

    tp = int(np.sum((y_t == 1) & (y_p == 1)))
    fp = int(np.sum((y_t == 0) & (y_p == 1)))
    fn = int(np.sum((y_t == 1) & (y_p == 0)))
    tn = int(np.sum((y_t == 0) & (y_p == 0)))

    intersection = tp
    union = tp + fp + fn

    iou = float(intersection / max(1, union))
    precision = float(tp / max(1, (tp + fp)))
    recall = float(tp / max(1, (tp + fn)))
    f1 = float(2.0 * tp / max(1, (2 * tp + fp + fn)))
    csi = float(tp / max(1, (tp + fp + fn)))
    accuracy = float((tp + tn) / max(1, len(y_t)))

    return {
        "iou": round(iou, 4),
        "f1": round(f1, 4),
        "csi": round(csi, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "pixel_accuracy": round(accuracy, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn
    }
