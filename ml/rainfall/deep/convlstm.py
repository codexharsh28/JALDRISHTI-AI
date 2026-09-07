"""
Multi-Layer Recurrent ConvLSTM Module for JALDRISHTI AI.
Processes 5D spatiotemporal sequence tensors (B, T, C, H, W) through stacked ConvLSTM layers.
"""

import torch
import torch.nn as nn
from typing import List, Tuple, Union, Optional

from ml.rainfall.deep.convlstm_cell import ConvLSTMCell

class ConvLSTM(nn.Module):
    """
    Multi-Layer 2D Convolutional LSTM.
    Unrolls input sequence across time dimension T.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dims: Union[int, List[int]],
        kernel_sizes: Union[int, List[int]] = 3,
        num_layers: int = 2,
        bias: bool = True,
        return_all_layers: bool = False
    ):
        super().__init__()

        if isinstance(hidden_dims, int):
            hidden_dims = [hidden_dims] * num_layers
        if isinstance(kernel_sizes, int):
            kernel_sizes = [kernel_sizes] * num_layers

        assert len(hidden_dims) == num_layers, "hidden_dims length must match num_layers"
        assert len(kernel_sizes) == num_layers, "kernel_sizes length must match num_layers"

        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.kernel_sizes = kernel_sizes
        self.num_layers = num_layers
        self.return_all_layers = return_all_layers

        cell_list = []
        for i in range(num_layers):
            cur_input_dim = input_dim if i == 0 else hidden_dims[i - 1]
            cell_list.append(
                ConvLSTMCell(
                    input_dim=cur_input_dim,
                    hidden_dim=hidden_dims[i],
                    kernel_size=kernel_sizes[i],
                    bias=bias
                )
            )

        self.cell_list = nn.ModuleList(cell_list)

    def forward(
        self,
        x: torch.Tensor,
        hidden_state: Optional[List[Tuple[torch.Tensor, torch.Tensor]]] = None
    ) -> Tuple[torch.Tensor, List[Tuple[torch.Tensor, torch.Tensor]]]:
        """
        Parameters:
        - x: 5D Tensor of shape (B, T, C, H, W)
        - hidden_state: List of (h, c) tuples for each layer. If None, initialized to zeros.

        Returns:
        - layer_output: Sequence output tensor of shape (B, T, C_last_hidden, H, W)
        - last_states: List of (h_last, c_last) tuples for each layer
        """
        batch_size, seq_len, _, height, width = x.shape

        if hidden_state is None:
            hidden_state = self._init_hidden(batch_size, height, width, x.device, x.dtype)

        current_input = x
        all_layer_outputs = []
        last_states = []

        for layer_idx, cell in enumerate(self.cell_list):
            h, c = hidden_state[layer_idx]
            layer_sequence = []

            for t in range(seq_len):
                x_t = current_input[:, t, :, :, :]
                h, c = cell(x_t, (h, c))
                layer_sequence.append(h)

            # Stack along temporal dimension: (B, T, C_hidden, H, W)
            stacked_layer = torch.stack(layer_sequence, dim=1)
            current_input = stacked_layer
            all_layer_outputs.append(stacked_layer)
            last_states.append((h, c))

        if self.return_all_layers:
            return all_layer_outputs, last_states
        else:
            return all_layer_outputs[-1], last_states

    def _init_hidden(
        self,
        batch_size: int,
        height: int,
        width: int,
        device: torch.device,
        dtype: torch.dtype
    ) -> List[Tuple[torch.Tensor, torch.Tensor]]:
        init_states = []
        for hidden_dim in self.hidden_dims:
            h = torch.zeros(batch_size, hidden_dim, height, width, device=device, dtype=dtype)
            c = torch.zeros(batch_size, hidden_dim, height, width, device=device, dtype=dtype)
            init_states.append((h, c))
        return init_states
