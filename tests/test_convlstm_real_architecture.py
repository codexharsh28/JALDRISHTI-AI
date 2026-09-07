"""
Automated Architecture Sanity Tests for PyTorch ConvLSTM Nowcaster.
Proves:
1. Genuine torch.nn modules exist (Conv2d, ModuleList, Sequential).
2. ConvLSTM recurrence over spatial hidden state (h_t, c_t) works.
3. Trainable parameter count > 0.
4. Forward and backward pass execute with non-zero gradients.
5. Non-negative precipitation output constraint is satisfied.
"""

import pytest
import torch
import torch.nn as nn
from ml.rainfall.deep.convlstm_cell import ConvLSTMCell
from ml.rainfall.deep.convlstm import ConvLSTM
from ml.rainfall.deep.encoder_decoder import ConvLSTMEncoderDecoder
from ml.rainfall.deep.losses import CompoundIntensityWeightedLoss

def test_convlstm_cell_convolutions_and_spatial_states():
    cell = ConvLSTMCell(input_dim=1, hidden_dim=16, kernel_size=3)
    assert isinstance(cell.conv, nn.Conv2d)
    
    # Input tensor (Batch=2, Channel=1, Height=16, Width=24)
    x = torch.randn(2, 1, 16, 24)
    h_next, c_next = cell(x)

    assert h_next.shape == (2, 16, 16, 24)
    assert c_next.shape == (2, 16, 16, 24)
    assert not torch.isnan(h_next).any()
    assert not torch.isnan(c_next).any()

def test_multi_layer_convlstm_temporal_unrolling():
    convlstm = ConvLSTM(input_dim=1, hidden_dims=[16, 32], kernel_sizes=3, num_layers=2)
    assert len(convlstm.cell_list) == 2

    # Sequence tensor (Batch=2, Timesteps=4, Channel=1, Height=16, Width=24)
    x_seq = torch.randn(2, 4, 1, 16, 24)
    out_seq, last_states = convlstm(x_seq)

    assert out_seq.shape == (2, 4, 32, 16, 24)
    assert len(last_states) == 2
    assert last_states[0][0].shape == (2, 16, 16, 24)
    assert last_states[1][0].shape == (2, 32, 16, 24)

def test_convlstm_encoder_decoder_forward_backward():
    model = ConvLSTMEncoderDecoder(
        input_dim=1,
        hidden_dims=(16, 32),
        kernel_size=3,
        num_output_steps=12,
        output_dim=1,
        activation="softplus"
    )

    param_count = model.count_parameters()
    assert param_count > 50000, f"Expected > 50k parameters, got {param_count}"

    # Forward pass
    x_input = torch.abs(torch.randn(2, 4, 1, 16, 24)) * 10.0
    y_pred = model(x_input)

    assert y_pred.shape == (2, 12, 1, 16, 24)
    # Output must be non-negative
    assert (y_pred >= 0.0).all(), "Rainfall prediction output contains negative values"

    # Backward pass
    y_target = torch.abs(torch.randn(2, 12, 1, 16, 24)) * 20.0
    criterion = CompoundIntensityWeightedLoss()
    loss = criterion(y_pred, y_target)
    loss.backward()

    # Verify gradients computed
    has_grad = False
    for p in model.parameters():
        if p.grad is not None and p.grad.norm().item() > 0:
            has_grad = True
            break
    assert has_grad, "No parameter received non-zero gradients during backward pass"
