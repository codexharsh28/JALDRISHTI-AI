# JALDRISHTI AI — Operational Event Streaming Runbook

## 1. Operating Modes & Streaming Behavior

1. **LIVE Mode**: Consumes real-time external telemetry (IMD AWS, CWC WRIS, IMERG, GloFAS). Requires explicit operator confirmation to enable. Emits `mode="LIVE"`.
2. **REPLAY Mode**: Replays synchronized historical flood scenarios (`EVT-MAHANADI-2020-08`, `EVT-MAHANADI-2022-08`, `EVT-MAHANADI-2024-08`). Emits `mode="REPLAY"`, `data_state="REAL_HISTORICAL_HINDCAST"`.
3. **SIMULATION Mode**: Interactive sandbox with configurable hydraulic stress parameters. Emits `mode="SIMULATION"`, `data_state="SYNTHETIC"`.

---

## 2. Emergency Alert Gating Runbook

When a critical surge occurs:
1. `ALERT_SAFETY_GATE` detects extreme hydraulic thresholds and emits `HUMAN_REVIEW_REQUIRED` (Priority: `CRITICAL`).
2. The operations dashboard displays the pending RED alert in the **Emergency Review Drawer** alongside explainability contributor features and data confidence flags.
3. The Incident Commander reviews the evidence and invokes:
   `POST /api/v1/alerts/{alert_id}/acknowledge`
4. The system transitions the alert to `ACKNOWLEDGED`, emits `ALERT_ACKNOWLEDGED`, and releases public early warning siren dispatches.
