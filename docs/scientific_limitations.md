# Scientific Assumptions & Technical Limitations Register
## JALDRISHTI AI (SIH26071)

---

## 1. Primary Scientific Assumptions

1. **Topographic HAND Surrogate:** The 2D flood depth surrogate assumes floodwater accumulates in topographic depressions constrained by HAND (Height Above Nearest Drainage) index and Copernicus DEM slope. It approximates 2D hydrodynamic wave attenuation without solving full 2D Saint-Venant shallow water equations at 1m resolution in real time.
2. **Atmospheric Motion Extrapolation:** ConvLSTM nowcasting assumes cloud advection and storm growth follow learned spatio-temporal dynamics over 0–6 hour windows. Convective storm initiation past 3 hours retains higher epistemic uncertainty.
3. **Rating Curve Stability:** Stage-to-discharge calculations assume stable river bathymetry without major dynamic channel scouring or catastrophic embankment breaches unless explicitly parameterized.

---

## 2. Institutional & Data Access Limitations

1. **Non-Public High-Frequency Radar Archives:** Multi-year polar volume archives for Paradip DWR are maintained internally by IMD and are not public time-series. Radar validation is conducted on standardized convective storm events.
2. **ECMWF Historical Forecasts:** ECMWF Open Data provides rolling real-time forecasts. Multi-year operational forecast hindcasting requires institutional MARS/TIGGE access.
3. **CWC Station Telemetry:** Real-time bulletins provide current flood marks; full historical sub-hourly telemetry archives require CWC/India-WRIS institutional research authorization.
