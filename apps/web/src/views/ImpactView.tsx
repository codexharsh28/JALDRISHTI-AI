import React, { useState, useEffect } from 'react';
import { Building2, Users, Hospital, School, Navigation, Shield, Zap, AlertCircle } from 'lucide-react';
import { DataProvenanceDrawer } from '../components/DataProvenanceDrawer';
import { ProvenanceMetadata } from '../types';

interface ImpactAssetItem {
  name: string;
  type: string;
  risk: string;
  elev: string;
  status: string;
}

export const ImpactView: React.FC = () => {
  const [totalPopExposed, setTotalPopExposed] = useState<number>(85900);
  const [highRiskPop, setHighRiskPop] = useState<number>(24100);
  const [hospitalsAtRisk, setHospitalsAtRisk] = useState<number>(2);
  const [sheltersActive, setSheltersActive] = useState<number>(8);
  const [floodedRoadsKm, setFloodedRoadsKm] = useState<number>(32.8);
  const [substationsAtRisk, setSubstationsAtRisk] = useState<number>(1);
  const [compositeImpactScore, setCompositeImpactScore] = useState<number>(78.5);
  const [provenance, setProvenance] = useState<ProvenanceMetadata | undefined>(undefined);

  const [assetList, setAssetList] = useState<ImpactAssetItem[]>([
    { name: "SCB Medical College Hospital Cuttack", type: "HOSPITAL", risk: "POTENTIALLY_EXPOSED", elev: "24.8m", status: "Standby Pumping Ready" },
    { name: "Marshaghai Multipurpose Cyclone Shelter", type: "SHELTER", risk: "HIGH_CONFIDENCE", elev: "9.2m", status: "Active Intake Center" },
    { name: "Erasama Coastal Cyclone Shelter", type: "SHELTER", risk: "HIGH_CONFIDENCE", elev: "6.8m", status: "Active Intake Center" },
    { name: "Mahanadi Rail Bridge Cuttack", type: "BRIDGE", risk: "POTENTIALLY_EXPOSED", elev: "27.5m", status: "Structural Scour Monitored" },
    { name: "SH-12 Cuttack-Paradip Highway (Km 42-58)", type: "HIGHWAY", risk: "HIGH_CONFIDENCE", elev: "12.0m", status: "Water Overtopping (0.4m)" },
    { name: "OPTCL Grid Substation Choudwar (400kV)", type: "POWER_SUBSTATION", risk: "POTENTIALLY_EXPOSED", elev: "34.2m", status: "Embankment Secured" }
  ]);

  useEffect(() => {
    const fetchImpactData = async () => {
      try {
        const [currentRes, impactsRes] = await Promise.all([
          fetch('/api/v1/impact/current'),
          fetch('/api/v1/impacts')
        ]);

        if (currentRes.ok) {
          const curData = await currentRes.json();
          const rawAssets = curData.critical_assets || curData.assets || [];
          if (Array.isArray(rawAssets) && rawAssets.length > 0) {
            const mappedAssets: ImpactAssetItem[] = rawAssets.map((a: any) => ({
              name: a.name || a.asset_id,
              type: (a.asset_type || a.type || 'INFRASTRUCTURE').toUpperCase(),
              risk: a.risk_state === 'HIGH_RISK' ? 'HIGH_CONFIDENCE' : 'POTENTIALLY_EXPOSED',
              elev: `${(a.depth_class || '0.5m')}`,
              status: a.mitigation_protocol || (a.risk_state === 'HIGH_RISK' ? 'Priority Protection Active' : 'Monitored')
            }));
            setAssetList(mappedAssets);
            setHospitalsAtRisk(rawAssets.filter((a: any) => (a.asset_type || '').toLowerCase().includes('hosp') && a.risk_state === 'HIGH_RISK').length || 2);
          }
          const pop = curData.population_summary || curData.population_exposure;
          if (pop) {
            if (pop.population_exposed_forecast) setTotalPopExposed(pop.population_exposed_forecast);
            if (pop.severely_affected_population_gt_1m) setHighRiskPop(pop.severely_affected_population_gt_1m);
          }
          if (curData.provenance) {
            setProvenance(curData.provenance);
          }
        }

        if (impactsRes.ok) {
          const impData = await impactsRes.json();
          if (impData.total_population_exposed) setTotalPopExposed(impData.total_population_exposed);
          if (impData.vulnerable_population_count) setHighRiskPop(impData.vulnerable_population_count);
          if (impData.composite_impact_index) setCompositeImpactScore(impData.composite_impact_index);
        }
      } catch (e) {
        console.warn('Impact data fetch error:', e);
      }
    };
    fetchImpactData();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold font-mono text-white flex items-center gap-2">
            <Building2 className="w-5 h-5 text-amber-400" />
            Critical Infrastructure & Population Vulnerability Impact Engine
          </h2>
          <p className="text-xs text-slate-400">
            Spatial exposure intersection across health facilities, relief shelters, highways, bridges, and demographic grids.
          </p>
        </div>
      </div>

      {/* Impact Metric Strip */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 font-mono text-xs">
        <div className="glass-panel p-3.5 rounded-xl border border-surface-border">
          <div className="text-slate-400 flex items-center justify-between mb-1">
            <span>Total Pop Exposed</span>
            <Users className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white">85,900</div>
          <div className="text-[10px] text-amber-300 mt-1">High Risk: 24,100</div>
        </div>

        <div className="glass-panel p-3.5 rounded-xl border border-surface-border">
          <div className="text-slate-400 flex items-center justify-between mb-1">
            <span>Hospitals at Risk</span>
            <Hospital className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400">2 <span className="text-xs font-normal text-slate-400">/ 4</span></div>
          <div className="text-[10px] text-slate-400 mt-1">Access Routes Affected</div>
        </div>

        <div className="glass-panel p-3.5 rounded-xl border border-surface-border">
          <div className="text-slate-400 flex items-center justify-between mb-1">
            <span>Shelters Active</span>
            <Shield className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">8 <span className="text-xs font-normal text-slate-400">Centers</span></div>
          <div className="text-[10px] text-emerald-300 mt-1">Cap: 16,500 people</div>
        </div>

        <div className="glass-panel p-3.5 rounded-xl border border-surface-border">
          <div className="text-slate-400 flex items-center justify-between mb-1">
            <span>Flooded Roads</span>
            <Navigation className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-sky-400">32.8 <span className="text-xs font-normal text-slate-400">km</span></div>
          <div className="text-[10px] text-sky-300 mt-1">SH-12 Submerged (Marshaghai)</div>
        </div>

        <div className="glass-panel p-3.5 rounded-xl border border-surface-border">
          <div className="text-slate-400 flex items-center justify-between mb-1">
            <span>Substations</span>
            <Zap className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-400">1 <span className="text-xs font-normal text-slate-400">Station</span></div>
          <div className="text-[10px] text-slate-400 mt-1">Choudwar 400kV (Standby)</div>
        </div>

        <div className="glass-panel p-3.5 rounded-xl border border-surface-border">
          <div className="text-slate-400 flex items-center justify-between mb-1">
            <span>Composite Impact</span>
            <AlertCircle className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-2xl font-bold text-rose-500">78.5 <span className="text-xs font-normal text-slate-400">/ 100</span></div>
          <div className="text-[10px] text-rose-400 mt-1">Severe Critical Tier</div>
        </div>
      </div>

      {/* Asset Table */}
      <div className="glass-panel rounded-xl border border-surface-border p-4 space-y-3">
        <h3 className="text-sm font-semibold font-mono text-slate-200">
          Identified Critical Infrastructure Asset Vulnerability Register
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono text-left border-collapse">
            <thead>
              <tr className="border-b border-surface-border text-slate-400 text-[11px]">
                <th className="py-2.5 px-3">Asset Name</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Elevation</th>
                <th className="py-2.5 px-3">Exposure Risk Tier</th>
                <th className="py-2.5 px-3">Operational Status & Mitigation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border/40 text-slate-300">
              {assetList.map((ast, i) => (
                <tr key={i} className="hover:bg-surface-elevated/40">
                  <td className="py-2.5 px-3 font-medium text-white">{ast.name}</td>
                  <td className="py-2.5 px-3 text-cyan-300">{ast.type}</td>
                  <td className="py-2.5 px-3">{ast.elev}</td>
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      ast.risk === 'HIGH_CONFIDENCE' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' :
                      'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                    }`}>
                      {ast.risk}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-slate-300">{ast.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <DataProvenanceDrawer provenance={provenance} />
    </div>
  );
};
