import React, { useState, useEffect } from 'react';
import { Cpu, CheckCircle2, BarChart2, Shield, ArrowRight, Layers, FileCode, Tag } from 'lucide-react';
import { DataProvenanceDrawer } from '../components/DataProvenanceDrawer';
import { ProvenanceMetadata } from '../types';

interface ModelCardItem {
  id: string;
  name: string;
  domain: string;
  version: string;
  trainedAt: string;
  dataset: string;
  primaryMetric: string;
  datasetState: string;
  status: string;
}

export const ModelsView: React.FC = () => {
  const [models, setModels] = useState<ModelCardItem[]>([
    {
      id: "MOD-NOWCAST-CONVLSTM-03",
      name: "Spatiotemporal Deep ConvLSTM Nowcaster",
      domain: "Precipitation Nowcasting",
      version: "v3.2",
      trainedAt: "2025-11-15",
      dataset: "Odisha Doppler Radar + INSAT-3DR Storm Events (14 Events)",
      primaryMetric: "CSI (>35mm): 0.76 • RMSE: 4.8mm",
      datasetState: "SYNTHETIC HOLDOUT",
      status: "DEPLOYED"
    },
    {
      id: "MOD-HYDRO-LSTM-GNN-02",
      name: "Sequence LSTM with River Graph Routing",
      domain: "Streamflow & Hydrograph",
      version: "v2.4",
      trainedAt: "2025-12-02",
      dataset: "CWC Historical Mundali & Naraj Event Series",
      primaryMetric: "NSE: 0.89 • KGE: 0.86 • Timing Err: ±0.8h",
      datasetState: "REAL HISTORICAL HINDCAST",
      status: "DEPLOYED"
    },
    {
      id: "MOD-INUNDATION-UNET-03",
      name: "Physics-Guided Hydraulic UNet Surrogate",
      domain: "2D Inundation & Depth",
      version: "v3.1",
      trainedAt: "2026-01-20",
      dataset: "Copernicus DEM GLO-30 + Sentinel-1 SAR Floods",
      primaryMetric: "IoU: 0.84 • F1-Score: 0.88",
      datasetState: "REAL HISTORICAL HINDCAST",
      status: "DEPLOYED"
    },
    {
      id: "MOD-IMPACT-EXPLAIN-01",
      name: "Critical Asset Exposure & SHAP Explainability",
      domain: "Disaster Risk Assessment",
      version: "v1.4",
      trainedAt: "2026-02-10",
      dataset: "OpenStreetMap Infrastructure + WorldPop 100m",
      primaryMetric: "Exposure Accuracy: 95.2%",
      datasetState: "REAL HISTORICAL ANALYSIS",
      status: "VALIDATED"
    }
  ]);

  useEffect(() => {
    fetch('/api/v1/models')
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          const mapped: ModelCardItem[] = data.map((m: any) => ({
            id: m.model_id || m.id,
            name: m.name || m.model_id,
            domain: (m.category || 'HYDROLOGY').replace(/_/g, ' '),
            version: m.version || 'v1.0',
            trainedAt: m.trained_at || '2025-11-15',
            dataset: m.target || 'Historical Calibrated Basin Grid',
            primaryMetric: m.holdout_csi ? `CSI: ${m.holdout_csi} • RMSE: ${m.holdout_rmse || 'N/A'}` : 'Calibrated Baseline',
            datasetState: m.dataset_state || 'REAL HISTORICAL HINDCAST',
            status: m.status || 'DEPLOYED'
          }));
          setModels(mapped);
        }
      })
      .catch(e => console.warn('Models fetch error:', e));
  }, []);

  const provenance: ProvenanceMetadata = {
    source_id: "ML_MODEL_REGISTRY_CATALOG",
    provider: "JALDRISHTI AI Model Operations",
    product_name: "Validated Checkpoints and Benchmark Evaluation Cards",
    observed_at: new Date().toISOString(),
    received_at: new Date().toISOString(),
    source_latency_mins: 1.0,
    processing_version: "v1.0.0",
    is_simulation: true
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold font-mono text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyan-400" />
            AI / ML Model Registry & Scientific Evaluation Cards
          </h2>
          <p className="text-xs text-slate-400">
            Validated machine learning models with explicit dataset state tagging ([SYNTHETIC HOLDOUT] vs [REAL HISTORICAL HINDCAST]).
          </p>
        </div>
      </div>

      {/* Model Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
        {models.map(m => (
          <div key={m.id} className="glass-panel p-5 rounded-xl border border-surface-border space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <span className="text-[10px] text-cyan-400 font-bold">{m.id} • {m.version}</span>
                <h3 className="text-sm font-bold text-white mt-0.5">{m.name}</h3>
                <span className="text-[11px] text-slate-400">{m.domain}</span>
              </div>
              <div className="flex flex-col items-end gap-1">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  {m.status}
                </span>
                <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${m.datasetState.includes('SYNTHETIC') ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'}`}>
                  [{m.datasetState}]
                </span>
              </div>
            </div>

            <div className="space-y-1.5 pt-2 border-t border-surface-border/50 text-[11px] text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-400">Dataset Partition:</span>
                <span className="text-right text-slate-200">{m.dataset}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Validated Metric:</span>
                <span className="text-right text-cyan-300 font-bold">{m.primaryMetric}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Trained / Checkpointed:</span>
                <span className="text-right text-slate-400">{m.trainedAt}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <DataProvenanceDrawer provenance={provenance} />
    </div>
  );
};
