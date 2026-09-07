"""
ConvLSTM Encoder-Decoder Architecture for JALDRISHTI AI.
Implements a multi-horizon spatiotemporal sequence-to-sequence nowcaster:
- Encoder: Ingests past rainfall sequence (e.g. T_in = 4 steps of 30 min = 2h)
- Decoder: Autoregressive or latent-state unrolling for T_out = 12 steps (+30m to +6h)
- Output Head: Convolutional projector with Softplus non-negative rainfall activation.
"""

import torch
import torch.nn as nn
from typing import Tuple, Dict, Any, Optional

from ml.rainfall.deep.convlstm import ConvLSTM
from ml.rainfall.deep.convlstm_cell import ConvLSTMCell

class ConvLSTMEncoderDecoder(nn.Module):
    """
    Spatiotemporal ConvLSTM Encoder-Decoder Nowcaster.
    Input: (B, T_in, C_in, H, W)
    Output: (B, T_out, C_out, H, W) where C_out is typically 1 (precipitation rate in mm/hr).
    """

    def __init__(
        self,
        input_dim: int = 1,
        hidden_dims: Tuple[int, ...] = (32, 64),
        kernel_size: int = 3,
        num_output_steps: int = 12,
        output_dim: int = 1,
        activation: str = "softplus"
    ):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dims = list(hidden_dims)
        self.kernel_size = kernel_size
        self.num_output_steps = num_output_steps
        self.output_dim = output_dim
        self.activation_type = activation

        # Encoder: Stacked ConvLSTM processing past sequence
        self.encoder = ConvLSTM(
            input_dim=self.input_dim,
            hidden_dims=self.hidden_dims,
            kernel_sizes=self.kernel_size,
            num_layers=len(self.hidden_dims),
            bias=True,
            return_all_layers=True
        )

        # Decoder ConvLSTM cell (top-level or multi-level)
        self.decoder_cell = ConvLSTMCell(
            input_dim=self.output_dim,
            hidden_dim=self.hidden_dims[-1],
            kernel_size=self.kernel_size,
            bias=True
        )

        # Output projection head: Projects hidden features (C_hidden) to rainfall rate (C_out)
        self.output_conv = nn.Sequential(
            nn.Conv2d(self.hidden_dims[-1], self.hidden_dims[0], kernel_size=3, padding=1),
            nn.LeakyReLU(0.1),
            nn.Conv2d(self.hidden_dims[0], self.output_dim, kernel_size=1)
        )

        # Non-negative activation function
        if activation == "softplus":
            self.non_negative_act = nn.Softplus(beta=1.0)
        elif activation == "relu":
            self.non_negative_act = nn.ReLU()
        else:
            self.non_negative_act = nn.Identity()

    def forward(
        self,
        x: torch.Tensor,
        future_steps: Optional[int] = None
    ) -> torch.Tensor:
        """
        Forward pass for the full sequence nowcasting model.

        Parameters:
        - x: Past sequence tensor of shape (B, T_in, C_in, H, W)
        - future_steps: Number of future steps to generate (defaults to self.num_output_steps)

        Returns:
        - output_sequence: Future rainfall grid predictions of shape (B, T_out, C_out, H, W)
        """
        steps_to_predict = future_steps or self.num_output_steps
        batch_size, _, _, height, width = x.shape

        # 1. Encode past sequence into spatiotemporal latent states
        _, encoder_states = self.encoder(x)
        # Use top-level encoder final state to initialize decoder
        dec_h, dec_c = encoder_states[-1]

        # Initial decoder input: Last observed frame (or zero tensor)
        # Take the rainfall channel (index 0) of the last input step
        current_input = x[:, -1, :self.output_dim, :, :]

        outputs = []
        for t in range(steps_to_predict):
            # Recurrent decode step
            dec_h, dec_c = self.decoder_cell(current_input, (dec_h, dec_c))

            # Project hidden state to rainfall prediction
            raw_pred = self.output_conv(dec_h)
            pos_pred = self.non_negative_act(raw_pred)

            outputs.append(pos_pred)
            # Autoregressive feedback: feed current prediction to next step
            current_input = pos_pred

        # Stack outputs along time dimension: (B, T_out, C_out, H, W)
        output_sequence = torch.stack(outputs, dim=1)
        return output_sequence

    def count_parameters(self) -> int:
        """Returns the total number of trainable parameters in the model."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def get_model_summary(self) -> Dict[str, Any]:
        """Returns structured metadata describing the model architecture."""
        return {
            "model_type": "ConvLSTM_EncoderDecoder",
            "framework": "PyTorch",
            "input_dim": self.input_dim,
            "hidden_dims": self.hidden_dims,
            "kernel_size": self.kernel_size,
            "num_output_steps": self.num_output_steps,
            "output_dim": self.output_dim,
            "activation": self.activation_type,
            "parameter_count": self.count_parameters()
        }
