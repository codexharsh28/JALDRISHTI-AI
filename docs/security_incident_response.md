# JALDRISHTI AI — Security Incident Response & Emergency Containment Playbook

## 1. Incident Severity Triage

| Level | Classification | Trigger Example | Response SLA |
| :--- | :--- | :--- | :--- |
| **SEV-1** | Critical Outage / Active Breach | Unauthorized alert broadcast / Database exposure | Immediate (< 15 mins) |
| **SEV-2** | High Security Event | Sustained rate limit bypass / Massive OTP abuse attempt | < 1 hour |
| **SEV-3** | Medium Vulnerability | Non-critical component degraded / Incomplete telemetry | < 4 hours |
| **SEV-4** | Low Informational | Minor log parsing anomaly / Low-priority config drift | Next release cycle |

---

## 2. Containment Playbook for Emergency Alert System
1. **Kill Switch Activation**: If unauthorized alert generation is detected, invoke the operator kill switch to immediately freeze the outbound notification queue (`notification_queue.pause()`).
2. **Provider Key Invalidation**: Instantly revoke the compromised SMS / Push gateway key at the upstream provider portal.
3. **Session Revocation**: Invalidate all active Bearer tokens by rotating `JWT_SECRET_KEY` and forcing re-authentication.
4. **Post-Mortem & Audit Review**: Extract immutable audit logs (`audit_logs`) to determine the root cause, actor IP, and affected records.
