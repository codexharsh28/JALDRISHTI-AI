import React, { useState, useEffect, useCallback } from 'react';
import { History, Play, Pause, RotateCcw, StepForward, StepBack, Clock, AlertTriangle, Layers } from 'lucide-react';
import { MapComponent } from '../components/MapComponent';
import { DataProvenanceDrawer } from '../components/DataProvenanceDrawer';
import { ProvenanceMetadata } from '../types';

export const ReplayView: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<number>(6); // Default at FLOOD_RISK_HIGH
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [speed, setSpeed] = useState<number>(1.0);

  const stages = [
    { name: "NORMAL", t: "T+00h", rain: 2.5, stage: 21.20, inun: 2.0, alert: "GREEN", desc: "Quiescent monsoon baseline. Normal agricultural discharges across barrage network." },
    { name: "RAINFALL_INCREASE", t: "T+06h", rain: 14.5, stage: 21.80, inun: 8.5, alert: "GREEN", desc: "Bay of Bengal low-pressure system organizes. Light-to-moderate rain begins." },
    { name: "HEAVY_RAIN", t: "T+12h", rain: 38.0, stage: 22.90, inun: 22.0, alert: "YELLOW", desc: "Intense convective cloud band makes landfall. Fused precipitation hits 38 mm/hr." },
    { name: "RUNOFF_INCREASE", t: "T+18h", rain: 54.0, stage: 24.20, inun: 42.0, alert: "YELLOW", desc: "Catchment soil reaches saturation. Rapid surface runoff enters tributaries." },
    { name: "RIVER_RISING", t: "T+24h", rain: 48.0, stage: 26.80, inun: 68.0, alert: "ORANGE", desc: "Upstream inflow pulse reaches Naraj weir. River stage rises rapidly (+0.45 m/hr)." },
    { name: "THRESHOLD_APPROACH", t: "T+30h", rain: 32.0, stage: 28.90, inun: 94.0, alert: "ORANGE", desc: "River stage crosses Warning Level (28.5m). Low embankments under pressure." },
    { name: "FLOOD_RISK_HIGH", t: "T+36h", rain: 26.0, stage: 30.60, inun: 128.0, alert: "RED", desc: "Naraj bifurcation exceeds 24,000 cumecs discharge. High flood surge propagating." },
    { name: "INUNDATION_EXPANSION", t: "T+42h", rain: 18.0, stage: 31.80, inun: 174.0, alert: "RED", desc: "Embankment spill in Kathajodi-Marshaghai corridor. 174 sq km flooded." },
    { name: "ALERT", t: "T+48h", rain: 12.0, stage: 32.40, inun: 210.0, alert: "RED", desc: "CRITICAL RED ALERT: Danger Level breached. Evacuation of 105,000 people active." },
    { name: "PEAK", t: "T+54h", rain: 6.0, stage: 32.75, inun: 235.0, alert: "RED", desc: "Flood crest peak reached (32.75m at Mundali / 12.80m at Marshaghai). Maximum inundation." },
    { name: "RECOVERY", t: "T+72h", rain: 1.0, stage: 25.10, inun: 45.0, alert: "YELLOW", desc: "Storm system moved inland. Discharge recedes below danger levels. Drainage active." }
  ];

  const fetchInitialReplayState = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/replay/EVT-MAHANADI-2020-08');
      if (res.ok) {
        const data = await res.json();
        if (data.current_state?.step_index !== undefined) {
          setCurrentStep(data.current_state.step_index);
        }
      }
    } catch (e) {
      console.warn('Replay state fetch error:', e);
    }
  }, []);

  useEffect(() => {
    fetchInitialReplayState();
  }, [fetchInitialReplayState]);

  const handleStepForward = async () => {
    try {
      const res = await fetch('/api/v1/replay/step?action=forward', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (data.state?.step_index !== undefined) {
          setCurrentStep(data.state.step_index);
          return;
        }
      }
    } catch (e) {
      console.warn('Replay step forward error:', e);
    }
    setCurrentStep(prev => Math.min(stages.length - 1, prev + 1));
  };

  const handleStepBackward = async () => {
    try {
      const res = await fetch('/api/v1/replay/step?action=backward', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (data.state?.step_index !== undefined) {
          setCurrentStep(data.state.step_index);
          return;
        }
      }
    } catch (e) {
      console.warn('Replay step backward error:', e);
    }
    setCurrentStep(prev => Math.max(0, prev - 1));
  };

  const handleReset = async () => {
    try {
      const res = await fetch('/api/v1/replay/step?action=reset', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (data.state?.step_index !== undefined) {
          setCurrentStep(data.state.step_index);
        }
      }
    } catch (e) {
      console.warn('Replay reset error:', e);
      setCurrentStep(0);
    }
    setIsPlaying(false);
  };

  const handleSetStep = async (stepIdx: number) => {
    try {
      const res = await fetch(`/api/v1/replay/step?action=set_step&step=${stepIdx}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (data.state?.step_index !== undefined) {
          setCurrentStep(data.state.step_index);
          return;
        }
      }
    } catch (e) {
      console.warn('Replay set_step error:', e);
    }
    setCurrentStep(stepIdx);
  };

  useEffect(() => {
    let timer: any = null;
    if (isPlaying) {
      timer = setInterval(() => {
        handleStepForward();
      }, Math.max(300, 2500 / speed));
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isPlaying, speed]);

  const activeStage = stages[currentStep];

  const provenance: ProvenanceMetadata = {
    source_id: "REPLAY_ENGINE_SYNCHRONIZER",
    provider: "JALDRISHTI AI Historical Scenario Mission Replay",
    product_name: "Deterministic Synchronized 11-Stage Flood Wave Replay",
    observed_at: new Date().toISOString(),
    received_at: new Date().toISOString(),
    source_latency_mins: 0.0,
    processing_version: "v1.0.0",
    is_simulation: true
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold font-mono text-white flex items-center gap-2">
            <History className="w-5 h-5 text-cyan-400" />
            Deterministic Historical Flood Event Mission Replay
          </h2>
          <p className="text-xs text-slate-400">
            Synchronized 11-stage timeline simulating the August 2024 Deep Depression Flood Wave.
          </p>
        </div>
      </div>

      {/* Playback Control Panel */}
      <div className="glass-panel p-4 rounded-xl border border-surface-border space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
          {/* Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleStepBackward}
              className="p-2 rounded bg-surface border border-surface-border text-slate-300 hover:text-white"
              title="Step Back"
            >
              <StepBack className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="px-3 py-2 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 hover:bg-cyan-500/30 flex items-center gap-1.5 font-bold"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              <span>{isPlaying ? 'PAUSE' : 'PLAY'}</span>
            </button>
            <button
              onClick={handleStepForward}
              className="p-2 rounded bg-surface border border-surface-border text-slate-300 hover:text-white"
              title="Step Forward"
            >
              <StepForward className="w-4 h-4" />
            </button>
            <button
              onClick={handleReset}
              className="p-2 rounded bg-surface border border-surface-border text-slate-300 hover:text-white ml-2"
              title="Reset to T+00h"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>

          {/* Speed Selector */}
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Speed:</span>
            {[0.5, 1.0, 2.0, 5.0, 10.0].map(s => (
              <button
                key={s}
                onClick={() => setSpeed(s)}
                className={`px-2 py-1 rounded text-[11px] ${
                  speed === s ? 'bg-cyan-500 text-black font-bold' : 'bg-surface text-slate-400 border border-surface-border'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>

          {/* Stage Name Badge */}
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Stage {currentStep + 1}/{stages.length}:</span>
            <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
              {activeStage.name} ({activeStage.t})
            </span>
          </div>
        </div>

        {/* 11-Stage Scrubbing Progress Bar */}
        <div className="grid grid-cols-11 gap-1 pt-1">
          {stages.map((stg, i) => (
            <button
              key={i}
              onClick={() => handleSetStep(i)}
              className={`py-2 px-1 rounded text-[10px] font-mono truncate transition-all text-center ${
                currentStep === i
                  ? 'bg-cyan-500 text-black font-bold shadow-md shadow-cyan-500/20'
                  : 'bg-surface border border-surface-border text-slate-400 hover:text-slate-200'
              }`}
              title={`${stg.name} (${stg.t})`}
            >
              {stg.t}
            </button>
          ))}
        </div>

        {/* Stage Narrative Callout */}
        <div className="bg-surface/80 p-3 rounded-lg border border-surface-border font-mono text-xs space-y-1">
          <div className="text-slate-400 text-[10px] uppercase font-semibold">Synchronized Narrative Stream:</div>
          <div className="text-slate-200 font-sans text-xs">{activeStage.desc}</div>
        </div>

        {/* Dynamic Metric Readouts */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
          <div className="p-2.5 rounded-lg bg-surface border border-surface-border">
            <div className="text-slate-400 text-[10px]">Rainfall Rate</div>
            <div className="text-lg font-bold text-cyan-300">{activeStage.rain} mm/h</div>
          </div>
          <div className="p-2.5 rounded-lg bg-surface border border-surface-border">
            <div className="text-slate-400 text-[10px]">River Stage (Mundali)</div>
            <div className="text-lg font-bold text-sky-400">{activeStage.stage} m</div>
          </div>
          <div className="p-2.5 rounded-lg bg-surface border border-surface-border">
            <div className="text-slate-400 text-[10px]">Inundation Footprint</div>
            <div className="text-lg font-bold text-purple-400">{activeStage.inun} km²</div>
          </div>
          <div className="p-2.5 rounded-lg bg-surface border border-surface-border">
            <div className="text-slate-400 text-[10px]">Active Alert</div>
            <div className={`text-lg font-bold ${
              activeStage.alert === 'RED' ? 'text-rose-500' :
              activeStage.alert === 'ORANGE' ? 'text-orange-400' :
              activeStage.alert === 'YELLOW' ? 'text-amber-400' : 'text-emerald-400'
            }`}>
              {activeStage.alert}
            </div>
          </div>
        </div>
      </div>

      {/* Tactical Map synchronized to step */}
      <div className="space-y-2">
        <div className="flex items-center justify-between font-mono text-xs text-slate-400">
          <span>Tactical Map • Synchronized to Stage {currentStep + 1} ({activeStage.name})</span>
          <span>Global Scenario Clock Active</span>
        </div>
        <MapComponent heightClass="h-[480px]" showInundation={currentStep >= 2} showAssets={true} />
      </div>

      <DataProvenanceDrawer provenance={provenance} />
    </div>
  );
};
