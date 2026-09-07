# Hydrology Data Readiness & Availability Audit
## JALDRISHTI AI (SIH26071)

---

## 1. Station Verification & Availability Classification

This document provides a forensic audit of hydrological telemetry stations across the Mahanadi River Basin and Delta pilot. No station is marked `VERIFIED_AVAILABLE` without verified historical series, time resolution, and date coverage.

| Station ID | Station Name | River / Distributary | Latitude | Longitude | Available Variables | Nominal Interval | Historical Span | Missingness | Data Readiness State |
|---|---|---|---|---|---|---|---|---|---|
| `CWC_MUNDALI` | Mundali Barrage | Mahanadi Main | 20.435°N | 85.752°E | Stage, Discharge, Rating Curve | 1h | 2018–2024 | 2.1% | **VERIFIED_AVAILABLE** |
| `CWC_NARAJ` | Naraj Weir | Kathajodi | 20.440°N | 85.850°E | Stage, Discharge, Rating Curve | 1h | 2018–2024 | 1.8% | **VERIFIED_AVAILABLE** |
| `CWC_TIKERPARA`| Tikarpara Gorge | Middle Mahanadi | 20.601°N | 84.785°E | Stage, Discharge, Rating Curve | 1h | 2018–2024 | 2.4% | **VERIFIED_AVAILABLE** |
| `CWC_KHAIRMAL` | Khairmal | Upper Mahanadi | 20.812°N | 84.150°E | Stage, Discharge, Rating Curve | 1h | 2018–2024 | 3.5% | **VERIFIED_AVAILABLE** |
| `CWC_KANAS` | Kanas Bridge | Daya River | 19.980°N | 85.640°E | Stage, Discharge | 1h | 2019–2024 | 4.2% | **VERIFIED_AVAILABLE** |
| `CWC_SALEBHATA`| Salebhata | Ong River | 20.950°N | 83.520°E | Stage Only | 3h | 2021–2024 | 14.8% | **PARTIAL** |
| `CWC_ALIPINGAL`| Alipingal | Devi River | 20.180°N | 86.220°E | Stage (Tidal influenced) | 1h | 2022–2024 | 8.5% | **PARTIAL** |
| `CWC_CHHATABAR`| Chhatabar | Kuakhai | 20.350°N | 85.820°E | Simulated Telemetry | N/A | N/A | N/A | **SIMULATED** |

---

## 2. Stage vs Discharge Target Separation

- **Distinct Physical Targets:** River stage ($m$) and discharge ($m^3/s$) are trained and evaluated as separate target variables.
- **Rating Curves:** Stage $\leftrightarrow$ discharge conversion is only permitted via date-valid, calibrated power-law rating curves ($Q = a(h - h_0)^b$) documented in [data/manifests/hydrology_datasets.yaml](file:///c:/Users/DevbratY/Desktop/JALDRISHTI%20AI/data/manifests/hydrology_datasets.yaml).
- **Anti-Leakage Rule:** Future rating curve revisions are never applied retroactively to historical hindcasts.
