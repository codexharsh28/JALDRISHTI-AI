"""
PyTorch Training Pipeline for Spatiotemporal ConvLSTM Nowcasting in JALDRISHTI AI.
Executes reproducible training, validation, early stopping, gradient clipping,
and state-dict checkpoint serialization.
"""

import os
import sys
import json
import time
import uuid
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ml.rainfall.deep.encoder_decoder import ConvLSTMEncoderDecoder
from ml.rainfall.deep.losses import CompoundIntensityWeightedLoss
from ml.rainfall.deep.metrics import compute_nowcast_metrics
from ml.rainfall.deep.dataset import create_partitioned_datasets

def set_seed(seed: int = 42):
    """Sets random seeds across Python, NumPy, and PyTorch for deterministic execution."""
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def compute_file_sha256(file_path: str) -> str:
    """Computes SHA256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def train_convlstm(
    epochs: int = 10,
    batch_size: int = 8,
    lr: float = 0.001,
    seed: int = 42,
    device_name: str = "auto",
    hidden_dims: Tuple[int, ...] = (16, 32),
    kernel_size: int = 3,
    t_in: int = 4,
    t_out: int = 12,
    grid_height: int = 16,
    grid_width: int = 24,
    checkpoint_dir: str = "model_registry",
    artifacts_dir: str = "artifacts/training/rainfall/convlstm",
    manifest_path: str = "data/manifests/rainfall_split_manifest.yaml"
) -> Dict[str, Any]:
    """
    Executes full ConvLSTM training pipeline.
    """
    set_seed(seed)

    # Device selection
    if device_name == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(device_name)

    print(f"1. Initializing ConvLSTM Training Pipeline on device: {device} (seed={seed})", flush=True)

    # Build dataset partitions with strict event boundary isolation
    train_ds, val_ds, test_ds = create_partitioned_datasets(
        manifest_path=manifest_path,
        t_in=t_in,
        t_out=t_out,
        grid_height=grid_height,
        grid_width=grid_width
    )

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    print(f"2. Datasets loaded: Train={len(train_ds)}, Val={len(val_ds)}, Test={len(test_ds)} samples.")

    # Initialize model
    model = ConvLSTMEncoderDecoder(
        input_dim=1,
        hidden_dims=hidden_dims,
        kernel_size=kernel_size,
        num_output_steps=t_out,
        output_dim=1,
        activation="softplus"
    ).to(device)

    param_count = model.count_parameters()
    print(f"3. Model instantiated: {param_count:,} trainable parameters.")

    # Criterion and Optimizer
    criterion = CompoundIntensityWeightedLoss(
        base_loss="huber",
        huber_delta=1.0,
        moderate_threshold=15.0,
        heavy_threshold=35.0,
        extreme_threshold=65.0
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    # Training state
    run_id = f"RUN-CONVLSTM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}-{str(uuid.uuid4())[:6]}"
    run_artifact_dir = Path(artifacts_dir) / run_id
    run_artifact_dir.mkdir(parents=True, exist_ok=True)
    Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)

    best_val_loss = float("inf")
    best_epoch = 0
    history = []
    start_time = time.time()

    print(f"4. Beginning training for {epochs} epochs...")

    for epoch in range(1, epochs + 1):
        epoch_start = time.time()
        model.train()
        train_loss_accum = 0.0

        for x_b, y_b, _ in train_loader:
            x_b = x_b.to(device)
            y_b = y_b.to(device)

            optimizer.zero_grad()
            y_pred = model(x_b)
            loss = criterion(y_pred, y_b)
            loss.backward()

            # Gradient clipping to prevent exploding gradients
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            train_loss_accum += loss.item() * len(x_b)

        train_loss = train_loss_accum / max(1, len(train_ds))

        # Validation pass
        model.eval()
        val_loss_accum = 0.0
        val_preds = []
        val_trues = []

        with torch.no_grad():
            for x_b, y_b, _ in val_loader:
                x_b = x_b.to(device)
                y_b = y_b.to(device)
                y_pred = model(x_b)
                loss = criterion(y_pred, y_b)
                val_loss_accum += loss.item() * len(x_b)

                val_preds.append(y_pred.cpu().numpy())
                val_trues.append(y_b.cpu().numpy())

        val_loss = val_loss_accum / max(1, len(val_ds))
        val_metrics = compute_nowcast_metrics(
            np.concatenate(val_preds, axis=0),
            np.concatenate(val_trues, axis=0)
        )

        epoch_duration = time.time() - epoch_start
        epoch_record = {
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "val_loss": round(val_loss, 4),
            "val_rmse": val_metrics["rmse_mm"],
            "val_csi_35mm": val_metrics["thresholds"].get("35mm", {}).get("csi", 0.0),
            "duration_seconds": round(epoch_duration, 2)
        }
        history.append(epoch_record)

        print(f"   Epoch {epoch:02d}/{epochs:02d} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, Val RMSE: {val_metrics['rmse_mm']:.2f} mm/hr ({epoch_duration:.1f}s)")

        # Save best model checkpoint
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch

            checkpoint_payload = {
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "epoch": epoch,
                "best_validation_loss": float(best_val_loss),
                "model_config": model.get_model_summary(),
                "normalization_config": train_ds.normalization_stats,
                "dataset_shapes": {
                    "t_in": t_in,
                    "t_out": t_out,
                    "grid_height": grid_height,
                    "grid_width": grid_width
                },
                "split_manifest": manifest_path,
                "random_seed": seed,
                "trained_at": datetime.now(timezone.utc).isoformat()
            }

            # Save in artifacts directory
            best_pt_path = run_artifact_dir / "checkpoint.pt"
            torch.save(checkpoint_payload, best_pt_path)

            # Also save canonical registry checkpoint
            reg_pt_path = Path(checkpoint_dir) / "convlstm_nowcast.pt"
            torch.save(checkpoint_payload, reg_pt_path)

    total_time = time.time() - start_time
    print(f"5. Training complete in {total_time:.1f}s. Best Epoch: {best_epoch} with Val Loss: {best_val_loss:.4f}")

    # Compute checkpoint hash
    ckpt_hash = compute_file_sha256(str(run_artifact_dir / "checkpoint.pt"))
    (run_artifact_dir / "checkpoint.sha256").write_text(ckpt_hash, encoding="utf-8")

    # Save training artifacts
    metadata = {
        "run_id": run_id,
        "model_id": "RAIN_L3_CONVLSTM",
        "model_name": "Deep Spatiotemporal ConvLSTM Precipitation Nowcaster",
        "framework": "PyTorch",
        "pytorch_version": torch.__version__,
        "device": str(device),
        "parameter_count": param_count,
        "trained_epochs": epochs,
        "best_epoch": best_epoch,
        "best_validation_loss": round(best_val_loss, 4),
        "total_training_duration_seconds": round(total_time, 2),
        "checkpoint_sha256": ckpt_hash,
        "status": "CANDIDATE" if best_val_loss < float("inf") else "EXPERIMENTAL"
    }

    with open(run_artifact_dir / "training_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    with open(run_artifact_dir / "normalization.json", "w", encoding="utf-8") as f:
        json.dump(train_ds.normalization_stats, f, indent=2)

    with open(run_artifact_dir / "model_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    with open(Path(checkpoint_dir) / "convlstm_checkpoint_meta.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return {
        "run_id": run_id,
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "parameter_count": param_count,
        "checkpoint_path": str(run_artifact_dir / "checkpoint.pt"),
        "checkpoint_sha256": ckpt_hash,
        "metadata": metadata
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train JALDRISHTI AI PyTorch ConvLSTM Nowcaster")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--device", type=str, default="auto", help="Device (cpu/cuda/auto)")
    parser.add_argument("--checkpoint-dir", type=str, default="model_registry", help="Checkpoint output directory")
    args = parser.parse_args()

    train_convlstm(
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        seed=args.seed,
        device_name=args.device,
        checkpoint_dir=args.checkpoint_dir
    )
