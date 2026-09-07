import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Layers,
  AlertTriangle,
  Building2,
  Users,
  ShieldAlert,
  Clock,
  Radio,
  Zap,
  Info,
  ChevronRight
} from 'lucide-react';

interface AssetExposure {
  asset_id: string;
  name: string;
  asset_type: string;
  latitude: number;
  longitude: number;
  flood_probability: number;
  depth_class: string;
  distance_to_flood_m: number;
  risk_state: string;
  confidence: string;
  dataset_state: string;
  mitigation_protocol?: string;
}

interface SpatialChange {
  current_snapshot_id: string;
  previous_snapshot_id: string;
  expansion_sqkm: number;
  contraction_sqkm: number;
  net_delta_sqkm: number;
  percentage_change: number;
  inundation_expansion_rate_km2_per_hour: number;
  spatial_trend: string;
  new_cells_count: number;
  receded_cells_count: number;
  unchanged_cells_count: number;
  is_material_change: boolean;
}

interface InundationSnapshotData {
  inundation_snapshot_id: string;
  snapshot_id: string;
  valid_time: string;
  scenario: string;
  inundated_area_sqkm: number;
  mean_flood_probability: number;
  peak_depth_m: number;
  depth_classes: {
    depth_0_to_0_3m_sqkm: number;
    depth_0_3_to_1m_sqkm: number;
    depth_1_to_2m_sqkm: number;
    depth_gt_2m_sqkm: number;
    dataset_state: string;
  };
  confidence: string;
  dataset_state: string;
  hydrology_source: string;
}

interface PopulationSummary {
  population_exposed_now: number;
  population_exposed_forecast: number;
  newly_exposed_population: number;
  severely_affected_population_gt_1m: number;
  dataset_state: string;
}

export const InundationEvolutionCard: React.FC = () => {
  const [snapshot, setSnapshot] = useState<InundationSnapshotData | null>(null);
  const [change, setChange] = useState<SpatialChange | null>(null);
  const [assets, setAssets] = useState<AssetExposure[]>([]);
  const [popSummary, setPopSummary] = useState<PopulationSummary | null>(null);
  const [history, setHistory] = useState<InundationSnapshotData[]>([]);
  const [selectedSnapshotIdx, setSelectedSnapshotIdx] = useState<number>(0);
  const [selectedAsset, setSelectedAsset] = useState<AssetExposure | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  const fetchLiveEvolution = async () => {
    try {
      const [snapRes, chgRes, impRes, histRes] = await Promise.all([
        fetch('/api/v1/inundation/current'),
        fetch('/api/v1/inundation/change'),
        fetch('/api/v1/impact/current'),
        fetch('/api/v1/inundation/history?limit=5')
      ]);

      if (snapRes.ok) setSnapshot(await snapRes.json());
      if (chgRes.ok) setChange(await chgRes.json());
      if (impRes.ok) {
        const impData = await impRes.json();
        setAssets(impData.critical_assets || impData.assets || []);
        setPopSummary(impData.population_summary || impData.population_exposure || null);
      }
      if (histRes.ok) setHistory(await histRes.json());
    } catch (e) {
      console.warn('Failed to fetch inundation evolution:', e);
    }
  };

  useEffect(() => {
    fetchLiveEvolution();
    const timer = setInterval(fetchLiveEvolution, 10000);
    return () => clearInterval(timer);
  }, []);

  const triggerTestSimulation = async (surge: boolean) => {
    setIsSimulating(true);
    try {
      const baseArea = snapshot?.inundated_area_sqkm || 380.0;
      const newArea = surge ? baseArea + 35.0 : Math.max(120.0, baseArea - 25.0);
      const newProb = surge ? 0.88 : 0.65;
      const newStage = surge ? 27.20 : 25.40;

      await fetch('/api/v1/inundation/inject-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          inundated_area_sqkm: newArea,
          flood_prob: newProb,
          stage_m: newStage,
          hydrology_source: 'OBSERVED_CWC',
          confidence: 'HIGH'
        })
      });
      await fetchLiveEvolution();
    } catch (e) {
      console.error('Failed to trigger simulation:', e);
    } finally {
      setIsSimulating(false);
    }
  };

  const isExpanding = (change?.net_delta_sqkm || 0) > 0;
  const isContracting = (change?.net_delta_sqkm || 0) < 0;
  const isGlofas = snapshot?.hydrology_source?.toUpperCase().includes('GLOFAS');

  return (
    <div className="bg-[#0b1329] rounded-xl border border-slate-800/90 shadow-md p-4 space-y-4 font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Live Inundation Evolution & Spatial Differencing (Phase 15)
              </h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                {snapshot?.scenario || 'P50'}
              </span>
              {isGlofas && (
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                  MODELED_GLOFAS
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400">
              Reactive spatial differencing tracking flood rate of change, depth evolution & critical asset propagation.
            </p>
          </div>
        </div>

        {/* Action / Simulation Trigger */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => triggerTestSimulation(true)}
            disabled={isSimulating}
            className="px-2.5 py-1 rounded bg-rose-600/30 hover:bg-rose-600/50 border border-rose-500/40 text-rose-300 text-xs font-semibold transition-all disabled:opacity-50"
          >
            + Hydraulic Surcharge
          </button>
          <button
            onClick={() => triggerTestSimulation(false)}
            disabled={isSimulating}
            className="px-2.5 py-1 rounded bg-emerald-600/30 hover:bg-emerald-600/50 border border-emerald-500/40 text-emerald-300 text-xs font-semibold transition-all disabled:opacity-50"
          >
            - Recession
          </button>
        </div>
      </div>

      {/* Primary Evolution Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 font-mono">
        {/* Metric 1: Extent */}
        <div className="bg-surface-elevated/80 border border-border/80 rounded-lg p-3">
          <span className="text-[11px] text-slate-400 font-sans font-medium">Inundated Extent</span>
          <div className="flex items-baseline gap-1.5 mt-1">
            <span className="text-2xl font-black text-white">
              {snapshot?.inundated_area_sqkm?.toFixed(1) || '380.0'}
            </span>
            <span className="text-xs text-slate-400 font-sans">km²</span>
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-sans">
            Peak Depth: <strong className="text-slate-200">{snapshot?.peak_depth_m || 2.4} m</strong>
          </div>
        </div>

        {/* Metric 2: Rate of Expansion */}
        <div className="bg-surface-elevated/80 border border-border/80 rounded-lg p-3">
          <span className="text-[11px] text-slate-400 font-sans font-medium">Rate of Expansion</span>
          <div className="flex items-center gap-1.5 mt-1">
            {isExpanding ? (
              <div className="flex items-center gap-1 text-rose-400">
                <TrendingUp className="w-5 h-5" />
                <span className="text-2xl font-black">+{change?.inundation_expansion_rate_km2_per_hour?.toFixed(1) || '0.0'}</span>
              </div>
            ) : isContracting ? (
              <div className="flex items-center gap-1 text-emerald-400">
                <TrendingDown className="w-5 h-5" />
                <span className="text-2xl font-black">{change?.inundation_expansion_rate_km2_per_hour?.toFixed(1) || '0.0'}</span>
              </div>
            ) : (
              <span className="text-2xl font-black text-slate-400">0.0</span>
            )}
            <span className="text-xs text-slate-400 font-sans">km²/hr</span>
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-sans">
            Trend: <strong className={isExpanding ? 'text-rose-300' : isContracting ? 'text-emerald-300' : 'text-slate-300'}>{change?.spatial_trend || 'STABLE'}</strong>
          </div>
        </div>

        {/* Metric 3: Population Exposed */}
        <div className="bg-surface-elevated/80 border border-border/80 rounded-lg p-3">
          <span className="text-[11px] text-slate-400 font-sans font-medium">Population Exposed</span>
          <div className="flex items-baseline gap-1.5 mt-1">
            <span className="text-2xl font-black text-amber-300">
              {popSummary?.population_exposed_forecast?.toLocaleString() || '116,500'}
            </span>
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-sans">
            Newly Exposed: <strong className="text-rose-400">+{popSummary?.newly_exposed_population?.toLocaleString() || '0'}</strong>
          </div>
        </div>

        {/* Metric 4: Critical Facilities at Risk */}
        <div className="bg-surface-elevated/80 border border-border/80 rounded-lg p-3">
          <span className="text-[11px] text-slate-400 font-sans font-medium">Critical Assets at Risk</span>
          <div className="flex items-baseline gap-1.5 mt-1">
            <span className="text-2xl font-black text-rose-400">
              {assets.filter(a => a.risk_state === 'HIGH_RISK').length}
            </span>
            <span className="text-xs text-slate-400 font-sans">/ {assets.length}</span>
          </div>
          <div className="text-[10px] text-slate-400 mt-1 font-sans">
            Moderate Risk: <strong className="text-amber-300">{assets.filter(a => a.risk_state === 'MODERATE_RISK').length}</strong>
          </div>
        </div>
      </div>

      {/* Snapshot Comparison Timeline (CURRENT, -1 Snapshot, -2 Snapshots) */}
      {history.length > 0 && (
        <div className="bg-surface-elevated/40 rounded-lg p-2.5 border border-border/50 space-y-1.5">
          <div className="flex justify-between items-center text-xs text-slate-300 font-semibold">
            <span>Snapshot Comparison Timeline (Before / After)</span>
            <span className="text-[10px] font-mono text-slate-400">Resolution: 30m Hydrodynamic Grid</span>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {history.map((h, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedSnapshotIdx(idx)}
                className={`flex-shrink-0 px-3 py-1.5 rounded text-left border transition-all ${
                  selectedSnapshotIdx === idx
                    ? 'bg-cyan-500/20 border-cyan-500/50 text-white shadow-sm'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                <div className="text-[10px] font-mono font-bold flex items-center gap-1.5">
                  <Clock className="w-3 h-3 text-cyan-400" />
                  {idx === 0 ? 'CURRENT' : `T-${idx} SNAPSHOT`}
                </div>
                <div className="text-xs font-mono font-extrabold mt-0.5">
                  {h.inundated_area_sqkm?.toFixed(1)} km²
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Depth Evolution & Critical Assets Table Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* Depth Class Breakdown */}
        <div className="bg-surface-elevated/60 border border-border/60 rounded-lg p-3 space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-xs font-semibold text-white">Depth Evolution Breakdown</span>
            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-slate-800 text-cyan-300 border border-slate-700">
              MODEL_ESTIMATE
            </span>
          </div>
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between items-center bg-slate-900/60 p-2 rounded border border-slate-800">
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2 h-2 rounded bg-amber-400"></span> 0.0–0.3m (Shallow)
              </span>
              <strong className="font-mono text-white">{snapshot?.depth_classes?.depth_0_to_0_3m_sqkm || 114.0} km²</strong>
            </div>
            <div className="flex justify-between items-center bg-slate-900/60 p-2 rounded border border-slate-800">
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2 h-2 rounded bg-orange-500"></span> 0.3–1.0m (Moderate)
              </span>
              <strong className="font-mono text-white">{snapshot?.depth_classes?.depth_0_3_to_1m_sqkm || 152.0} km²</strong>
            </div>
            <div className="flex justify-between items-center bg-slate-900/60 p-2 rounded border border-slate-800">
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2 h-2 rounded bg-rose-500"></span> 1.0–2.0m (Severe)
              </span>
              <strong className="font-mono text-white">{snapshot?.depth_classes?.depth_1_to_2m_sqkm || 76.0} km²</strong>
            </div>
            <div className="flex justify-between items-center bg-slate-900/60 p-2 rounded border border-slate-800">
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2 h-2 rounded bg-rose-800"></span> &gt;2.0m (Extreme)
              </span>
              <strong className="font-mono text-white">{snapshot?.depth_classes?.depth_gt_2m_sqkm || 38.0} km²</strong>
            </div>
          </div>
        </div>

        {/* Critical Infrastructure Exposure List */}
        <div className="bg-surface-elevated/60 border border-border/60 rounded-lg p-3 space-y-2 lg:col-span-2">
          <div className="flex justify-between items-center">
            <span className="text-xs font-semibold text-white">Critical Asset Exposure Profile</span>
            <span className="text-[10px] text-slate-400 font-mono">{assets.length} Facilities Monitored</span>
          </div>
          <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-1">
            {assets.map((asset, i) => (
              <div
                key={i}
                onClick={() => setSelectedAsset(asset)}
                className="flex items-center justify-between bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/40 p-2 rounded text-xs cursor-pointer transition-all"
              >
                <div className="flex items-center gap-2 truncate max-w-[240px]">
                  <Building2 className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  <span className="text-slate-200 font-medium truncate">{asset.name || asset.asset_id}</span>
                </div>
                <div className="flex items-center gap-2 font-mono text-[11px]">
                  <span className="text-slate-400">{asset.depth_class}</span>
                  <span
                    className={`px-1.5 py-0.5 rounded font-bold text-[10px] ${
                      asset.risk_state === 'HIGH_RISK'
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                        : asset.risk_state === 'MODERATE_RISK'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    }`}
                  >
                    {asset.risk_state}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Asset Exposure Details Modal */}
      {selectedAsset && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-lg max-w-lg w-full p-5 space-y-4 shadow-2xl">
            <div className="flex justify-between items-start border-b border-border pb-3">
              <div>
                <h4 className="text-base font-bold text-white flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-cyan-400" />
                  Asset Exposure & Inundation Assessment
                </h4>
                <span className="text-xs text-slate-400">{selectedAsset.name || selectedAsset.asset_id}</span>
              </div>
              <button
                onClick={() => setSelectedAsset(null)}
                className="text-slate-400 hover:text-white text-sm px-2 py-1 rounded bg-surface-elevated"
              >
                ✕ Close
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-surface-elevated p-2.5 rounded">
                <span className="text-slate-400 block">Asset Type:</span>
                <strong className="text-cyan-300 text-sm">{selectedAsset.asset_type}</strong>
              </div>
              <div className="bg-surface-elevated p-2.5 rounded">
                <span className="text-slate-400 block">Risk State:</span>
                <strong className={`text-sm ${selectedAsset.risk_state === 'HIGH_RISK' ? 'text-rose-400' : 'text-amber-300'}`}>
                  {selectedAsset.risk_state}
                </strong>
              </div>
              <div className="bg-surface-elevated p-2.5 rounded">
                <span className="text-slate-400 block">Flood Probability:</span>
                <strong className="text-white text-sm font-mono">{((selectedAsset.flood_probability || 0) * 100).toFixed(0)}%</strong>
              </div>
              <div className="bg-surface-elevated p-2.5 rounded">
                <span className="text-slate-400 block">Estimated Depth Class:</span>
                <strong className="text-white text-sm font-mono">{selectedAsset.depth_class}</strong>
              </div>
              <div className="bg-surface-elevated p-2.5 rounded col-span-2">
                <span className="text-slate-400 block">Hydrological Source Attribution:</span>
                <strong className="text-amber-300 font-mono">{selectedAsset.dataset_state || 'OBSERVED_CWC'}</strong>
              </div>
            </div>

            <div className="bg-surface-elevated p-3 rounded space-y-1 text-xs">
              <span className="text-slate-400 font-semibold block">Operational Mitigation Protocol:</span>
              <p className="text-slate-200">{selectedAsset.mitigation_protocol || 'Routine floodplain vigilance'}</p>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedAsset(null)}
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
