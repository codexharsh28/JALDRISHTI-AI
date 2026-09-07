# JALDRISHTI AI — Master Judge Demonstration Runbook

**Scenario**: `DEMO-MAHANADI-STORM-01`  
**Duration**: 3–5 Minutes  
**Mode**: Sandboxed Simulation (Isolated from Live State)  

---

## Chronological Demonstration Sequence

### 0:00 – 0:30 | Mission & Problem Context
1. **Explain Purpose**: JALDRISHTI AI is an AI-powered hydrometeorological decision-support system delivering hyperlocal flood intelligence for the Mahanadi Delta, Odisha.
2. **Show Data Health**: Open **Data Health View**. Point out the **Official IMD Automatic Weather Station (AWS)** card. Show that the system is scientifically honest — if official government IP whitelisting is not configured, it accurately displays `NOT_CONFIGURED`, never fabricating artificial observations.

### 0:30 – 1:15 | Initiation & Rainfall Intensification
1. **Start Scenario**: Navigate to **Live Operations Control Panel** and click **Start Demo Scenario** (`DEMO-MAHANADI-STORM-01`).
2. **Watch Rainfall Grid**: Show the 2.5 km computational model grid dynamically lighting up over the Tikarpara-Mundali catchment as ConvLSTM nowcasting predicts intensifying precipitation (peak 45 mm/h).

### 1:15 – 2:00 | River Response & Inundation Evolution
1. **Observe River Forecast**: River hydrograph at Mundali Gauge rises from 24.5 m to 28.6 m, crossing the CWC Warning Level (27.5 m) and approaching Danger Level (29.0 m).
2. **View Inundation Map**: The 2D HAND hydraulic model renders spatial flood extents across Cuttack and Kendrapara lowlands. Show temporal differencing (expansion vectors and depth classes).

### 2:00 – 2:45 | Impact & Causal Risk Explainability
1. **Impact Table**: Highlighting exposed assets (2 hospitals, 4 cyclone shelters, 14 km highway).
2. **"Why Did Risk Change?"**: Open Risk View. Explain the causal waterfall decomposition showing that 62% of the risk delta is driven by upstream Mundali stage surge and 28% by local rainfall nowcast.

### 2:45 – 3:30 | Safety-Gated Alert & Human Review
1. **Alert Lifecycle**: Red / Critical alert candidate is generated.
2. **Human Operator Gate**: Point out that the system **refuses to blast public SMS automatically**. The alert pauses in `PENDING_HUMAN_REVIEW`.
3. **Operator Action**: Operator confirms the alert with one click (`ACKNOWLEDGE & DISPATCH`).

### 3:30 – 4:15 | Geo-Targeted Citizen Notification
1. **Citizen Portal**: Switch to the Public Citizen Safety Portal.
2. **Affected vs Outside Citizen Verification**:
   - `DEMO_USER_AFFECTED` (Cuttack Home): Receives urgent targeted alert and Mock SMS with actionable advice.
   - `DEMO_USER_OUTSIDE_AREA` (Sundargarh Home): Receives **no spam / no false alert**.
3. **Disclaimer**: Highlight the mandatory safety footer: *"JALDRISHTI Decision-Support Alert. Follow official local authority instructions."*

### 4:15 – 5:00 | Real vs Simulated Honesty & Conclusion
1. **Reset Demo**: Click **Reset Demo State**. Show that simulation state is cleared cleanly without corrupting real historical or live data.
2. **Summary**: Emphasize multi-region configuration readiness, zero data fabrication, and enterprise security.
