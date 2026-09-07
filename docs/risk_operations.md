# JALDRISHTI AI — Real-Time Risk Operations Runbook (Phase 14)

## 1. Scope & Role

This runbook instructs emergency duty commanders and technical analysts in interpreting real-time risk state transitions, investigating the **"Why Did Risk Change?"** causal cards, and evaluating emergency alert gating.

---

## 2. Risk Level Decision Policies

| Level | Range | Automated System Actions | Operator Protocol |
|---|---|---|---|
| **NORMAL** | $0 - 24$ | Background telemetry polling, standard nowcasting cadence. | Normal monitoring. |
| **WATCH** | $25 - 44$ | Polling interval halved; nowcast models scheduled every 15 min. | Notify flood cell duty hydrologist. |
| **WARNING** | $45 - 64$ | Hydraulic surrogate pre-computes 24h inundation extent. | Verify upstream barrage releases (Hirakud / Naraj). |
| **ALERT** | $65 - 79$ | Generates `ALERT_CANDIDATE` for human review. | Prepare evacuation routes and field verification teams. |
| **CRITICAL** | $80 - 100$ | Triggers Red Alert candidate gate (requires high confidence). | Execute immediate emergency coordination protocols. |

---

## 3. Investigating "Why Did Risk Change?"

When risk escalates materially ($\ge 3.0\text{ pts}$):
1. **Locate the "Why Risk Changed" Card** on the Operations Overview Dashboard.
2. **Review Top Contributors**:
   - Check whether precipitation or upstream discharge is the primary driver.
   - If `Category == CONFIDENCE`, verify whether ground gauges have suffered outages rather than actual weather deterioration.
3. **Inspect the Risk Evolution Timeline**:
   - Review historical risk points across the past 8 cycles to discern monotonic surge vs transient spike.

---

## 4. API Endpoints

- `GET /api/v1/risk/current`: Current active risk state, score, level, and top contributors.
- `GET /api/v1/risk/history?limit=50`: Monotonic historical sequence of risk snapshots.
- `GET /api/v1/risk/{risk_state_id}`: Targeted retrieval of specific historical risk version.
- `GET /api/v1/risk/explanation`: Detailed breakdown of causal contributors.
