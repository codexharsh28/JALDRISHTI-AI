# JALDRISHTI AI — Database Backup, Disaster Recovery & Retention Policy

## 1. Backup Strategy
- **Frequency**:
  - Full backups: Daily at 02:00 UTC.
  - WAL Archiving / Point-in-Time Recovery (PITR): Continuous 15-minute intervals.
- **Storage & Encryption**: Backups are encrypted using AES-256 (GCM) and replicated to geographically distributed object storage buckets.
- **Retention**:
  - Daily backups: 30 days retention.
  - Monthly snapshots: 12 months retention.
  - Audit logs: 365 days retention (compliance requirement).

---

## 2. Disaster Recovery & Restoration Verification
- Automated weekly test restorations into staging sandboxes verify snapshot integrity and schema migration consistency.
- Mean Time to Recovery (MTTR) target: < 15 minutes for full database failover.
