import React, { useState, useEffect } from 'react';
import { ThemeProvider, useTheme } from './hooks/useTheme';
import { ErrorBoundary } from './components/ErrorBoundary';
import { PermanentBanner } from './components/PermanentBanner';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { OverviewView } from './views/OverviewView';
import { MonsoonMonitorView } from './views/MonsoonMonitorView';
import { RainfallNowcastView } from './views/RainfallNowcastView';
import { RiverForecastView } from './views/RiverForecastView';
import { InundationView } from './views/InundationView';
import { ImpactView } from './views/ImpactView';
import { AlertsView } from './views/AlertsView';
import { DataHealthView } from './views/DataHealthView';
import { ReplayView } from './views/ReplayView';
import { StationsView } from './views/StationsView';
import { ForecastRunsView } from './views/ForecastRunsView';
import { ModelsView } from './views/ModelsView';
import { ArchitectureView } from './views/ArchitectureView';
import { SettingsView } from './views/SettingsView';
import { PublicPortalView } from './views/PublicPortalView';
import { AdminSecurityView } from './views/AdminSecurityView';
import { ConfidenceLevel, SystemMode } from './types';

const MainAppContent: React.FC = () => {
  const [activeView, setActiveView] = useState<string>('overview');
  const [lang, setLang] = useState<'en' | 'hi'>('en');
  const [lowBandwidth, setLowBandwidth] = useState<boolean>(false);
  const [systemMode, setSystemMode] = useState<SystemMode>('SIMULATION');
  const [activeRunId, setActiveRunId] = useState<string>('RUN-20260827-OD01');
  const [dataConfidence, setDataConfidence] = useState<ConfidenceLevel>('HIGH');
  const [alertSummary, setAlertSummary] = useState<{
    active_alerts: number;
    active_warnings: number;
    total_active: number;
  }>({
    active_alerts: 0,
    active_warnings: 0,
    total_active: 0
  });
  const { effectiveTheme } = useTheme();

  const fetchAlertSummary = async () => {
    try {
      const res = await fetch('/api/v1/alerts/summary');
      if (res.ok) {
        const data = await res.json();
        setAlertSummary({
          active_alerts: data.active_alerts || 0,
          active_warnings: data.active_warnings || 0,
          total_active: data.total_active ?? ((data.active_alerts || 0) + (data.active_warnings || 0))
        });
      }
    } catch (err) {
      console.warn('Alert summary fetch error (fallback to defaults):', err);
    }
  };

  useEffect(() => {
    fetchAlertSummary();
    const interval = setInterval(fetchAlertSummary, 10000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket Live Connection (with automatic exponential backoff reconnect and fallback to periodic polling)
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: any = null;
    let delay = 1000;
    const maxDelay = 30000;
    let isUnmounted = false;

    const connect = () => {
      if (isUnmounted) return;
      try {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsHost = window.location.host || '127.0.0.1:8000';
        ws = new WebSocket(`${wsProtocol}//${wsHost}/ws/v1/live`);

        ws.onopen = () => {
          delay = 1000;
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'TELEMETRY_TICK') {
              if (data.forecast_run_id) setActiveRunId(data.forecast_run_id);
              if (data.data_health_summary?.overall_confidence) {
                setDataConfidence(data.data_health_summary.overall_confidence);
              }
              if (data.alert_summary) {
                setAlertSummary({
                  active_alerts: data.alert_summary.active_alerts || 0,
                  active_warnings: data.alert_summary.active_warnings || 0,
                  total_active: data.alert_summary.total_active ?? ((data.alert_summary.active_alerts || 0) + (data.alert_summary.active_warnings || 0))
                });
              }
            } else if (['ALERT_CREATED', 'ALERT_STATE_CHANGED', 'ALERT_CANDIDATE_CREATED', 'DEMO_STAGE_ADVANCE', 'DEMO_RESET', 'ALERT_ACKNOWLEDGED', 'ALERT_DISMISSED', 'ALERT_INCIDENT_UPDATED'].includes(data.type)) {
              fetchAlertSummary();
            }
          } catch (e) {
            console.warn('WS frame parse warning:', e);
          }
        };

        ws.onerror = () => {
          // Socket error will trigger onclose
        };

        ws.onclose = () => {
          if (!isUnmounted) {
            reconnectTimer = setTimeout(() => {
              delay = Math.min(delay * 1.5, maxDelay);
              connect();
            }, delay);
          }
        };
      } catch (e) {
        if (!isUnmounted) {
          reconnectTimer = setTimeout(() => {
            delay = Math.min(delay * 1.5, maxDelay);
            connect();
          }, delay);
        }
      }
    };

    connect();

    return () => {
      isUnmounted = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) {
        ws.onclose = null;
        ws.close();
      }
    };
  }, []);

  const handleRefreshRun = async () => {
    try {
      const res = await fetch('/api/v1/forecast/run', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setActiveRunId(data.forecast_run_id);
      }
    } catch (err) {
      console.warn('Forecast run refresh error:', err);
      setActiveRunId(`RUN-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${Math.random().toString(36).substring(2, 7)}`);
    }
  };

  const renderActiveView = () => {
    switch (activeView) {
      case 'overview':
        return <OverviewView lang={lang} onNavigate={setActiveView} />;
      case 'public-portal':
        return <PublicPortalView />;
      case 'monsoon-monitor':
        return <MonsoonMonitorView />;
      case 'rainfall-nowcast':
        return <RainfallNowcastView />;
      case 'river-forecast':
        return <RiverForecastView />;
      case 'inundation':
        return <InundationView />;
      case 'impact':
        return <ImpactView />;
      case 'alerts':
        return <AlertsView />;
      case 'data-health':
        return <DataHealthView />;
      case 'replay':
        return <ReplayView />;
      case 'stations':
        return <StationsView />;
      case 'forecast-runs':
        return <ForecastRunsView />;
      case 'models':
        return <ModelsView />;
      case 'architecture':
        return <ArchitectureView />;
      case 'admin':
        return <AdminSecurityView />;
      case 'settings':
        return <SettingsView />;
      default:
        return <OverviewView lang={lang} onNavigate={setActiveView} />;
    }
  };

  return (
    <div className={`min-h-screen flex flex-col ${effectiveTheme === 'light' ? 'bg-slate-100 text-slate-900' : 'bg-[#060b17] text-slate-100'} ${lowBandwidth ? 'low-bandwidth-mode' : ''}`}>
      {/* Permanent Warning & Disclaimer Banner */}
      <PermanentBanner lang={lang} />

      {/* Operations Top Header */}
      <Header
        lang={lang}
        setLang={setLang}
        lowBandwidth={lowBandwidth}
        setLowBandwidth={setLowBandwidth}
        systemMode={systemMode}
        activeRunId={activeRunId}
        dataConfidence={dataConfidence}
        onRefreshRun={handleRefreshRun}
        activeAlertCount={alertSummary.total_active}
        onNavigateToAlerts={() => setActiveView('alerts')}
        onNavigateToAdmin={() => setActiveView('admin')}
      />

      {/* Main Workspace: Sidebar + Operational Canvas */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar activeView={activeView} setActiveView={setActiveView} lang={lang} alertCount={alertSummary.total_active} />

        <main className={`flex-1 p-3 md:p-4 overflow-y-auto w-full ${effectiveTheme === 'light' ? 'bg-slate-50' : 'bg-[#080d1a]'}`}>
          <ErrorBoundary>
            {renderActiveView()}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <MainAppContent />
    </ThemeProvider>
  );
};
