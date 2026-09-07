import React from 'react';
import { Network, ArrowRight, ShieldCheck, Database, Cpu, Radio, Waves, MapPin, BellRing, CheckCircle2 } from 'lucide-react';
import { DataProvenanceDrawer } from '../components/DataProvenanceDrawer';

export const ArchitectureView: React.FC = () => {
  const pipelineStages = [
    {
      step: "01",
      title: "Data Ingestion & Adapters",
      desc: "Provider-agnostic connectors for IMD AWS/ARG, Paradip Doppler Radar, INSAT-3DR MOSDAC, NASA GPM IMERG, ECMWF NWP, CWC river telemetry, Copernicus DEM, Sentinel-1 SAR, and WorldPop.",
      icon: Database
    },
    {
      step: "02",
      title: "Deterministic Quality Control",
      desc: "Pre-inference physical bounds verification, spike detection, coordinate validation, staleness filters, and quality flags (GOOD, SUSPECT, BAD, MISSING, STALE, ESTIMATED).",
      icon: ShieldCheck
    },
    {
      step: "03",
      title: "Multi-Source Precipitation Fusion",
      desc: "Quality-weighted fusion with gauge bias correction and uncertainty quantification across radar, satellite, and ground telemetry.",
      icon: Radio
    },
    {
      step: "04",
      title: "0–6h Nowcast & 6–72h Hydrograph",
      desc: "Hierarchical ML suite: Persistence (L0), Semi-Lagrangian Advection (L1), XGBoost (L2), and Deep ConvLSTM (L3) nowcasting coupled with LSTM River Network Graph streamflow.",
      icon: Cpu
    },
    {
      step: "05",
      title: "Physics-Guided Inundation & Depth",
      desc: "Hydrodynamic surrogate model predicting flood probability and 4 depth classifications (0-0.3m, 0.3-1m, 1-2m, >2m) using HAND and DEM slope features.",
      icon: MapPin
    },
    {
      step: "06",
      title: "Impact Assessment & Alert Decision",
      desc: "Spatial intersection with population grids and critical infrastructure, SHAP explainability ('Why did risk change?'), and human-review gated alerts.",
      icon: BellRing
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold font-mono text-white flex items-center gap-2">
            <Network className="w-5 h-5 text-cyan-400" />
            End-to-End Hydrometeorological Intelligence Architecture
          </h2>
          <p className="text-xs text-slate-400">
            System pipeline architecture from multi-sensor observation to decision support and mission replay.
          </p>
        </div>
      </div>

      {/* Pipeline Flow Steps */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 font-mono text-xs">
        {pipelineStages.map((stage) => {
          const Icon = stage.icon;
          return (
            <div key={stage.step} className="glass-panel p-5 rounded-xl border border-surface-border space-y-2 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold font-mono text-cyan-500/40">#{stage.step}</span>
                <Icon className="w-5 h-5 text-cyan-400" />
              </div>
              <h3 className="text-sm font-bold text-white mt-1">{stage.title}</h3>
              <p className="text-xs text-slate-300 font-sans leading-relaxed">{stage.desc}</p>
            </div>
          );
        })}
      </div>

      {/* Core Engineering Principles */}
      <div className="glass-panel p-5 rounded-xl border border-surface-border space-y-3 font-mono text-xs">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          Core Engineering & Scientific Principles
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-slate-300 font-sans text-xs">
          <div className="p-3 rounded-lg bg-surface/70 border border-surface-border">
            <b className="text-cyan-300 font-mono block mb-1">1. Data Quality as a First-Class Feature</b>
            Sensor health, staleness, and missingness directly modulate model uncertainty and alert confidence.
          </div>
          <div className="p-3 rounded-lg bg-surface/70 border border-surface-border">
            <b className="text-cyan-300 font-mono block mb-1">2. Model vs Data Confidence Separation</b>
            Sensor degradation never silently reduces model spread; degraded feeds trigger clear fallback indicators.
          </div>
          <div className="p-3 rounded-lg bg-surface/70 border border-surface-border">
            <b className="text-cyan-300 font-mono block mb-1">3. Causal & Topographic Coupling</b>
            River routing respects directed catchment topology, and inundation surrogates use DEM/HAND constraints.
          </div>
          <div className="p-3 rounded-lg bg-surface/70 border border-surface-border">
            <b className="text-cyan-300 font-mono block mb-1">4. Auditable Reproducibility</b>
            Every single forecast contains Run ID, input timestamps, model versions, and hash provenance.
          </div>
        </div>
      </div>
    </div>
  );
};
