import React, { useState } from 'react';
import { Database, FileCheck, ShieldCheck, ChevronDown, ChevronUp, Cpu, Clock, Layers } from 'lucide-react';
import { ProvenanceMetadata } from '../types';

interface Props {
  provenance?: ProvenanceMetadata;
}

export const DataProvenanceDrawer: React.FC<Props> = ({ provenance }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!provenance) return null;

  return (
    <div className="glass-panel rounded-lg border border-surface-border p-3 mt-4 text-xs font-mono">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-slate-300 hover:text-cyan-300 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-cyan-400" />
          <span className="font-semibold text-slate-200">Data Provenance & Model Audit Record</span>
          {provenance.is_simulation && (
            <span className="px-1.5 py-0.2 rounded text-[9px] bg-purple-500/20 text-purple-300 border border-purple-500/30">
              SIMULATION
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-slate-500 text-[10px] hidden sm:inline">{provenance.source_id}</span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {isOpen && (
        <div className="mt-3 pt-3 border-t border-surface-border/60 grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px] text-slate-300">
          <div className="space-y-1">
            <div className="text-slate-500 flex items-center gap-1">
              <Layers className="w-3 h-3 text-slate-400" /> Source & Provider
            </div>
            <div className="text-white font-medium">{provenance.provider}</div>
            <div className="text-slate-400 text-[10px]">{provenance.product_name}</div>
          </div>

          <div className="space-y-1">
            <div className="text-slate-500 flex items-center gap-1">
              <Clock className="w-3 h-3 text-slate-400" /> Timestamps & Latency
            </div>
            <div>Observed: <span className="text-white">{new Date(provenance.observed_at).toLocaleTimeString()}</span></div>
            <div>Latency: <span className="text-amber-300">{provenance.source_latency_mins} mins</span></div>
          </div>

          <div className="space-y-1">
            <div className="text-slate-500 flex items-center gap-1">
              <Cpu className="w-3 h-3 text-slate-400" /> Model Pipeline
            </div>
            <div>Model Version: <span className="text-cyan-300">{provenance.model_version_id || "v1.0-standard"}</span></div>
            <div>Processing Engine: <span className="text-slate-200">{provenance.processing_version}</span></div>
          </div>
        </div>
      )}
    </div>
  );
};
