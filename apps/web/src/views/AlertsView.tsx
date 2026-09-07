import React, { useState, useEffect } from 'react';
import { BellRing, ShieldAlert, CheckCircle2, UserCheck, AlertTriangle, Clock, MapPin, ArrowRight, RefreshCw, FileText, ArrowDownCircle, XCircle, Search, ShieldCheck } from 'lucide-react';
import { DataProvenanceDrawer } from '../components/DataProvenanceDrawer';
import { AlertItem, AlertSeverity, ProvenanceMetadata } from '../types';

export const AlertsView: React.FC = () => {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [selectedAuditIncident, setSelectedAuditIncident] = useState<any | null>(null);
  const [currentRole, setCurrentRole] = useState<string>('OPERATOR');
  const [operatorName, setOperatorName] = useState<string>('Duty Disaster Officer');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const fetchIncidents = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/v1/alerts/incidents');
      if (res.ok) {
        const data = await res.json();
        setIncidents(data || []);
      }
    } catch (e) {
      console.warn(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (alertId: string, actionType: 'acknowledge' | 'downgrade' | 'dismiss' | 'field-verification') => {
    try {
      const res = await fetch(`/api/v1/alerts/${alertId}/${actionType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          operator_id: operatorName,
          role: currentRole,
          reason: `Action ${actionType.toUpperCase()} executed by ${operatorName} (${currentRole})`,
          notes: `Field reconnaissance requested for ${alertId}`
        })
      });
      if (res.ok) {
        const updated = await res.json();
        setActionMessage(`Action ${actionType.toUpperCase()} successfully applied.`);
        setTimeout(() => setActionMessage(null), 4000);
        await fetchIncidents();
      } else {
        const err = await res.json();
        alert(`Action Failed: ${err.detail || 'Unauthorized action'}`);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleViewAudit = async (alertId: string) => {
    try {
      const res = await fetch(`/api/v1/alerts/${alertId}/history`);
      if (res.ok) {
        const data = await res.json();
        setSelectedAuditIncident(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const provenance: ProvenanceMetadata = {
    source_id: "ALERT_DECISION_SUPPORT_ENGINE",
    provider: "JALDRISHTI AI Rule Matrix & Safety Workflow",
    product_name: "Multi-Hazard Emergency Operations Early Warning Trigger",
    observed_at: new Date().toISOString(),
    received_at: new Date().toISOString(),
    source_latency_mins: 1.5,
    processing_version: "v2.1.0",
    is_simulation: true
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4">
      {/* Header & RBAC Role Switcher */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-border pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <BellRing className="w-6 h-6 text-rose-500" />
            Operational Alert Decision Support & Human Review Center (Phase 16)
          </h2>
          <p className="text-xs text-slate-400">
            Decision support queue. <b>RED alerts require mandatory human review</b> before dispatch. Full audit trail recorded.
          </p>
        </div>

        {/* Operator Role Switcher for RBAC Testing */}
        <div className="flex items-center gap-2 bg-surface-elevated p-2 rounded-lg border border-border text-xs">
          <span className="text-slate-400 font-semibold">Active Role:</span>
          <select
            value={currentRole}
            onChange={(e) => setCurrentRole(e.target.value)}
            className="bg-slate-900 text-white font-mono text-xs px-2 py-1 rounded border border-slate-700 outline-none"
          >
            <option value="VIEWER">VIEWER (Read-Only)</option>
            <option value="ANALYST">ANALYST (Field Verification)</option>
            <option value="OPERATOR">OPERATOR (Acknowledge/Downgrade/Dismiss)</option>
            <option value="ADMINISTRATOR">ADMINISTRATOR (Full Access)</option>
          </select>
          <button
            onClick={fetchIncidents}
            disabled={isLoading}
            className="px-2 py-1 rounded bg-slate-800 text-slate-300 hover:text-white border border-slate-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-200 text-xs font-semibold flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          {actionMessage}
        </div>
      )}

      {/* Incidents List */}
      <div className="space-y-4">
        {incidents.length === 0 ? (
          <div className="glass-panel p-8 text-center text-slate-400 text-sm">
            No active alert candidates in the queue. All hydrological thresholds within normal limits.
          </div>
        ) : (
          incidents.map((incident) => {
            const isRed = incident.severity === 'RED';
            const isPending = incident.status === 'PENDING_HUMAN_REVIEW';
            const isAck = incident.status === 'ACKNOWLEDGED';

            return (
              <div
                key={incident.alert_id}
                className={`glass-panel p-5 rounded-xl border transition-all ${
                  isRed ? 'border-rose-500/50 shadow-lg shadow-rose-500/10' : 'border-amber-500/40'
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                  <div className="flex items-center gap-2.5">
                    <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold ${
                      isRed ? 'bg-rose-500 text-white animate-pulse' : 'bg-amber-500 text-black'
                    }`}>
                      {incident.severity} ALERT
                    </span>
                    <h3 className="text-sm font-bold font-mono text-white">
                      {incident.title}
                    </h3>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                      Status: {incident.status}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-xs font-mono">
                    <span className="text-slate-400 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" /> {incident.lead_time_hours}h Lead Horizon
                    </span>
                    <span className="text-slate-400">
                      Prob: <b className="text-white">{((incident.flood_probability || 0.86) * 100).toFixed(0)}%</b>
                    </span>
                  </div>
                </div>

                {/* Body */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 text-xs font-mono">
                  <div className="lg:col-span-2 space-y-3">
                    <div>
                      <div className="text-slate-400 text-[11px] mb-0.5">Hazard Trigger Analysis:</div>
                      <div className="text-slate-200 leading-relaxed font-sans text-xs bg-surface/60 p-2.5 rounded-lg border border-surface-border">
                        {incident.why_alert_created}
                      </div>
                    </div>

                    <div className="flex items-center gap-4 text-[11px] text-slate-400">
                      <span>Location: <strong className="text-slate-200">{incident.location_name}</strong></span>
                      <span>Confidence: <strong className="text-cyan-300">{incident.data_confidence}</strong></span>
                      <span>Crossing: <strong className="text-slate-300">{incident.threshold_crossing_time ? new Date(incident.threshold_crossing_time).toLocaleTimeString() : 'N/A'}</strong></span>
                    </div>
                  </div>

                  {/* Operational Review Gate & Actions */}
                  <div className="space-y-3 bg-surface/80 p-3 rounded-lg border border-surface-border flex flex-col justify-between">
                    <div className="space-y-2">
                      <div className="text-slate-400 text-[11px] font-semibold flex justify-between items-center">
                        <span>Human Review Gate</span>
                        <button
                          onClick={() => handleViewAudit(incident.alert_id)}
                          className="text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 underline"
                        >
                          <FileText className="w-3 h-3" /> View Audit Trail ({incident.audit_history?.length || 0})
                        </button>
                      </div>

                      {incident.requires_human_review && isPending && (
                        <div className="text-[11px] text-amber-300 flex items-center gap-1.5 p-1.5 rounded bg-amber-500/10 border border-amber-500/30">
                          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
                          <span>MANDATORY human verification for RED severity escalation</span>
                        </div>
                      )}

                      <div className="text-[11px] text-slate-300">
                        {isAck ? (
                          <span className="text-emerald-400 font-bold flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Acknowledged by Human Officer
                          </span>
                        ) : (
                          <span className="text-rose-400 font-bold flex items-center gap-1">
                            <AlertTriangle className="w-3.5 h-3.5" /> PENDING OPERATOR ACTION
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Operational Review Action Buttons */}
                    <div className="space-y-1.5 pt-2 border-t border-border/50">
                      <button
                        onClick={() => handleAction(incident.alert_id, 'acknowledge')}
                        className="w-full py-1.5 px-2.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
                      >
                        <UserCheck className="w-3.5 h-3.5" />
                        Acknowledge & Sign-off SOP
                      </button>

                      <div className="grid grid-cols-3 gap-1">
                        <button
                          onClick={() => handleAction(incident.alert_id, 'downgrade')}
                          className="py-1 px-1.5 rounded bg-amber-600/30 hover:bg-amber-600/50 text-amber-300 border border-amber-500/40 text-[10px] font-bold flex items-center justify-center gap-1"
                          title="Downgrade to lower severity tier"
                        >
                          <ArrowDownCircle className="w-3 h-3" /> Downgrade
                        </button>
                        <button
                          onClick={() => handleAction(incident.alert_id, 'dismiss')}
                          className="py-1 px-1.5 rounded bg-rose-600/30 hover:bg-rose-600/50 text-rose-300 border border-rose-500/40 text-[10px] font-bold flex items-center justify-center gap-1"
                          title="Dismiss and mark as cancelled"
                        >
                          <XCircle className="w-3 h-3" /> Dismiss
                        </button>
                        <button
                          onClick={() => handleAction(incident.alert_id, 'field-verification')}
                          className="py-1 px-1.5 rounded bg-cyan-600/30 hover:bg-cyan-600/50 text-cyan-300 border border-cyan-500/40 text-[10px] font-bold flex items-center justify-center gap-1"
                          title="Dispatch field gauge inspection"
                        >
                          <Search className="w-3 h-3" /> Verify Field
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Audit History Drawer / Modal */}
      {selectedAuditIncident && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-lg max-w-2xl w-full p-5 space-y-4 shadow-2xl">
            <div className="flex justify-between items-start border-b border-border pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-cyan-400" />
                  Immutable Alert Audit Trail ({selectedAuditIncident.alert_id})
                </h3>
                <span className="text-xs text-slate-400">Recorded in append-only system audit log</span>
              </div>
              <button
                onClick={() => setSelectedAuditIncident(null)}
                className="text-slate-400 hover:text-white text-sm px-2 py-1 rounded bg-surface-elevated"
              >
                ✕ Close
              </button>
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {(selectedAuditIncident.audit_history || []).length === 0 ? (
                <div className="text-xs text-slate-400 text-center py-4">No human review actions recorded yet.</div>
              ) : (
                selectedAuditIncident.audit_history.map((rec: any, i: number) => (
                  <div key={i} className="p-2.5 rounded bg-surface-elevated border border-border text-xs space-y-1">
                    <div className="flex justify-between items-center font-mono">
                      <span className="text-cyan-300 font-bold">{rec.action}</span>
                      <span className="text-[10px] text-slate-400">{new Date(rec.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div className="text-slate-300">
                      Operator: <strong className="text-white">{rec.operator_id}</strong> ({rec.operator_role})
                    </div>
                    <div className="text-slate-400 text-[11px]">
                      Transition: <span className="font-mono text-amber-300">{rec.previous_state} → {rec.new_state}</span>
                    </div>
                    <div className="text-slate-300 text-[11px] italic bg-slate-900/60 p-1.5 rounded">
                      "{rec.reason}"
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      <DataProvenanceDrawer provenance={provenance} />
    </div>
  );
};
