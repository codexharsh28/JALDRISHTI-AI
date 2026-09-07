# PyTorch ConvLSTM Spatiotemporal Rainfall Nowcaster — System Specification

**Subsystem:** Precipitation Nowcasting (0–6 Hours)  
**Model Identifier:** `RAIN_L3_CONVLSTM`  
**Framework:** PyTorch (Genuine `torch.nn.Module`)  
**Status:** `EXPERIMENTAL` $\rightarrow$ `CANDIDATE` $\rightarrow$ `VALIDATED`  

---

## 1. Mathematical Formulation

The model adopts the Convolutional Long Short-Term Memory (ConvLSTM) architecture designed for spatial-temporal sequence prediction (Shi et al., NeurIPS 2015).

Given an input sequence of spatial precipitation observation fields $\mathcal{X}_{1:T_{in}} = (x_1, x_2, \dots, x_{T_{in}})$ where each $x_t \in \mathbb{R}^{C_{in} \times H \times W}$, the goal is to predict the future sequence $\hat{\mathcal{Y}}_{1:T_{out}} = (\hat{y}_1, \hat{y}_2, \dots, \hat{y}_{T_{out}})$ where each $\hat{y}_t \in \mathbb{R}^{C_{out} \times H \times W}$.

### ConvLSTM Cell Equations

At each timestep $t$ and spatial location $(h, w)$:

$$\begin{aligned}
i_t &= \sigma(W_{xi} * x_t + W_{hi} * h_{t-1} + b_i) \\
f_t &= \sigma(W_{xf} * x_t + W_{hf} * h_{t-1} + b_f) \\
\tilde{c}_t &= \tanh(W_{xc} * x_t + W_{hc} * h_{t-1} + b_c) \\
c_t &= f_t \odot c_{t-1} + i_t \odot \tilde{c}_t \\
o_t &= \sigma(W_{xo} * x_t + W_{ho} * h_{t-1} + b_o) \\
h_t &= o_t \odot \tanh(c_t)
\end{aligned}$$

where:
- $*$ denotes a 2D spatial convolution operation with kernel size $k \times k$ and padding $\lfloor k/2 \rfloor$.
- $\odot$ denotes element-wise Hadamard tensor multiplication.
- $\sigma(\cdot)$ is the logistic sigmoid activation function.
- $h_t, c_t \in \mathbb{R}^{C_{hidden} \times H \times W}$ preserve spatial geometry across all recurrent operations.

---

## 2. Computational Grid & Resolution Specifications

- **Native Data Ingestion Sources:**
  - IMD Gridded Rainfall: $0.25^\circ \approx 27\text{ km}$ native resolution (resampled to model grid).
  - NASA GPM IMERG V07B: $0.1^\circ \approx 10\text{ km}$, 30-minute cadence (resampled to model grid).
- **Computational Model Grid:** $2.5\text{ km}$ ($0.0225^\circ \times 0.025^\circ$ cell size) over the Mahanadi Delta pilot catchment ($[85.0^\circ\text{E}, 20.0^\circ\text{N}] \rightarrow [87.0^\circ\text{E}, 21.0^\circ\text{N}]$).
- **Spatial Grid Dimensions ($H \times W$):** $16 \times 24$ computational mesh cells.
- **Temporal Input Window ($T_{in}$):** 4 steps of 30 minutes ($t_{-120}, t_{-90}, t_{-60}, t_{-30}$).
- **Temporal Forecast Horizons ($T_{out}$):** 12 steps of 30 minutes ($+30\text{m}, +60\text{m}, \dots, +360\text{m}$).

---

## 3. Loss Function & Optimization

To prevent zero-collapse during training under severe spatial rainfall class imbalance, training employs a **Compound Intensity-Weighted Huber Loss**:

$$\mathcal{L}(y, \hat{y}) = \frac{1}{|\Omega|} \sum_{p \in \Omega} w(y_p) \cdot \ell_{\delta}(y_p, \hat{y}_p)$$

where:
$$\ell_{\delta}(y, \hat{y}) = \begin{cases} \frac{1}{2}(y - \hat{y})^2 & \text{if } |y - \hat{y}| \le \delta \\ \delta(|y - \hat{y}| - \frac{1}{2}\delta) & \text{otherwise} \end{cases}$$

and the intensity weight function is:
$$w(y) = 1.0 + 2.0 \cdot \mathbb{I}(y \ge 15) + 5.0 \cdot \mathbb{I}(y \ge 35) + 10.0 \cdot \mathbb{I}(y \ge 65)$$

---

## 4. Physical Consistency Guarantees

1. **Non-Negativity:** Output projections apply a continuous Softplus transformation $\hat{y} = \text{Softplus}(\text{Conv2D}(h_t))$, ensuring strictly non-negative precipitation rates ($\hat{y} \ge 0.0\text{ mm/hr}$).
2. **Leakage Elimination:** Input normalization $(\mu_{train}, \sigma_{train})$ is fit strictly on training partitions; sliding windows never cross event boundaries.
