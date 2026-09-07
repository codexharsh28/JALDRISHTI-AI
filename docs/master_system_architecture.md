# JALDRISHTI AI — Master System Architecture

## 1. System Overview

JALDRISHTI AI is an end-to-end, configuration-driven **Hydrometeorological Decision-Support Platform**. It implements a unified, single-authoritative causal chain linking multi-source raw observations down to last-mile geo-targeted citizen warning delivery.

```
                  ┌─────────────────────────────────────────────────────────┐
                  │                 MULTI-SOURCE OBSERVATION                │
                  │  • IMD AWS (Real Telemetry / Status Governed)           │
                  │  • CWC River Telemetry (Ground Gauges)                  │
                  │  • NASA GPM IMERG Early (NRT Satellite)                │
                  │  • ISRO INSAT-3DR HEM QPE (Geostationary)               │
                  │  • NWP ECMWF IFS 0.25° / GFS Grid                       │
                  │  • Paradip Doppler Weather Radar PPI (Polar Volume)     │
                  └────────────────────────────┬────────────────────────────┘
                                               │
                                               ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │             QUALITY CONTROL & ANOMALY GATEWAY           │
                  │  • 5-Layer Screening (Physical bounds, temporal jump,   │
                  │    robust Z-score, EWMA, spatial cross-corroboration)   │
                  │  • Anomaly Separation: VALID_EXTREME vs SENSOR_ERROR    │
                  └────────────────────────────┬────────────────────────────┘
                                               │
                                               ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │             MULTI-SOURCE RAINFALL FUSION                │
                  │  • 2.5 km Computational Model Grid                      │
                  │  • Inverse-Distance Variance Weighting                  │
                  │  • Gauge-Radar-Satellite Bias Correction                │
                  └────────────────────────────┬────────────────────────────┘
                                               │
                                               ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │           PYTORCH CONVLSTM RAINFALL NOWCASTER           │
                  │  • 0–6h Spatial Convolutional Recurrent Network         │
                  │  • Encoder-Decoder Architecture                         │
                  └────────────────────────────┬────────────────────────────┘
                                               │
                                               ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │           HYDROLOGICAL FORECASTING (0–24h)              │
                  │  • Gauge-to-Gauge Routing & Discharge Model             │
                  │  • GloFAS Modeled Fallback (clearly tagged)             │
                  │  • P10 / P50 / P90 Prediction Envelopes                 │
                  └────────────────────────────┬────────────────────────────┘
                                               │
                                               ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │            2D HYDRAULIC INUNDATION ENGINE               │
                  │  • Physics-Guided HAND Inundation Dynamics              │
                  │  • Temporal Inundation Evolution Differencing           │
                  │  • Sentinel-1 SAR / Bhuvan Extent Validation (IoU, CSI) │
                  └────────────────────────────┬────────────────────────────┘
                                               │
                                               ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │           IMPACT & CRITICAL ASSET EXPOSURE              │
                  │  • Hospitals, Schools, Shelters, Bridges, Power Grids   │
                  │  • Estimated Population Exposure (WorldPop 100m)        │
                  └────────────────────────────┬────────────────────────────┘
                                               │
                                               ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │          LIVE RISK ENGINE & CAUSAL EXPLAINER            │
                  │  • Versioned Composite Risk Score (0.00 – 1.00)         │
                  │  • "Why Did Risk Change?" Causal Waterfall              │
                  │  • Material Change Gating                               │
                  └────────────────────────────┬────────────────────────────┘
                                               │
                                               ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │               SAFETY-GATED ALERT ENGINE                 │
                  │  • Lifecycle: WATCH -> CANDIDATE -> PENDING_REVIEW      │
                  │  • RED / CRITICAL Gate: Requires Human Confirmation     │
                  │  • Hysteresis, Deduplication, Condition Fingerprinting  │
                  └────────────────────────────┬────────────────────────────┘
                                               │
                                               ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │          GEO-TARGETED LAST-MILE NOTIFICATIONS           │
                  │  • Point-in-Polygon Geofencing (HOME/WORK/FAMILY)       │
                  │  • SMS (MSG91/Twilio/Mock) + Web Push + In-App Inbox    │
                  │  • Masked Phone & OTP Security                          │
                  └─────────────────────────────────────────────────────────┘
```

---

## 2. Unification Principles (Zero Parallel Duplication)

1. **One Authoritative Rainfall Engine**:
   - `services/fusion/` produces the single computational rainfall field. No parallel frontend or mock rain simulation exists in production paths.

2. **One Authoritative Risk & Alert Engine**:
   - `services/risk/risk_calculator.py` computes all risk scores.
   - `services/alerts/alert_engine.py` evaluates all alert conditions. No frontend self-assigned alerts.

3. **One Authoritative Notification Engine**:
   - `services/notifications/notification_service.py` evaluates geofencing, fanout, and dispatch queues.

4. **Multi-Region Reusability**:
   - All spatial boundaries, subbasins, gauge coordinates, and thresholds are loaded dynamically from `basin_config.yaml` and region configuration tables, ensuring portability beyond the Mahanadi Delta pilot.
