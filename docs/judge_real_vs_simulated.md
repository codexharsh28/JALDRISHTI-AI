# JALDRISHTI AI — Judge Reference: Real vs. Simulated Cheat Sheet

## One-Line Truth per Subsystem

- **IMD AWS**: Official observed telemetry (`https://city.imd.gov.in/api/aws_data_api.php`) — reports `LIVE_OBSERVED` or `NOT_CONFIGURED` depending on verified IP whitelisting; never fabricates fake observations.
- **CWC Gauges**: Ground-truth river stage observations where telemetry feeds are connected; compared against official government warning/danger marks.
- **GloFAS Fallback**: Modeled ECMWF/Copernicus global river discharge — always tagged `MODELED_GLOFAS`, never claimed as observed telemetry.
- **NASA IMERG**: NRT satellite precipitation product (0.1° half-hourly) with ~4h operational latency.
- **ISRO INSAT-3DR**: Geostationary infrared precipitation estimates (HEM L2B).
- **Paradip Doppler Radar**: Polar volume Max-Z PPI reflectivity — clearly marked `UNAVAILABLE` when sensor feed is offline.
- **Computational Grid (2.5 km)**: Fused multi-source numerical modeling grid — explicitly distinguished from native sensor resolutions.
- **ConvLSTM Nowcaster**: Genuine PyTorch recurrent convolutional neural network — only labeled `RAIN_L3_CONVLSTM` when active model weights execute.
- **Inundation Extent**: Physics-guided HAND 2D simulation — spatial extent validated against Sentinel-1 SAR overpasses (IoU / F1 / CSI).
- **Inundation Depth**: Depth labeled `MODEL_ESTIMATE`; depth validation declared `UNAVAILABLE` as SAR does not measure water column thickness.
- **Population Exposure**: Labeled `ESTIMATED POPULATION EXPOSURE` derived from WorldPop 100m gridded distributions.
- **Risk Score Attribution**: Mathematical sensitivity decomposition explaining why risk changed — no arbitrary fake percentages.
- **Emergency Alerts**: Red / Critical alerts are safety-gated by mandatory human operator review; no raw ML directly sends public alerts.
- **Citizen Notifications**: Point-in-polygon geofenced delivery (HOME/WORK/FAMILY) to affected residents; isolates test SMS to `MockSMSSink`.
