import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, Clock, FastForward } from 'lucide-react';

interface Props {
  activeMinutes: number;
  onHorizonChange: (minutes: number) => void;
}

export const MapTimelineScrubber: React.FC<Props> = ({ activeMinutes, onHorizonChange }) => {
  const [isPlaying, setIsPlaying] = useState(false);

  const timeSteps = [
    { label: '-60m', minutes: -60, type: 'OBSERVED' },
    { label: '-30m', minutes: -30, type: 'OBSERVED' },
    { label: 'NOW', minutes: 0, type: 'CURRENT' },
    { label: '+30m', minutes: 30, type: 'NOWCAST' },
    { label: '+1h', minutes: 60, type: 'NOWCAST' },
    { label: '+2h', minutes: 120, type: 'NOWCAST' },
    { label: '+3h', minutes: 180, type: 'NOWCAST' },
    { label: '+4h', minutes: 240, type: 'NOWCAST' },
    { label: '+5h', minutes: 300, type: 'NOWCAST' },
    { label: '+6h', minutes: 360, type: 'NOWCAST' }
  ];

  const currentIdx = timeSteps.findIndex(t => t.minutes === activeMinutes);
  const currentStep = timeSteps[currentIdx >= 0 ? currentIdx : 2];

  useEffect(() => {
    let timer: any = null;
    if (isPlaying) {
      timer = setInterval(() => {
        const nextIdx = (currentIdx + 1) % timeSteps.length;
        onHorizonChange(timeSteps[nextIdx].minutes);
      }, 1500);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isPlaying, currentIdx, onHorizonChange]);

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-[500] w-11/12 max-w-2xl font-mono text-xs">
      <div className="glass-panel border border-surface-border p-3 rounded-2xl shadow-2xl backdrop-blur-md space-y-2">
        <div className="flex items-center justify-between gap-2">
          {/* Controls & Label */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="p-2 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 transition-colors"
              title={isPlaying ? 'Pause timeline animation' : 'Play timeline animation'}
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </button>

            <button
              onClick={() => { setIsPlaying(false); onHorizonChange(0); }}
              className="p-2 rounded-lg bg-surface-base hover:bg-surface-border text-slate-300 border border-surface-border transition-colors"
              title="Reset to NOW"
            >
              <RotateCcw className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-1.5 pl-1">
              <Clock className="w-4 h-4 text-cyan-400" />
              <span className="text-slate-200 font-bold">Horizon:</span>
              <span className="text-cyan-300 font-extrabold text-sm">{currentStep.label}</span>
            </div>
          </div>

          {/* Observed vs Nowcast Indicator Badge */}
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
            currentStep.type === 'OBSERVED' 
              ? 'bg-blue-500/20 text-blue-300 border-blue-500/40' 
              : (currentStep.type === 'CURRENT' 
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                  : 'bg-purple-500/20 text-purple-300 border-purple-500/40')
          }`}>
            [{currentStep.type} DATA LAYER]
          </span>
        </div>

        {/* Step Buttons Track */}
        <div className="grid grid-cols-10 gap-1 pt-1">
          {timeSteps.map((t, idx) => {
            const isSelected = t.minutes === activeMinutes;
            return (
              <button
                key={t.label}
                onClick={() => { setIsPlaying(false); onHorizonChange(t.minutes); }}
                className={`py-1.5 rounded-lg text-[10px] font-bold transition-all text-center border ${
                  isSelected
                    ? 'bg-cyan-500 text-slate-950 font-black border-cyan-300 shadow-md shadow-cyan-500/20 scale-105'
                    : (t.type === 'OBSERVED'
                        ? 'bg-blue-950/40 text-blue-300 hover:bg-blue-900/50 border-blue-800/40'
                        : 'bg-surface-base/80 text-slate-400 hover:text-slate-100 hover:bg-surface-border/50 border-surface-border/50')
                }`}
              >
                {t.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
