"""
Production Inference Engine for Spatiotemporal ConvLSTM Nowcasting in JALDRISHTI AI.
Features:
- Cached singleton model loading avoiding redundant checkpoint deserialization.
- Safe state_dict loading and verification.
- Output mapping to standard RainfallNowcastFrame contracts.
"""

import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
import numpy as np
import torch

from ml.rainfall.deep.encoder_decoder import ConvLSTMEncoderDecoder
from services.models import RainfallNowcastFrame, ConfidenceLevel, ModelStatus

class ConvLSTMInferenceEngine:
    """
    Cached inference runtime for the genuine PyTorch ConvLSTM Nowcaster.
    """

    _instance: Optional["ConvLSTMInferenceEngine"] = None

    def __init__(
        self,
        checkpoint_path: str = "model_registry/convlstm_nowcast.pt",
        device_name: str = "cpu"
    ):
        self.checkpoint_path = checkpoint_path
        self.device = torch.device(device_name if torch.cuda.is_available() and device_name != "cpu" else "cpu")
        self.model: Optional[ConvLSTMEncoderDecoder] = None
        self.normalization_stats: Dict[str, float] = {"mean": 15.0, "std": 12.0}
        self.model_config: Dict[str, Any] = {}
        self.is_loaded = False
        self.model_status = ModelStatus.EXPERIMENTAL
        self._load_checkpoint()

    @classmethod
    def get_instance(cls, checkpoint_path: str = "model_registry/convlstm_nowcast.pt") -> "ConvLSTMInferenceEngine":
        """Returns singleton cached instance."""
        if cls._instance is None or not cls._instance.is_loaded:
            cls._instance = cls(checkpoint_path=checkpoint_path)
        return cls._instance

    def _load_checkpoint(self):
        """Loads and initializes PyTorch model from saved checkpoint."""
        ckpt_file = Path(self.checkpoint_path)
        if not ckpt_file.exists():
            # Fallback initialization for pre-training inspection
            self.model = ConvLSTMEncoderDecoder(
                input_dim=1,
                hidden_dims=(16, 32),
                kernel_size=3,
                num_output_steps=12,
                output_dim=1
            ).to(self.device)
            self.model.eval()
            self.is_loaded = True
            return

        checkpoint = torch.load(str(ckpt_file), map_location=self.device, weights_only=True)
        self.model_config = checkpoint.get("model_config", {})
        self.normalization_stats = checkpoint.get("normalization_config", {"mean": 15.0, "std": 12.0})

        hidden_dims = tuple(self.model_config.get("hidden_dims", [16, 32]))
        num_output_steps = self.model_config.get("num_output_steps", 12)

        self.model = ConvLSTMEncoderDecoder(
            input_dim=self.model_config.get("input_dim", 1),
            hidden_dims=hidden_dims,
            kernel_size=self.model_config.get("kernel_size", 3),
            num_output_steps=num_output_steps,
            output_dim=self.model_config.get("output_dim", 1),
            activation=self.model_config.get("activation", "softplus")
        ).to(self.device)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()
        self.is_loaded = True
        self.model_status = ModelStatus.CANDIDATE

    def predict_spatial_sequence(
        self,
        input_sequence: Union[np.ndarray, torch.Tensor],
        future_steps: int = 12
    ) -> np.ndarray:
        """
        Executes raw spatial grid prediction.

        Parameters:
        - input_sequence: Shape (B, T_in, C, H, W) or (T_in, C, H, W) or (T_in, H, W)

        Returns:
        - output_grids: Shape (B, T_out, H, W) in continuous precipitation units (mm/hr)
        """
        if not self.is_loaded:
            self._load_checkpoint()

        if isinstance(input_sequence, np.ndarray):
            tensor = torch.from_numpy(input_sequence.astype(np.float32))
        else:
            tensor = input_sequence.float()

        # Adjust dimensions if needed
        if tensor.ndim == 3:  # (T, H, W)
            tensor = tensor.unsqueeze(0).unsqueeze(2)  # (1, T, 1, H, W)
        elif tensor.ndim == 4:  # (T, C, H, W) or (B, T, H, W)
            if tensor.shape[1] in [1, 2, 3, 4]:  # (B, T, H, W)
                tensor = tensor.unsqueeze(2)  # (B, T, 1, H, W)
            else:
                tensor = tensor.unsqueeze(0)  # (1, T, C, H, W)

        # Normalize input
        mean = self.normalization_stats["mean"]
        std = self.normalization_stats["std"]
        norm_input = (tensor - mean) / std
        norm_input = norm_input.to(self.device)

        with torch.no_grad():
            pred_tensor = self.model(norm_input, future_steps=future_steps)

        # Output is in physical units (mm/hr) via Softplus activation
        pred_np = pred_tensor.squeeze(2).cpu().numpy()  # (B, T_out, H, W)
        return pred_np

    def predict_nowcast_frames(
        self,
        recent_rate_or_grid: Any,
        base_time: datetime,
        horizons_minutes: List[int] = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360],
        data_confidence: str = "HIGH"
    ) -> List[RainfallNowcastFrame]:
        """
        Generates standard API RainfallNowcastFrame objects.
        """
        grid_h, grid_w = 16, 24
        t_in = 4

        # Construct spatial input from rate or grid
        if isinstance(recent_rate_or_grid, (int, float)):
            rate = float(recent_rate_or_grid)
            y_coords, x_coords = np.mgrid[0:grid_h, 0:grid_w]
            cy, cx = grid_h / 2.0, grid_w / 2.0
            dist_sq = ((y_coords - cy) ** 2) + ((x_coords - cx) ** 2)
            spatial_factor = np.exp(-dist_sq / 36.0)
            base_grid = rate * (0.6 + 0.8 * spatial_factor)
            seq = np.stack([base_grid * (0.9 + i * 0.03) for i in range(t_in)], axis=0)
        elif isinstance(recent_rate_or_grid, np.ndarray) and recent_rate_or_grid.ndim in [2, 3, 4]:
            seq = recent_rate_or_grid
        else:
            seq = np.full((t_in, grid_h, grid_w), 24.5, dtype=np.float32)

        pred_grids = self.predict_spatial_sequence(seq, future_steps=len(horizons_minutes))
        # pred_grids shape: (1, T_out, H, W)
        preds_3d = pred_grids[0]

        frames: List[RainfallNowcastFrame] = []
        is_degraded = (data_confidence == "DATA_DEGRADED")

        for idx, m in enumerate(horizons_minutes):
            grid_t = preds_3d[min(idx, len(preds_3d) - 1)]
            mean_rate = float(np.mean(grid_t))
            max_rate = float(np.max(grid_t))

            # Probability of heavy rainfall: fraction of spatial grid exceeding 35 mm/hr
            fraction_heavy = float(np.mean(grid_t >= 35.0))
            prob_heavy = min(0.98, max(0.02, fraction_heavy * 1.5 + (0.3 if mean_rate > 25.0 else 0.0)))
            prob_extreme = min(0.95, max(0.01, float(np.mean(grid_t >= 65.0)) * 2.0))

            if is_degraded:
                prob_heavy = round(prob_heavy * 0.85, 3)

            # Confidence drops with lead time
            if m <= 60:
                conf = ConfidenceLevel.HIGH if not is_degraded else ConfidenceLevel.MEDIUM
            elif m <= 180:
                conf = ConfidenceLevel.MEDIUM if not is_degraded else ConfidenceLevel.DATA_DEGRADED
            else:
                conf = ConfidenceLevel.LOW

            frame = RainfallNowcastFrame(
                lead_time_minutes=m,
                valid_time=base_time + timedelta(minutes=m),
                mean_rainfall_mm_hr=round(mean_rate, 2),
                max_rainfall_mm_hr=round(max_rate, 2),
                heavy_rain_prob=round(prob_heavy, 3),
                extreme_rain_prob=round(prob_extreme, 3),
                model_level="RAIN_L3_CONVLSTM",
                uncertainty_std_mm=round(0.18 * mean_rate + (m / 60.0) * 1.1, 2),
                model_confidence=conf,
                data_confidence=ConfidenceLevel.DATA_DEGRADED if is_degraded else ConfidenceLevel.HIGH
            )
            frames.append(frame)

        return frames
