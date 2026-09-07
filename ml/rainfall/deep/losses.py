"""
Intensity-Weighted Compound Loss Functions for JALDRISHTI AI.
Prevents the common failure mode of deep nowcasting models predicting zero everywhere
due to extreme class imbalance in spatial precipitation fields.
"""

import torch
import torch.nn as nn
from typing import Dict, Any, Optional

class CompoundIntensityWeightedLoss(nn.Module):
    """
    Weighted Huber / MAE loss penalizing errors on heavy and extreme rainfall
    significantly more than dry/light-rain background pixels.
    """

    def __init__(
        self,
        base_loss: str = "huber",
        huber_delta: float = 1.0,
        moderate_threshold: float = 15.0,
        heavy_threshold: float = 35.0,
        extreme_threshold: float = 65.0,
        moderate_weight: float = 2.0,
        heavy_weight: float = 5.0,
        extreme_weight: float = 10.0
    ):
        super().__init__()
        self.base_loss = base_loss
        self.huber_delta = huber_delta
        self.mod_thresh = moderate_threshold
        self.heavy_thresh = heavy_threshold
        self.ext_thresh = extreme_threshold
        self.mod_w = moderate_weight
        self.heavy_w = heavy_weight
        self.ext_w = extreme_weight

    def forward(self, y_pred: torch.Tensor, y_true: torch.Tensor) -> torch.Tensor:
        """
        Computes weighted loss.
        Both y_pred and y_true are of shape (B, T, C, H, W).
        """
        diff = torch.abs(y_pred - y_true)

        # Base error computation
        if self.base_loss == "huber":
            # Smooth L1 / Huber formulation
            huber_mask = diff < self.huber_delta
            error = torch.where(huber_mask, 0.5 * (diff ** 2), self.huber_delta * (diff - 0.5 * self.huber_delta))
        elif self.base_loss == "mse":
            error = diff ** 2
        else:  # mae
            error = diff

        # Dynamic intensity weight map based on true rainfall intensity
        weights = torch.ones_like(y_true)
        weights = torch.where(y_true >= self.mod_thresh, weights + self.mod_w, weights)
        weights = torch.where(y_true >= self.heavy_thresh, weights + self.heavy_w, weights)
        weights = torch.where(y_true >= self.ext_thresh, weights + self.ext_w, weights)

        weighted_error = error * weights
        return torch.mean(weighted_error)

    def get_config(self) -> Dict[str, Any]:
        return {
            "loss_name": "CompoundIntensityWeightedLoss",
            "base_loss": self.base_loss,
            "huber_delta": self.huber_delta,
            "thresholds": {
                "moderate_mm_hr": self.mod_thresh,
                "heavy_mm_hr": self.heavy_thresh,
                "extreme_mm_hr": self.ext_thresh
            },
            "weights": {
                "moderate": self.mod_w,
                "heavy": self.heavy_w,
                "extreme": self.ext_w
            }
        }
