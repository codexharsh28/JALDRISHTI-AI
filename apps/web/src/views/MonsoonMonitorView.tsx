import React from 'react';
import { CloudRain, Wind, Gauge, Sun, Thermometer, Compass, CloudLightning, Satellite } from 'lucide-react';
import { DataProvenanceDrawer } from '../components/DataProvenanceDrawer';
import { ProvenanceMetadata } from '../types';

export const MonsoonMonitorView: React.FC = () => {
  const provenance: ProvenanceMetadata = {
    source_id: "SYNOPTIC_MET_FUSION",
    provider: "IMD Synoptic & ECMWF Open Data NWP Blend",
    product_name: "Regional Atmospheric Dynamics & Convective Precursors",
    observed_at: new Date().toISOString(),
    received_at: new Date().toISOString(),
    source_latency_mins: 15.0,
    processing_version: "v1.0.0",
    is_simulation: true
  };

  const nwpHorizons = [
    { lead: "+6h", precip: "48.5 mm", wind: "14.2 m/s", t2m: "27.5°C", cape: "2400 J/kg", rh: "94%" },
    { lead: "+12h", precip: "95.0 mm", wind: "16.5 m/s", t2m: "26.8°C", cape: "2850 J/kg", rh: "96%" },
    { lead: "+24h", precip: "172.0 mm", wind: "18.0 m/s", t2m: "26.0°C", cape: "2200 J/kg", rh: "98%" },
    { lead: "+48h", precip: "245.0 mm", wind: "12.0 m/s", t2m: "28.2°C", cape: "1500 J/kg", rh: "90%" },
    { lead: "+72h", precip: "278.0 mm", wind: "8.5 m/s", t2m: "29.5°C", cape: "800 J/kg", rh: "82%" }
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold font-mono text-white flex items-center gap-2">
            <CloudRain className="w-5 h-5 text-cyan-400" />
            Monsoon & Numerical Weather Prediction (NWP) Synoptic Monitor
          </h2>
          <p className="text-xs text-slate-400">
            Regional atmospheric circulation, Bay of Bengal depression tracks, and ECMWF/GFS ensemble guidance.
          </p>
        </div>
        <span className="px-2.5 py-1 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 text-xs font-mono">
          Synoptic Stage: Deep Convective Landfall
        </span>
      </div>

      {/* Atmospheric Indices Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs">
        <div className="glass-panel p-4 rounded-xl border border-surface-border">
          <div className="text-slate-400 flex items-center justify-between mb-1">
            <span>MSLP Central Pressure</span>
            <Gauge className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-white">996.4 <span className="text-xs font-normal text-slate-400">hPa</span></div>
          <div className="text-[10px] text-amber-400 mt-1">Deep Depression (-8.5 hPa anomaly)</div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-surface-border">
          <div className="text-slate-400 flex items-center justify-between mb-1">
            <span>Convective Instability (CAPE)</span>
            <CloudLightning className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400">2,850 <span className="text-xs font-normal text-slate-400">J/kg</span></div>
          <div className="text-[10px] text-rose-400 mt-1">High Severe Thunderstorm Potential</div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-surface-border">
          <div className="text-slate-400 flex items-center justify-between mb-1">
            <span>Precipitable Water (PWAT)</span>
            <CloudRain className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-sky-400">68.2 <span className="text-xs font-normal text-slate-400">mm</span></div>
          <div className="text-[10px] text-sky-300 mt-1">98th percentile tropical moisture</div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-surface-border">
          <div className="text-slate-400 flex items-center justify-between mb-1">
            <span>INSAT Cloud Top Temp</span>
            <Satellite className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-300">-64.8 <span className="text-xs font-normal text-slate-400">°C</span></div>
          <div className="text-[10px] text-purple-400 mt-1">Deep Convective Overshooting Top</div>
        </div>
      </div>

      {/* NWP Horizon Table */}
      <div className="glass-panel rounded-xl border border-surface-border p-4 space-y-3">
        <h3 className="text-sm font-semibold font-mono text-slate-200">
          ECMWF / Open Data NWP Horizon Projections (Mahanadi Catchment Mean)
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono text-left border-collapse">
            <thead>
              <tr className="border-b border-surface-border text-slate-400 text-[11px]">
                <th className="py-2.5 px-3">Horizon</th>
                <th className="py-2.5 px-3">Cumulative Precip</th>
                <th className="py-2.5 px-3">Wind Speed (10m)</th>
                <th className="py-2.5 px-3">2m Temp</th>
                <th className="py-2.5 px-3">CAPE</th>
                <th className="py-2.5 px-3">Relative Humidity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border/40 text-slate-300">
              {nwpHorizons.map((row, i) => (
                <tr key={i} className="hover:bg-surface-elevated/40">
                  <td className="py-2.5 px-3 font-bold text-cyan-300">{row.lead}</td>
                  <td className="py-2.5 px-3 font-semibold text-white">{row.precip}</td>
                  <td className="py-2.5 px-3">{row.wind}</td>
                  <td className="py-2.5 px-3">{row.t2m}</td>
                  <td className="py-2.5 px-3 text-amber-300">{row.cape}</td>
                  <td className="py-2.5 px-3">{row.rh}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <DataProvenanceDrawer provenance={provenance} />
    </div>
  );
};
