"""
Spatiotemporal Precipitation Verification Metrics for JALDRISHTI AI.
Computes categorical contingency table metrics (CSI, POD, FAR) across precipitation thresholds,
as well as continuous grid error metrics (RMSE, MAE).
"""

import numpy as np
from typing import Dict, Any, List, Union
import torch

def compute_contingency_table(
    y_pred: np.ndarray,
    y_true: np.ndarray,
    threshold: float
) -> Dict[str, int]:
    """
    Computes Hits (TP), False Alarms (FP), Misses (FN), and Correct Negatives (TN)
    for a given precipitation rate threshold (mm/hr).
    """
    pred_bin = (y_pred >= threshold).astype(int)
    true_bin = (y_true >= threshold).astype(int)

    hits = int(np.sum((pred_bin == 1) & (true_bin == 1)))
    false_alarms = int(np.sum((pred_bin == 1) & (true_bin == 0)))
    misses = int(np.sum((pred_bin == 0) & (true_bin == 1)))
    correct_neg = int(np.sum((pred_bin == 0) & (true_bin == 0)))

    return {
        "hits": hits,
        "false_alarms": false_alarms,
        "misses": misses,
        "correct_negatives": correct_neg
    }

def compute_nowcast_metrics(
    y_pred: Union[np.ndarray, torch.Tensor],
    y_true: Union[np.ndarray, torch.Tensor],
    thresholds: List[float] = [5.0, 15.0, 35.0, 65.0]
) -> Dict[str, Any]:
    """
    Computes comprehensive nowcasting evaluation metrics.

    Parameters:
    - y_pred: Array or Tensor of predictions (mm/hr)
    - y_true: Array or Tensor of ground truth observations (mm/hr)
    - thresholds: List of intensity thresholds in mm/hr

    Returns:
    - Dict with RMSE, MAE, and threshold-specific CSI, POD, FAR.
    """
    if isinstance(y_pred, torch.Tensor):
        y_p = y_pred.detach().cpu().numpy()
    else:
        y_p = np.asarray(y_pred)

    if isinstance(y_true, torch.Tensor):
        y_t = y_true.detach().cpu().numpy()
    else:
        y_t = np.asarray(y_true)

    # Continuous error metrics
    diff = y_p - y_t
    mae = float(np.mean(np.abs(diff)))
    rmse = float(np.sqrt(np.mean(diff ** 2)))

    metrics = {
        "mae_mm": round(mae, 3),
        "rmse_mm": round(rmse, 3),
        "thresholds": {}
    }

    for thresh in thresholds:
        ct = compute_contingency_table(y_p, y_t, thresh)
        h = ct["hits"]
        fa = ct["false_alarms"]
        m = ct["misses"]

        # CSI = Hits / (Hits + FalseAlarms + Misses)
        csi_denom = h + fa + m
        csi = float(h / csi_denom) if csi_denom > 0 else (1.0 if (fa + m == 0) else 0.0)

        # POD = Hits / (Hits + Misses)
        pod_denom = h + m
        pod = float(h / pod_denom) if pod_denom > 0 else 0.0

        # FAR = FalseAlarms / (Hits + FalseAlarms)
        far_denom = h + fa
        far = float(fa / far_denom) if far_denom > 0 else 0.0

        thresh_key = f"{int(thresh)}mm"
        metrics["thresholds"][thresh_key] = {
            "threshold_mm_hr": thresh,
            "csi": round(csi, 4),
            "pod": round(pod, 4),
            "far": round(far, 4),
            "hits": h,
            "false_alarms": fa,
            "misses": m
        }

    return metrics
