# JALDRISHTI AI — Notification Provider Matrix

## 1. Provider Capabilities & Configuration Matrix

| Provider | Type | Protocol | Config Status Check | Fallback Provider | Purpose |
|---|---|---|---|---|---|
| `MockSMSSink` | SMS | In-Memory Queue | Always `True` (Dev/Test) | None | Local development, automated CI testing, zero telecommunication cost |
| `MSG91Provider` | SMS | HTTPS POST (DLT API) | `MSG91_AUTH_KEY` + `DLT_ENTITY_ID` + `DLT_SENDER_ID` | `TwilioSMSProvider` / `MockSMSSink` | Production Indian citizen emergency SMS |
| `TwilioSMSProvider` | SMS | REST API | `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` | `MockSMSSink` | Secondary SMS Gateway Failover |
| `MockPushSink` | Push | In-Memory Queue | Always `True` | None | Push notification CI/CD validation |
| `FCMPushProvider` | Push | HTTP v1 OAuth2 | `FIREBASE_CREDENTIALS_PATH` / `FIREBASE_PROJECT_ID` | `MockPushSink` | Production Android / Web Push Alerts |
| `InAppNotificationProvider` | In-App | In-Memory Indexed Store | Always `True` | None | Citizen Portal Inbox Feed & Audit Log |

## 2. Dynamic Provider Status Resolution
The runtime provider endpoint (`GET /api/v1/notifications/providers`) returns:
- `active_sms_provider`: Active provider name (`MOCK_SMS_SINK` vs `MSG91_DLT_GATEWAY`)
- `active_push_provider`: Active push sink
- `active_in_app_provider`: In-app store
- `dlt_entity_id_configured`: Boolean
- `dlt_sender_id_configured`: Boolean
- `mock_mode`: Boolean flag indicating whether isolated mock sinks are active.
