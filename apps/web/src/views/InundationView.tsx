import React, { useState } from 'react';
import { MapPin, Sliders, Layers, Eye, ShieldCheck, BarChart2 } from 'lucide-react';
import { MapComponent } from '../components/MapComponent';
import { DataProvenanceDrawer } from '../components/DataProvenanceDrawer';
import { InundationEvolutionCard } from '../components/InundationEvolutionCard';
import { ProvenanceMetadata } from '../types';

export const InundationView: React.FC = () => {
  const [leadTime, setLeadTime] = useState<number>(12);
  const [rainScenario, setRainScenario] = useState<number>(140);
  const [stageSurge, setStageSurge] = useState<number>(0.8);

  const provenance: ProvenanceMetadata = {
    source_id: "UNET_HYDRAULIC_SURROGATE",
    provider: "JALDRISHTI AI Hydraulic Modeling Core",
    product_name: "2D Physics-Guided Inundation Depth & Extent Surface",
    observed_at: new Date().toISOString(),
    received_at: new Date().toISOString(),
    source_latency_mins: 10.0,
    processing_version: "v1.0.0",
    model_version_id: "UNet-Surrogate-v3.1",
    is_simulation: true
  };

  // Calculate dynamic scenario inundation
  const totalInundated = (110.0 + (rainScenario - 100) * 0.45 + stageSurge * 55.0).toFixed(1);
  const depth0_30 = (parseFloat(totalInundated) * 0.35).toFixed(1);
  const depth30_100 = (parseFloat(totalInundated) * 0.40).toFixed(1);
  const depth1_2 = (parseFloat(totalInundated) * 0.18).toFixed(1);
  const depthGt2 = (parseFloat(totalInundated) * 0.07).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Phase 15: Live Inundation Evolution, Spatial Differencing & Asset Exposure Card */}
      <InundationEvolutionCard />

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold font-mono text-white flex items-center gap-2">
            <MapPin className="w-5 h-5 text-purple-400" />
            2D Physics-Guided Inundation Extent & Depth Classification
          </h2>
          <p className="text-xs text-slate-400">
            High-resolution hydrodynamic surrogate mapping coupled with Copernicus DEM slope and HAND terrain indices.
          </p>
        </div>
      </div>

      {/* Scenario Controls & Statistics Strip */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 font-mono text-xs">
        {/* Scenario Sliders */}
        <div className="glass-panel p-4 rounded-xl border border-surface-border space-y-3 lg:col-span-2">
          <div className="flex items-center justify-between text-slate-200 font-bold">
            <span className="flex items-center gap-1.5"><Sliders className="w-4 h-4 text-cyan-400" /> Scenario Stress Testing</span>
            <span className="text-[10px] text-cyan-300">Dynamic Inference</span>
          </div>

          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-[11px] text-slate-300 mb-1">
                <span>Catchment 24h Rainfall:</span>
                <span className="text-cyan-300 font-bold">{rainScenario} mm</span>
              </div>
              <input
                type="range"
                min="50"
                max="300"
                value={rainScenario}
                onChange={(e) => setRainScenario(Number(e.target.value))}
                className="w-full h-1.5 bg-surface rounded-lg appearance-none cursor-pointer accent-cyan-400"
              />
            </div>

            <div>
              <div className="flex justify-between text-[11px] text-slate-300 mb-1">
                <span>River Stage Surcharge above Bankfull:</span>
                <span className="text-rose-400 font-bold">+{stageSurge.toFixed(1)} m</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="2.5"
                step="0.1"
                value={stageSurge}
                onChange={(e) => setStageSurge(Number(e.target.value))}
                className="w-full h-1.5 bg-surface rounded-lg appearance-none cursor-pointer accent-rose-500"
              />
            </div>
          </div>
        </div>

        {/* Inundation Metrics Summary */}
        <div className="glass-panel p-4 rounded-xl border border-surface-border space-y-2">
          <div className="text-slate-400 text-[11px]">Total Inundated Footprint</div>
          <div className="text-2xl font-bold text-white font-mono">{totalInundated} <span className="text-xs font-normal text-slate-400">km²</span></div>
          <div className="text-[10px] text-slate-400">
            Flood Risk Probability: <span className="text-rose-400 font-semibold">86%</span>
          </div>
          <div className="text-[10px] text-emerald-400 flex items-center gap-1 mt-2">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Sentinel-1 SAR IoU: 0.84</span>
          </div>
        </div>

        {/* Depth Class Breakdown */}
        <div className="glass-panel p-4 rounded-xl border border-surface-border space-y-1.5 text-[11px]">
          <div className="text-slate-400 font-semibold mb-1">Depth Class Breakdown</div>
          <div className="flex justify-between items-center text-slate-300">
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded bg-amber-400"></span> 0.0–0.3m (Shallow):</span>
            <span className="font-bold text-white">{depth0_30} km²</span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded bg-orange-500"></span> 0.3–1.0m (Moderate):</span>
            <span className="font-bold text-white">{depth30_100} km²</span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded bg-rose-500"></span> 1.0–2.0m (Severe):</span>
            <span className="font-bold text-white">{depth1_2} km²</span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded bg-rose-800"></span> &gt;2.0m (Extreme):</span>
            <span className="font-bold text-white">{depthGt2} km²</span>
          </div>
        </div>
      </div>

      {/* Map Display */}
      <div className="space-y-2">
        <div className="flex items-center justify-between font-mono text-xs text-slate-400">
          <span>Surrogate Map Output • Valid at +{leadTime}h Lead</span>
          <span>Surrogate Resolution: 30m Grid</span>
        </div>
        <MapComponent heightClass="h-[520px]" showInundation={true} showAssets={true} />
      </div>

      <DataProvenanceDrawer provenance={provenance} />
    </div>
  );
};
