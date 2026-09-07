# JALDRISHTI AI — Operational Latency Benchmarks & Monitoring

## 1. End-to-End Latency Architecture

Operational latency is tracked across the complete observation-to-decision causal chain:

```
[External Obs Time] ──> [Ingestion & QC] ──> [Queue Wait] ──> [ML Inference] ──> [Inundation & Alert] ──> [WebSocket Delivery]
      (t0)                  (+120ms)            (+25ms)          (+268ms)             (+177ms)                  (+15ms)
```

$$\text{Total End-to-End Latency} \approx 677.2\text{ ms}$$

---

## 2. Component Latency Budgets

| Pipeline Stage | Nominal Latency Budget | Measured Benchmark |
| :--- | :---: | :---: |
| **Source Ingestion & Network Fetch** | $\le 200\text{ ms}$ | $120.5\text{ ms}$ |
| **QC Validation & Checksum Verification** | $\le 30\text{ ms}$ | $18.2\text{ ms}$ |
| **Precipitation Fusion** | $\le 50\text{ ms}$ | $42.0\text{ ms}$ |
| **Forecast Queue Scheduling** | $\le 50\text{ ms}$ | $25.0\text{ ms}$ |
| **XGBoost / ConvLSTM Inference** | $\le 350\text{ ms}$ | $268.0\text{ ms}$ |
| **Inundation Surrogate Model** | $\le 200\text{ ms}$ | $145.0\text{ ms}$ |
| **Impact & Alert Safety Gating** | $\le 50\text{ ms}$ | $44.0\text{ ms}$ |
| **WebSocket Serialization & Delivery** | $\le 25\text{ ms}$ | $14.5\text{ ms}$ |
| **Total System Pipeline** | **$\le 1000\text{ ms}$** | **$677.2\text{ ms}$** |
