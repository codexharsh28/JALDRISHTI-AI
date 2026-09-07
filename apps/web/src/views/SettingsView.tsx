import React, { useState } from 'react';
import { Settings, Save, RefreshCw, Shield, Bell, Database, CheckCircle2 } from 'lucide-react';

export const SettingsView: React.FC = () => {
  const [yellowRainThreshold, setYellowRainThreshold] = useState<number>(15.0);
  const [orangeRainThreshold, setOrangeRainThreshold] = useState<number>(35.0);
  const [redRainThreshold, setRedRainThreshold] = useState<number>(65.0);
  const [humanReviewEnabled, setHumanReviewEnabled] = useState<boolean>(true);
  const [saved, setSaved] = useState<boolean>(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold font-mono text-white flex items-center gap-2">
            <Settings className="w-5 h-5 text-cyan-400" />
            Operational Basin Settings & Threshold Calibration
          </h2>
          <p className="text-xs text-slate-400">
            Configure pilot catchment parameters, decision support thresholds, and API connection profiles.
          </p>
        </div>
      </div>

      {/* Thresholds Card */}
      <div className="glass-panel p-5 rounded-xl border border-surface-border space-y-4 font-mono text-xs">
        <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-surface-border/60 pb-2">
          <Bell className="w-4 h-4 text-cyan-400" />
          Rainfall & Stage Threshold Matrix
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-1.5">
            <label className="text-slate-400 text-[11px]">Yellow Advisory Rain Rate (mm/h)</label>
            <input
              type="number"
              value={yellowRainThreshold}
              onChange={(e) => setYellowRainThreshold(Number(e.target.value))}
              className="w-full bg-surface border border-surface-border rounded-lg p-2 text-white font-bold focus:border-cyan-400 outline-none"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-400 text-[11px]">Orange Warning Rain Rate (mm/h)</label>
            <input
              type="number"
              value={orangeRainThreshold}
              onChange={(e) => setOrangeRainThreshold(Number(e.target.value))}
              className="w-full bg-surface border border-surface-border rounded-lg p-2 text-white font-bold focus:border-cyan-400 outline-none"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-400 text-[11px]">Red Extreme Rain Rate (mm/h)</label>
            <input
              type="number"
              value={redRainThreshold}
              onChange={(e) => setRedRainThreshold(Number(e.target.value))}
              className="w-full bg-surface border border-surface-border rounded-lg p-2 text-white font-bold focus:border-cyan-400 outline-none"
            />
          </div>
        </div>

        {/* Human Review Checkbox */}
        <div className="pt-2 flex items-center gap-3">
          <input
            type="checkbox"
            id="humanReview"
            checked={humanReviewEnabled}
            onChange={(e) => setHumanReviewEnabled(e.target.checked)}
            className="w-4 h-4 rounded bg-surface border-surface-border text-cyan-500 focus:ring-cyan-400"
          />
          <label htmlFor="humanReview" className="text-slate-200 text-xs font-sans cursor-pointer">
            <b>Enforce Human Operator Review Gate for RED Alerts</b> (Recommended for emergency safety)
          </label>
        </div>

        <div className="pt-3">
          <button
            onClick={handleSave}
            className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-xs flex items-center gap-2 transition-colors"
          >
            <Save className="w-4 h-4" />
            <span>Save Configuration</span>
          </button>
          {saved && (
            <span className="text-emerald-400 text-xs ml-3 font-semibold inline-flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Saved successfully
            </span>
          )}
        </div>
      </div>

      {/* External Service Endpoints */}
      <div className="glass-panel p-5 rounded-xl border border-surface-border space-y-3 font-mono text-xs">
        <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-surface-border/60 pb-2">
          <Database className="w-4 h-4 text-cyan-400" />
          Data Provider Service Endpoints
        </h3>

        <div className="space-y-2 text-slate-300 text-[11px]">
          <div className="flex justify-between p-2 rounded bg-surface/50 border border-surface-border/50">
            <span>FastAPI Backend Server:</span>
            <code className="text-cyan-300">http://127.0.0.1:8000</code>
          </div>
          <div className="flex justify-between p-2 rounded bg-surface/50 border border-surface-border/50">
            <span>WebSocket Live Broadcast Stream:</span>
            <code className="text-cyan-300">ws://127.0.0.1:8000/ws/v1/live</code>
          </div>
          <div className="flex justify-between p-2 rounded bg-surface/50 border border-surface-border/50">
            <span>OpenAPI Interactive Swagger Docs:</span>
            <code className="text-cyan-300">http://127.0.0.1:8000/docs</code>
          </div>
        </div>
      </div>
    </div>
  );
};
