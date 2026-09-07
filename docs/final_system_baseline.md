# JALDRISHTI AI — Final System Baseline & Technical Freeze

**Freeze Date**: 2026-08-27  
**Build Status**: `PASSING (0 ERRORS)`  
**Test Suite Status**: `365 / 365 TESTS PASSED (100%)`  
**Security Status**: Zero Critical / High Findings  

---

## 1. System Metadata & Verification State

- **Platform Architecture**: Fast-API backend (`apps/api/main.py`) + React/TypeScript/Tailwind/Leaflet frontend (`apps/web/`)
- **PyTorch Models**: ConvLSTM Nowcasting Network (`ml/models/convlstm.py`)
- **Database Support**: SQLite development (`data/notifications.db`, `data/imd_aws.db`) + PostgreSQL / PostGIS production DDL (`services/notifications/db/schema_postgres.sql`)
- **Primary Live Ingestion**: Official IMD AWS Client (`services/ingestion/providers/imd_aws_client.py`), CWC, IMERG, INSAT-3DR, GloFAS
- **Safety Gate**: Human-in-the-loop review required for RED/CRITICAL alerts before citizen notification dispatch
- **Public Privacy**: SHA-256 salted phone hash, masked display (`******3210`), salted OTP storage with 5-minute expiry and rate-limiting
- **Geofencing**: Point-in-polygon spatial containment over active flood hazard geometries

---

## 2. Test Execution Verification

```
================================ test session starts ================================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\DevbratY\Desktop\JALDRISHTI AI
plugins: anyio-4.14.2
collected 365 items

tests/test_*.py ............................................................. [100%]

=========================== 365 passed, 325 warnings in 30.89s ======================
```

---

## 3. Frontend Production Build Verification

```
> tsc && vite build
vite v6.4.3 building for production...
transforming...
✓ 2513 modules transformed.
rendering chunks...
dist/index.html                   1.16 kB │ gzip:   0.65 kB
dist/assets/index-HASZfO7M.css   58.90 kB │ gzip:  14.46 kB
dist/assets/index-Bf2F10Qv.js   978.99 kB │ gzip: 264.68 kB
✓ built in 5.69s
```

---

## 4. Known Limitations & Roadmap

1. **IMD AWS Gateway IP Whitelisting**:
   - Official IMD AWS endpoint requires static public IP registration with IMD NWP Division. In non-whitelisted development environments, the adapter cleanly and truthfully reports `NOT_CONFIGURED`.
2. **Doppler Radar Active Feed**:
   - Paradip DWR Max-Z PPI raw polar volume feed is marked `UNAVAILABLE` pending direct FTP/NRT stream configuration from IMD Radar Division.
3. **SMS Gateway DLT Credentials**:
   - Production SMS dispatch requires genuine TRAI DLT Entity and Template IDs. Local tests run in isolated `MockSMSSink` mode.
