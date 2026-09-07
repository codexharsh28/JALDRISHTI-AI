import React, { useState, useEffect, useCallback } from 'react';
import { 
  Shield, 
  Lock, 
  Key, 
  Activity, 
  AlertTriangle, 
  CheckCircle2, 
  RefreshCw, 
  Database, 
  Server, 
  Users, 
  Radio, 
  Eye, 
  EyeOff, 
  FileText,
  Cpu,
  BellRing,
  Wifi,
  Zap,
  HardDrive,
  Filter,
  Search,
  Check,
  XCircle,
  ArrowDownCircle,
  ShieldCheck,
  LogOut,
  ChevronRight,
  AlertCircle,
  HelpCircle,
  Layers,
  Clock,
  Send,
  Sliders
} from 'lucide-react';

export type AdminTab = 
  | 'overview' 
  | 'alerts' 
  | 'datasources' 
  | 'security' 
  | 'database' 
  | 'eventbus' 
  | 'websocket' 
  | 'notifications' 
  | 'models' 
  | 'audit';

export const AdminSecurityView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');
  
  // Auth state
  const [tokenInput, setTokenInput] = useState<string>(() => {
    return localStorage.getItem('jaldrishti_admin_token') || '';
  });
  const [usernameInput, setUsernameInput] = useState<string>('admin');
  const [passwordInput, setPasswordInput] = useState<string>('');
  const [loginRole, setLoginRole] = useState<'OPERATOR' | 'ADMIN'>('ADMIN');
  const [showToken, setShowToken] = useState<boolean>(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isAuthorized, setIsAuthorized] = useState<boolean>(false);
  const [sessionUser, setSessionUser] = useState<string>('ADMIN_USER');
  const [sessionRole, setSessionRole] = useState<string>('ADMIN');

  // Observability & Section Data
  const [securityStatus, setSecurityStatus] = useState<any | null>(null);
  const [databaseStats, setDatabaseStats] = useState<any | null>(null);
  const [eventBusMetrics, setEventBusMetrics] = useState<any | null>(null);
  const [websocketMetrics, setWebsocketMetrics] = useState<any | null>(null);
  const [modelsCatalog, setModelsCatalog] = useState<any[]>([]);
  const [notificationHealth, setNotificationHealth] = useState<any | null>(null);
  const [notificationProviders, setNotificationProviders] = useState<any | null>(null);
  const [notificationMetrics, setNotificationMetrics] = useState<any | null>(null);
  const [rateLimitData, setRateLimitData] = useState<any | null>(null);

  // Human Review State
  const [pendingCandidates, setPendingCandidates] = useState<any[]>([]);
  const [reviewActionModal, setReviewActionModal] = useState<any | null>(null);
  const [reviewActionType, setReviewActionType] = useState<'ACKNOWLEDGE' | 'DOWNGRADE' | 'DISMISS'>('ACKNOWLEDGE');
  const [reviewActionReason, setReviewActionReason] = useState<string>('');
  const [reviewTargetSeverity, setReviewTargetSeverity] = useState<string>('WATCH');
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);
  const [actionErrorMsg, setActionErrorMsg] = useState<string | null>(null);

  // Audit Logs State
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [auditTotal, setAuditTotal] = useState<number>(0);
  const [auditFilterAction, setAuditFilterAction] = useState<string>('');
  const [auditFilterStatus, setAuditFilterStatus] = useState<string>('');
  const [auditSearchQuery, setAuditSearchQuery] = useState<string>('');
  const [auditPage, setAuditPage] = useState<number>(0);

  // IMD Telemetry Refresh State
  const [imdCooldown, setImdCooldown] = useState<number>(0);
  const [isRefreshingImd, setIsRefreshingImd] = useState<boolean>(false);
  const [imdRefreshFeedback, setImdRefreshFeedback] = useState<string | null>(null);

  // Auth Verification
  const verifyAdminAccess = useCallback(async (tokenToUse?: string) => {
    const token = tokenToUse !== undefined ? tokenToUse : tokenInput;
    setIsLoading(true);
    setAuthError(null);

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch('/api/v1/security/status', { method: 'GET', headers });

      if (res.status === 200) {
        const data = await res.json();
        setSecurityStatus(data);
        setSessionRole(data.rbac_role || 'OPERATOR');
        setSessionUser(data.operator_id || 'OPERATOR');
        setIsAuthorized(true);
        if (token) {
          localStorage.setItem('jaldrishti_admin_token', token);
        }
      } else if (res.status === 401) {
        setIsAuthorized(false);
        setSecurityStatus(null);
        setAuthError('HTTP 401 Unauthorized: Valid Operator / Administrator Bearer token required.');
      } else if (res.status === 403) {
        setIsAuthorized(false);
        setSecurityStatus(null);
        setAuthError('HTTP 403 Forbidden: Account does not possess OPERATOR or ADMIN role.');
      } else {
        setIsAuthorized(false);
        setSecurityStatus(null);
        setAuthError(`HTTP ${res.status}: Access verification failed.`);
      }
    } catch (err: any) {
      setIsAuthorized(false);
      setSecurityStatus(null);
      setAuthError(`Network error reaching security endpoint: ${err?.message || err}`);
    } finally {
      setIsLoading(false);
    }
  }, [tokenInput]);

  const handleDirectLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!usernameInput || !passwordInput) {
      setAuthError('Username and password are required.');
      return;
    }
    setIsLoading(true);
    setAuthError(null);

    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: usernameInput,
          password: passwordInput,
          requested_role: loginRole
        })
      });

      if (res.ok) {
        const data = await res.json();
        setTokenInput(data.access_token);
        setSessionUser(data.username);
        setSessionRole(data.role);
        localStorage.setItem('jaldrishti_admin_token', data.access_token);
        await verifyAdminAccess(data.access_token);
      } else {
        const errData = await res.json();
        setAuthError(errData.detail || 'Login failed. Invalid credentials or rate limit exceeded.');
      }
    } catch (err: any) {
      setAuthError(`Login request error: ${err?.message || err}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    const token = tokenInput || localStorage.getItem('jaldrishti_admin_token');
    if (token) {
      try {
        await fetch('/api/v1/auth/logout', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        });
      } catch {
        // offline logout
      }
    }
    localStorage.removeItem('jaldrishti_admin_token');
    setTokenInput('');
    setPasswordInput('');
    setIsAuthorized(false);
    setSecurityStatus(null);
    setAuthError(null);
  };

  // Fetch Section Data when Authorized
  const fetchAllSectionData = useCallback(async () => {
    const token = tokenInput || localStorage.getItem('jaldrishti_admin_token');
    if (!token || !isAuthorized) return;

    const headers = { 'Authorization': `Bearer ${token}` };

    try {
      // 1. Security Status
      const secRes = await fetch('/api/v1/security/status', { headers });
      if (secRes.ok) setSecurityStatus(await secRes.json());

      // 2. Database Stats
      const dbRes = await fetch('/api/v1/admin/database/stats', { headers });
      if (dbRes.ok) setDatabaseStats(await dbRes.json());

      // 3. Event Bus Metrics
      const ebRes = await fetch('/api/v1/admin/event-bus/metrics', { headers });
      if (ebRes.ok) setEventBusMetrics(await ebRes.json());

      // 4. WebSocket Metrics
      const wsRes = await fetch('/api/v1/admin/websocket/metrics', { headers });
      if (wsRes.ok) setWebsocketMetrics(await wsRes.json());

      // 5. Models Catalog
      const modRes = await fetch('/api/v1/admin/models/catalog', { headers });
      if (modRes.ok) {
        const mData = await modRes.json();
        setModelsCatalog(mData.models || []);
      }

      // 6. Rate Limits
      const rlRes = await fetch('/api/v1/admin/rate-limits', { headers });
      if (rlRes.ok) setRateLimitData(await rlRes.json());

      // 7. Human Review Candidates
      const hrRes = await fetch('/api/v1/admin/human-review', { headers });
      if (hrRes.ok) {
        const hrData = await hrRes.json();
        setPendingCandidates(hrData.candidates || []);
      }

      // 8. Notifications Health & Providers
      const nhRes = await fetch('/api/v1/notifications/health');
      if (nhRes.ok) setNotificationHealth(await nhRes.json());

      const npRes = await fetch('/api/v1/notifications/providers');
      if (npRes.ok) setNotificationProviders(await npRes.json());

      const nmRes = await fetch('/api/v1/notifications/metrics');
      if (nmRes.ok) setNotificationMetrics(await nmRes.json());

      // 9. Audit Logs
      const auditQuery = new URLSearchParams({
        limit: '30',
        offset: String(auditPage * 30)
      });
      if (auditFilterAction) auditQuery.append('action', auditFilterAction);
      if (auditFilterStatus) auditQuery.append('status', auditFilterStatus);

      const auditRes = await fetch(`/api/v1/admin/audit-logs?${auditQuery.toString()}`, { headers });
      if (auditRes.ok) {
        const aData = await auditRes.json();
        setAuditLogs(aData.logs || []);
        setAuditTotal(aData.total || 0);
      }
    } catch (err) {
      console.warn('Observability poll error:', err);
    }
  }, [tokenInput, isAuthorized, auditPage, auditFilterAction, auditFilterStatus]);

  useEffect(() => {
    if (tokenInput) {
      verifyAdminAccess(tokenInput);
    } else {
      verifyAdminAccess('');
    }
  }, []);

  useEffect(() => {
    if (isAuthorized) {
      fetchAllSectionData();
      const interval = setInterval(fetchAllSectionData, 8000);
      return () => clearInterval(interval);
    }
  }, [isAuthorized, fetchAllSectionData]);

  // Handle Human Review Submission
  const handleExecuteReviewAction = async () => {
    if (!reviewActionModal || !reviewActionReason.trim() || reviewActionReason.trim().length < 5) {
      setActionErrorMsg('Mandatory reason required (minimum 5 characters).');
      return;
    }

    const token = tokenInput || localStorage.getItem('jaldrishti_admin_token');
    setActionErrorMsg(null);

    try {
      const res = await fetch('/api/v1/admin/human-review/action', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          alert_id: reviewActionModal.alert_id,
          action: reviewActionType,
          reason: reviewActionReason.trim(),
          target_severity: reviewActionType === 'DOWNGRADE' ? reviewTargetSeverity : undefined
        })
      });

      if (res.ok) {
        const data = await res.json();
        setActionSuccessMsg(`Alert ${data.alert_id} ${data.action} successfully recorded and audited.`);
        setReviewActionModal(null);
        setReviewActionReason('');
        await fetchAllSectionData();
        setTimeout(() => setActionSuccessMsg(null), 5000);
      } else {
        const errData = await res.json();
        setActionErrorMsg(errData.detail || 'Action failed.');
      }
    } catch (err: any) {
      setActionErrorMsg(`Error submitting decision: ${err?.message || err}`);
    }
  };

  // Handle Manual IMD AWS Telemetry Ingestion Refresh
  const handleRefreshImdTelemetry = async () => {
    if (imdCooldown > 0 || isRefreshingImd) return;
    setIsRefreshingImd(true);
    setImdRefreshFeedback(null);

    const token = tokenInput || localStorage.getItem('jaldrishti_admin_token');
    try {
      const res = await fetch('/api/v1/live/imd-aws/refresh', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setImdRefreshFeedback(`Ingestion cycle triggered (${data.station_count || 12} stations synced).`);
        setImdCooldown(5);
        const timer = setInterval(() => {
          setImdCooldown(prev => {
            if (prev <= 1) {
              clearInterval(timer);
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
      } else if (res.status === 429) {
        setImdRefreshFeedback('Rate limited: Cooldown in progress.');
      } else {
        const err = await res.json();
        setImdRefreshFeedback(err.detail || 'Refresh failed.');
      }
    } catch (err: any) {
      setImdRefreshFeedback(`Network error: ${err?.message || err}`);
    } finally {
      setIsRefreshingImd(false);
    }
  };

  const filteredAuditLogs = auditLogs.filter(log => {
    if (!auditSearchQuery) return true;
    const q = auditSearchQuery.toLowerCase();
    return (
      (log.action || '').toLowerCase().includes(q) ||
      (log.actor_id || '').toLowerCase().includes(q) ||
      (log.event_type || '').toLowerCase().includes(q) ||
      (log.target_resource || '').toLowerCase().includes(q)
    );
  });

  return (
    <div className="p-3 md:p-6 space-y-6 max-w-7xl mx-auto font-sans">
      {/* Top Header & Operator Session Bar */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 border-b border-border/80 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
              Administrative Control Plane
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              v2.4.0 • Hardened
            </span>
          </div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-2 mt-1">
            <Shield className="w-6 h-6 text-indigo-400" />
            Admin, RBAC & Security Operations Console
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Backend-authoritative control plane for human review, rate limits, spatial database, real-time event bus & telemetry gateways.
          </p>
        </div>

        {/* Action Controls & Session State */}
        <div className="flex flex-wrap items-center gap-2">
          {isAuthorized && (
            <div className="flex items-center gap-2 bg-surface-elevated px-3 py-1.5 rounded-lg border border-border text-xs">
              <span className="text-slate-400">Actor:</span>
              <span className="font-mono text-cyan-300 font-bold">{sessionUser}</span>
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${sessionRole === 'ADMIN' ? 'bg-indigo-500/30 text-indigo-200 border border-indigo-500/40' : 'bg-emerald-500/30 text-emerald-200 border border-emerald-500/40'}`}>
                {sessionRole}
              </span>
            </div>
          )}

          {isAuthorized && (
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign Out
            </button>
          )}

          <button
            onClick={() => {
              if (isAuthorized) fetchAllSectionData();
              else verifyAdminAccess();
            }}
            disabled={isLoading}
            className="px-3 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface-border text-slate-200 text-xs font-semibold border border-border flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Sync Status
          </button>
        </div>
      </div>

      {/* Global Action Feedback Alert */}
      {actionSuccessMsg && (
        <div className="p-3 rounded-lg bg-emerald-950/80 border border-emerald-500/50 text-emerald-200 text-xs font-medium flex items-center gap-2 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{actionSuccessMsg}</span>
        </div>
      )}

      {/* Unauthenticated / Unauthorized Gate Card */}
      {!isAuthorized && (
        <div className="bg-surface rounded-xl border border-rose-500/40 p-6 space-y-6 shadow-2xl bg-gradient-to-br from-surface via-surface to-rose-950/20">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center shrink-0">
              <Lock className="w-6 h-6 text-rose-400" />
            </div>
            <div className="space-y-1">
              <h2 className="text-base font-bold text-white font-sans">
                Operator / Administrator Authentication Required
              </h2>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                Access to the administrative control plane is backend-authoritative. Public citizen credentials cannot access these controls. Sign in with operator or admin credentials to generate a cryptographically signed HMAC token.
              </p>
            </div>
          </div>

          {authError && (
            <div className="p-3 rounded-lg bg-rose-950/80 border border-rose-500/50 text-rose-200 text-xs font-mono flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{authError}</span>
            </div>
          )}

          {/* Form Login */}
          <form onSubmit={handleDirectLogin} className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-300">Operator Username:</label>
              <input
                type="text"
                value={usernameInput}
                onChange={e => setUsernameInput(e.target.value)}
                placeholder="e.g. admin or operator"
                className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-xs text-white font-mono focus:border-cyan-400 focus:outline-none"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-300">Password / Secret:</label>
              <div className="relative">
                <input
                  type={showToken ? 'text' : 'password'}
                  value={passwordInput}
                  onChange={e => setPasswordInput(e.target.value)}
                  placeholder="Enter operator password..."
                  className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-xs text-white font-mono focus:border-cyan-400 focus:outline-none pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowToken(!showToken)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-white"
                >
                  {showToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-300">Role Scope:</label>
              <div className="flex gap-2">
                <select
                  value={loginRole}
                  onChange={e => setLoginRole(e.target.value as any)}
                  className="flex-1 bg-surface-elevated border border-border rounded-lg px-3 py-2 text-xs text-white font-mono focus:border-cyan-400 focus:outline-none"
                >
                  <option value="ADMIN">ADMIN (Full Control)</option>
                  <option value="OPERATOR">OPERATOR (Operations Only)</option>
                </select>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-semibold text-xs flex items-center justify-center gap-1.5 transition-all shadow-md shrink-0"
                >
                  <Key className="w-4 h-4" />
                  <span>Sign In</span>
                </button>
              </div>
            </div>
          </form>

          {/* Quick Token Paste Accordion */}
          <div className="border-t border-border/60 pt-4 space-y-2">
            <label className="block text-[11px] font-semibold text-slate-400">
              Or Authenticate with Existing Bearer JWT Token:
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={tokenInput}
                onChange={e => setTokenInput(e.target.value)}
                placeholder="Paste Bearer JWT token..."
                className="flex-1 bg-surface-elevated border border-border rounded-lg px-3 py-1.5 text-xs text-slate-300 font-mono placeholder:text-slate-600 focus:border-cyan-400 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => verifyAdminAccess(tokenInput)}
                disabled={isLoading || !tokenInput}
                className="px-4 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface-border text-slate-200 text-xs font-semibold border border-border shrink-0"
              >
                Validate Token
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Authorized Operator Operations Workspace */}
      {isAuthorized && (
        <div className="space-y-6">
          {/* Navigation Tabs Bar (10 Sections) */}
          <div className="bg-surface rounded-xl border border-border p-1.5 flex flex-wrap items-center gap-1.5 shadow-md">
            {[
              { id: 'overview', label: 'Overview', icon: Activity },
              { id: 'alerts', label: 'Alert Operations', icon: BellRing, badge: pendingCandidates.length > 0 ? pendingCandidates.length : undefined },
              { id: 'datasources', label: 'Data Sources', icon: Radio },
              { id: 'security', label: 'Security', icon: Lock },
              { id: 'database', label: 'Database', icon: Database },
              { id: 'eventbus', label: 'Event Bus', icon: Zap },
              { id: 'websocket', label: 'WebSocket', icon: Wifi },
              { id: 'notifications', label: 'Notifications', icon: Send },
              { id: 'models', label: 'Models', icon: Cpu },
              { id: 'audit', label: 'Audit Log', icon: FileText, badge: auditTotal > 0 ? auditTotal : undefined }
            ].map(tab => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as AdminTab)}
                  className={`px-3 py-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                    isActive 
                      ? 'bg-cyan-600 text-white shadow-md' 
                      : 'text-slate-300 hover:bg-surface-elevated hover:text-white'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                  {tab.badge !== undefined && (
                    <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                      isActive ? 'bg-white text-cyan-900' : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                    }`}>
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div className="space-y-6 animate-fadeIn">
              {/* Vitals Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-surface rounded-xl border border-border p-4 space-y-1">
                  <span className="text-[11px] text-slate-400 font-medium">Control Plane Status</span>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    <strong className="text-sm font-bold text-white uppercase tracking-wider">
                      {securityStatus?.status || 'HARDENED'}
                    </strong>
                  </div>
                </div>

                <div className="bg-surface rounded-xl border border-border p-4 space-y-1">
                  <span className="text-[11px] text-slate-400 font-medium">Pending Human Reviews</span>
                  <div className="flex items-center gap-2">
                    <BellRing className="w-4 h-4 text-rose-400" />
                    <strong className="text-sm font-bold text-rose-300">
                      {pendingCandidates.length} Active Gate(s)
                    </strong>
                  </div>
                </div>

                <div className="bg-surface rounded-xl border border-border p-4 space-y-1">
                  <span className="text-[11px] text-slate-400 font-medium">Database & WAL State</span>
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-cyan-400" />
                    <strong className="text-xs text-white">
                      {databaseStats?.engine || 'SQLite WAL'}
                    </strong>
                  </div>
                </div>

                <div className="bg-surface rounded-xl border border-border p-4 space-y-1">
                  <span className="text-[11px] text-slate-400 font-medium">Live WS Connections</span>
                  <div className="flex items-center gap-2">
                    <Wifi className="w-4 h-4 text-indigo-400" />
                    <strong className="text-xs text-white">
                      {websocketMetrics?.active_connections || 0} / {websocketMetrics?.max_connection_limit || 100}
                    </strong>
                  </div>
                </div>
              </div>

              {/* Sub-system Status Matrix */}
              <div className="bg-surface rounded-xl border border-border p-5 space-y-4">
                <h2 className="text-sm font-bold text-white flex items-center gap-2 border-b border-border/60 pb-3">
                  <Activity className="w-4 h-4 text-cyan-400" />
                  Operational Health & Service Readiness Matrix
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border/60 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300 font-sans font-semibold">Notification Engine</span>
                      <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px]">
                        {notificationHealth?.status || 'HEALTHY'}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 space-y-1">
                      <div>SMS Sink: <span className="text-slate-200">{notificationProviders?.active_sms_provider || 'MockSMSSink'}</span></div>
                      <div>Push Sink: <span className="text-slate-200">{notificationProviders?.active_push_provider || 'MockPushSink'}</span></div>
                      <div>DLT Status: <span className="text-slate-200">{notificationProviders?.dlt_entity_id_configured ? 'CONFIGURED' : 'DEV_MOCK'}</span></div>
                    </div>
                  </div>

                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border/60 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300 font-sans font-semibold">Event Bus & State</span>
                      <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 text-[10px]">
                        {eventBusMetrics?.status || 'ONLINE'}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 space-y-1">
                      <div>Stored Events: <span className="text-slate-200">{eventBusMetrics?.total_events_stored || 0}</span></div>
                      <div>Active Listeners: <span className="text-slate-200">{eventBusMetrics?.active_subscribers || 0}</span></div>
                      <div>State Version: <span className="text-slate-200">v{eventBusMetrics?.last_event_version || 1}</span></div>
                    </div>
                  </div>

                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border/60 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300 font-sans font-semibold">AI / ML Model Suites</span>
                      <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 text-[10px]">
                        4 DEPLOYED
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 space-y-1">
                      <div>Precipitation: <span className="text-slate-200">ConvLSTM v3.2</span></div>
                      <div>Hydrograph: <span className="text-slate-200">LSTM-GNN v2.4</span></div>
                      <div>Inundation: <span className="text-slate-200">UNet Surrogate v3.1</span></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: ALERT OPERATIONS & HUMAN REVIEW */}
          {activeTab === 'alerts' && (
            <div className="space-y-6 animate-fadeIn">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <BellRing className="w-5 h-5 text-rose-500" />
                    Human Review Safety Queue & Gating Controls
                  </h2>
                  <p className="text-xs text-slate-400">
                    High severity alerts (RED) require mandatory operator justification before automated public notification dispatch.
                  </p>
                </div>
              </div>

              {/* Review Modal Dialog */}
              {reviewActionModal && (
                <div className="bg-surface rounded-xl border border-indigo-500/60 p-5 space-y-4 shadow-2xl bg-gradient-to-br from-surface to-indigo-950/20 animate-fadeIn">
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <span className="text-[10px] font-mono text-indigo-400 uppercase font-bold">
                        Executing Decision on Alert ID: {reviewActionModal.alert_id}
                      </span>
                      <h3 className="text-sm font-bold text-white">{reviewActionModal.title}</h3>
                    </div>
                    <button
                      onClick={() => setReviewActionModal(null)}
                      className="text-slate-400 hover:text-white text-xs font-semibold"
                    >
                      Cancel
                    </button>
                  </div>

                  {actionErrorMsg && (
                    <div className="p-2.5 rounded bg-rose-950/80 border border-rose-500/50 text-rose-200 text-xs flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                      <span>{actionErrorMsg}</span>
                    </div>
                  )}

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <button
                      type="button"
                      onClick={() => setReviewActionType('ACKNOWLEDGE')}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        reviewActionType === 'ACKNOWLEDGE'
                          ? 'bg-emerald-500/20 border-emerald-500 text-emerald-200 font-bold'
                          : 'bg-surface-elevated border-border text-slate-400'
                      }`}
                    >
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mb-1" />
                      <div className="text-xs font-semibold">Acknowledge</div>
                      <div className="text-[10px] text-slate-400 font-normal">Approve alert for public broadcast</div>
                    </button>

                    <button
                      type="button"
                      onClick={() => setReviewActionType('DOWNGRADE')}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        reviewActionType === 'DOWNGRADE'
                          ? 'bg-amber-500/20 border-amber-500 text-amber-200 font-bold'
                          : 'bg-surface-elevated border-border text-slate-400'
                      }`}
                    >
                      <ArrowDownCircle className="w-4 h-4 text-amber-400 mb-1" />
                      <div className="text-xs font-semibold">Downgrade</div>
                      <div className="text-[10px] text-slate-400 font-normal">Lower severity to Watch/Advisory</div>
                    </button>

                    <button
                      type="button"
                      onClick={() => setReviewActionType('DISMISS')}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        reviewActionType === 'DISMISS'
                          ? 'bg-rose-500/20 border-rose-500 text-rose-200 font-bold'
                          : 'bg-surface-elevated border-border text-slate-400'
                      }`}
                    >
                      <XCircle className="w-4 h-4 text-rose-400 mb-1" />
                      <div className="text-xs font-semibold">Dismiss</div>
                      <div className="text-[10px] text-slate-400 font-normal">Suppress false positive trigger</div>
                    </button>
                  </div>

                  {reviewActionType === 'DOWNGRADE' && (
                    <div className="space-y-1">
                      <label className="block text-xs text-slate-300 font-semibold">Target Downgrade Severity:</label>
                      <select
                        value={reviewTargetSeverity}
                        onChange={e => setReviewTargetSeverity(e.target.value)}
                        className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-xs text-white font-mono focus:border-cyan-400 focus:outline-none"
                      >
                        <option value="WATCH">ORANGE / WATCH (High Alert)</option>
                        <option value="ADVISORY">YELLOW / ADVISORY (Monitor)</option>
                        <option value="INFO">GREEN / INFO (Normal)</option>
                      </select>
                    </div>
                  )}

                  <div className="space-y-1">
                    <label className="block text-xs text-slate-300 font-semibold">
                      Mandatory Operator Decision Justification (min 5 chars):
                    </label>
                    <textarea
                      value={reviewActionReason}
                      onChange={e => setReviewActionReason(e.target.value)}
                      placeholder="Enter verified field reconnaissance notes, barrage discharge adjustments, or operational reason..."
                      rows={3}
                      className="w-full bg-surface-elevated border border-border rounded-lg p-3 text-xs text-white font-mono placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none"
                    />
                  </div>

                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => setReviewActionModal(null)}
                      className="px-4 py-2 rounded-lg bg-surface-elevated text-slate-300 text-xs font-semibold border border-border"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleExecuteReviewAction}
                      disabled={reviewActionReason.trim().length < 5}
                      className="px-5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white text-xs font-bold shadow-md transition-all flex items-center gap-1.5"
                    >
                      <Check className="w-4 h-4" />
                      <span>Commit Operator Decision</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Candidates Queue */}
              <div className="bg-surface rounded-xl border border-border p-5 space-y-4">
                <h3 className="text-sm font-bold text-white">Pending Alert Review Queue</h3>
                {pendingCandidates.length === 0 ? (
                  <div className="p-8 text-center border border-dashed border-border rounded-xl space-y-2">
                    <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                    <p className="text-xs text-slate-300 font-medium">All alert candidates are reviewed and acknowledged.</p>
                    <p className="text-[11px] text-slate-500">No pending safety review gates blocking public dispatch.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {pendingCandidates.map((cand, idx) => (
                      <div key={cand.alert_id || idx} className="bg-surface-elevated p-4 rounded-xl border border-rose-500/40 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">
                              {cand.severity || 'RED'}
                            </span>
                            <span className="font-mono text-xs text-white font-bold">{cand.alert_id}</span>
                            <span className="text-[11px] text-slate-400">• {cand.location_name}</span>
                          </div>
                          <p className="text-xs text-slate-200">{cand.title}</p>
                          <p className="text-[11px] text-slate-400 italic">Trigger: {cand.why_alert_created}</p>
                        </div>
                        <button
                          onClick={() => {
                            setReviewActionModal(cand);
                            setReviewActionType('ACKNOWLEDGE');
                            setReviewActionReason('');
                          }}
                          className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md transition-all shrink-0"
                        >
                          Review & Decide
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: DATA SOURCES */}
          {activeTab === 'datasources' && (
            <div className="space-y-6 animate-fadeIn">
              <div className="bg-surface rounded-xl border border-border p-5 space-y-4">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-border/60 pb-3">
                  <div>
                    <h2 className="text-sm font-bold text-white flex items-center gap-2">
                      <Radio className="w-4 h-4 text-cyan-400" />
                      IMD AWS Automated Telemetry Gateway
                    </h2>
                    <p className="text-xs text-slate-400">
                      Real-time automated weather station integration with rate-limited manual sync gate (5s cooldown).
                    </p>
                  </div>
                  <button
                    onClick={handleRefreshImdTelemetry}
                    disabled={imdCooldown > 0 || isRefreshingImd}
                    className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white text-xs font-bold flex items-center gap-2 transition-all shadow-md shrink-0"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isRefreshingImd ? 'animate-spin' : ''}`} />
                    <span>{imdCooldown > 0 ? `Cooldown (${imdCooldown}s)` : 'Trigger Ingestion Refresh'}</span>
                  </button>
                </div>

                {imdRefreshFeedback && (
                  <div className="p-2.5 rounded bg-cyan-950/80 border border-cyan-500/40 text-cyan-200 text-xs font-mono">
                    {imdRefreshFeedback}
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">Active Ingestion Adapter</span>
                    <strong className="text-emerald-300 block">IMDLiveAdapter (Odisha Region)</strong>
                    <p className="text-[11px] text-slate-400">Station Filter: Cuttack, Bhubaneswar, Naraj, Mundali</p>
                  </div>
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">Rate Limit Constraint</span>
                    <strong className="text-cyan-300 block">5s Cooldown Per Trigger</strong>
                    <p className="text-[11px] text-slate-400">Protects upstream telemetry servers from flooding</p>
                  </div>
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">Fallback Redundancy</span>
                    <strong className="text-indigo-300 block">GloFAS + ERA5 Synthetic Hindcast</strong>
                    <p className="text-[11px] text-slate-400">Autonomous fallback on provider timeout</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: SECURITY */}
          {activeTab === 'security' && (
            <div className="space-y-6 animate-fadeIn">
              {/* Rate Limits Grid */}
              <div className="bg-surface rounded-xl border border-border p-5 space-y-4">
                <h2 className="text-sm font-bold text-white flex items-center gap-2 border-b border-border/60 pb-3">
                  <Lock className="w-4 h-4 text-cyan-400" />
                  Active Multi-Dimensional Rate Limiting Rules & Lockouts
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                  {[
                    { name: 'Admin Auth Login', limit: '5 req / 60s', key: 'Client IP', breach: '120s Lockout' },
                    { name: 'OTP Request Throttling', limit: '3 req / 60s', key: 'IP + Phone Hash', breach: '60s Lockout' },
                    { name: 'User Subscriptions', limit: '10 mut / min', key: 'User UUID', breach: 'HTTP 429' },
                    { name: 'IMD AWS Refresh', limit: '5s cooldown', key: 'Provider Key', breach: 'Throttled' }
                  ].map((rule, i) => (
                    <div key={i} className="bg-surface-elevated p-3.5 rounded-lg border border-border/60 space-y-1">
                      <strong className="text-white block font-sans">{rule.name}</strong>
                      <p className="text-slate-400 text-[11px]">Limit: <span className="text-cyan-300 font-mono">{rule.limit}</span></p>
                      <p className="text-slate-400 text-[11px]">Key: <span className="text-slate-200 font-mono">{rule.key}</span></p>
                      <span className="inline-block px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-mono">
                        ACTIVE ({rule.breach})
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Security Guard Rails */}
              <div className="bg-surface rounded-xl border border-border p-5 space-y-4">
                <h2 className="text-sm font-bold text-white flex items-center gap-2 border-b border-border/60 pb-3">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Security Controls & Privacy Protections
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <strong className="text-white block font-sans">PII & Phone Masking</strong>
                    <p className="text-slate-400 text-[11px]">Phone numbers are masked (`******3210`) in all APIs and error logs.</p>
                  </div>
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <strong className="text-white block font-sans">Payload Size Guard</strong>
                    <p className="text-slate-400 text-[11px]">Strict 1MB max HTTP body & 64KB WebSocket frame enforcement.</p>
                  </div>
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <strong className="text-white block font-sans">HMAC SHA-256 Auth</strong>
                    <p className="text-slate-400 text-[11px]">Backend secret signed tokens with expiration and scope validation.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: DATABASE */}
          {activeTab === 'database' && (
            <div className="space-y-6 animate-fadeIn">
              <div className="bg-surface rounded-xl border border-border p-5 space-y-4">
                <h2 className="text-sm font-bold text-white flex items-center gap-2 border-b border-border/60 pb-3">
                  <Database className="w-4 h-4 text-cyan-400" />
                  Relational & Spatial Database Engine Metrics
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">Engine Runtime</span>
                    <strong className="text-white block">{databaseStats?.engine || 'SQLite (WAL Mode)'}</strong>
                  </div>
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">Spatial Extensions</span>
                    <strong className="text-cyan-300 block">{databaseStats?.spatial_extensions || 'Euclidean KDTree / GeoJSON'}</strong>
                  </div>
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">Connection Pool</span>
                    <strong className="text-emerald-300 block">{databaseStats?.connection_pool || 'Thread-Local Context Pool'}</strong>
                  </div>
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">WAL Mode</span>
                    <strong className="text-emerald-300 block">{databaseStats?.wal_enabled ? 'ENABLED' : 'ACTIVE'}</strong>
                  </div>
                </div>

                <div className="pt-2">
                  <h3 className="text-xs font-bold text-slate-300 font-sans mb-2">Table Record Counts:</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs font-mono">
                    {Object.entries(databaseStats?.table_stats || {}).map(([tbl, count]) => (
                      <div key={tbl} className="bg-surface-elevated p-2.5 rounded border border-border/60 text-center">
                        <span className="text-[10px] text-slate-400 block uppercase font-sans">{tbl}</span>
                        <strong className="text-cyan-300 text-sm">{String(count)}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 6: EVENT BUS */}
          {activeTab === 'eventbus' && (
            <div className="space-y-6 animate-fadeIn">
              <div className="bg-surface rounded-xl border border-border p-5 space-y-4">
                <h2 className="text-sm font-bold text-white flex items-center gap-2 border-b border-border/60 pb-3">
                  <Zap className="w-4 h-4 text-amber-400" />
                  Real-Time In-Memory Event Bus & Queue
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">Total Stored Events</span>
                    <strong className="text-amber-300 text-base">{eventBusMetrics?.total_events_stored || 0}</strong>
                  </div>
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">Active Handlers</span>
                    <strong className="text-cyan-300 text-base">{eventBusMetrics?.active_subscribers || 0}</strong>
                  </div>
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">Event Types Registered</span>
                    <strong className="text-emerald-300 text-base">{eventBusMetrics?.registered_event_types || 0}</strong>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 7: WEBSOCKET */}
          {activeTab === 'websocket' && (
            <div className="space-y-6 animate-fadeIn">
              <div className="bg-surface rounded-xl border border-border p-5 space-y-4">
                <h2 className="text-sm font-bold text-white flex items-center gap-2 border-b border-border/60 pb-3">
                  <Wifi className="w-4 h-4 text-cyan-400" />
                  WebSocket Live Telemetry & Streaming Server
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">Concurrent Connections</span>
                    <strong className="text-cyan-300 text-base">{websocketMetrics?.active_connections || 0} / {websocketMetrics?.max_connection_limit || 100}</strong>
                  </div>
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">Max Frame Guard</span>
                    <strong className="text-emerald-300 text-base">{websocketMetrics?.max_frame_size_bytes || 65536} Bytes</strong>
                  </div>
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">Broadcast Channel</span>
                    <strong className="text-indigo-300 text-base">{websocketMetrics?.broadcast_channel || '/ws/v1/live'}</strong>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 8: NOTIFICATIONS */}
          {activeTab === 'notifications' && (
            <div className="space-y-6 animate-fadeIn">
              <div className="bg-surface rounded-xl border border-border p-5 space-y-4">
                <h2 className="text-sm font-bold text-white flex items-center gap-2 border-b border-border/60 pb-3">
                  <Send className="w-4 h-4 text-indigo-400" />
                  Public Alert Notification Delivery Engine
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">SMS Gateway</span>
                    <strong className="text-emerald-300 block">{notificationProviders?.active_sms_provider || 'MockSMSSink'}</strong>
                    <p className="text-[11px] text-slate-400 font-sans">DLT Compliance: {notificationProviders?.dlt_entity_id_configured ? 'Registered' : 'Isolated Mock'}</p>
                  </div>
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">Push Gateway</span>
                    <strong className="text-cyan-300 block">{notificationProviders?.active_push_provider || 'MockPushSink'}</strong>
                    <p className="text-[11px] text-slate-400 font-sans">FCM WebPush Standard</p>
                  </div>
                  <div className="bg-surface-elevated p-3.5 rounded-lg border border-border space-y-1">
                    <span className="text-slate-400 block font-sans font-semibold">In-App Citizen Inbox</span>
                    <strong className="text-indigo-300 block">{notificationProviders?.active_in_app_provider || 'InAppInboxProvider'}</strong>
                    <p className="text-[11px] text-slate-400 font-sans">Persistence: SQLite WAL</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 9: MODELS */}
          {activeTab === 'models' && (
            <div className="space-y-6 animate-fadeIn">
              <div className="bg-surface rounded-xl border border-border p-5 space-y-4">
                <h2 className="text-sm font-bold text-white flex items-center gap-2 border-b border-border/60 pb-3">
                  <Cpu className="w-4 h-4 text-cyan-400" />
                  AI / ML Model Registry & Checkpoints
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                  {modelsCatalog.map((m: any) => (
                    <div key={m.id} className="bg-surface-elevated p-4 rounded-xl border border-border space-y-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="text-[10px] text-cyan-400 font-bold">{m.id} • {m.version}</span>
                          <h4 className="text-sm font-bold text-white font-sans">{m.name}</h4>
                          <span className="text-[11px] text-slate-400 font-sans">{m.domain}</span>
                        </div>
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${m.dataset_state.includes('SYNTHETIC') ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'}`}>
                          [{m.dataset_state}]
                        </span>
                      </div>
                      <div className="text-[11px] space-y-1 pt-2 border-t border-border/60">
                        <div className="text-slate-300">Metric: <span className="text-cyan-300 font-bold">{m.primary_metric}</span></div>
                        <div className="text-slate-400">Dataset: {m.dataset}</div>
                        <div className="text-slate-500 text-[10px]">Checkpoint: {m.checkpoint}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 10: AUDIT LOG */}
          {activeTab === 'audit' && (
            <div className="space-y-6 animate-fadeIn">
              <div className="bg-surface rounded-xl border border-border p-5 space-y-4">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-border/60 pb-3">
                  <div>
                    <h2 className="text-sm font-bold text-white flex items-center gap-2">
                      <FileText className="w-4 h-4 text-indigo-400" />
                      Administrative & Security Audit Logs ({auditTotal} Total Records)
                    </h2>
                    <p className="text-xs text-slate-400">
                      Immutable forensic log of logins, alert review actions, and security gate checks.
                    </p>
                  </div>

                  {/* Filters */}
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <div className="relative">
                      <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
                      <input
                        type="text"
                        value={auditSearchQuery}
                        onChange={e => setAuditSearchQuery(e.target.value)}
                        placeholder="Search audit trail..."
                        className="bg-surface-elevated border border-border rounded-lg pl-8 pr-3 py-1.5 text-xs text-white font-mono placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none"
                      />
                    </div>
                  </div>
                </div>

                {/* Audit Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-border text-slate-400 font-semibold text-[11px]">
                        <th className="py-2.5 px-3">Timestamp (UTC)</th>
                        <th className="py-2.5 px-3">Event Type</th>
                        <th className="py-2.5 px-3">Action</th>
                        <th className="py-2.5 px-3">Actor ID</th>
                        <th className="py-2.5 px-3">Role</th>
                        <th className="py-2.5 px-3">Status</th>
                        <th className="py-2.5 px-3">Target / Detail</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/40 font-mono text-[11px]">
                      {filteredAuditLogs.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-6 text-center text-slate-400">
                            No audit log records found matching current criteria.
                          </td>
                        </tr>
                      ) : (
                        filteredAuditLogs.map((log, i) => (
                          <tr key={log.audit_id || i} className="hover:bg-surface-elevated/40">
                            <td className="py-2 px-3 text-slate-400">
                              {(log.timestamp || '').replace('T', ' ').slice(0, 19)}
                            </td>
                            <td className="py-2 px-3 text-cyan-300 font-bold">{log.event_type}</td>
                            <td className="py-2 px-3 text-slate-200">{log.action}</td>
                            <td className="py-2 px-3 text-indigo-300">{log.actor_id}</td>
                            <td className="py-2 px-3 text-slate-400">{log.actor_role || 'OPERATOR'}</td>
                            <td className="py-2 px-3">
                              <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                log.status === 'SUCCESS' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                              }`}>
                                {log.status}
                              </span>
                            </td>
                            <td className="py-2 px-3 text-slate-300 max-w-xs truncate">
                              {log.target_resource || JSON.stringify(log.details || {})}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Pagination Bar */}
                <div className="flex justify-between items-center pt-3 border-t border-border/60 text-xs">
                  <span className="text-slate-400">
                    Page {auditPage + 1} of {Math.max(1, Math.ceil(auditTotal / 30))}
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setAuditPage(prev => Math.max(0, prev - 1))}
                      disabled={auditPage === 0}
                      className="px-3 py-1 rounded bg-surface-elevated text-slate-300 hover:text-white disabled:opacity-40 border border-border"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setAuditPage(prev => prev + 1)}
                      disabled={(auditPage + 1) * 30 >= auditTotal}
                      className="px-3 py-1 rounded bg-surface-elevated text-slate-300 hover:text-white disabled:opacity-40 border border-border"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
