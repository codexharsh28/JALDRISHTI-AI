import React, { useState, useEffect } from 'react';
import { Shield, Bell, Moon, Sun, Laptop, ChevronDown, Clock, Key } from 'lucide-react';
import { translations } from '../translations';
import { ConfidenceLevel, SystemMode } from '../types';
import { useTheme } from '../hooks/useTheme';

interface Props {
  lang: 'en' | 'hi';
  setLang: (lang: 'en' | 'hi') => void;
  lowBandwidth: boolean;
  setLowBandwidth: (val: boolean) => void;
  systemMode: SystemMode;
  activeRunId: string;
  dataConfidence: ConfidenceLevel;
  onRefreshRun?: () => void;
  activeAlertCount?: number;
  onNavigateToAlerts?: () => void;
  onNavigateToAdmin?: () => void;
}

export const Header: React.FC<Props> = ({
  lang,
  setLang,
  lowBandwidth,
  setLowBandwidth,
  systemMode,
  activeRunId,
  dataConfidence,
  onRefreshRun,
  activeAlertCount = 0,
  onNavigateToAlerts,
  onNavigateToAdmin
}) => {
  const t = translations[lang];
  const [currentTime, setCurrentTime] = useState<string>('');
  const { theme, effectiveTheme, setTheme, toggleTheme } = useTheme();
  const [showThemeMenu, setShowThemeMenu] = useState(false);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const options: Intl.DateTimeFormatOptions = {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
        timeZoneName: 'short'
      };
      setCurrentTime(now.toLocaleString('en-IN', options).replace('GMT+5:30', 'IST'));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="bg-[#0b1329] dark:bg-[#0b1329] border-b border-slate-800/80 px-4 py-2.5 flex items-center justify-between gap-4 sticky top-0 z-40 shrink-0 select-none shadow-md">
      {/* Brand Title with Drop Logo */}
      <div className="flex items-center gap-3 min-w-max">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 via-blue-500 to-indigo-600 flex items-center justify-center shadow-md shadow-cyan-500/20 ring-1 ring-cyan-400/30">
          <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
          </svg>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-extrabold tracking-tight text-white font-sans">
              JALDRISHTI AI
            </h1>
          </div>
          <p className="text-[11px] text-slate-400 font-sans tracking-wide">
            Hydrometeorological Intelligence System
          </p>
        </div>
      </div>

      {/* Center Operational Status & Live Clock */}
      <div className="hidden sm:flex items-center gap-4 text-xs font-sans">
        {/* System Status Pill */}
        <div className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-2 text-emerald-400 font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="tracking-wide uppercase text-[11px]">
            {systemMode === 'LIVE_DATA' ? 'SYSTEM LIVE' : (systemMode === 'REPLAY' ? 'SYSTEM REPLAY' : 'SYSTEM OPERATIONAL')}
          </span>
        </div>

        {/* Live Clock */}
        <div className="flex items-center gap-1.5 text-slate-300 font-sans text-xs bg-slate-900/60 px-3 py-1 rounded-full border border-slate-800">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>{currentTime || '27 Aug 2026, 11:25 AM IST'}</span>
        </div>
      </div>

      {/* Right Controls (Notifications, Theme, Admin Profile) */}
      <div className="flex items-center gap-2.5 min-w-max">
        {/* Notifications Bell */}
        <button
          onClick={onNavigateToAlerts}
          title="Active Alerts & Warnings"
          aria-label="View Active Alerts"
          className="relative p-2 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition-all focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
        >
          <Bell className="w-4 h-4" />
          {activeAlertCount > 0 && (
            <span className="absolute -top-1 -right-1 px-1.5 py-0.2 bg-rose-500 text-white text-[10px] font-bold rounded-full border border-slate-900 shadow-sm">
              {activeAlertCount}
            </span>
          )}
        </button>

        {/* Theme Button with Dropdown / Quick Toggle */}
        <div className="relative">
          <button
            onClick={toggleTheme}
            title={`Current theme: ${theme.toUpperCase()} (Click to toggle)`}
            aria-label={`Toggle theme, current is ${theme}`}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white text-xs flex items-center gap-1.5 transition-all font-sans focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
          >
            {effectiveTheme === 'dark' ? (
              <Moon className="w-3.5 h-3.5 text-cyan-400" />
            ) : (
              <Sun className="w-3.5 h-3.5 text-amber-400" />
            )}
            <span className="capitalize">{theme === 'system' ? 'Auto' : theme}</span>
          </button>
        </div>

        {/* Admin / Security Navigation Button */}
        <button
          onClick={onNavigateToAdmin}
          title="Open Admin & Security Operations Console"
          aria-label="Open Admin & Security Console"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-950/60 hover:bg-indigo-900/80 border border-indigo-500/40 text-indigo-200 hover:text-white text-xs font-semibold cursor-pointer transition-all shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400/50"
        >
          <div className="w-5 h-5 rounded-full bg-indigo-600 flex items-center justify-center text-[10px] text-white font-bold">
            <Key className="w-3 h-3" />
          </div>
          <span>Admin</span>
        </button>
      </div>
    </header>
  );
};
