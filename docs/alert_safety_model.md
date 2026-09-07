# JALDRISHTI AI — Alert Safety Model & Multi-Gate Gating (Phase 16)

## 1. Safety Principles & Operational Invariants

1. **Zero Autonomous RED Alerts**: RED alerts must never transition directly from `CANDIDATE` to `ESCALATED`. They must always pass through `PENDING_HUMAN_REVIEW` and require explicit operator acknowledgement or escalation.
2. **Degraded-Data Constrained Escalation**: When critical hydrometric or radar telemetry is flagged as `DATA_DEGRADED`, `STALE`, or `OFFLINE` (such as during GloFAS emergency fallback), automated RED alert creation is constrained to `ORANGE` with an explicit reason displayed to the commander.
3. **Deadband Hysteresis**: 5-point rolling severity buffers and rate limits prevent high-frequency oscillating warnings when river levels fluctuate near threshold marks.
4. **Condition Deduplication**: Fingerprinting (`basin:station:hazard:severity:window`) ensures continuous evolving floods update the existing active incident record rather than spawning redundant duplicate alerts.

---

## 2. Decision Logic Matrix

```
                          ┌───────────────────────────┐
                          │ Physical Exceedance Check │
                          └─────────────┬─────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
        Stage >= Danger Mark?                   Stage >= Warning Mark?
                    │                                       │
        ┌───────────┴───────────┐                           ▼
        ▼                       ▼                      [ ORANGE ]
  Confidence = HIGH?     Confidence = DEGRADED?             │
        │                       │                           ▼
        ▼                       ▼                   [ AUTO-DISPATCH ]
   [ RED CANDIDATE ]      [ ORANGE CANDIDATE ]
        │                       │
        ▼                       ▼
[ PENDING HUMAN REVIEW ] ◄──────┘
        │
        ▼ (Operator Assesses Evidence)
  [ ACKNOWLEDGED / ESCALATED / DOWNGRADED ]
```

---

## 3. Human Review Audit Integrity

Every review action produces a cryptographically referenced, timestamped `AlertAuditRecord` recording:
- `operator_id`
- `operator_role`
- `action` (`ACKNOWLEDGE`, `ESCALATE`, `DOWNGRADE`, `DISMISS`, `SUPPRESS`, `REQUEST_FIELD_VERIFICATION`)
- `previous_state` & `new_state`
- `reason`
