import React, { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  ShieldAlert,
  Clock,
  Zap,
  Info,
  ChevronRight,
  Database,
  CloudRain,
  Waves,
  Home,
  CheckCircle2
} from 'lucide-react';

interface Contributor {
  factor_name: string;
  delta_score: number;
  direction: string;
  category: string;
  evidence_value: any;
  baseline_value?: any;
  explanation: string;
}

interface RiskStateProps {
  risk_score: number;
  previous_risk_score: number;
  risk_level: string;
  risk_change: number;
  is_material_change: boolean;
  top_causal_summary: string;
  contributors: Contributor[];
  forecast_run_id?: string;
  data_confidence?: string;
  timestamp?: string;
}

interface Props {
  riskState: RiskStateProps;
  riskHistory?: any[];
  onTriggerRecalculate?: () => void;
}

export const WhyRiskChangedCard: React.FC<Props> = ({ riskState, riskHistory = [], onTriggerRecalculate }) => {
  const [showAllContributors, setShowAllContributors] = useState(false);
  const [selectedContributor, setSelectedContributor] = useState<Contributor | null>(null);

  const delta = riskState.risk_change ?? (riskState.risk_score - riskState.previous_risk_score);
  const isPositiveDelta = delta > 0;
  const isNegativeDelta = delta < 0;

  const getLevelColor = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40 ring-rose-500/30';
      case 'ALERT':
        return 'bg-orange-500/20 text-orange-300 border-orange-500/40 ring-orange-500/30';
      case 'WARNING':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40 ring-amber-500/30';
      case 'WATCH':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40 ring-yellow-500/30';
      default:
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 ring-emerald-500/30';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category?.toUpperCase()) {
      case 'PRECIPITATION':
        return <CloudRain className="w-3.5 h-3.5 text-cyan-400" />;
      case 'HYDROLOGY':
        return <Waves className="w-3.5 h-3.5 text-sky-400" />;
      case 'INUNDATION':
        return <Home className="w-3.5 h-3.5 text-indigo-400" />;
      case 'CONFIDENCE':
        return <Database className="w-3.5 h-3.5 text-amber-400" />;
      default:
        return <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />;
    }
  };

  return (
    <div className="bg-[#0b1329] rounded-xl border border-slate-800/90 shadow-md p-4 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Why Did Risk Change? (Phase 14 Causal Attribution)
              </h3>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getLevelColor(riskState.risk_level)}`}>
                {riskState.risk_level || 'NORMAL'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Live causal decomposition of hydrometeorological risk dynamics & asset vulnerability shifts.
            </p>
          </div>
        </div>

        {/* Action / Run Provenance */}
        <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
          <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
            Run: {riskState.forecast_run_id || 'FR-LATEST'}
          </span>
          <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
            Conf: <strong className="text-emerald-400">{riskState.data_confidence || 'HIGH'}</strong>
          </span>
        </div>
      </div>

      {/* Main Score & Delta Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Current Score */}
        <div className="bg-surface-elevated/80 border border-border/80 rounded-lg p-3 flex flex-col justify-between">
          <span className="text-[11px] text-slate-400 font-medium">Composite Basin Risk</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-3xl font-black font-mono text-white tracking-tight">
              {riskState.risk_score?.toFixed(1) || '24.5'}
            </span>
            <span className="text-xs text-slate-400 font-mono">/ 100</span>
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            Previous: <span className="font-mono text-slate-300">{riskState.previous_risk_score?.toFixed(1) || '24.5'}</span>
          </div>
        </div>

        {/* Delta */}
        <div className="bg-surface-elevated/80 border border-border/80 rounded-lg p-3 flex flex-col justify-between">
          <span className="text-[11px] text-slate-400 font-medium">Material Risk Delta</span>
          <div className="flex items-center gap-2 mt-1">
            {isPositiveDelta ? (
              <div className="flex items-center gap-1 text-rose-400">
                <TrendingUp className="w-6 h-6" />
                <span className="text-2xl font-black font-mono">+{delta.toFixed(1)}</span>
              </div>
            ) : isNegativeDelta ? (
              <div className="flex items-center gap-1 text-emerald-400">
                <TrendingDown className="w-6 h-6" />
                <span className="text-2xl font-black font-mono">{delta.toFixed(1)}</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-slate-400">
                <span className="text-sm font-bold font-mono text-slate-300">NO MATERIAL CHANGE</span>
              </div>
            )}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            {riskState.is_material_change ? (
              <span className="text-amber-300 font-medium">● Material Shift Detected</span>
            ) : (
              <span className="text-slate-400">Stable Baseline State</span>
            )}
          </div>
        </div>

        {/* Top Causal Summary */}
        <div className="bg-surface-elevated/80 border border-border/80 rounded-lg p-3 flex flex-col justify-between">
          <span className="text-[11px] text-slate-400 font-medium">Primary Driver</span>
          <div className="text-xs text-slate-200 line-clamp-2 mt-1 font-sans font-medium" title={riskState.top_causal_summary}>
            {riskState.top_causal_summary || (riskState.contributors?.length ? 'Decomposed physical contributions' : 'Stable baseline indicators')}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 flex items-center gap-1">
            <Clock className="w-3 h-3 text-slate-400" />
            <span>Updated {riskState.timestamp ? new Date(riskState.timestamp).toLocaleTimeString() : 'Just now'}</span>
          </div>
        </div>
      </div>

      {/* Causal Contributors Breakdown */}
      <div className="space-y-2">
        <div className="flex justify-between items-center text-xs font-semibold text-slate-300">
          <span>Additive Causal Contributors (Δ Score Decomposition)</span>
          {riskState.contributors && riskState.contributors.length > 3 && (
            <button
              onClick={() => setShowAllContributors(!showAllContributors)}
              className="text-cyan-400 hover:text-cyan-300 text-[11px] font-sans font-normal"
            >
              {showAllContributors ? 'Show Top 3' : `View All (${riskState.contributors.length})`}
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
          {(riskState.contributors || [])
            .slice(0, showAllContributors ? undefined : 3)
            .map((c, idx) => {
              const isPos = c.delta_score > 0;
              const isNeg = c.delta_score < 0;
              return (
                <div
                  key={idx}
                  onClick={() => setSelectedContributor(c)}
                  className="bg-surface-elevated/60 hover:bg-surface-elevated border border-border/60 hover:border-cyan-500/40 rounded-lg p-2.5 cursor-pointer transition-all space-y-1.5"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-1.5">
                      {getCategoryIcon(c.category)}
                      <span className="text-xs font-semibold text-white truncate max-w-[170px]" title={c.factor_name}>
                        {c.factor_name}
                      </span>
                    </div>
                    <span
                      className={`text-xs font-mono font-bold px-1.5 py-0.5 rounded ${
                        isPos
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : isNeg
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {isPos ? `+${c.delta_score.toFixed(1)}` : `${c.delta_score.toFixed(1)}`}
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-300 leading-tight">
                    {c.explanation}
                  </div>

                  <div className="flex justify-between text-[10px] text-slate-400 pt-1 border-t border-border/40 font-mono">
                    <span>Evidence: <strong className="text-slate-300">{c.evidence_value}</strong></span>
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* Risk Evolution Sparkline / Timeline */}
      {riskHistory.length > 0 && (
        <div className="bg-surface-elevated/40 rounded-lg p-3 border border-border/50 space-y-2">
          <span className="text-xs font-semibold text-slate-300 block">Risk Evolution Timeline</span>
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {riskHistory.slice(0, 8).map((h, i) => (
              <div
                key={i}
                className="flex-shrink-0 bg-slate-900/80 border border-slate-800 rounded px-2.5 py-1.5 text-center min-w-[75px]"
              >
                <div className="text-[10px] font-mono text-slate-400">
                  {h.timestamp ? new Date(h.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : `T-${i}`}
                </div>
                <div className="text-xs font-bold font-mono text-white mt-0.5">
                  {h.risk_score?.toFixed(1)}
                </div>
                <div className={`text-[9px] font-bold mt-0.5 ${h.risk_change > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {h.risk_change > 0 ? `+${h.risk_change?.toFixed(1)}` : `${h.risk_change?.toFixed(1)}`}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contributor Evidence Detail Modal */}
      {selectedContributor && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-lg max-w-lg w-full p-5 space-y-4 shadow-2xl animate-in fade-in zoom-in duration-200">
            <div className="flex justify-between items-start border-b border-border pb-3">
              <div>
                <h4 className="text-base font-bold text-white flex items-center gap-2">
                  <Info className="w-5 h-5 text-cyan-400" />
                  Causal Attribution Factor Details
                </h4>
                <span className="text-xs text-slate-400">{selectedContributor.factor_name}</span>
              </div>
              <button
                onClick={() => setSelectedContributor(null)}
                className="text-slate-400 hover:text-white text-sm px-2 py-1 rounded bg-surface-elevated"
              >
                ✕ Close
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-surface-elevated p-2.5 rounded">
                <span className="text-slate-400 block">Category:</span>
                <strong className="text-cyan-300 text-sm">{selectedContributor.category}</strong>
              </div>
              <div className="bg-surface-elevated p-2.5 rounded">
                <span className="text-slate-400 block">Delta Contribution:</span>
                <strong className={`text-sm font-mono ${selectedContributor.delta_score > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {selectedContributor.delta_score > 0 ? `+${selectedContributor.delta_score}` : selectedContributor.delta_score} pts
                </strong>
              </div>
              <div className="bg-surface-elevated p-2.5 rounded col-span-2">
                <span className="text-slate-400 block">Observed Evidence:</span>
                <strong className="text-white text-sm font-mono">{selectedContributor.evidence_value}</strong>
              </div>
            </div>

            <div className="bg-surface-elevated p-3 rounded space-y-1 text-xs">
              <span className="text-slate-400 font-semibold block">Decomposition Rationale:</span>
              <p className="text-slate-200">{selectedContributor.explanation}</p>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedContributor(null)}
                className="px-4 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
