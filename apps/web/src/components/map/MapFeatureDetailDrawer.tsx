import React from 'react';
import { X, ExternalLink, ShieldAlert, Activity, Droplets, Building, Compass } from 'lucide-react';
import { SelectedFeatureDetail } from '../../types/map';
import { DataProvenanceDrawer } from '../DataProvenanceDrawer';

interface Props {
  feature: SelectedFeatureDetail | null;
  onClose: () => void;
  onNavigateDetail?: (view: string) => void;
}

export const MapFeatureDetailDrawer: React.FC<Props> = ({ feature, onClose, onNavigateDetail }) => {
  if (!feature) return null;

  const getIcon = () => {
    switch (feature.type) {
      case 'grid_cell': return <Droplets className="w-5 h-5 text-cyan-400" />;
      case 'station': return <Activity className="w-5 h-5 text-emerald-400" />;
      case 'asset': return <Building className="w-5 h-5 text-purple-400" />;
      case 'alert': return <ShieldAlert className="w-5 h-5 text-rose-400" />;
      default: return <Compass className="w-5 h-5 text-cyan-400" />;
    }
  };

  return (
    <div className="absolute top-4 right-4 z-[500] max-w-sm w-96 font-mono text-xs">
      <div className="glass-panel border border-surface-border rounded-xl shadow-2xl backdrop-blur-md overflow-hidden animate-in slide-in-from-right-4 duration-200">
        {/* Header */}
        <div className="p-3.5 bg-surface-base/90 border-b border-surface-border/60 flex items-start justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-surface-border/40 border border-surface-border">
              {getIcon()}
            </div>
            <div>
              <span className="text-[10px] text-cyan-400 font-bold uppercase tracking-wider">
                {feature.type.replace('_', ' ')}
              </span>
              <h3 className="text-sm font-bold text-slate-100 leading-tight">{feature.title}</h3>
              <p className="text-[11px] text-slate-400">{feature.subtitle}</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-surface-border text-slate-400 hover:text-slate-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Metric Key-Value List */}
        <div className="p-3.5 space-y-2 max-h-72 overflow-y-auto">
          {Object.entries(feature.data).map(([key, val]) => (
            <div key={key} className="flex justify-between items-center py-1 border-b border-surface-border/30 text-[11px]">
              <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}:</span>
              <span className="text-slate-100 font-bold text-right">{String(val)}</span>
            </div>
          ))}
        </div>

        {/* Provenance Record */}
        {feature.provenance && (
          <div className="px-3.5 pb-3">
            <DataProvenanceDrawer provenance={feature.provenance} />
          </div>
        )}
      </div>
    </div>
  );
};
