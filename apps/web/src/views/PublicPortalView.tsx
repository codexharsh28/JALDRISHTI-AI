import React, { useState, useEffect } from 'react';
import { ShieldAlert, Bell, MapPin, CheckCircle, AlertTriangle, Smartphone, Plus, Trash2, Clock, ShieldCheck, RefreshCw, Send, Globe, Radio } from 'lucide-react';

export const PublicPortalView: React.FC = () => {
  const [publicAlerts, setPublicAlerts] = useState<any[]>([]);
  const [regionInfo, setRegionInfo] = useState<any>({
    region_id: 'MAHANADI_DELTA',
    region_name: 'Mahanadi Delta',
    state: 'Odisha',
    country: 'India',
    authority_guidance_entity: 'OSDMA / DDMA',
    is_pilot_deployment: true
  });
  const [providerHealth, setProviderHealth] = useState<{
    sms: string;
    push: string;
    in_app: string;
  }>({ sms: 'MOCK_MODE_ACTIVE', push: 'MOCK_MODE_ACTIVE', in_app: 'ONLINE' });
  const [phone, setPhone] = useState<string>('9876543210');
  const [maskedPhone, setMaskedPhone] = useState<string>('******3210');
  const [otp, setOtp] = useState<string>('');
  const [otpSent, setOtpSent] = useState<boolean>(false);
  const [phoneVerified, setPhoneVerified] = useState<boolean>(false);
  const [userId, setUserId] = useState<string>('');
  const [authToken, setAuthToken] = useState<string>('');
  const [subscriptions, setSubscriptions] = useState<any[]>([]);
  const [inbox, setInbox] = useState<any[]>([]);
  const [newLocName, setNewLocName] = useState<string>('Cuttack Cantonment');
  const [newLocLat, setNewLocLat] = useState<number>(20.46);
  const [newLocLon, setNewLocLon] = useState<number>(85.88);
  const [newLocLabel, setNewLocLabel] = useState<string>('HOME');
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [otpCooldown, setOtpCooldown] = useState<number>(0);

  useEffect(() => {
    if (otpCooldown <= 0) return;
    const timer = setInterval(() => {
      setOtpCooldown(prev => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [otpCooldown]);

  const getAuthHeaders = () => {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }
    return headers;
  };

  // 1. Fetch regional metadata & provider health
  const fetchMetadataAndHealth = async () => {
    try {
      const [resRegion, resHealth] = await Promise.all([
        fetch('/api/v1/notifications/region'),
        fetch('/api/v1/notifications/health')
      ]);
      if (resRegion.ok) {
        const data = await resRegion.json();
        setRegionInfo(data);
      }
      if (resHealth.ok) {
        const data = await resHealth.json();
        if (data.providers) {
          setProviderHealth(data.providers);
        }
      }
    } catch (e) {
      console.warn("Metadata fetch error:", e);
    }
  };

  // 2. Register citizen / retrieve user ID
  const handleRegister = async () => {
    try {
      const res = await fetch('/api/v1/user/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: phone, preferred_language: 'en' })
      });
      if (res.ok) {
        const data = await res.json();
        setUserId(data.user_id);
        const masked = data.masked_destination || data.phone_masked || `******${phone.slice(-4)}`;
        setMaskedPhone(masked);
        setPhoneVerified(Boolean(data.phone_verified));
        fetchSubscriptions(data.user_id);
        fetchInbox(data.user_id);
      }
    } catch (e) {
      console.warn("User register error:", e);
    }
  };

  const handleSendOtp = async () => {
    if (otpCooldown > 0) return;
    try {
      const res = await fetch('/api/v1/user/send-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: phone })
      });
      if (res.ok) {
        const data = await res.json();
        setOtpSent(true);
        const destination = data.masked_destination || maskedPhone || `******${phone.slice(-4)}`;
        const retrySec = data.retry_after || 60;
        setOtpCooldown(retrySec);
        setStatusMsg(`OTP sent to ${destination}. Please enter your 6-digit code below.`);
      } else if (res.status === 429) {
        const retryHeader = res.headers.get('Retry-After');
        const retrySec = retryHeader ? parseInt(retryHeader, 10) : 600;
        setOtpCooldown(retrySec || 600);
        const err = await res.json();
        setStatusMsg(`Rate limit exceeded: ${err.detail || `Too many requests. Please wait ${retrySec}s.`}`);
      } else {
        const err = await res.json();
        setStatusMsg(`Failed to send OTP: ${err.detail || 'Please check mobile number.'}`);
      }
    } catch (e) {
      console.error(e);
      setStatusMsg("Network error connecting to notification server.");
    }
  };

  const handleVerifyOtp = async () => {
    if (!otp.trim()) {
      setStatusMsg("Please enter the 6-digit OTP code.");
      return;
    }
    try {
      const res = await fetch('/api/v1/user/verify-phone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: phone, otp: otp.trim() })
      });
      if (res.ok) {
        const data = await res.json();
        setPhoneVerified(Boolean(data.phone_verified));
        if (data.masked_destination) {
          setMaskedPhone(data.masked_destination);
        }
        if (data.access_token) {
          setAuthToken(data.access_token);
        }
        setStatusMsg("Phone successfully verified! Emergency SMS notifications activated.");
        setOtp('');
        setTimeout(() => setStatusMsg(null), 5000);
      } else {
        const err = await res.json();
        setStatusMsg(`Verification failed: ${err.detail || 'Invalid or expired OTP'}`);
      }
    } catch (e) {
      console.error(e);
      setStatusMsg("Network error during verification.");
    }
  };

  const fetchSubscriptions = async (uid: string) => {
    try {
      const res = await fetch(`/api/v1/user/subscriptions?user_id=${uid}`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setSubscriptions(data || []);
      } else if (res.status === 401) {
        setStatusMsg("Phone verification required: please complete OTP verification to load saved location subscriptions.");
      }
    } catch (e) {
      console.warn('Subscriptions fetch error:', e);
    }
  };

  const handleAddSubscription = async () => {
    if (!userId) return;
    try {
      const res = await fetch('/api/v1/user/subscriptions', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          user_id: userId,
          label: newLocLabel,
          locality_name: newLocName,
          latitude: newLocLat,
          longitude: newLocLon,
          radius_km: 10.0
        })
      });
      if (res.ok) {
        fetchSubscriptions(userId);
        setStatusMsg(`Added location subscription for ${newLocName}`);
        setTimeout(() => setStatusMsg(null), 4000);
      } else if (res.status === 401) {
        setStatusMsg("Phone verification required: please verify your phone with OTP first before adding location warnings.");
      } else {
        const err = await res.json();
        setStatusMsg(`Could not add subscription: ${err.detail || 'Validation error'}`);
      }
    } catch (e) {
      console.error(e);
      setStatusMsg("Network error adding location subscription.");
    }
  };

  const handleDeleteSubscription = async (subId: string) => {
    if (!userId) return;
    try {
      const res = await fetch(`/api/v1/user/subscriptions/${subId}?user_id=${userId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });
      if (res.ok) {
        fetchSubscriptions(userId);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchInbox = async (uid: string) => {
    try {
      const res = await fetch(`/api/v1/user/notifications?user_id=${uid}`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setInbox(data || []);
      }
    } catch (e) {
      console.warn(e);
    }
  };

  const fetchPublicAlerts = async () => {
    try {
      const res = await fetch('/api/v1/public-alerts/current');
      if (res.ok) {
        const data = await res.json();
        setPublicAlerts(data || []);
      }
    } catch (e) {
      console.warn(e);
    }
  };

  useEffect(() => {
    fetchMetadataAndHealth();
    handleRegister();
    fetchPublicAlerts();
    const interval = setInterval(() => {
      fetchPublicAlerts();
      fetchMetadataAndHealth();
      if (userId) fetchInbox(userId);
    }, 6000);
    return () => clearInterval(interval);
  }, [userId, authToken]);

  return (
    <div className="max-w-6xl mx-auto space-y-6 p-4">
      {/* Top Header with Pilot Region Info & Authoritative Provider Status */}
      <div className="border-b border-border pb-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-white flex items-center gap-2.5 tracking-tight">
              <ShieldAlert className="w-7 h-7 text-sky-400" />
              JALDRISHTI Citizen Safety Portal
            </h1>
            <span className="text-[10px] px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800 font-mono font-bold uppercase tracking-wider flex items-center gap-1">
              <Globe className="w-3 h-3" /> {regionInfo.region_name}, {regionInfo.state}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time public flood alerts, localized SMS notifications & official decision support guidance.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {providerHealth.sms === 'CONFIGURED' ? (
            <span className="text-[11px] px-2.5 py-1 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center gap-1.5 font-medium">
              <ShieldCheck className="w-3.5 h-3.5" /> DLT & SMS Gateway Active
            </span>
          ) : providerHealth.sms === 'MOCK_MODE_ACTIVE' ? (
            <span className="text-[11px] px-2.5 py-1 rounded bg-indigo-950 text-indigo-400 border border-indigo-800 flex items-center gap-1.5 font-medium">
              <ShieldCheck className="w-3.5 h-3.5" /> SMS Mock Gateway (Dev Simulation)
            </span>
          ) : (
            <span className="text-[11px] px-2.5 py-1 rounded bg-amber-950 text-amber-400 border border-amber-800 flex items-center gap-1.5 font-medium">
              <AlertTriangle className="w-3.5 h-3.5" /> SMS Gateway Not Configured (In-App Only)
            </span>
          )}
          <button
            onClick={fetchPublicAlerts}
            className="p-1.5 bg-surface-elevated hover:bg-border rounded text-slate-400 hover:text-white transition-colors"
            title="Refresh Public Alerts"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {statusMsg && (
        <div className="p-3 bg-sky-950/60 border border-sky-700 text-sky-200 text-xs rounded-lg flex items-center gap-2 animate-fadeIn">
          <CheckCircle className="w-4 h-4 text-sky-400 shrink-0" />
          <span>{statusMsg}</span>
        </div>
      )}

      {/* 1. Active Public Alerts (Answering: Am I Affected? How Serious? When? What To Do?) */}
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Current Basin Safety Advisories
          </h2>
          <span className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
            <Radio className="w-3 h-3 text-emerald-400 animate-pulse" /> Live Telemetry Feed
          </span>
        </div>

        {publicAlerts.length === 0 ? (
          <div className="p-6 bg-surface-elevated/40 border border-border rounded-xl text-center space-y-2">
            <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto" />
            <h3 className="text-sm font-bold text-white">No Active Emergency Flood Warnings</h3>
            <p className="text-xs text-slate-400">
              River stages and heavy rainfall across {regionInfo.region_name} remain within safe operational bounds.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {publicAlerts.map(alert => (
              <div
                key={alert.alert_id}
                className={`p-5 rounded-xl border space-y-3 shadow-lg ${
                  alert.severity === 'RED' ? 'bg-rose-950/40 border-rose-600/60 text-white' :
                  alert.severity === 'ORANGE' ? 'bg-amber-950/40 border-amber-600/60 text-white' :
                  'bg-sky-950/40 border-sky-600/60 text-white'
                }`}
              >
                <div className="flex justify-between items-start">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded font-mono uppercase tracking-wider ${
                    alert.severity === 'RED' ? 'bg-rose-600 text-white' :
                    alert.severity === 'ORANGE' ? 'bg-amber-500 text-slate-950' : 'bg-sky-500 text-white'
                  }`}>
                    {alert.severity} FLOOD ALERT
                  </span>
                  <span className="text-[11px] text-slate-300 flex items-center gap-1 font-mono">
                    <Clock className="w-3 h-3" /> +{alert.lead_time_hours}h Horizon
                  </span>
                </div>

                <div>
                  <h3 className="text-base font-bold flex items-center gap-1.5">
                    <MapPin className="w-4 h-4 text-rose-400 shrink-0" />
                    {alert.area}
                  </h3>
                  <p className="text-xs text-slate-200 mt-1">
                    {alert.why_alert_created}
                  </p>
                </div>

                <div className="p-3 bg-black/40 rounded-lg border border-white/10 space-y-1 text-xs">
                  <span className="text-[10px] font-semibold text-amber-300 uppercase tracking-wider block">
                    Official Guidance & Action ({regionInfo.authority_guidance_entity}):
                  </span>
                  <p className="text-slate-200">{alert.official_guidance}</p>
                </div>

                <div className="text-[10px] text-slate-400 flex justify-between pt-1 font-mono">
                  <span>Probability: <b>{(alert.flood_probability * 100).toFixed(0)}%</b></span>
                  <span>Data State: <b>{alert.data_state}</b></span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 2. Citizen Subscriptions & Phone OTP Verification */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Phone Verification Box */}
        <div className="bg-surface border border-border rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2.5 border-b border-border pb-3">
            <Smartphone className="w-5 h-5 text-indigo-400" />
            <div>
              <h3 className="text-sm font-bold text-white">Emergency SMS Phone Verification</h3>
              <p className="text-xs text-slate-400">Verify your mobile to activate localized emergency SMS alerts</p>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs text-slate-300 font-medium block mb-1">Mobile Number (+91)</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={phone}
                  onChange={e => setPhone(e.target.value)}
                  placeholder="Enter 10-digit mobile"
                  className="flex-1 bg-surface-elevated border border-border text-white text-xs px-3 py-2 rounded-lg outline-none font-mono"
                />
                <button
                  onClick={handleSendOtp}
                  disabled={otpCooldown > 0}
                  className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs rounded-lg font-semibold transition-colors flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  {otpCooldown > 0 ? `Wait ${otpCooldown}s` : (otpSent ? 'Resend OTP' : 'Send OTP')}
                </button>
              </div>
            </div>

            {otpSent && (
              <div className="p-3 bg-surface-elevated rounded-lg border border-border space-y-2 animate-fadeIn">
                <label className="text-xs text-slate-300 font-medium block">Enter 6-Digit SMS Verification Code</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    maxLength={6}
                    value={otp}
                    onChange={e => setOtp(e.target.value)}
                    placeholder="••••••"
                    className="flex-1 bg-slate-950 border border-border text-cyan-300 text-sm font-mono px-3 py-1.5 rounded outline-none tracking-widest text-center"
                  />
                  <button
                    onClick={handleVerifyOtp}
                    className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs rounded font-semibold transition-colors"
                  >
                    Verify
                  </button>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between text-xs pt-1">
              <span className="text-slate-400">Active Mobile: <b className="text-slate-300 font-mono">{maskedPhone}</b></span>
              <span className={`font-semibold ${phoneVerified ? 'text-emerald-400' : 'text-amber-400'}`}>
                {phoneVerified ? '✓ Verified (SMS Active)' : '⚠ Unverified (In-App Only)'}
              </span>
            </div>
          </div>
        </div>

        {/* Location Subscriptions Box */}
        <div className="bg-surface border border-border rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2.5 border-b border-border pb-3">
            <MapPin className="w-5 h-5 text-sky-400" />
            <div>
              <h3 className="text-sm font-bold text-white">Your Monitored Locations</h3>
              <p className="text-xs text-slate-400">Add Home, Work, or Family locations for geo-targeted warnings</p>
            </div>
          </div>

          {/* Existing Subscriptions List */}
          <div className="space-y-2 max-h-36 overflow-y-auto">
            {subscriptions.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-2">No location subscriptions added yet.</p>
            ) : (
              subscriptions.map(s => (
                <div key={s.subscription_id} className="flex justify-between items-center bg-surface-elevated/70 p-2.5 rounded-lg border border-border text-xs">
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800 text-[10px] font-mono">
                      {s.label}
                    </span>
                    <span className="font-semibold text-slate-200">{s.locality_name}</span>
                    <span className="text-[10px] text-slate-400">({s.radius_km}km radius)</span>
                  </div>
                  <button
                    onClick={() => handleDeleteSubscription(s.subscription_id)}
                    className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                    title="Remove Subscription"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>

          {/* Add New Subscription Form */}
          <div className="pt-2 border-t border-border flex gap-2">
            <select
              value={newLocLabel}
              onChange={e => setNewLocLabel(e.target.value)}
              className="bg-surface-elevated border border-border text-xs text-slate-300 rounded px-2 py-1.5 outline-none"
            >
              <option value="HOME">HOME</option>
              <option value="WORK">WORK</option>
              <option value="FAMILY">FAMILY</option>
              <option value="FARMLAND">FARMLAND</option>
            </select>
            <input
              type="text"
              value={newLocName}
              onChange={e => setNewLocName(e.target.value)}
              placeholder="Locality Name"
              className="flex-1 bg-surface-elevated border border-border text-white text-xs px-2.5 py-1.5 rounded outline-none"
            />
            <button
              onClick={handleAddSubscription}
              className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs rounded font-semibold flex items-center gap-1 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" /> Add
            </button>
          </div>
        </div>
      </div>

      {/* 3. In-App Notification Feed */}
      <div className="bg-surface border border-border rounded-xl p-5 space-y-4">
        <div className="flex justify-between items-center border-b border-border pb-3">
          <div className="flex items-center gap-2.5">
            <Bell className="w-5 h-5 text-amber-400" />
            <div>
              <h3 className="text-sm font-bold text-white">Your Notification Inbox</h3>
              <p className="text-xs text-slate-400">Historical alert dispatches for your registered locations</p>
            </div>
          </div>
          <span className="text-xs text-slate-400 font-mono">{inbox.length} messages</span>
        </div>

        <div className="space-y-2.5 max-h-56 overflow-y-auto">
          {inbox.length === 0 ? (
            <p className="text-xs text-slate-500 italic py-4 text-center">Inbox is empty. No emergency alerts dispatched to your registered zones.</p>
          ) : (
            inbox.map(item => (
              <div key={item.notification_id} className="bg-surface-elevated/50 p-3 rounded-lg border border-border space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-bold text-slate-200">{item.title}</span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {new Date(item.issued_at).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-xs text-slate-300">{item.body}</p>
                <div className="flex justify-between text-[10px] text-slate-400 pt-1 font-mono">
                  <span>Channel: <b>{item.channel}</b></span>
                  <span>Status: <b className="text-emerald-400">{item.status}</b></span>
                  <span>Template: <b>{item.provenance?.template_id}</b></span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
