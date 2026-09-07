"""
Convolutional LSTM Cell Module for JALDRISHTI AI.
Implements the genuine spatiotemporal recurrent ConvLSTM equations (Shi et al., NeurIPS 2015):
- 2D Convolutions over concatenated spatial input and recurrent hidden states.
- Explicit spatial hidden state h_t and spatial cell state c_t.
- Fully differentiable PyTorch nn.Module with learnable convolution kernels.
"""

import torch
import torch.nn as nn
from typing import Tuple, Optional

class ConvLSTMCell(nn.Module):
    """
    2D Convolutional LSTM Cell.
    Processes spatial tensor inputs x_t of shape (B, C_in, H, W) and recurrent
    spatial states (h_{t-1}, c_{t-1}) of shape (B, C_hidden, H, W).
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        kernel_size: int = 3,
        bias: bool = True
    ):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.kernel_size = kernel_size
        self.padding = kernel_size // 2
        self.bias = bias

        # Combined convolution for all 4 gates (input, forget, candidate, output)
        # Weight shape: (4 * hidden_dim, input_dim + hidden_dim, kernel_size, kernel_size)
        self.conv = nn.Conv2d(
            in_channels=self.input_dim + self.hidden_dim,
            out_channels=4 * self.hidden_dim,
            kernel_size=self.kernel_size,
            padding=self.padding,
            bias=self.bias
        )

        self._init_weights()

    def _init_weights(self):
        """Initializes weights using Xavier uniform and zero biases (with positive forget gate bias)."""
        nn.init.xavier_uniform_(self.conv.weight)
        if self.conv.bias is not None:
            nn.init.zeros_(self.conv.bias)
            # Set forget gate bias to 1.0 to encourage information retention initially
            self.conv.bias.data[self.hidden_dim:2 * self.hidden_dim].fill_(1.0)

    def forward(
        self,
        x: torch.Tensor,
        hx: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass for a single timestep.

        Parameters:
        - x: Input tensor of shape (B, C_in, H, W)
        - hx: Tuple (h_prev, c_prev) where each is of shape (B, C_hidden, H, W).
              If None, states are initialized to zeros on the same device as x.

        Returns:
        - (h_next, c_next): Updated spatial hidden and cell state tensors.
        """
        batch_size, _, height, width = x.shape

        if hx is None:
            h_prev = torch.zeros(batch_size, self.hidden_dim, height, width, device=x.device, dtype=x.dtype)
            c_prev = torch.zeros(batch_size, self.hidden_dim, height, width, device=x.device, dtype=x.dtype)
        else:
            h_prev, c_prev = hx

        # Concatenate spatial input and recurrent hidden state along channel dimension
        combined = torch.cat([x, h_prev], dim=1)  # (B, C_in + C_hidden, H, W)

        # Compute all 4 gates simultaneously
        conv_output = self.conv(combined)  # (B, 4 * C_hidden, H, W)

        # Split into (i_gate, f_gate, g_candidate, o_gate)
        cc_i, cc_f, cc_g, cc_o = torch.split(conv_output, self.hidden_dim, dim=1)

        # Gate activations
        i = torch.sigmoid(cc_i)
        f = torch.sigmoid(cc_f)
        g = torch.tanh(cc_g)
        o = torch.sigmoid(cc_o)

        # State updates
        c_next = f * c_prev + i * g
        h_next = o * torch.tanh(c_next)

        return h_next, c_next
