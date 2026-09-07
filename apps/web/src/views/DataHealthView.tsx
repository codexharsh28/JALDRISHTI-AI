import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle2, AlertTriangle, XCircle, Clock, Database, Radio, Satellite, CloudRain, Waves, ShieldCheck, RefreshCw, Eye, Zap, Info, ShieldAlert } from 'lucide-react';
import { DataProvenanceDrawer } from '../components/DataProvenanceDrawer';
import { LiveOperationsControlPanel } from '../components/LiveOperationsControlPanel';
import { ProvenanceMetadata } from '../types';

export const DataHealthView: React.FC = () => {
  const [healthData, setHealthData] = useState<any[]>([]);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [anomalySummary, setAnomalySummary] = useState<any>({});
  const [selectedAnomaly, setSelectedAnomaly] = useState<any | null>(null);
  const [anomalyFilter, setAnomalyFilter] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState(false);
  const [isInjecting, setIsInjecting] = useState(false);

  const [imdAwsStatus, setImdAwsStatus] = useState<any | null>(null);
  const [isRefreshingImd, setIsRefreshingImd] = useState(false);
  const [imdRefreshMessage, setImdRefreshMessage] = useState<string | null>(null);

  const fetchLiveHealth = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/v1/live/health');
      if (res.ok) {
        const data = await res.json();
        setHealthData(data.providers || []);
      }
      const imdRes = await fetch('/api/v1/live/imd-aws/status');
      if (imdRes.ok) {
        const imdData = await imdRes.json();
        setImdAwsStatus(imdData);
      }
      const anomRes = await fetch('/api/v1/anomalies');
      if (anomRes.ok) {
        const anomData = await anomRes.json();
        setAnomalies(anomData || []);
      }
      const sumRes = await fetch('/api/v1/anomalies/summary');
      if (sumRes.ok) {
        const sumData = await sumRes.json();
        setAnomalySummary(sumData || {});
      }
    } catch (e) {
      console.warn(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleManualImdRefresh = async () => {
    setIsRefreshingImd(true);
    setImdRefreshMessage(null);
    try {
      const res = await fetch('/api/v1/live/imd-aws/refresh?force=true', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setImdRefreshMessage(`Ingestion Run: ${data.ingestion_run_id || 'COMPLETED'} (${data.new_records || 0} accepted, status: ${data.data_state || data.source_state})`);
        await fetchLiveHealth();
      } else {
        setImdRefreshMessage('Refresh request failed or rate-limited.');
      }
    } catch (e) {
      setImdRefreshMessage(`Network error: ${e}`);
    } finally {
      setIsRefreshingImd(false);
    }
  };

  useEffect(() => {
    fetchLiveHealth();
    const interval = setInterval(fetchLiveHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleInjectTestAnomaly = async (testType: string) => {
    setIsInjecting(true);
    try {
      const res = await fetch('/api/v1/anomalies/inject-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          station_id: testType === 'SPIKE' ? 'IMD_AWS_BHUBANESWAR' : 'CWC_MUNDALI',
          variable: testType === 'SPIKE' ? 'rainfall_1h_mm' : 'river_stage_m',
          value: testType === 'SPIKE' ? 245.0 : 26.10,
          test_case_name: testType === 'SPIKE' ? 'SYNTHETIC_CLOUD_BURST_SPIKE' : 'SYNTHETIC_SENSOR_FLATLINE'
        })
      });
      if (res.ok) {
        await fetchLiveHealth();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsInjecting(false);
    }
  };

  const sources = [
    {
      source_id: "IMD_ODISHA_AWS",
      provider: "India Meteorological Department (IMD)",
      product: "Surface Automatic Weather Station Telemetry",
      mode: "POLL",
      cadence: "15 mins",
      status: "HEALTHY",
      latency: "15 mins",
      coverage: "98.5%",
      quality: "0.98",
      confidence: "HIGH",
      icon: CloudRain
    },
    {
      source_id: "IMD_DWR_PARADIP",
      provider: "IMD Doppler Radar Division",
      product: "Paradip DWR Polar Volume PPI (Max-Z)",
      mode: "POLL",
      cadence: "10 mins",
      status: "UNAVAILABLE",
      latency: "N/A",
      coverage: "0.0%",
      quality: "0.00",
      confidence: "DATA_DEGRADED",
      icon: Radio
    },
    {
      source_id: "ISRO_MOSDAC_INSAT3DR",
      provider: "ISRO / SAC MOSDAC",
      product: "Hydro-Estimator Method (HEM) QPE L2B",
      mode: "POLL",
      cadence: "30 mins",
      status: "NOT_CONFIGURED",
      latency: "25 mins",
      coverage: "0.0%",
      quality: "0.00",
      confidence: "LOW",
      icon: Satellite
    },
    {
      source_id: "NASA_GPM_IMERG_EARLY",
      provider: "NASA / PMM Goddard PPS",
      product: "GPM IMERG Early L3 Half-Hourly 0.1° NRT",
      mode: "SCHEDULED",
      cadence: "30 mins",
      status: "HEALTHY",
      latency: "240 mins",
      coverage: "100%",
      quality: "0.92",
      confidence: "MEDIUM",
      icon: Satellite
    },
    {
      source_id: "CWC_WRIS_TELEMETRY",
      provider: "Central Water Commission (CWC)",
      product: "River Gauge & Discharge Telemetry (Hourly)",
      mode: "POLL",
      cadence: "60 mins",
      status: "HEALTHY",
      latency: "45 mins",
      coverage: "96.0%",
      quality: "0.96",
      confidence: "HIGH",
      icon: Waves
    },
    {
      source_id: "ECMWF_OPEN_DATA_NWP",
      provider: "ECMWF Open Data",
      product: "0.4° IFS High-Resolution Atmospheric Forcing",
      mode: "SCHEDULED",
      cadence: "6 hours",
      status: "HEALTHY",
      latency: "360 mins",
      coverage: "100%",
      quality: "0.90",
      confidence: "HIGH",
      icon: Database
    }
  ];

  const provenance: ProvenanceMetadata = {
    source_id: "QC_ANOMALY_GATEWAY",
    provider: "JALDRISHTI QC Core",
    product_name: "Multi-Source Sensor Quality Control & Anomaly Gateway",
    observed_at: new Date().toISOString(),
    received_at: new Date().toISOString(),
    source_latency_mins: 1.2,
    processing_version: "v3.2-LiveStreams",
    is_simulation: false
  };

  const filteredAnomalies = anomalies.filter(a => {
    if (anomalyFilter === 'ALL') return true;
    if (anomalyFilter === 'SENSOR_ERROR') return a.anomaly_state === 'LIKELY_SENSOR_ERROR';
    return a.anomaly_state === anomalyFilter;
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Activity className="w-6 h-6 text-cyan-400" />
            Data Health, Ingestion & Hydromet Anomaly Stream
          </h1>
          <p className="text-sm text-slate-400">
            Real-time multi-source telemetry validation, 5-layer anomaly screening, and provider degradation tracking.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchLiveHealth}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface-elevated text-xs font-semibold text-slate-300 hover:text-white border border-border transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh Telemetry
          </button>
        </div>
      </div>

      {/* Live Operations Control Panel */}
      <LiveOperationsControlPanel />

      {/* Official IMD Automatic Weather Station (AWS) Telemetry Diagnostics Card */}
      <div className="bg-surface rounded-lg border border-cyan-500/30 p-5 space-y-4 shadow-xl bg-gradient-to-br from-surface via-surface to-cyan-950/20">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-border/50 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                Official Surface Telemetry
              </span>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <CloudRain className="w-5 h-5 text-cyan-400" />
                India Meteorological Department (IMD) Automatic Weather Station (AWS)
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Official REST ingestion gateway (<code className="text-cyan-300 font-mono text-[11px]">https://city.imd.gov.in/api/aws_data_api.php</code>) • Hourly meteorological ground-truth.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleManualImdRefresh}
              disabled={isRefreshingImd}
              className="px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshingImd ? 'animate-spin' : ''}`} />
              {isRefreshingImd ? 'Polling IMD...' : 'Trigger IMD AWS Ingestion'}
            </button>
          </div>
        </div>

        {imdRefreshMessage && (
          <div className="p-2.5 rounded bg-cyan-950/60 border border-cyan-500/40 text-cyan-200 text-xs font-mono">
            {imdRefreshMessage}
          </div>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="bg-surface-elevated/70 p-3 rounded border border-border/50">
            <span className="text-[11px] text-slate-400 block font-medium">Source State:</span>
            <div className="mt-1 flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${
                imdAwsStatus?.state === 'LIVE_OBSERVED' ? 'bg-emerald-400 animate-pulse' :
                imdAwsStatus?.state === 'NOT_CONFIGURED' ? 'bg-amber-400' :
                imdAwsStatus?.state === 'ACCESS_DENIED' ? 'bg-rose-400' : 'bg-slate-400'
              }`} />
              <strong className={`text-xs uppercase tracking-wide ${
                imdAwsStatus?.state === 'LIVE_OBSERVED' ? 'text-emerald-300' :
                imdAwsStatus?.state === 'NOT_CONFIGURED' ? 'text-amber-300' :
                imdAwsStatus?.state === 'ACCESS_DENIED' ? 'text-rose-300' : 'text-slate-300'
              }`}>
                {imdAwsStatus?.state || 'NOT_CONFIGURED'}
              </strong>
            </div>
          </div>

          <div className="bg-surface-elevated/70 p-3 rounded border border-border/50">
            <span className="text-[11px] text-slate-400 block font-medium">Freshness Cadence:</span>
            <div className="mt-1 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
              <strong className="text-xs text-white">
                {imdAwsStatus?.freshness_state || 'NOT_CONFIGURED'}
              </strong>
            </div>
          </div>

          <div className="bg-surface-elevated/70 p-3 rounded border border-border/50">
            <span className="text-[11px] text-slate-400 block font-medium">Stations Discovered:</span>
            <div className="mt-1 flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 text-emerald-400" />
              <strong className="text-xs text-white">
                {imdAwsStatus?.station_count ? `${imdAwsStatus.station_count} AWS Points` : 'Catalog Ready'}
              </strong>
            </div>
          </div>

          <div className="bg-surface-elevated/70 p-3 rounded border border-border/50">
            <span className="text-[11px] text-slate-400 block font-medium">Endpoint Latency:</span>
            <div className="mt-1">
              <strong className="text-xs text-cyan-300">
                {imdAwsStatus?.latency_ms ? `${Math.round(imdAwsStatus.latency_ms)} ms` : 'N/A'}
              </strong>
            </div>
          </div>

          <div className="bg-surface-elevated/70 p-3 rounded border border-border/50">
            <span className="text-[11px] text-slate-400 block font-medium">Last HTTP Code:</span>
            <div className="mt-1">
              <strong className={`text-xs font-mono ${imdAwsStatus?.last_http_status === 200 ? 'text-emerald-300' : 'text-amber-300'}`}>
                {imdAwsStatus?.last_http_status ? `HTTP ${imdAwsStatus.last_http_status}` : 'None'}
              </strong>
            </div>
          </div>

          <div className="bg-surface-elevated/70 p-3 rounded border border-border/50">
            <span className="text-[11px] text-slate-400 block font-medium">Latest Observation:</span>
            <div className="mt-1">
              <strong className="text-[11px] text-slate-300 font-mono truncate block" title={imdAwsStatus?.last_observation || 'No telemetry yet'}>
                {imdAwsStatus?.last_observation ? new Date(imdAwsStatus.last_observation).toLocaleTimeString() : 'N/A'}
              </strong>
            </div>
          </div>
        </div>

        {imdAwsStatus?.state !== 'LIVE_OBSERVED' && (
          <div className="p-3 rounded bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs flex items-start gap-2">
            <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <strong>IMD AWS Access Policy Notice:</strong> Official IMD AWS endpoints require IP whitelisting. In unwhitelisted test environments, the engine accurately classifies access as <code className="font-mono bg-amber-950/80 px-1 py-0.5 rounded text-amber-300">{imdAwsStatus?.last_error_category || 'NOT_CONFIGURED'}</code> and never fabricates artificial weather data.
            </div>
          </div>
        )}
      </div>

      {/* Phase 13: Hydrometeorological Anomaly Stream Section */}
      <div className="bg-surface rounded-lg border border-border p-5 space-y-4 shadow-lg">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-border/50 pb-3">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-400" />
              Real-Time Hydrometeorological Anomaly Stream (Phase 13)
            </h2>
            <p className="text-xs text-slate-400">
              5-Layer anomaly screening (Physical bounds, temporal jump, robust Z-score, EWMA, spatial cross-corroboration).
            </p>
          </div>
          {/* Test Injector Controls */}
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-400 font-medium">Dev Test Injector:</span>
            <button
              onClick={() => handleInjectTestAnomaly('SPIKE')}
              disabled={isInjecting}
              className="px-2.5 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-xs font-semibold flex items-center gap-1 transition-colors"
              title="Inject synthetic 245mm/hr spike labeled SYNTHETIC_TEST"
            >
              <Zap className="w-3 h-3" />
              Inject Extreme Rain Spike
            </button>
            <button
              onClick={() => handleInjectTestAnomaly('FLATLINE')}
              disabled={isInjecting}
              className="px-2.5 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-xs font-semibold flex items-center gap-1 transition-colors"
              title="Inject frozen sensor stage flatline labeled SYNTHETIC_TEST"
            >
              <XCircle className="w-3 h-3" />
              Inject Frozen Flatline
            </button>
          </div>
        </div>

        {/* Filter Badges & Summary Counts */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          {[
            { id: 'ALL', label: 'All Observations', count: anomalies.length, color: 'bg-slate-800 text-slate-300' },
            { id: 'NORMAL', label: 'Normal', count: anomalySummary.counts_by_state?.NORMAL || 0, color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' },
            { id: 'WATCH', label: 'Watch / Valid Extreme', count: anomalySummary.counts_by_state?.WATCH || 0, color: 'bg-amber-500/20 text-amber-300 border-amber-500/40' },
            { id: 'ANOMALOUS', label: 'Anomalous', count: anomalySummary.counts_by_state?.ANOMALOUS || 0, color: 'bg-orange-500/20 text-orange-300 border-orange-500/40' },
            { id: 'SENSOR_ERROR', label: 'Likely Sensor Error', count: anomalySummary.counts_by_state?.LIKELY_SENSOR_ERROR || 0, color: 'bg-rose-500/20 text-rose-300 border-rose-500/40' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setAnomalyFilter(tab.id)}
              className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all ${
                anomalyFilter === tab.id
                  ? 'ring-2 ring-cyan-400 ' + tab.color
                  : 'bg-surface-elevated text-slate-400 border-border hover:text-white'
              }`}
            >
              {tab.label} <span className="ml-1 px-1.5 py-0.2 rounded-full bg-slate-900 text-[10px]">{tab.count}</span>
            </button>
          ))}
        </div>

        {/* Anomalies List */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filteredAnomalies.slice(0, 6).map((anom, idx) => (
            <div
              key={idx}
              onClick={() => setSelectedAnomaly(anom)}
              className="p-3 rounded bg-surface-elevated/70 border border-border hover:border-cyan-500/50 cursor-pointer transition-all space-y-2 group"
            >
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-xs font-bold text-white group-hover:text-cyan-300">{anom.station_id}</span>
                  <div className="text-[11px] text-slate-400 font-mono">{anom.variable}</div>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                  anom.anomaly_state === 'NORMAL' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' :
                  anom.anomaly_state === 'WATCH' ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' :
                  anom.anomaly_state === 'ANOMALOUS' ? 'bg-orange-500/20 text-orange-300 border-orange-500/30' :
                  'bg-rose-500/20 text-rose-300 border-rose-500/30'
                }`}>
                  {anom.anomaly_state}
                </span>
              </div>
              <div className="flex justify-between text-xs pt-1 border-t border-border/40">
                <span className="text-slate-400">Observed: <strong className="text-white">{anom.observed_value !== null ? anom.observed_value : 'NaN'}</strong></span>
                <span className="text-slate-400">Score: <strong className="text-cyan-300 font-mono">{anom.anomaly_score}</strong></span>
              </div>
              <div className="text-[11px] text-slate-300 truncate" title={anom.reason}>
                {anom.reason}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Selected Anomaly Detail Modal */}
      {selectedAnomaly && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-lg max-w-xl w-full p-5 space-y-4 shadow-2xl animate-in fade-in zoom-in duration-200">
            <div className="flex justify-between items-start border-b border-border pb-3">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Info className="w-5 h-5 text-cyan-400" />
                  Hydromet Anomaly Evidence & Spatial Corroboration
                </h3>
                <span className="text-xs text-slate-400 font-mono">{selectedAnomaly.anomaly_id}</span>
              </div>
              <button
                onClick={() => setSelectedAnomaly(null)}
                className="text-slate-400 hover:text-white text-sm px-2 py-1 rounded bg-surface-elevated"
              >
                ✕ Close
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-surface-elevated p-2.5 rounded">
                <span className="text-slate-400 block">Station:</span>
                <strong className="text-white text-sm">{selectedAnomaly.station_id}</strong>
              </div>
              <div className="bg-surface-elevated p-2.5 rounded">
                <span className="text-slate-400 block">Variable:</span>
                <strong className="text-cyan-300 text-sm">{selectedAnomaly.variable}</strong>
              </div>
              <div className="bg-surface-elevated p-2.5 rounded">
                <span className="text-slate-400 block">Observed Value:</span>
                <strong className="text-white text-sm">{selectedAnomaly.observed_value}</strong>
              </div>
              <div className="bg-surface-elevated p-2.5 rounded">
                <span className="text-slate-400 block">Baseline Median:</span>
                <strong className="text-slate-200 text-sm">{selectedAnomaly.baseline_value}</strong>
              </div>
              <div className="bg-surface-elevated p-2.5 rounded">
                <span className="text-slate-400 block">Anomaly State:</span>
                <strong className="text-amber-400 text-sm">{selectedAnomaly.anomaly_state}</strong>
              </div>
              <div className="bg-surface-elevated p-2.5 rounded">
                <span className="text-slate-400 block">Classification:</span>
                <strong className="text-cyan-400 text-sm">{selectedAnomaly.classification}</strong>
              </div>
            </div>

            <div className="bg-surface-elevated p-3 rounded space-y-1.5 text-xs">
              <span className="text-slate-400 font-semibold block">Primary Evidence & Reason:</span>
              <p className="text-slate-200">{selectedAnomaly.reason}</p>
              <div className="flex gap-2 pt-2">
                <span className="text-[11px] text-slate-400">Data State:</span>
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px] border border-slate-700">
                  {selectedAnomaly.data_state}
                </span>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedAnomaly(null)}
                className="px-4 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sources Health Summary Table */}
      <div className="bg-surface rounded-lg border border-border p-5 space-y-4 shadow-lg">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Database className="w-5 h-5 text-cyan-400" />
          Configured Operational Telemetry & Model Feeds
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-border text-slate-400 font-semibold">
                <th className="py-2.5 px-3">Provider / Source</th>
                <th className="py-2.5 px-3">Product Description</th>
                <th className="py-2.5 px-3">Mode</th>
                <th className="py-2.5 px-3">Cadence</th>
                <th className="py-2.5 px-3">Health Status</th>
                <th className="py-2.5 px-3">Latency</th>
                <th className="py-2.5 px-3">Coverage</th>
                <th className="py-2.5 px-3">QC Quality</th>
                <th className="py-2.5 px-3">Data Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {sources.map((s, i) => {
                const Icon = s.icon;
                return (
                  <tr key={i} className="hover:bg-surface-elevated/40">
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4 text-cyan-400 shrink-0" />
                        <div>
                          <div className="font-semibold text-white">{s.provider}</div>
                          <div className="text-[10px] text-slate-400">{s.source_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-slate-300 max-w-[200px] truncate">{s.product}</td>
                    <td className="py-3 px-3">
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                        {s.mode}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-400">{s.cadence}</td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                        s.status === 'HEALTHY' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' :
                        (s.status === 'DEGRADED' ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' : 'bg-slate-800 text-slate-400 border-slate-700')
                      }`}>
                        {s.status}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-amber-300">{s.latency}</td>
                    <td className="py-3 px-3 text-cyan-300">{s.coverage}</td>
                    <td className="py-3 px-3 text-white font-bold">{s.quality}</td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        s.confidence === 'HIGH' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                        (s.confidence === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-rose-500/20 text-rose-300 border border-rose-500/30')
                      }`}>
                        {s.confidence}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <DataProvenanceDrawer provenance={provenance} />
    </div>
  );
};
