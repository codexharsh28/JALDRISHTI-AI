# JALDRISHTI AI — Public Notification Policy & Anti-Spam Guidelines

## 1. Multi-Channel Routing Matrix
Notification channels are selectively activated depending on incident severity and user verification state:

| Severity Level | Eligible Channels | Mandatory Prerequisites |
|---|---|---|
| `INFO` / `GREEN` | `IN_APP` | User registered |
| `WATCH` / `YELLOW` | `IN_APP`, `PUSH` | Registered device token for Push |
| `WARNING` / `ORANGE` | `IN_APP`, `PUSH`, `SMS` | Verified phone (+91 OTP) for SMS |
| `HIGH_RISK` | `IN_APP`, `PUSH`, `SMS` | Verified phone (+91 OTP) for SMS |
| `CRITICAL` / `RED` | `IN_APP`, `PUSH`, `SMS` | Operator approval + verified phone for SMS |
| `RESOLVED` | `IN_APP`, `PUSH` | Alert engine state transition to RESOLVED |

## 2. Anti-Spam & Deduplication Policy
To prevent notification fatigue and message storms caused by minor model fluctuations (e.g. 67% -> 68% -> 66%):
1. **Deterministic Fingerprinting**:
   $$\text{Fingerprint} = \text{SHA-256}(\text{alert\_id} + \text{severity} + \text{locality} + \text{hazard})[:16]$$
2. **Cooldown Window**:
   - Default 45-minute suppression window for identical fingerprints.
3. **Escalation Bypass**:
   - Upward state transitions (e.g. `WATCH` -> `WARNING` or `HIGH_RISK` -> `CRITICAL`) immediately bypass cooldown windows and dispatch notifications.
4. **Rate Limiting**:
   - OTP requests: Max 3 requests per 10 minutes per phone number.
   - Max 3 verification attempts per OTP cycle.
