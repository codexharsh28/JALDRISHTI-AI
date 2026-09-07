# JALDRISHTI AI — Public Citizen Alert Architecture

## 1. Overview & Architectural Hierarchy
The Public Notification Layer in JALDRISHTI AI provides the secure, anti-spam, geofenced last-mile alerting system connecting scientific hydrometeorological intelligence to citizens across the Mahanadi Delta basin.

### System Data Flow Pipeline
```
REAL SENSOR & SATELLITE DATA (IMD/CWC/Bhuvan/GloFAS)
       │
       ▼
HYDROLOGY & INUNDATION SURROGATE (L3/ConvLSTM)
       │
       ▼
IMPACT & EXPOSURE ENGINE
       │
       ▼
PHASE 16 ALERT ENGINE (Incidents, State Machine & Gating)
       │
       ▼ [Human Review Gate for RED Alerts]
NOTIFICATION POLICY ENGINE (Anti-Spam & Routing)
       │
       ▼
GEOFENCE & SPATIAL ENGINE (Haversine & Polygon Buffering)
       │
       ▼
MULTILINGUAL TEMPLATE ENGINE (English & Hindi Parameters)
       │
       ▼
ASYNC BACKGROUND QUEUE & WORKER (Retries & Backoff)
       │
   ┌───┴───────────────────────┬───────────────────────┐
   ▼                           ▼                       ▼
SMS GATEWAYS (MSG91/DLT)   PUSH (FCM HTTP v1)     IN-APP INBOX & REST
   │                           │                       │
   └───────────────────────────┴───────────────────────┘
                               │
                               ▼
                   CITIZEN / PUBLIC RECIPIENT
```

## 2. Core Safety Invariants
1. **No Direct Frontend Triggering**: Public notifications can NEVER be directly initiated from web/client interfaces or raw unvalidated model scores.
2. **Phase 16 Alert Consumption**: The notification service strictly listens to authoritative domain events (`ALERT_STATE_CHANGED`, `ALERT_ESCALATED`, etc.) emitted by the alert engine.
3. **Human-in-the-Loop Gating**: RED alerts marked `PENDING_HUMAN_REVIEW` are strictly suppressed from public dispatch until confirmed by authorized emergency operators.
4. **Data-Degraded Disclosures**: When hydrological telemetry is degraded or fallback models (e.g. GloFAS) are active, explicit non-technical advisories accompany the alert.
5. **Clear Separation of Concerns**: Expert command center operations (ConvLSTM internals, SHAP analysis, raw telemetry streams) remain isolated from the Citizen Safety Portal.
