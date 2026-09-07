import React, { useState } from 'react';
import { HelpCircle, ChevronUp, ChevronDown } from 'lucide-react';
import { MapLayerConfig } from '../../types/map';

interface Props {
  layers: MapLayerConfig[];
}

export const MapLegendPanel: React.FC<Props> = ({ layers }) => {
  const [isOpen, setIsOpen] = useState(true);

  const isLayerActive = (id: string) => layers.some(l => l.id === id && l.enabled);

  return (
    <div className="absolute bottom-24 right-4 z-[500] max-w-xs w-72 font-mono text-[11px]">
      <div className="glass-panel border border-surface-border rounded-xl shadow-2xl backdrop-blur-md overflow-hidden">
        {/* Header */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-3 py-2 bg-surface-base/80 flex items-center justify-between hover:bg-surface-border/30 transition-colors border-b border-surface-border/40"
        >
          <span className="font-bold text-slate-200 flex items-center gap-1.5">
            <HelpCircle className="w-3.5 h-3.5 text-cyan-400" />
            Scientific Legend
          </span>
          {isOpen ? <ChevronDown className="w-3.5 h-3.5 text-slate-400" /> : <ChevronUp className="w-3.5 h-3.5 text-slate-400" />}
        </button>

        {isOpen && (
          <div className="p-3 space-y-3 max-h-64 overflow-y-auto">
            {/* 1. Rainfall Intensity Grid (mm/h) */}
            {(isLayerActive('RAINFALL_FUSED') || isLayerActive('RAINFALL_NOWCAST')) && (
              <div className="space-y-1">
                <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                  Rainfall Rate (mm/h) — 2.5km Model Grid
                </div>
                <div className="grid grid-cols-4 gap-1 text-[9px] text-center text-slate-300 font-bold">
                  <div className="p-1 rounded bg-blue-500/40 border border-blue-400/50">0–15<br/><span className="text-[8px] font-normal">Light</span></div>
                  <div className="p-1 rounded bg-emerald-500/50 border border-emerald-400/50">15–35<br/><span className="text-[8px] font-normal">Moderate</span></div>
                  <div className="p-1 rounded bg-amber-500/60 border border-amber-400/60 text-amber-100">35–65<br/><span className="text-[8px] font-normal">Heavy</span></div>
                  <div className="p-1 rounded bg-rose-600/70 border border-rose-400/70 text-rose-100">&gt;65<br/><span className="text-[8px] font-normal">Extreme</span></div>
                </div>
              </div>
            )}

            {/* 2. Inundation Depth Classes */}
            {(isLayerActive('FLOOD_DEPTH') || isLayerActive('INUNDATION_PROBABILITY')) && (
              <div className="space-y-1">
                <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                  HAND Hydraulic Flood Depth (meters)
                </div>
                <div className="grid grid-cols-4 gap-1 text-[9px] text-center text-slate-300 font-bold">
                  <div className="p-1 rounded bg-cyan-400/30 border border-cyan-400/50">0–0.3m<br/><span className="text-[8px] font-normal">Ankle</span></div>
                  <div className="p-1 rounded bg-cyan-500/50 border border-cyan-400/60">0.3–1m<br/><span className="text-[8px] font-normal">Knee/Waist</span></div>
                  <div className="p-1 rounded bg-blue-600/70 border border-blue-400/70 text-blue-100">1–2m<br/><span className="text-[8px] font-normal">Severe</span></div>
                  <div className="p-1 rounded bg-indigo-900/90 border border-indigo-400 text-indigo-100">&gt;2m<br/><span className="text-[8px] font-normal">Critical</span></div>
                </div>
              </div>
            )}

            {/* 3. Alert Severity Zones */}
            {isLayerActive('ALERT_ZONES') && (
              <div className="space-y-1">
                <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                  Early Warning Alert Severity
                </div>
                <div className="grid grid-cols-4 gap-1 text-[9px] text-center font-bold">
                  <div className="p-1 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">GREEN</div>
                  <div className="p-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">YELLOW</div>
                  <div className="p-1 rounded bg-orange-500/20 text-orange-300 border border-orange-500/40">ORANGE</div>
                  <div className="p-1 rounded bg-rose-500/30 text-rose-300 border border-rose-500/50 animate-pulse">RED*</div>
                </div>
                <div className="text-[8px] text-slate-500 italic">*RED alert requires human officer verification sign-off.</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
