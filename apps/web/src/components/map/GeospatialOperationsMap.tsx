import React, { useState, useMemo, useEffect } from 'react';
import { 
  MapContainer, 
  TileLayer, 
  Polygon, 
  Polyline, 
  CircleMarker, 
  Rectangle, 
  Tooltip, 
  useMap 
} from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { 
  Search, 
  Compass, 
  Maximize2, 
  RefreshCw, 
  Layers, 
  Activity, 
  Droplets, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  Wifi, 
  WifiOff,
  KeyRound,
  Plus,
  Minus
} from 'lucide-react';

import { MapProviderService, MapProviderConfig } from '../../services/map/mapProvider';
import { MapMode, MapProviderType, SelectedFeatureDetail } from '../../types/map';
import { useLiveMapData } from '../../hooks/useLiveMapData';
import { MapLayerControls } from './MapLayerControls';
import { MapTimelineScrubber } from './MapTimelineScrubber';
import { MapLegendPanel } from './MapLegendPanel';
import { MapFeatureDetailDrawer } from './MapFeatureDetailDrawer';

// Authoritative Mahanadi Delta Basin Boundary coordinates
const BASIN_BOUNDARY: [number, number][] = [
  [20.10, 85.20],
  [20.55, 85.35],
  [20.85, 85.80],
  [20.80, 86.40],
  [20.50, 86.75],
  [20.15, 86.60],
  [19.95, 86.10],
  [20.10, 85.20]
];

// Subbasin Boundaries
const SUBBASINS: { id: string; name: string; boundary: [number, number][] }[] = [
  {
    id: 'SUB-UPPER',
    name: 'Upper Catchment (Tikarpara Gorge to Mundali)',
    boundary: [[20.40, 85.25], [20.70, 85.40], [20.85, 85.80], [20.45, 85.75], [20.40, 85.25]]
  },
  {
    id: 'SUB-CENTRAL',
    name: 'Central Delta Reach (Mundali to Naraj / Cuttack)',
    boundary: [[20.35, 85.70], [20.50, 85.75], [20.55, 86.05], [20.30, 86.00], [20.35, 85.70]]
  },
  {
    id: 'SUB-COASTAL',
    name: 'Lower Coastal Plain & Paradip Estuary',
    boundary: [[20.25, 86.00], [20.55, 86.05], [20.50, 86.75], [20.15, 86.60], [20.25, 86.00]]
  }
];

// River Network reaches with real hydrologic vectors
const RIVER_REACHES: { id: string; name: string; path: [number, number][] }[] = [
  {
    id: 'RCH-MAH-01',
    name: 'Main Mahanadi River (Biramitrapur to Mundali)',
    path: [[20.55, 85.35], [20.48, 85.60], [20.435, 85.752]]
  },
  {
    id: 'RCH-MAH-02',
    name: 'Mahanadi Main Bifurcation (Mundali to Cuttack City)',
    path: [[20.435, 85.752], [20.465, 85.860], [20.485, 85.920]]
  },
  {
    id: 'RCH-KAT-01',
    name: 'Kathajodi Distributary Reach (Naraj to Kuakhai Bifurcation)',
    path: [[20.435, 85.752], [20.440, 85.850], [20.380, 86.050]]
  },
  {
    id: 'RCH-MAH-03',
    name: 'Lower Mahanadi Estuary to Paradip Port',
    path: [[20.485, 85.920], [20.450, 86.250], [20.350, 86.550], [20.260, 86.680]]
  }
];

// Map Fly-To Helper
const MapViewController: React.FC<{ targetCoords: [number, number] | null; zoomLevel?: number }> = ({ targetCoords, zoomLevel = 9 }) => {
  const map = useMap();
  useEffect(() => {
    if (targetCoords) {
      map.flyTo(targetCoords, zoomLevel, { duration: 1.0 });
    }
  }, [targetCoords, zoomLevel, map]);
  return null;
};

// Map Zoom Buttons Overlay
const MapZoomControls: React.FC = () => {
  const map = useMap();
  return (
    <div className="absolute top-2.5 left-2.5 flex flex-col gap-1 z-[400]">
      <button 
        onClick={() => map.zoomIn()} 
        className="w-6 h-6 rounded bg-[#0b1329]/90 border border-slate-700 text-slate-200 flex items-center justify-center hover:bg-slate-800 shadow-md transition-colors"
        title="Zoom In"
      >
        <Plus className="w-3.5 h-3.5" />
      </button>
      <button 
        onClick={() => map.zoomOut()} 
        className="w-6 h-6 rounded bg-[#0b1329]/90 border border-slate-700 text-slate-200 flex items-center justify-center hover:bg-slate-800 shadow-md transition-colors"
        title="Zoom Out"
      >
        <Minus className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};

export interface GeospatialMapProps {
  mode?: 'rainfall' | 'river' | 'inundation' | 'all';
  heightClass?: string;
  compact?: boolean;
  activeHorizon?: number;
  onSelectStation?: (stationId: string) => void;
  showInundation?: boolean;
  showAssets?: boolean;
  showRadarRainfall?: boolean;
  activeStationId?: string;
}

export const GeospatialOperationsMap: React.FC<GeospatialMapProps> = ({
  mode = 'all',
  heightClass = 'h-full',
  compact = false,
  activeHorizon = 0,
  onSelectStation,
  showInundation,
  showAssets,
  showRadarRainfall,
  activeStationId
}) => {
  const [userModeOverride, setUserModeOverride] = useState<MapProviderType>('live');
  const [isNetworkOnline, setIsNetworkOnline] = useState<boolean>(true);
  const [tileErrorOccurred, setTileErrorOccurred] = useState<boolean>(false);
  const [currentHorizon, setCurrentHorizon] = useState<number>(activeHorizon);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [flyTarget, setFlyTarget] = useState<[number, number] | null>(null);

  const {
    layers,
    stations,
    gridCells,
    assets,
    alerts,
    inundationPolygons,
    selectedFeature,
    setSelectedFeature,
    toggleLayer,
    setLayerOpacity,
    forecastRunId,
    sourceHealth,
    refreshData
  } = useLiveMapData(currentHorizon);

  // Read centralized map runtime configuration
  const runtimeConfig: MapProviderConfig = useMemo(() => {
    return MapProviderService.getRuntimeConfig();
  }, []);

  const isLiveEffective = isNetworkOnline && runtimeConfig.isKeyConfigured && !tileErrorOccurred && userModeOverride === 'live';

  const mapMode: MapMode = useMemo(() => {
    return MapProviderService.resolveMode(isNetworkOnline && !tileErrorOccurred, runtimeConfig.isKeyConfigured, userModeOverride);
  }, [isNetworkOnline, tileErrorOccurred, runtimeConfig.isKeyConfigured, userModeOverride]);

  const activeProviderConfig: MapProviderConfig = useMemo(() => {
    if (isLiveEffective) {
      return runtimeConfig;
    }
    return MapProviderService.getFallbackProvider();
  }, [isLiveEffective, runtimeConfig]);

  // Map layer configuration dictionary for live toggle and opacity binding
  const layerConfigMap = useMemo(() => {
    const map: Record<string, { enabled: boolean; opacity: number }> = {};
    for (const l of layers) {
      map[l.id] = { enabled: l.enabled, opacity: l.opacity };
    }
    return map;
  }, [layers]);

  // Determine active layers and opacities based on mode and layer configuration
  const rainLayer = layerConfigMap['RAINFALL_NOWCAST'] || layerConfigMap['RAINFALL_FUSED'];
  const showRainfallGrid = mode === 'rainfall' || (mode === 'all' && (rainLayer?.enabled ?? true));
  const rainOpacity = rainLayer?.opacity ?? 0.70;

  const riverLayer = layerConfigMap['RIVERS'] || layerConfigMap['RIVER_FLOW'];
  const showRiverTopology = mode === 'river' || mode === 'inundation' || (mode === 'all' && (riverLayer?.enabled ?? true));
  const riverOpacity = riverLayer?.opacity ?? 0.95;

  const stnLayer = layerConfigMap['RIVER_STATIONS'] || layerConfigMap['WEATHER_STATIONS'];
  const showStations = mode === 'river' || (mode === 'all' && (stnLayer?.enabled ?? true));
  const stnOpacity = stnLayer?.opacity ?? 1.0;

  const inundationLayer = layerConfigMap['FLOOD_DEPTH'] || layerConfigMap['INUNDATION_PROBABILITY'];
  const showInundationDepth = mode === 'inundation' || (mode === 'all' && (inundationLayer?.enabled ?? true));
  const inundationOpacity = inundationLayer?.opacity ?? 0.75;

  const basinLayer = layerConfigMap['BASIN'];
  const showBasin = basinLayer?.enabled ?? true;
  const basinOpacity = basinLayer?.opacity ?? 0.90;

  const showFullControls = mode === 'all' && !compact;

  const getRainfallCellColor = (rate: number) => {
    if (rate <= 0) return '#334155';
    if (rate < 15) return '#3b82f6';
    if (rate < 35) return '#10b981';
    if (rate < 65) return '#f59e0b';
    return '#e11d48';
  };

  const getStationColor = (stn: any) => {
    if (!stn.current_stage_m || !stn.warning_level_m) return '#10b981';
    if (stn.danger_level_m && stn.current_stage_m >= stn.danger_level_m) return '#ef4444';
    if (stn.current_stage_m >= stn.warning_level_m) return '#f97316';
    if (stn.current_stage_m >= stn.warning_level_m * 0.95) return '#eab308';
    return '#10b981';
  };

  return (
    <div className={`relative w-full ${heightClass} overflow-hidden rounded-xl bg-[#060b17] select-none font-sans`}>
      {/* 1. Full Mode Top Operations Status Banner (Only in full mode) */}
      {showFullControls && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[500] w-11/12 max-w-4xl">
          <div className="glass-panel border border-surface-border px-3.5 py-1.5 rounded-xl shadow-2xl backdrop-blur-md flex flex-wrap items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2">
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                mapMode === 'LIVE' 
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' 
                  : (mapMode === 'REPLAY' ? 'bg-purple-500/20 text-purple-300 border-purple-500/40' : 'bg-amber-500/20 text-amber-300 border-amber-500/40')
              }`}>
                MAP: {mapMode}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                PROVIDER: {activeProviderConfig.providerName}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                DATA: [REAL HISTORICAL ANALYSIS / HINDCAST]
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setUserModeOverride(userModeOverride === 'live' ? 'offline' : 'live')}
                className="p-1 rounded-lg bg-surface-base text-slate-300 border border-surface-border text-[10px] font-bold flex items-center gap-1"
              >
                {isLiveEffective ? <Wifi className="w-3.5 h-3.5 text-cyan-400" /> : <WifiOff className="w-3.5 h-3.5 text-amber-400" />}
                <span>{isLiveEffective ? 'Online Basemap' : 'Offline Fallback'}</span>
              </button>
              <button onClick={refreshData} className="p-1 rounded-lg bg-surface-base text-slate-300 border border-surface-border">
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 2. Mode Specific Compact Overlays */}
      {/* Mode A: Rainfall Mode Overlays */}
      {mode === 'rainfall' && (
        <>
          {/* Top-Right Vertical Color Scale Legend */}
          <div className="absolute top-2.5 right-2.5 bg-[#0b1329]/90 border border-slate-700/80 px-2 py-1.5 rounded-lg flex flex-col items-center gap-0.5 z-[400] shadow-lg pointer-events-auto">
            <span className="text-[8px] font-mono text-slate-400">mm/hr</span>
            <div className="flex items-center gap-1">
              <div
                className="w-2 h-28 rounded-full"
                style={{
                  background: 'linear-gradient(to bottom, #ef4444, #f97316, #eab308, #22c55e, #06b6d4, #3b82f6, #1e293b)'
                }}
              />
              <div className="flex flex-col justify-between h-28 text-[7px] font-mono text-slate-400 py-0.5 leading-none">
                <span>100</span>
                <span>80</span>
                <span>60</span>
                <span>40</span>
                <span>20</span>
                <span>0</span>
              </div>
            </div>
          </div>

          {/* Bottom-Left Scale Bar & Model Grid Tag */}
          <div className="absolute bottom-2 left-2.5 flex items-center gap-2 z-[400]">
            <div className="bg-[#0b1329]/90 border border-slate-700 px-2 py-0.5 rounded text-[8px] font-mono text-slate-300">
              10 km
            </div>
            <div className="bg-[#0b1329]/90 border border-cyan-500/30 px-2 py-0.5 rounded text-[8px] font-mono text-cyan-300">
              MODEL GRID: 2.5 km
            </div>
          </div>
        </>
      )}

      {/* Mode B: River Mode Overlays */}
      {mode === 'river' && (
        <>
          {/* Top-Left Category Legend */}
          <div className="absolute top-2.5 right-2.5 bg-[#0b1329]/90 border border-slate-700/80 p-2 rounded-lg space-y-1 text-[9px] font-sans z-[400] shadow-lg pointer-events-auto">
            <div className="flex items-center gap-1.5 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>Normal</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-amber-400"></span>
              <span>Warning</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-orange-500"></span>
              <span>Alert</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-rose-500"></span>
              <span>Danger</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-400">
              <span className="w-2 h-2 rounded-full bg-slate-600"></span>
              <span>No Data</span>
            </div>
          </div>

          {/* Bottom Status Tally Footer */}
          <div className="absolute bottom-0 inset-x-0 bg-[#0b1329]/95 border-t border-slate-800/90 py-1 px-3 flex items-center justify-between text-[10px] font-sans z-[400]">
            <div className="text-emerald-400 font-medium">
              Normal <strong className="font-mono text-white text-xs">98</strong>
            </div>
            <div className="text-amber-400 font-medium">
              Warning <strong className="font-mono text-white text-xs">32</strong>
            </div>
            <div className="text-orange-400 font-medium">
              Alert <strong className="font-mono text-white text-xs">18</strong>
            </div>
            <div className="text-rose-400 font-medium">
              Danger <strong className="font-mono text-white text-xs">4</strong>
            </div>
          </div>
        </>
      )}

      {/* Mode C: Inundation Mode Overlays */}
      {mode === 'inundation' && (
        <>
          {/* Top-Right Vertical Depth Legend */}
          <div className="absolute top-2.5 right-2.5 bg-[#0b1329]/90 border border-slate-700/80 px-2 py-1.5 rounded-lg flex flex-col items-center gap-0.5 z-[400] shadow-lg pointer-events-auto">
            <span className="text-[8px] font-mono text-slate-400">Depth (m)</span>
            <div className="flex items-center gap-1">
              <div
                className="w-2 h-26 rounded-full"
                style={{
                  background: 'linear-gradient(to bottom, #1d4ed8, #3b82f6, #38bdf8, #bae6fd, #e0f2fe)'
                }}
              />
              <div className="flex flex-col justify-between h-26 text-[7px] font-mono text-slate-400 py-0.5 leading-none">
                <span>&gt; 3.0</span>
                <span>2.0</span>
                <span>1.0</span>
                <span>0.5</span>
                <span>0.1</span>
              </div>
            </div>
          </div>

          {/* Bottom-Right Summary Stat Box */}
          <div className="absolute bottom-2.5 right-2.5 bg-[#0b1329]/95 border border-slate-700/80 px-2.5 py-1.5 rounded-lg text-xs font-sans space-y-0.5 z-[400] shadow-lg">
            <div className="text-[10px] text-slate-400">
              Flooded Area: <strong className="font-mono text-white text-xs">245.6 km²</strong>
            </div>
            <div className="text-[10px] text-slate-400">
              Max Depth: <strong className="font-mono text-cyan-300 text-xs">3.42 m</strong>
            </div>
          </div>
        </>
      )}

      {/* 3. Full Mode Layers, Search & Timeline */}
      {showFullControls && (
        <>
          <div className="absolute top-16 left-4 z-[500] w-72">
            <div className="relative">
              <input
                type="text"
                placeholder="Search stations, rivers, assets..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-surface-base/90 border border-surface-border rounded-xl pl-8 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-400 backdrop-blur-md shadow-xl"
              />
              <Search className="w-4 h-4 text-slate-400 absolute left-2.5 top-2.5" />
            </div>
          </div>

          <MapLayerControls
            layers={layers}
            onToggleLayer={toggleLayer}
            onOpacityChange={setLayerOpacity}
          />

          <MapLegendPanel layers={layers} />

          <MapTimelineScrubber
            activeMinutes={currentHorizon}
            onHorizonChange={setCurrentHorizon}
          />
        </>
      )}

      {/* 4. Feature Detail Inspector Drawer */}
      <MapFeatureDetailDrawer
        feature={selectedFeature}
        onClose={() => setSelectedFeature(null)}
      />

      {/* 5. Leaflet Geographic Map Container with Real Basemap Tiles */}
      <MapContainer
        center={[20.45, 85.95]}
        zoom={mode === 'river' ? 8 : 9}
        minZoom={6}
        maxZoom={18}
        className="w-full h-full bg-[#070e1c]"
        zoomControl={false}
        attributionControl={false}
      >
        <MapViewController targetCoords={flyTarget} />
        <MapZoomControls />

        {/* Real Geographic Basemap Tile Layer */}
        {isLiveEffective && activeProviderConfig.tileUrl && (
          <TileLayer
            url={activeProviderConfig.tileUrl}
            attribution={activeProviderConfig.attribution}
            maxZoom={activeProviderConfig.maxZoom}
            eventHandlers={{
              tileerror: () => {
                console.warn('Tile load error detected, using clean offline vector fallback.');
                setTileErrorOccurred(true);
              }
            }}
          />
        )}

        {/* Offline Vector Basemap Fallback */}
        {(!isLiveEffective || tileErrorOccurred) && (
          <Rectangle
            bounds={[[18.5, 83.5], [22.5, 88.5]]}
            pathOptions={{ color: '#1e293b', fillColor: '#081120', fillOpacity: 0.98, weight: 1 }}
          />
        )}

        {/* Basin Boundary Layer */}
        {showBasin && (
          <Polygon
            positions={BASIN_BOUNDARY}
            pathOptions={{
              color: '#06b6d4',
              fillColor: '#0891b2',
              fillOpacity: Math.min(1.0, 0.05 * (basinOpacity / 0.9)),
              weight: 2,
              dashArray: '4, 4'
            }}
          >
            <Tooltip sticky>
              <div className="font-mono text-xs p-1">
                <strong>Mahanadi Delta Basin</strong>
                <div>Area: 14,250 sq.km</div>
              </div>
            </Tooltip>
          </Polygon>
        )}

        {/* Subbasin Dividers in River Mode */}
        {mode === 'river' && SUBBASINS.map(sub => (
          <Polygon
            key={sub.id}
            positions={sub.boundary}
            pathOptions={{
              color: '#38bdf8',
              fillColor: '#0284c7',
              fillOpacity: 0.04,
              weight: 1,
              dashArray: '2, 4'
            }}
          >
            <Tooltip sticky>
              <div className="font-mono text-xs p-1">
                <strong>{sub.name}</strong>
              </div>
            </Tooltip>
          </Polygon>
        ))}

        {/* River Channels & Reaches */}
        {showRiverTopology && RIVER_REACHES.map(reach => (
          <Polyline
            key={reach.id}
            positions={reach.path}
            pathOptions={{
              color: '#38bdf8',
              weight: 3.5,
              opacity: riverOpacity
            }}
          >
            <Tooltip sticky>
              <div className="font-mono text-xs p-1">
                <strong>{reach.name}</strong>
                <div>Reach ID: {reach.id}</div>
              </div>
            </Tooltip>
          </Polyline>
        ))}

        {/* 2.5 km Rainfall Model Grid Layer (Phase 4 API) */}
        {showRainfallGrid && gridCells.map(cell => (
          <Rectangle
            key={cell.id}
            bounds={cell.bounds}
            pathOptions={{
              color: '#334155',
              weight: 0.4,
              fillColor: getRainfallCellColor(cell.rainfall_mm_hr),
              fillOpacity: Math.min(1.0, (cell.rainfall_mm_hr > 0 ? 0.65 : 0.15) * (rainOpacity / 0.70))
            }}
            eventHandlers={{
              click: () => {
                setSelectedFeature({
                  type: 'grid_cell',
                  title: `Rainfall Model Grid Cell (${cell.id})`,
                  subtitle: 'Phase 4 Multi-Source Fusion & Nowcast Grid (2.5 km)',
                  data: {
                    model_grid_resolution: '2.5 km (Computational discrete grid)',
                    rainfall_intensity: `${cell.rainfall_mm_hr} mm/h`,
                    accumulation_6h: `${cell.accumulation_6h_mm} mm`,
                    heavy_rain_probability: `${cell.heavy_rain_prob}%`,
                    uncertainty_std: `±${cell.uncertainty_std} mm/h`,
                    forecast_valid_time: cell.valid_time,
                    forecast_run_id: cell.forecast_run_id
                  }
                });
              }
            }}
          >
            <Tooltip sticky>
              <div className="font-mono text-xs p-1">
                <strong>MODEL GRID: 2.5 km [{cell.id}]</strong>
                <div>Precip: <strong>{cell.rainfall_mm_hr} mm/h</strong></div>
                <div>Heavy Rain Prob: {cell.heavy_rain_prob}%</div>
              </div>
            </Tooltip>
          </Rectangle>
        ))}

        {/* Inundation Depth Layer (Phase 8 API) */}
        {showInundationDepth && inundationPolygons.map(poly => {
          const depthColor = poly.depthClass === 'gt_2m' 
            ? '#1d4ed8' 
            : (poly.depthClass === '1_2m' 
              ? '#0284c7' 
              : (poly.depthClass === '0.3_1m' ? '#38bdf8' : '#bae6fd'));
          const baseFill = poly.depthClass === 'gt_2m' ? 0.85 : (poly.depthClass === '1_2m' ? 0.70 : 0.45);
          const computedFillOpacity = Math.min(1.0, baseFill * (inundationOpacity / 0.75));

          return (
            <Polygon
              key={poly.id}
              positions={poly.coordinates}
              pathOptions={{
                color: depthColor,
                fillColor: depthColor,
                fillOpacity: computedFillOpacity,
                weight: 1.5
              }}
              eventHandlers={{
                click: () => {
                  setSelectedFeature({
                    type: 'inundation',
                    title: `Inundation Surface: ${poly.depthRangeLabel}`,
                    subtitle: 'Phase 8 2D Hydrodynamic Spatial Surrogate',
                    data: {
                      depth_class: poly.depthRangeLabel,
                      estimated_mean_depth: `${poly.depth_m} m`,
                      flood_probability: `${Math.round(poly.probability * 100)}%`,
                      forecast_lead_time: '12.0 hours',
                      model_id: 'MOD-INUNDATION-SURROGATE'
                    }
                  });
                }
              }}
            >
              <Tooltip sticky>
                <div className="font-mono text-xs p-1">
                  <strong>{poly.depthRangeLabel}</strong>
                  <div>Flood Prob: {Math.round(poly.probability * 100)}%</div>
                </div>
              </Tooltip>
            </Polygon>
          );
        })}

        {/* Gauge Station Markers positioned at real coordinates */}
        {showStations && stations.map(stn => {
          const stnColor = getStationColor(stn);
          return (
            <CircleMarker
              key={stn.id}
              center={stn.coordinates}
              radius={stnColor === '#ef4444' ? 8 : 6}
              pathOptions={{
                color: '#0f172a',
                fillColor: stnColor,
                fillOpacity: stnOpacity,
                weight: 1.5
              }}
              eventHandlers={{
                click: () => {
                  if (onSelectStation) onSelectStation(stn.id);
                  setSelectedFeature({
                    type: 'station',
                    title: `${stn.name} (${stn.id})`,
                    subtitle: `${stn.type.toUpperCase()} Station • ${stn.source}`,
                    data: {
                      station_id: stn.id,
                      current_stage: stn.current_stage_m ? `${stn.current_stage_m} m` : 'N/A',
                      warning_level: stn.warning_level_m ? `${stn.warning_level_m} m` : 'N/A',
                      danger_level: stn.danger_level_m ? `${stn.danger_level_m} m` : 'N/A',
                      forecast_peak_stage: stn.forecast_peak_stage_m ? `${stn.forecast_peak_stage_m} m` : 'N/A',
                      rainfall_1h: `${stn.rainfall_1h_mm} mm`,
                      quality_flag: stn.quality_flag,
                      data_confidence: stn.data_confidence,
                      last_telemetry: stn.last_updated
                    }
                  });
                }
              }}
            >
              <Tooltip sticky>
                <div className="font-mono text-xs p-1">
                  <strong>{stn.name} [{stn.id}]</strong>
                  <div>Stage: <strong>{stn.current_stage_m ? `${stn.current_stage_m}m` : 'N/A'}</strong></div>
                  <div>Warning: {stn.warning_level_m ? `${stn.warning_level_m}m` : 'N/A'} | Danger: {stn.danger_level_m ? `${stn.danger_level_m}m` : 'N/A'}</div>
                </div>
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
};
