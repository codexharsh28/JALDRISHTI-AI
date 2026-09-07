"""
Automated Checkpoint Serialization & Deserialization Tests for ConvLSTM.
Verifies:
1. State dict loading integrity.
2. Metadata preservation (normalization config, optimizer state, model architecture).
3. Inference engine reproduction after checkpoint reload.
"""

import pytest
import torch
from pathlib import Path
from ml.rainfall.deep.inference import ConvLSTMInferenceEngine
from ml.rainfall.deep.encoder_decoder import ConvLSTMEncoderDecoder

def test_checkpoint_state_dict_and_metadata():
    ckpt_path = "model_registry/convlstm_nowcast.pt"
    assert Path(ckpt_path).exists(), f"Checkpoint {ckpt_path} does not exist"

    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    
    assert "model_state_dict" in ckpt
    assert "optimizer_state_dict" in ckpt
    assert "normalization_config" in ckpt
    assert "model_config" in ckpt
    assert "epoch" in ckpt
    assert "best_validation_loss" in ckpt

    # Verify model instantiates and loads weights cleanly
    config = ckpt["model_config"]
    model = ConvLSTMEncoderDecoder(
        input_dim=config["input_dim"],
        hidden_dims=tuple(config["hidden_dims"]),
        kernel_size=config["kernel_size"],
        num_output_steps=config["num_output_steps"],
        output_dim=config["output_dim"]
    )
    model.load_state_dict(ckpt["model_state_dict"])
    assert model.count_parameters() == config["parameter_count"]

def test_inference_engine_prediction_pipeline():
    engine = ConvLSTMInferenceEngine.get_instance("model_registry/convlstm_nowcast.pt")
    assert engine.is_loaded

    # Single rate input
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    frames = engine.predict_nowcast_frames(recent_rate_or_grid=25.0, base_time=now)

    assert len(frames) == 12
    for f in frames:
        assert f.mean_rainfall_mm_hr >= 0.0
        assert f.max_rainfall_mm_hr >= f.mean_rainfall_mm_hr
        assert 0.0 <= f.heavy_rain_prob <= 1.0
        assert f.model_level == "RAIN_L3_CONVLSTM"
