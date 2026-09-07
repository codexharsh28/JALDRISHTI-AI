import React, { useState } from 'react';
import { Layers, Eye, EyeOff, ChevronDown, ChevronUp, AlertCircle, Shield, Droplets, Activity, Building, Zap } from 'lucide-react';
import { MapLayerConfig } from '../../types/map';

interface Props {
  layers: MapLayerConfig[];
  onToggleLayer: (id: string) => void;
  onOpacityChange: (id: string, opacity: number) => void;
}

export const MapLayerControls: React.FC<Props> = ({ layers, onToggleLayer, onOpacityChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string>('all');

  const categories = [
    { id: 'all', name: 'All Layers', count: layers.length },
    { id: 'meteorology', name: 'Meteorology & Rainfall', icon: Droplets },
    { id: 'hydrology', name: 'Hydrology & Rivers', icon: Activity },
    { id: 'inundation', name: 'Inundation Depth', icon: Shield },
    { id: 'assets', name: 'Critical Assets', icon: Building },
    { id: 'alerts', name: 'Alert Zones', icon: Zap }
  ];

  const filteredLayers = activeCategory === 'all' 
    ? layers 
    : layers.filter(l => l.category === activeCategory);

  return (
    <div className="absolute top-4 left-4 z-[500] max-w-xs w-80 font-mono text-xs">
      <div className="glass-panel border border-surface-border rounded-xl shadow-2xl backdrop-blur-md overflow-hidden">
        {/* Header Toggle */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-4 py-3 bg-surface-base/80 flex items-center justify-between hover:bg-surface-border/30 transition-colors border-b border-surface-border/50"
        >
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span className="font-bold text-slate-100">GIS Operations Layers</span>
            <span className="px-1.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 text-[10px] font-bold">
              {layers.filter(l => l.enabled).length}/{layers.length}
            </span>
          </div>
          {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </button>

        {isOpen && (
          <div className="p-3 space-y-3 max-h-[70vh] overflow-y-auto">
            {/* Category Filter Pills */}
            <div className="flex flex-wrap gap-1 pb-2 border-b border-surface-border/40">
              {categories.map(c => (
                <button
                  key={c.id}
                  onClick={() => setActiveCategory(c.id)}
                  className={`px-2 py-1 rounded text-[10px] font-semibold transition-all ${
                    activeCategory === c.id 
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' 
                      : 'bg-surface-base text-slate-400 hover:text-slate-200 border border-surface-border/50'
                  }`}
                >
                  {c.name}
                </button>
              ))}
            </div>

            {/* Layer Item List */}
            <div className="space-y-1.5">
              {filteredLayers.map(layer => (
                <div 
                  key={layer.id}
                  className={`p-2 rounded-lg border transition-all ${
                    layer.enabled 
                      ? 'bg-surface-base/70 border-cyan-500/30' 
                      : 'bg-surface-base/30 border-surface-border/40 opacity-75'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <label className="flex items-center gap-2 cursor-pointer select-none flex-1">
                      <input
                        type="checkbox"
                        checked={layer.enabled}
                        onChange={() => onToggleLayer(layer.id)}
                        disabled={!layer.available}
                        className="rounded border-slate-600 text-cyan-500 focus:ring-cyan-400 bg-surface-base w-3.5 h-3.5"
                      />
                      <span className={`text-[11px] ${layer.enabled ? 'text-slate-100 font-semibold' : 'text-slate-400'}`}>
                        {layer.name}
                      </span>
                    </label>

                    {!layer.available && (
                      <span className="px-1.5 py-0.5 rounded text-[9px] bg-red-500/20 text-red-300 border border-red-500/30">
                        {layer.statusText || 'UNAVAILABLE'}
                      </span>
                    )}
                  </div>

                  {/* Opacity Slider */}
                  {layer.enabled && layer.available && (
                    <div className="mt-1.5 flex items-center gap-2 pt-1 border-t border-surface-border/30">
                      <span className="text-[9px] text-slate-500">Opacity</span>
                      <input
                        type="range"
                        min="0.1"
                        max="1.0"
                        step="0.05"
                        value={layer.opacity}
                        onChange={(e) => onOpacityChange(layer.id, parseFloat(e.target.value))}
                        className="w-full accent-cyan-400 h-1 bg-surface-border rounded-lg cursor-pointer"
                      />
                      <span className="text-[9px] text-slate-400 w-6 text-right">
                        {Math.round(layer.opacity * 100)}%
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
