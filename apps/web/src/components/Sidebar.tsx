import React from 'react';
import {
  LayoutDashboard,
  Activity,
  Cloud,
  AlertTriangle,
  Waves,
  MapPin,
  Cpu,
  Database,
  PlayCircle,
  FileText,
  Settings,
  BarChart2,
  Check,
  Shield
} from 'lucide-react';
import { translations } from '../translations';

interface Props {
  activeView: string;
  setActiveView: (view: string) => void;
  lang: 'en' | 'hi';
  alertCount?: number;
  ingestionStats?: {
    rainfallFeeds: string;
    riverGauges: string;
    satellites: string;
    weatherModels: string;
    status: string;
  };
  systemHealthPct?: number;
}

export const Sidebar: React.FC<Props> = ({
  activeView,
  setActiveView,
  lang,
  alertCount = 0,
  ingestionStats = {
    rainfallFeeds: '8 / 8',
    riverGauges: '152 / 152',
    satellites: '6 / 6',
    weatherModels: '3 / 3',
    status: 'Live'
  },
  systemHealthPct = 98
}) => {
  const t = translations[lang];

  const navItems = [
    { id: 'overview', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'public-portal', label: 'Citizen Safety Portal', icon: AlertTriangle },
    { id: 'monsoon-monitor', label: 'Live Monitor', icon: Activity },
    { id: 'rainfall-nowcast', label: 'Forecasts', icon: Cloud },
    { id: 'alerts', label: 'Alerts & Warnings', icon: AlertTriangle, badge: alertCount },
    { id: 'stations', label: 'River Basins', icon: Waves },
    { id: 'inundation', label: 'Inundation Map', icon: MapPin },
    { id: 'models', label: 'Models', icon: Cpu },
    { id: 'data-health', label: 'Data Sources', icon: Database },
    { id: 'replay', label: 'Replay System', icon: PlayCircle },
    { id: 'forecast-runs', label: 'Reports', icon: FileText },
    { id: 'admin', label: 'Admin & Security', icon: Shield },
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'architecture', label: 'System Status', icon: BarChart2 }
  ];

  return (
    <aside className="w-60 bg-[#080e1e] border-r border-slate-800/80 flex flex-col justify-between h-[calc(100vh-3.75rem)] shrink-0 select-none overflow-y-auto">
      {/* Top Navigation Links */}
      <div className="p-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id || (activeView === 'overview' && item.id === 'overview');
          return (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-[#1b5bf7] text-white shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <div className="flex items-center gap-3 min-w-0">
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span className="truncate">{item.label}</span>
              </div>
              {item.badge !== undefined && item.badge > 0 && (
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                  isActive ? 'bg-white text-[#1b5bf7]' : 'bg-rose-500 text-white'
                }`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Lower Operational Status Panels */}
      <div className="p-3 space-y-3 border-t border-slate-800/80 bg-[#060b17]/80">
        {/* Data Ingestion Card */}
        <div className="p-2.5 rounded-lg bg-[#0d1527] border border-slate-800/90 text-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold text-slate-200 text-[11px]">Data Ingestion</span>
            <span className="text-emerald-400 font-semibold text-[11px] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              {ingestionStats.status}
            </span>
          </div>
          <div className="space-y-1.5 text-[10px] font-sans">
            <div className="flex items-center justify-between text-slate-300">
              <span className="text-slate-400">Rainfall Feeds</span>
              <div className="flex items-center gap-1.5">
                <span className="font-mono">{ingestionStats.rainfallFeeds}</span>
                <span className="w-3.5 h-3.5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[9px] font-bold">✓</span>
              </div>
            </div>
            <div className="flex items-center justify-between text-slate-300">
              <span className="text-slate-400">River Gauges</span>
              <div className="flex items-center gap-1.5">
                <span className="font-mono">{ingestionStats.riverGauges}</span>
                <span className="w-3.5 h-3.5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[9px] font-bold">✓</span>
              </div>
            </div>
            <div className="flex items-center justify-between text-slate-300">
              <span className="text-slate-400">Satellites</span>
              <div className="flex items-center gap-1.5">
                <span className="font-mono">{ingestionStats.satellites}</span>
                <span className="w-3.5 h-3.5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[9px] font-bold">✓</span>
              </div>
            </div>
            <div className="flex items-center justify-between text-slate-300">
              <span className="text-slate-400">Weather Models</span>
              <div className="flex items-center gap-1.5">
                <span className="font-mono">{ingestionStats.weatherModels}</span>
                <span className="w-3.5 h-3.5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[9px] font-bold">✓</span>
              </div>
            </div>
          </div>
        </div>

        {/* System Health Circular Widget */}
        <div className="p-2.5 rounded-lg bg-[#0d1527] border border-slate-800/90 flex items-center gap-3">
          <div className="relative w-11 h-11 shrink-0 flex items-center justify-center">
            {/* SVG circular progress */}
            <svg className="w-11 h-11 transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-slate-800"
                strokeWidth="3"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="text-emerald-400 transition-all duration-1000 ease-out"
                strokeDasharray={`${systemHealthPct}, 100`}
                strokeWidth="3"
                strokeLinecap="round"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <span className="absolute text-[10px] font-bold text-white font-mono">{systemHealthPct}%</span>
          </div>
          <div>
            <div className="text-[11px] font-bold text-slate-200">System Health</div>
            <div className="text-[10px] text-emerald-400 font-medium">All Systems Healthy</div>
          </div>
        </div>
      </div>
    </aside>
  );
};
