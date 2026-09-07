import React, { useState, useEffect } from 'react';
import { 
  Radio, 
  Play, 
  Square, 
  RefreshCw, 
  Activity, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  ShieldAlert, 
  Zap 
} from 'lucide-react';

interface Props {
  onRefresh?: () => void;
}

export const LiveOperationsControlPanel: React.FC<Props> = ({ onRefresh }) => {
  const [systemMode, setSystemMode] = useState<string>('SIMULATION');
  const [dataState, setDataState] = useState<string>('SYNTHETIC');
  const [dataConfidence, setDataConfidence] = useState<string>('HIGH');
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [eventLog, setEventLog] = useState<{ timestamp: string; message: string }[]>([]);
  const [healthSummary, setHealthSummary] = useState<any[]>([]);
  const [demoState, setDemoState] = useState<any>(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/v1/live/status');
      if (res.ok) {
        const data = await res.json();
        setSystemMode(data.system_mode);
        setDataState(data.data_state);
        setDataConfidence(data.data_confidence);
      }
      const demoRes = await fetch('/api/v1/demo/status');
      if (demoRes.ok) {
        const dData = await demoRes.json();
        setDemoState(dData);
      }
      const logRes = await fetch('/api/v1/live/last-updates?limit=8');
      if (logRes.ok) {
        const logData = await logRes.json();
        setEventLog(logData.events || []);
      }
      const healthRes = await fetch('/api/v1/live/health');
      if (healthRes.ok) {
        const hData = await healthRes.json();
        setHealthSummary(hData.providers || []);
      }
    } catch (e) {
      // ignore
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleStartDemo = async () => {
    setIsLoading(true);
    try {
      await fetch('/api/v1/demo/start', { method: 'POST' });
      fetchStatus();
      if (onRefresh) onRefresh();
    } finally {
      setIsLoading(false);
    }
  };

  const handleStepDemo = async (direction: 'forward' | 'backward') => {
    try {
      await fetch(`/api/v1/demo/step?direction=${direction}`, { method: 'POST' });
      fetchStatus();
      if (onRefresh) onRefresh();
    } catch (e) {
      console.error(e);
    }
  };

  const handlePauseResumeDemo = async () => {
    if (!demoState) return;
    const endpoint = demoState.is_playing ? '/api/v1/demo/pause' : '/api/v1/demo/resume';
    await fetch(endpoint, { method: 'POST' });
    fetchStatus();
  };

  const handleResetDemo = async () => {
    await fetch('/api/v1/demo/reset', { method: 'POST' });
    fetchStatus();
    if (onRefresh) onRefresh();
  };

  const handleAcknowledgeGate = async () => {
    await fetch('/api/v1/demo/acknowledge', { method: 'POST' });
    fetchStatus();
    if (onRefresh) onRefresh();
  };

  const handleConnectLive = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/v1/live/connect?confirm=true', { method: 'POST' });
      if (res.ok) {
        setIsConfirmModalOpen(false);
        fetchStatus();
        if (onRefresh) onRefresh();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnectLive = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/v1/live/disconnect', { method: 'POST' });
      if (res.ok) {
        fetchStatus();
        if (onRefresh) onRefresh();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleForceRefresh = async () => {
    setIsLoading(true);
    try {
      await fetch('/api/v1/live/refresh', { method: 'POST' });
      fetchStatus();
      if (onRefresh) onRefresh();
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="glass-panel border border-surface-border rounded-2xl p-4 font-mono shadow-2xl space-y-4">
      {/* ========================================================================= */}
      {/* 0. ONE-CLICK END-TO-END DEMO CONTROL BAR */}
      {/* ========================================================================= */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-cyan-500/40 rounded-xl p-3.5 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 animate-pulse">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                Deterministic End-to-End Scenario: DEMO-MAHANADI-STORM-01
                <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  {demoState?.is_active ? `STAGE ${demoState.current_step + 1}/${demoState.total_steps}` : 'IDLE'}
                </span>
              </div>
              <p className="text-[10px] text-slate-400 font-sans">
                Full causal demonstration: Rain Nowcast → Streamflow Surge → 2D Inundation → Impact Exposure → Risk Waterfall → Geofenced Mock Citizen SMS
              </p>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-1.5">
            {!demoState?.is_active ? (
              <button
                onClick={handleStartDemo}
                disabled={isLoading}
                className="px-3.5 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow-lg shadow-emerald-500/20 transition-all font-sans"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                START END-TO-END DEMO
              </button>
            ) : (
              <>
                <button
                  onClick={() => handleStepDemo('backward')}
                  disabled={demoState.current_step === 0}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 border border-slate-700 text-xs"
                  title="Step Backward"
                >
                  ◀ Prev
                </button>
                <button
                  onClick={handlePauseResumeDemo}
                  className="px-2.5 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-xs font-bold"
                >
                  {demoState.is_playing ? 'Pause' : 'Play'}
                </button>
                <button
                  onClick={() => handleStepDemo('forward')}
                  disabled={demoState.current_step >= demoState.total_steps - 1}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 border border-slate-700 text-xs font-bold"
                  title="Step Forward"
                >
                  Next ▶
                </button>
                <button
                  onClick={handleResetDemo}
                  className="px-2 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-xs"
                >
                  Reset
                </button>
              </>
            )}
          </div>
        </div>

        {/* Live Scenario Status Ticker when active */}
        {demoState?.is_active && demoState.current_stage && (
          <div className="bg-slate-950/80 rounded-lg p-2.5 border border-slate-800 text-xs space-y-1.5 font-sans">
            <div className="flex flex-wrap items-center justify-between gap-1 text-[11px]">
              <span className="font-bold text-cyan-300 flex items-center gap-1.5">
                ● T+{demoState.current_step}: {demoState.current_stage.name} — {demoState.current_stage.headline}
              </span>
              <span className="text-slate-400 font-mono text-[10px]">
                Next: <strong className="text-slate-200">{demoState.next_stage}</strong>
              </span>
            </div>
            <p className="text-[11px] text-slate-300">
              {demoState.current_stage.description}
            </p>

            {/* Operator Review Gate Alert if required */}
            {demoState.current_stage.requires_operator_review && (
              <div className="mt-2 p-2 rounded bg-rose-950/60 border border-rose-500/60 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-rose-200 text-xs font-semibold">
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                  Mandatory Human Operator Authorization Gate: High-risk breach criteria reached.
                </div>
                <button
                  onClick={handleAcknowledgeGate}
                  className="px-3 py-1 rounded bg-rose-500 hover:bg-rose-400 text-white font-bold text-xs shrink-0 shadow"
                >
                  AUTHORIZE DISPATCH
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Header & Mode Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-surface-border/50">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-xl border ${
            systemMode === 'LIVE' 
              ? 'bg-rose-500/20 text-rose-400 border-rose-500/40 animate-pulse' 
              : 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
          }`}>
            <Radio className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              Data Ingestion & Operational Mode Plane
              <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold border ${
                systemMode === 'LIVE' 
                  ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' 
                  : (systemMode === 'REPLAY' ? 'bg-purple-500/20 text-purple-300 border-purple-500/40' : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40')
              }`}>
                SYSTEM: {systemMode}
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">Centralized mode switching and external data plane orchestration</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {systemMode !== 'LIVE' ? (
            <button
              onClick={() => setIsConfirmModalOpen(true)}
              className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-xs font-bold flex items-center gap-1.5 transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
              Engage LIVE Mode
            </button>
          ) : (
            <button
              onClick={handleDisconnectLive}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-600 text-xs font-bold flex items-center gap-1.5 transition-colors"
            >
              <Square className="w-3.5 h-3.5" />
              Return to Simulation
            </button>
          )}

          <button
            onClick={handleForceRefresh}
            disabled={isLoading}
            className="p-1.5 rounded-lg bg-surface-base hover:bg-surface-border text-slate-300 border border-surface-border text-xs transition-colors"
            title="Force refresh all configured providers"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Multi-Dimensional Status Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
        <div className="p-2.5 rounded-xl bg-surface-base/80 border border-surface-border/60">
          <span className="text-[10px] text-slate-400 uppercase font-bold">1. System Operating Mode</span>
          <div className="text-sm font-extrabold text-slate-100 mt-0.5">{systemMode}</div>
          <div className="text-[10px] text-slate-500">
            {systemMode === 'SIMULATION' ? 'Deterministic scenario engine' : (systemMode === 'REPLAY' ? 'Historical hindcast' : 'Live feeds active')}
          </div>
        </div>

        <div className="p-2.5 rounded-xl bg-surface-base/80 border border-surface-border/60">
          <span className="text-[10px] text-slate-400 uppercase font-bold">2. Data Quality State</span>
          <div className="text-sm font-extrabold text-slate-100 mt-0.5 flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${
              dataState === 'HEALTHY' ? 'bg-emerald-400' : (dataState === 'DEGRADED' ? 'bg-amber-400' : 'bg-blue-400')
            }`} />
            {dataState}
          </div>
          <div className="text-[10px] text-slate-500">Confidence: <strong>{dataConfidence}</strong></div>
        </div>

        <div className="p-2.5 rounded-xl bg-surface-base/80 border border-surface-border/60">
          <span className="text-[10px] text-slate-400 uppercase font-bold">3. Legal & Disclaimer State</span>
          <div className="text-xs font-bold text-amber-300 mt-0.5">DECISION SUPPORT RESEARCH</div>
          <div className="text-[9px] text-slate-500">Not an official government warning system</div>
        </div>
      </div>

      {/* Provider Cadence & Ingestion Mode Matrix */}
      <div className="space-y-1.5">
        <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Configured Live Ingestion Adapters</span>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
          {healthSummary.map((p) => (
            <div key={p.provider_id} className="p-2 rounded-lg bg-surface-base/60 border border-surface-border/40 text-[10px] space-y-1">
              <div className="flex justify-between items-center font-bold">
                <span className="text-slate-300 truncate" title={p.provider_id}>{p.provider_id.split('_')[0]}</span>
                <span className={`px-1 rounded text-[8px] ${
                  p.status === 'HEALTHY' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'
                }`}>
                  {p.ingestion_mode}
                </span>
              </div>
              <div className="text-[9px] text-slate-500">Cadence: {p.refresh_interval_seconds}s</div>
              <div className="text-[9px] font-semibold text-slate-400">State: <strong className={p.data_state === 'LIVE_OPERATIONAL' ? 'text-emerald-400' : 'text-slate-400'}>{p.data_state}</strong></div>
            </div>
          ))}
        </div>
      </div>

      {/* Real-Time Operational Event Feed */}
      <div className="space-y-1.5 pt-2 border-t border-surface-border/40">
        <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider flex items-center gap-1.5">
          <Clock className="w-3 h-3 text-cyan-400" />
          Live Event Provenance Feed
        </span>
        <div className="bg-surface-base/90 rounded-xl p-2 max-h-28 overflow-y-auto space-y-1 text-[10px] border border-surface-border/50">
          {eventLog.length > 0 ? (
            eventLog.map((ev, idx) => (
              <div key={idx} className="flex items-center justify-between text-slate-300 font-mono py-0.5 border-b border-surface-border/20 last:border-0">
                <span>{ev.message}</span>
                <span className="text-slate-500 text-[9px]">{new Date(ev.timestamp).toLocaleTimeString()}</span>
              </div>
            ))
          ) : (
            <div className="text-slate-500 italic text-center py-1">No ingestion events logged yet.</div>
          )}
        </div>
      </div>

      {/* Confirmation Safety Modal */}
      {isConfirmModalOpen && (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="glass-panel border border-rose-500/40 rounded-2xl p-5 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-rose-400">
              <ShieldAlert className="w-7 h-7 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-bold text-slate-100">Confirm Switch to LIVE Operational Mode</h4>
                <p className="text-xs text-rose-300">Safety & Operational Disclaimer</p>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/30 text-xs text-slate-200 space-y-2">
              <p className="font-bold text-rose-300">⚠️ LIVE DATA MAY BE DELAYED OR DEGRADED.</p>
              <p className="text-[11px] text-slate-300">
                Switching to LIVE mode initiates external network connections to configured hydrometeorological feeds.
                If any external provider is unavailable, the system will record degraded states and lower data confidence.
              </p>
              <p className="text-[10px] text-slate-400 italic">
                Permanent Disclaimer: This system is a research decision-support prototype and must not control infrastructure.
              </p>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setIsConfirmModalOpen(false)}
                className="px-3 py-1.5 rounded-lg bg-surface-base hover:bg-surface-border text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleConnectLive}
                disabled={isLoading}
                className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold shadow-lg shadow-rose-600/30"
              >
                {isLoading ? 'Connecting...' : 'Confirm & Engage LIVE'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
