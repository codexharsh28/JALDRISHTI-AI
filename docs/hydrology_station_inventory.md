# Hydrological Station Inventory & Flood Threshold Register
## JALDRISHTI AI (SIH26071)

---

## 1. Station Hydraulic Attributes & Safety Thresholds

All flood threshold elevations are referenced to Survey of India (SOI) Mean Sea Level (MSL) datums.

| Station ID | River Reach | Catchment Area ($\text{km}^2$) | Warning Level ($m$) | Danger Level ($m$) | Highest Flood Level (HFL, $m$) | Design Discharge Capacity ($\text{m}^3/\text{s}$) |
|---|---|---|---|---|---|---|
| `CWC_MUNDALI` | Mahanadi Main | 132,100 | 26.30 | 26.85 | 27.85 (2008) | 35,400 |
| `CWC_NARAJ` | Kathajodi | 132,100 | 25.41 | 26.41 | 27.10 (1982) | 22,600 |
| `CWC_TIKERPARA`| Middle Mahanadi | 124,450 | 69.50 | 70.80 | 72.85 (2001) | 42,500 |
| `CWC_KHAIRMAL` | Upper Mahanadi | 114,800 | 102.50 | 104.00 | 106.20 (2011) | 38,000 |
| `CWC_KANAS` | Daya Distributary | 2,150 | 4.80 | 5.50 | 6.12 (2020) | 1,850 |

---

## 2. Threshold Calibration Separation

Thresholds were calibrated using training/validation flood events only. Test partitions (`EVT-MAHANADI-2022-08`, `EVT-MAHANADI-2024-08`) were untouched during threshold and rating curve parameter calibration.
