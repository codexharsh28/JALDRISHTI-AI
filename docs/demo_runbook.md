# JALDRISHTI AI — Judge Walkthrough & Demonstration Runbook (3–5 Minutes)

This runbook outlines the recommended 5-minute presentation script demonstrating JALDRISHTI AI's full causal pipeline: **Rain $\to$ River $\to$ Flood $\to$ Impact $\to$ Risk $\to$ Alert $\to$ Citizen**.

---

## ⏱️ Minute-by-Minute Demonstration Sequence

### 0:00 – 0:45 | Problem & Operational Mission
- **Opening Statement**: "In flood management, there is a dangerous gap between meteorological rain forecasts, river stage monitoring, and the last-mile citizen who needs to evacuate. JALDRISHTI AI bridges this entire chain."
- **Point to Dashboard**: Point to the **Overview Dashboard** showing the Mahanadi Delta basin, CWC stations, sensor health, and verified baseline state.

---

### 0:45 – 1:30 | Start End-to-End Demo & Rainfall Nowcast
- **Action**: Click **"START END-TO-END DEMO"** on the control panel.
- **Narrative**:
  - Point to the **Rainfall Nowcast** evolution as convective storm cells intensify from $2.0\text{ mm/h} \to 38.5\text{ mm/h} \to 48.0\text{ mm/h}$.
  - Explain: "The PyTorch ConvLSTM nowcaster tracks spatiotemporal advection and storm intensity over the next 6 hours, feeding directly into the hydrological routing models."

---

### 1:30 – 2:30 | Hydrology Surge & 2D Inundation Expansion
- **Action**: Step through stages $T4 \to T7$.
- **Narrative**:
  - Show the **River Stage & Discharge Hydrograph**: Mundali Barrage stage surges past Warning Level ($25.40\text{m}$) and approaches Danger Level ($26.30\text{m}$).
  - Switch to the **Inundation Map**: Show 2D floodwaters expanding across Cuttack and Kendrapara lowlands ($0 \to 158.2\text{ km}^2$), depth reaching $1.6\text{m}$.

---

### 2:30 – 3:30 | Causal Risk Waterfall & Operator Review Gate
- **Action**: Highlight the **"Why Did Risk Change?"** attribution card at stage $T10$.
- **Narrative**:
  - Explain: "Unlike black-box AI, JALDRISHTI decomposes risk into transparent additive components: $+4.5\text{ pts}$ from inundation, $+6.1\text{ pts}$ from river surge, $-0\text{ pts}$ data penalty."
  - **Show the Safety Gate**: "When risk enters RED, the system enforces a mandatory human operator review gate before any sirens or public SMS are triggered."
  - **Action**: Click **"AUTHORIZE DISPATCH"**.

---

### 3:30 – 4:30 | Geofenced Public Citizen Alerts (Mock SMS / Push)
- **Action**: Open the **Public Citizen Portal**.
- **Narrative**:
  - Show that **DEMO USER** (located in Cuttack) receives the multilingual high-severity flood warning via Mock SMS and In-App inbox.
  - Show that **OUTSIDE USER** (located in Sundargarh) is completely isolated by the geofence to prevent alert fatigue.

---

### 4:30 – 5:00 | Cybersecurity, Verification Evidence & Conclusion
- **Action**: Scroll to the **Verification Evidence Panel**.
- **Narrative**:
  - "The entire platform is backed by 328 automated test suites passing with 100% reliability, PostgreSQL/PostGIS schemas, PostGIS geometry models, salted OTP hashing, IDOR authorization, and sliding-window rate limiters."
- **Closing**: "JALDRISHTI AI provides end-to-end, scientifically defensible, and actionable early warnings from cloudburst to citizen."
