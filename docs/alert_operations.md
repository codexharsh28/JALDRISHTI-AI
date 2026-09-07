# JALDRISHTI AI — Operational Alert Lifecycle & Human Review Runbook (Phase 16)

## 1. Executive Summary

Phase 16 converts JALDRISHTI's alert dispatch into an explicit, stateful, and audited decision-support workflow.

JALDRISHTI AI is a **decision-support prototype** and is **not authorized to command real infrastructure** or act as a legal warning authority. All emergency escalations follow human-in-the-loop validation.

---

## 2. Alert Lifecycle State Machine

```
   [ NORMAL / WATCH ]
           │
           ▼
     [ CANDIDATE ] ─────────────┐
           │                    │ (degraded / suppressed)
           ▼                    ▼
[ PENDING_HUMAN_REVIEW ]   [ SUPPRESSED / DISMISSED ]
           │
  ┌────────┼────────┬────────┐
  ▼        ▼        ▼        ▼
[ ACK ] [ ESC ]  [ DOWN ] [ FIELD_VERIF ]
  │        │        │
  └────────┴────────┴──► [ EXPIRED / CANCELLED ]
```

### Supported Lifecycle States:
- `NORMAL`: All variables within safe baselines.
- `WATCH`: Elevated stage/rain requiring enhanced monitoring.
- `CANDIDATE`: Automated threshold crossed, preparing incident candidate.
- `PENDING_HUMAN_REVIEW`: Multi-hazard criteria met; awaiting duty officer review.
- `ACKNOWLEDGED`: Operator acknowledged receipt and confirmed assessment.
- `ESCALATED`: Confirmed severe flood threat escalated to district command.
- `DOWNGRADED`: Hazard mitigated or localized; severity decreased.
- `DISMISSED`: False positive or localized non-critical drainage issue.
- `SUPPRESSED`: Muted by administrator due to sensor calibration/maintenance.
- `EXPIRED`: Horizon window passed without incident continuation.
- `CANCELLED`: Source error or operational override.

---

## 3. Role-Based Access Control (RBAC)

| Role | Permissions |
|---|---|
| **VIEWER** | Read-only inspection of alert feed and maps. |
| **ANALYST** | Analysis, request field verification. |
| **OPERATOR** | Acknowledge, escalate, downgrade, dismiss, submit field data. |
| **ADMIN** | Full administrative controls, configuration, alert suppression. |

---

## 4. REST API Endpoints

- `GET /api/v1/alerts`: Active alerts list.
- `GET /api/v1/alerts/{id}`: Detailed incident payload with evidence.
- `GET /api/v1/alerts/{id}/history`: Immutable audit trail.
- `POST /api/v1/alerts/{id}/acknowledge`: Operator acknowledgement.
- `POST /api/v1/alerts/{id}/escalate`: Emergency command escalation.
- `POST /api/v1/alerts/{id}/downgrade`: Severity downgrade.
- `POST /api/v1/alerts/{id}/dismiss`: Incident dismissal.
- `POST /api/v1/alerts/{id}/suppress`: Administrative suppression.
- `POST /api/v1/alerts/{id}/field-verification`: Field team dispatch / data submission.
