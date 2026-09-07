# JALDRISHTI AI — Operational Alert Decision Support & Safety Workflow (Phase 16)

## 1. Core Rule & Legal Invariant
> **IMPORTANT DECISION SUPPORT NOTICE**:
> JALDRISHTI AI is an **Operational Decision Support Platform**, NOT an official emergency authority.
> No automated system routine may directly command or dispatch sirens, close dam floodgates, order public evacuations, or manipulate physical municipal infrastructure without human operator authorization.

## 2. Alert Lifecycle State Machine
```
NORMAL → WATCH → CANDIDATE → PENDING_HUMAN_REVIEW → ACKNOWLEDGED → ESCALATED → EXPIRED / CANCELLED / SUPPRESSED
```

| Lifecycle State | Description |
| :--- | :--- |
| **NORMAL** | Baseline monitoring; indicators within standard non-flood boundaries. |
| **WATCH** | Advisory threshold exceeded ($fused\_rain \ge 15\text{ mm/hr}$ or stage near warning mark). |
| **CANDIDATE** | Automated algorithm identified potential multi-hazard threshold exceedance. |
| **PENDING_HUMAN_REVIEW** | Mandatory gate for all RED alerts and degraded telemetry scenarios before SOP authorization. |
| **ACKNOWLEDGED** | Human officer verified telemetry, approved SOP, and signed off with timestamp. |
| **ESCALATED** | Incident escalated to District Disaster Management Authority (DDMA) or NDRF. |
| **SUPPRESSED** | Temporarily silenced due to duplicate fingerprint, known sensor maintenance, or localized non-critical drainage. |
| **CANCELLED** | Model prediction demoted or dismissed following physical field inspection. |

## 3. Deadband Hysteresis & Condition Deduplication
1. **Deadband Hysteresis**: Prevents oscillation between `RED` and `ORANGE` when river stage fluctuates around $26.30\text{ m} \pm 0.05\text{ m}$. Downgrading requires $\ge 2$ consecutive cycles below threshold minus a $0.20\text{ m}$ safety margin.
2. **Condition Fingerprint**: SHA-256 hash of `basin:severity:stage_bracket:lead_time` prevents creating duplicate incident tickets for the same ongoing hydraulic situation.

## 4. Role-Based Access Control (RBAC) Matrix
| Operator Role | View Queue | Request Field Verification | Acknowledge SOP | Downgrade / Dismiss | Suppress / Override |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **VIEWER** | ✓ | ✗ | ✗ | ✗ | ✗ |
| **ANALYST** | ✓ | ✓ | ✗ | ✗ | ✗ |
| **OPERATOR** | ✓ | ✓ | ✓ | ✓ | ✗ |
| **ADMINISTRATOR** | ✓ | ✓ | ✓ | ✓ | ✓ |

## 5. Immutable Audit Trail
Every lifecycle state change and human review decision is recorded to `data/alerts/audit_log_YYYYMMDD.jsonl` with:
- `timestamp`: UTC ISO timestamp
- `operator_id`: Verified officer identifier
- `operator_role`: User role under RBAC
- `action`: Operator action executed
- `previous_state` $\rightarrow$ `new_state`
- `reason`: Justification rationale
- `field_notes`: Observations from ground reconnaissance teams
