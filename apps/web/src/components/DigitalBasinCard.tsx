import React, { useState, useEffect } from 'react';
import { Waves, Droplets, Layers, Anchor, Activity, RefreshCw } from 'lucide-react';

interface DigitalBasinCardProps {
  className?: string;
}

export const DigitalBasinCard: React.FC<DigitalBasinCardProps> = ({ className = '' }) => {
  const [basinState, setBasinState] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchBasinState = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/v1/basin/state/current');
      if (res.ok) {
        const data = await res.json();
        setBasinState(data);
      }
    } catch (e) {
      console.warn("Failed to fetch digital basin state:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBasinState();
    const interval = setInterval(fetchBasinState, 8000);
    return () => clearInterval(interval);
  }, []);

  if (!basinState) return null;

  const soil = basinState.soil_moisture || {};
  const channel = basinState.channel_storage || {};
  const barrages = (basinState.barrage_operations?.structures || []) as any[];
  const tide = basinState.tidal_boundary || {};

  return (
    <div className={`bg-surface border border-border rounded-xl p-5 shadow-lg space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center border-b border-border pb-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-cyan-500/10 rounded-lg border border-cyan-500/30 text-cyan-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              Digital Basin Twin State (Phase 17)
              <span className="text-[10px] bg-cyan-950 text-cyan-400 px-2 py-0.5 rounded-full border border-cyan-800">
                v{basinState.version}
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Live physics twin: soil moisture deficit, channel routing, barrage gates & tidal boundary
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="text-right hidden sm:block">
            <span className="text-[10px] text-slate-400 block">Basin Hydraulic Risk</span>
            <span className={`text-xs font-mono font-bold ${
              basinState.basin_hydraulic_risk_index > 75 ? 'text-rose-400' :
              basinState.basin_hydraulic_risk_index > 50 ? 'text-amber-400' : 'text-emerald-400'
            }`}>
              {basinState.basin_hydraulic_risk_index} / 100
            </span>
          </div>
          <button
            onClick={fetchBasinState}
            disabled={isLoading}
            className="p-1.5 bg-surface-elevated hover:bg-border rounded text-slate-400 hover:text-white transition-colors"
            title="Refresh Basin State"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 4 Multi-Domain Quadrants */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Quadrant 1: Soil Moisture */}
        <div className="bg-surface-elevated/50 p-3 rounded-lg border border-border/70 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-300">
            <span className="font-semibold flex items-center gap-1.5">
              <Droplets className="w-3.5 h-3.5 text-blue-400" />
              Soil Saturation
            </span>
            <span className="font-mono text-blue-400 font-bold">
              {(soil.saturation_index * 100).toFixed(0)}%
            </span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, soil.saturation_index * 100)}%` }}
            />
          </div>
          <div className="text-[11px] text-slate-400 flex justify-between pt-1">
            <span>Deficit: <b className="text-slate-200">{soil.moisture_deficit_mm}mm</b></span>
            <span>API-30d: <b className="text-slate-200">{soil.antecedent_precipitation_index_30d}mm</b></span>
          </div>
        </div>

        {/* Quadrant 2: Channel Storage */}
        <div className="bg-surface-elevated/50 p-3 rounded-lg border border-border/70 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-300">
            <span className="font-semibold flex items-center gap-1.5">
              <Waves className="w-3.5 h-3.5 text-cyan-400" />
              Channel Volume
            </span>
            <span className="font-mono text-cyan-400 font-bold">
              {channel.capacity_utilization_pct}%
            </span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all duration-500 ${
                channel.capacity_utilization_pct > 85 ? 'bg-rose-500' :
                channel.capacity_utilization_pct > 70 ? 'bg-amber-500' : 'bg-cyan-500'
              }`}
              style={{ width: `${Math.min(100, channel.capacity_utilization_pct)}%` }}
            />
          </div>
          <div className="text-[11px] text-slate-400 flex justify-between pt-1">
            <span>Storage: <b className="text-slate-200">{channel.current_storage_mcm} MCM</b></span>
            <span>Travel: <b className="text-slate-200">{channel.reach_travel_time_hours}h</b></span>
          </div>
        </div>

        {/* Quadrant 3: Barrage Operations */}
        <div className="bg-surface-elevated/50 p-3 rounded-lg border border-border/70 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-300">
            <span className="font-semibold flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-amber-400" />
              Delta Regulators
            </span>
            <span className="font-mono text-amber-400 font-bold">
              {barrages.length} Barrages
            </span>
          </div>
          <div className="text-[11px] text-slate-300 space-y-1">
            {barrages.slice(0, 2).map((b: any) => (
              <div key={b.structure_id} className="flex justify-between">
                <span className="truncate max-w-[120px]">{b.name.split('(')[0]}</span>
                <span className="font-mono text-slate-400">
                  {b.open_gates}/{b.total_gates} gates ({(b.discharge_cumec/1000).toFixed(1)}k cumec)
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Quadrant 4: Coastal Tidal Boundary */}
        <div className="bg-surface-elevated/50 p-3 rounded-lg border border-border/70 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-300">
            <span className="font-semibold flex items-center gap-1.5">
              <Anchor className="w-3.5 h-3.5 text-indigo-400" />
              Paradip Estuary Tide
            </span>
            <span className="font-mono text-indigo-400 font-bold">
              +{tide.total_water_level_m}m MSL
            </span>
          </div>
          <div className="text-[11px] text-slate-400 flex justify-between pt-1">
            <span>Astro: <b className="text-slate-200">{tide.astronomical_tide_m}m</b></span>
            <span>Surge: <b className="text-slate-200">+{tide.storm_surge_residual_m}m</b></span>
          </div>
          <div className="text-[10px] text-indigo-300 flex justify-between">
            <span>Phase: <b>{tide.tidal_phase}</b></span>
            <span>Backwater: <b>{tide.backwater_propagation_km} km</b></span>
          </div>
        </div>
      </div>
    </div>
  );
};
