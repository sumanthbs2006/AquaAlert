import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Activity, 
  Send, 
  Sliders, 
  CheckCircle, 
  AlertTriangle, 
  Truck, 
  Radio, 
  FileText, 
  Users, 
  Clock, 
  Check, 
  X, 
  Flame,
  LifeBuoy
} from 'lucide-react';
import { getTranslation } from '../i18n';

export default function AdminControlRoom({ activeScenario, sensorsSummary, currentLang = 'en' }) {
  const t = getTranslation(currentLang);
  const [triageData, setTriageData] = useState([]);
  const [resourcesData, setResourcesData] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  // Dispatch Modal State
  const [dispatchModalOpen, setDispatchModalOpen] = useState(false);
  const [selectedResource, setSelectedResource] = useState(null);
  const [dispatchWardId, setDispatchWardId] = useState('');
  const [dispatchQty, setDispatchQty] = useState(1);
  const [authorizerName, setAuthorizerName] = useState('Commandant Patil (SDMA)');
  const [isSubmittingDispatch, setIsSubmittingDispatch] = useState(false);

  // Alert Override Modal State
  const [overrideModalOpen, setOverrideModalOpen] = useState(false);
  const [overrideAlertId, setOverrideAlertId] = useState('ALERT-20260901-003');
  const [overrideSeverity, setOverrideSeverity] = useState('Severe');
  const [overrideReason, setOverrideReason] = useState('Ground radar sweep confirms intensifying cloud cell over subway.');

  // Broadcast Success Toast
  const [broadcastFeedback, setBroadcastFeedback] = useState(null);

  useEffect(() => {
    fetchAdminData();
  }, [activeScenario]);

  const fetchAdminData = () => {
    setLoading(true);
    Promise.all([
      fetch('/api/admin/triage').then(r => r.json()),
      fetch('/api/admin/resources').then(r => r.json()),
      fetch('/api/admin/audit-log').then(r => r.json())
    ])
    .then(([triageRes, resRes, auditRes]) => {
      setTriageData(triageRes.triage || []);
      setResourcesData(resRes);
      setAuditLogs(auditRes.logs || []);
      setLoading(false);
    })
    .catch((err) => {
      console.error('Error fetching admin data:', err);
      setLoading(false);
    });
  };

  const handleOpenDispatch = (resource) => {
    setSelectedResource(resource);
    setDispatchQty(1);
    setDispatchWardId(triageData[0]?.ward_id || 'ward-L-kurla-w');
    setDispatchModalOpen(true);
  };

  const submitDispatch = (e) => {
    e.preventDefault();
    if (!selectedResource) return;
    setIsSubmittingDispatch(true);

    fetch('/api/admin/dispatch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        resource_id: selectedResource.id,
        target_ward_id: dispatchWardId,
        quantity: Number(dispatchQty),
        authorized_by: authorizerName
      })
    })
    .then(r => r.json())
    .then((data) => {
      setIsSubmittingDispatch(false);
      setDispatchModalOpen(false);
      setBroadcastFeedback(`Resource dispatched: ${data.message}`);
      fetchAdminData(); // Refresh counts
      setTimeout(() => setBroadcastFeedback(null), 5000);
    })
    .catch((err) => {
      console.error(err);
      setIsSubmittingDispatch(false);
    });
  };

  const submitOverride = (e) => {
    e.preventDefault();
    fetch('/api/admin/override-alert', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        alert_id: overrideAlertId,
        new_severity: overrideSeverity,
        override_reason: overrideReason,
        authorized_by: authorizerName
      })
    })
    .then(r => r.json())
    .then((data) => {
      setOverrideModalOpen(false);
      setBroadcastFeedback(`Alert modified: ${data.message}`);
      fetchAdminData();
      setTimeout(() => setBroadcastFeedback(null), 5000);
    });
  };

  const triggerCitizenBroadcast = () => {
    fetch('/api/admin/broadcast', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        alert_id: 'ALERT-20260901-001',
        channels: ['cell_broadcast', 'sms', 'whatsapp'],
        target_ward_ids: ['ward-L-kurla-w', 'ward-GN-dharavi'],
        authorized_by: authorizerName
      })
    })
    .then(r => r.json())
    .then((data) => {
      setBroadcastFeedback(`Cell Broadcast Triggered! Reaching ~${data.broadcast_details?.estimated_citizen_reach?.toLocaleString()} citizens in flood corridor.`);
      setTimeout(() => setBroadcastFeedback(null), 6000);
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Top Operations Header */}
      <div className="bg-slate-900 border border-slate-800 p-4 sm:p-5 rounded-2xl shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="bg-red-500/20 text-red-400 border border-red-500/40 text-[10px] sm:text-xs font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5" />
              {t.adminHeaderTag}
            </span>
            <span className="text-[11px] sm:text-xs text-slate-400 font-mono">{t.adminHeaderDivision}</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight">
            {t.adminHeaderTitle}
          </h1>
          <p className="text-[11px] sm:text-xs text-slate-400 mt-0.5">
            {t.adminHeaderDesc}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full sm:w-auto">
          <button
            onClick={() => setOverrideModalOpen(true)}
            className="flex items-center justify-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-3.5 py-2 rounded-xl font-bold border border-slate-700 transition-colors shadow"
          >
            <Sliders className="w-4 h-4 text-amber-400" />
            {t.adminOverrideBtn}
          </button>

          <button
            onClick={triggerCitizenBroadcast}
            className="flex items-center justify-center gap-1.5 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white text-xs px-4 py-2 rounded-xl font-bold transition-all shadow-lg shadow-red-600/30"
          >
            <Radio className="w-4 h-4" />
            {t.adminBroadcastBtn}
          </button>
        </div>
      </div>

      {/* Broadcast Toast Notification */}
      {broadcastFeedback && (
        <div className="p-3.5 bg-emerald-950/90 border border-emerald-600 text-emerald-200 rounded-xl text-xs flex items-center justify-between shadow-2xl animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
            <span className="font-semibold">{broadcastFeedback}</span>
          </div>
          <button onClick={() => setBroadcastFeedback(null)} className="text-emerald-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Top 4 Mission Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow-lg">
          <span className="text-[11px] font-semibold text-slate-400 block">{t.adminCriticalZones}</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-3xl font-black text-red-400">
              {triageData.filter(t => t.risk_level === 'Severe').length}
            </span>
            <span className="text-xs text-slate-400">of 8 monitored wards</span>
          </div>
          <span className="text-[10px] text-red-400/80 block mt-1">Immediate dewatering required</span>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow-lg">
          <span className="text-[11px] font-semibold text-slate-400 block">{t.adminBasinRainIntensity}</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-3xl font-black text-sky-400">
              {sensorsSummary?.avg_basin_rain_mm_hr ?? 48.0}
            </span>
            <span className="text-xs text-slate-400">mm/hr average</span>
          </div>
          <span className="text-[10px] text-sky-400/80 block mt-1">Radar reflectivity: {sensorsSummary?.max_radar_reflectivity_dbz ?? 54} dBZ</span>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow-lg">
          <span className="text-[11px] font-semibold text-slate-400 block">{t.adminRiverGaugeSurcharge}</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className={`text-3xl font-black ${sensorsSummary?.peak_river_danger_status === 'DANGER' ? 'text-red-400' : 'text-amber-400'}`}>
              {sensorsSummary?.peak_river_danger_status ?? 'DANGER'}
            </span>
            <span className="text-xs text-slate-400">Mithi Sector</span>
          </div>
          <span className="text-[10px] text-amber-400/80 block mt-1">Tidal lock: Warning Level Exceeded</span>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow-lg">
          <span className="text-[11px] font-semibold text-slate-400 block">NDRF / SDRF Deployments</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-3xl font-black text-emerald-400">
              {resourcesData?.inventory?.reduce((acc, r) => acc + (r.dispatched || 0), 0) || 5}
            </span>
            <span className="text-xs text-slate-400">teams active</span>
          </div>
          <span className="text-[10px] text-emerald-400/80 block mt-1">6 units on immediate standby</span>
        </div>
      </div>

      {/* AI Resource Pre-Positioning Recommendations */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <div className="flex items-center gap-2">
            <Flame className="w-4 h-4 text-orange-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              {t.adminPrepositioningTitle}
            </h2>
          </div>
          <span className="text-[11px] text-cyan-400 font-mono">Hydrological Runoff Matrix</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {resourcesData?.ai_prepositioning_recommendations?.map((rec, i) => (
            <div key={i} className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 flex flex-col justify-between space-y-2">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-[10px] font-black px-1.5 py-0.5 rounded ${
                    rec.priority === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border border-red-500/40' : 'bg-amber-500/20 text-amber-400'
                  }`}>
                    {rec.priority}
                  </span>
                  <span className="text-[11px] text-slate-400 font-semibold">{rec.target}</span>
                </div>
                <h3 className="text-xs font-bold text-slate-100">{rec.action}</h3>
                <p className="text-[11px] text-slate-400 mt-1 leading-snug">{rec.rationale}</p>
              </div>
              <button
                onClick={() => {
                  const resType = rec.action.includes('Pump') ? 'res-pump-01' : (rec.action.includes('Boat') ? 'res-boat-02' : 'res-amb-03');
                  const match = resourcesData?.inventory?.find(r => r.id === resType);
                  if (match) handleOpenDispatch(match);
                }}
                className="w-full py-1.5 bg-cyan-700 hover:bg-cyan-600 text-white text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-1.5 shadow"
              >
                <Send className="w-3 h-3" />
                {t.adminDispatchEquipment}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Priority Triage Matrix Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              {t.adminTriageTableTitle}
            </h2>
          </div>
          <span className="text-xs text-slate-400">Total Wards: {triageData.length}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] font-bold border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">{t.adminRank}</th>
                <th className="px-4 py-3">{t.adminWardBasin}</th>
                <th className="px-4 py-3">{t.adminTriageScore}</th>
                <th className="px-4 py-3">Risk Level</th>
                <th className="px-4 py-3">{t.adminEstDepth}</th>
                <th className="px-4 py-3">{t.adminPopulation}</th>
                <th className="px-4 py-3">{t.adminAiAction}</th>
                <th className="px-4 py-3">{t.adminAction}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {triageData.map((row, idx) => (
                <tr key={row.ward_id} className="hover:bg-slate-800/50 transition-colors">
                  <td className="px-4 py-3 font-mono font-bold text-slate-400">#{idx + 1}</td>
                  <td className="px-4 py-3">
                    <span className="font-bold text-white block">{row.ward_name}</span>
                    <span className="text-[10px] text-slate-400">{row.zone} ({row.code})</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-bold text-sm text-cyan-400 font-mono">{row.triage_score}</span>
                    <span className="text-[10px] text-slate-500"> / 100</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      row.risk_level === 'Severe'
                        ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                        : (row.risk_level === 'High'
                        ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                        : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30')
                    }`}>
                      {row.risk_level}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-bold text-white font-mono">
                    {row.predicted_depth_cm} cm
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {row.population_at_risk?.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-[11px] text-slate-300">
                    {row.recommended_actions?.[0] || 'Standard monitoring'}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => {
                        const pump = resourcesData?.inventory?.find(r => r.id === 'res-pump-01');
                        if (pump) {
                          setSelectedResource(pump);
                          setDispatchWardId(row.ward_id);
                          setDispatchQty(2);
                          setDispatchModalOpen(true);
                        }
                      }}
                      className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-400 text-[11px] font-bold rounded border border-slate-700 transition-colors shadow"
                    >
                      Allocate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Emergency Resources Inventory Cards */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <div className="flex items-center gap-2">
            <Truck className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Emergency Logistics & Resource Fleet Status
            </h2>
          </div>
          <span className="text-xs text-slate-400">Live Inventory Telemetry</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {resourcesData?.inventory?.map((res) => (
            <div key={res.id} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-white">{res.name}</h3>
                </div>
                <div className="flex items-center gap-4 mt-2 text-xs">
                  <div>
                    <span className="text-slate-400 text-[10px] block">Deployed:</span>
                    <strong className="text-amber-400 text-sm font-mono">{res.deployed}</strong>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block">Standby:</span>
                    <strong className="text-emerald-400 text-sm font-mono">{res.standby}</strong>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block">Total Stock:</span>
                    <strong className="text-slate-200 text-sm font-mono">{res.total_available}</strong>
                  </div>
                </div>
              </div>

              <button
                onClick={() => handleOpenDispatch(res)}
                disabled={res.standby <= 0}
                className="w-full py-1.5 bg-slate-800 hover:bg-cyan-700 disabled:opacity-40 text-white text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-1.5"
              >
                <Send className="w-3 h-3" />
                Dispatch Units
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Incident Action Audit Log */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Emergency Action & Incident Audit Log
            </h2>
          </div>
          <span className="text-xs text-slate-400">Total Entries: {auditLogs.length}</span>
        </div>

        <div className="space-y-2">
          {auditLogs.map((log) => (
            <div key={log.id} className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-2 text-xs">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-white">{log.resource_name}</span>
                  <span className="text-slate-500 font-mono text-[10px]">[{log.timestamp}]</span>
                </div>
                <span className="text-slate-400 text-[11px] block mt-0.5">
                  Destination: <strong className="text-slate-200">{log.destination_ward}</strong> ({log.destination_location})
                </span>
                {log.notes && (
                  <span className="text-[10px] text-slate-500 italic block">Notes: {log.notes}</span>
                )}
              </div>
              <div className="text-right">
                <span className="bg-emerald-950 text-emerald-400 text-[10px] font-bold px-2 py-0.5 rounded border border-emerald-800">
                  {log.status}
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">
                  Auth: {log.authorized_by}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Dispatch Resource Modal */}
      {dispatchModalOpen && selectedResource && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md shadow-2xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div>
                <span className="text-xs font-bold text-cyan-400 block uppercase">Emergency Dispatch Order</span>
                <h3 className="text-sm font-bold text-white">{selectedResource.name}</h3>
              </div>
              <button onClick={() => setDispatchModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={submitDispatch} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Target Flood Ward / Basin:</label>
                <select
                  value={dispatchWardId}
                  onChange={(e) => setDispatchWardId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-medium"
                >
                  {triageData.map((t) => (
                    <option key={t.ward_id} value={t.ward_id}>
                      {t.ward_name} ({t.risk_level} Risk - Depth: {t.predicted_depth_cm}cm)
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Units to Deploy (Max {selectedResource.standby}):
                  </label>
                  <input
                    type="number"
                    min="1"
                    max={selectedResource.standby}
                    value={dispatchQty}
                    onChange={(e) => setDispatchQty(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200 font-mono"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Authorizing Officer:</label>
                  <input
                    type="text"
                    value={authorizerName}
                    onChange={(e) => setAuthorizerName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200"
                    required
                  />
                </div>
              </div>

              <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-[11px] text-slate-400">
                Units will be logged in the public disaster ledger and GPS tracking beacon enabled.
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setDispatchModalOpen(false)}
                  className="bg-slate-800 text-slate-300 px-3 py-1.5 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingDispatch}
                  className="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-1.5 rounded-lg font-bold shadow"
                >
                  {isSubmittingDispatch ? 'Executing...' : 'Authorize Dispatch'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Override Alert Modal */}
      {overrideModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md shadow-2xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div>
                <span className="text-xs font-bold text-amber-400 block uppercase">Human-in-the-loop Verification</span>
                <h3 className="text-sm font-bold text-white">Manual Alert Severity Override</h3>
              </div>
              <button onClick={() => setOverrideModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={submitOverride} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Target Alert ID:</label>
                <input
                  type="text"
                  value={overrideAlertId}
                  onChange={(e) => setOverrideAlertId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200 font-mono"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">New Severity Level:</label>
                <select
                  value={overrideSeverity}
                  onChange={(e) => setOverrideSeverity(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200 font-semibold"
                >
                  <option value="Severe">Severe (Red Alert - Immediate Evacuation)</option>
                  <option value="High">High (Orange Alert - Major Waterlogging)</option>
                  <option value="Moderate">Moderate (Yellow Watch - Advisory)</option>
                  <option value="Silenced">Silenced (Cancel / False Positive)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Reason for Override:</label>
                <textarea
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  rows={3}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setOverrideModalOpen(false)}
                  className="bg-slate-800 text-slate-300 px-3 py-1.5 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-amber-600 hover:bg-amber-500 text-white px-4 py-1.5 rounded-lg font-bold shadow"
                >
                  Apply Override
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
