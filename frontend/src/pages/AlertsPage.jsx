import React, { useState, useEffect } from 'react';
import { 
  BellRing, 
  ShieldAlert, 
  Clock, 
  MapPin, 
  Radio, 
  Smartphone, 
  MessageSquare, 
  CheckCircle2, 
  AlertOctagon, 
  X, 
  ExternalLink,
  Download,
  Share2,
  Volume2
} from 'lucide-react';
import { getTranslation } from '../i18n';

export default function AlertsPage({ 
  currentLang, 
  setCurrentLang, 
  onNavigateToLocation,
  currentUser,
  onTriggerSmsForAlert,
  currentRegion,
  smsHistory = []
}) {
  const t = getTranslation(currentLang);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');
  const [selectedAlertForPreview, setSelectedAlertForPreview] = useState(null);
  const [previewChannel, setPreviewChannel] = useState('cell_broadcast'); // 'cell_broadcast', 'whatsapp', 'sms'

  useEffect(() => {
    fetchAlerts();
  }, [currentLang]);

  const fetchAlerts = () => {
    setLoading(true);
    fetch(`/api/alerts?lang=${currentLang}`)
      .then((res) => res.json())
      .then((data) => {
        setAlerts(data.alerts || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching alerts:', err);
        setLoading(false);
      });
  };

  const filteredAlerts = alerts.filter((a) => {
    if (selectedSeverity === 'ALL') return true;
    return a.severity.toUpperCase() === selectedSeverity;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Top Banner & Title */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/90 border border-slate-800 p-5 rounded-2xl shadow-xl">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-red-500/20 text-red-400 border border-red-500/40 text-xs font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
              <Radio className="w-3 h-3 animate-pulse" />
              CAP v1.2 CERTIFIED BROADCAST
            </span>
            <span className="text-xs text-slate-400 font-mono">ITU-T X.1303 Compliant</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight">
            {t.alertsTitle}
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            {t.alertsSubtitle}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <span className="flex items-center gap-1.5 bg-emerald-950/80 border border-emerald-800/80 text-emerald-400 text-xs px-3 py-1.5 rounded-xl font-semibold shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            Live National Feeds Active
          </span>
          <button
            onClick={fetchAlerts}
            className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-3 py-1.5 rounded-xl font-semibold border border-slate-700 transition-colors shadow cursor-pointer"
            title="Refresh Live National Alerts"
          >
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            Sync Feeds
          </button>
        </div>
      </div>

      {/* Registered Handset SMS Alert Output Status Banner */}
      {currentUser?.phone ? (
        <div className="bg-gradient-to-r from-red-950/80 via-slate-900 to-amber-950/80 border border-red-500/50 rounded-2xl p-4 shadow-xl flex flex-wrap items-center justify-between gap-3 animate-in fade-in">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-500/20 border border-red-500/40 flex items-center justify-center text-red-400 shrink-0">
              <Smartphone className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-red-400 uppercase tracking-wide flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping inline-block"></span>
                  Emergency SMS Alert Output Service Active
                </span>
                <span className="text-[10px] bg-red-900/60 text-red-200 border border-red-700/60 px-2 py-0.2 rounded-full font-mono">
                  TRAI-DND Priority 1
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                Registered Handset: <strong className="text-cyan-300 font-mono text-sm">{currentUser.phone}</strong>
                <span className="text-slate-400 ml-2 hidden sm:inline">• Automated SMS warnings are dispatched whenever an alert is near your location.</span>
              </p>
            </div>
          </div>

          <button
            onClick={() => onTriggerSmsForAlert && onTriggerSmsForAlert(null, {
              area_name: currentRegion?.name || 'Local Basin',
              hazard_type: 'Urgent Weather & Flood Advisory Test',
              rainfall_mm_hr: 75.0,
              severity: 'Severe'
            })}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white rounded-xl text-xs font-bold shadow-md cursor-pointer transition-all active:scale-95 shrink-0"
          >
            <Smartphone className="w-3.5 h-3.5" />
            <span>Test SMS Output to My Handset</span>
          </button>
        </div>
      ) : (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-3.5 flex items-center justify-between text-xs text-slate-300">
          <div className="flex items-center gap-2">
            <Smartphone className="w-4 h-4 text-cyan-400" />
            <span>Login with your Indian mobile number to enable automated emergency SMS alerts sent to your phone.</span>
          </div>
        </div>
      )}

      {/* Severity Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 bg-slate-950 p-1 rounded-xl border border-slate-800 flex-wrap">
          {[
            { id: 'ALL', label: t.filterAll },
            { id: 'SEVERE', label: t.filterSevere },
            { id: 'HIGH', label: t.filterHigh },
            { id: 'MODERATE', label: t.filterModerate }
          ].map((sev) => (
            <button
              key={sev.id}
              onClick={() => setSelectedSeverity(sev.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                selectedSeverity === sev.id
                  ? 'bg-slate-800 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {sev.label}
            </button>
          ))}
        </div>

        <div className="text-xs text-slate-400">
          Showing <strong>{filteredAlerts.length}</strong> active warnings in{' '}
          <strong className="text-cyan-400 uppercase">{currentLang}</strong>
        </div>
      </div>

      {/* Alerts Cards List */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 text-sm">
          Loading verified meteorological alerts...
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAlerts.map((alert) => {
            const isSevere = alert.severity === 'Severe';
            const isHigh = alert.severity === 'High';

            const borderTheme = isSevere
              ? 'border-red-500/50 bg-red-950/20'
              : isHigh
              ? 'border-orange-500/50 bg-orange-950/20'
              : 'border-yellow-500/50 bg-yellow-950/20';

            const badgeTheme = isSevere
              ? 'bg-red-600 text-white'
              : isHigh
              ? 'bg-orange-600 text-white'
              : 'bg-yellow-600 text-black font-extrabold';

            return (
              <div
                key={alert.id}
                className={`p-5 rounded-2xl border ${borderTheme} backdrop-blur-md shadow-2xl transition-all hover:scale-[1.005] space-y-4`}
              >
                {/* Header Row */}
                <div className="flex flex-wrap items-start justify-between gap-2 border-b border-slate-800/80 pb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-[10px] uppercase font-black px-2 py-0.5 rounded tracking-wider ${badgeTheme}`}>
                        {alert.severity} ALERT
                      </span>
                      <span className="text-xs text-slate-400 font-mono">
                        ID: {alert.identifier}
                      </span>
                      <span className="text-slate-600">|</span>
                      <span className="text-xs text-slate-400 flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-400" />
                        Issued: {alert.sent}
                      </span>
                    </div>
                    <h2 className="text-lg font-black text-white tracking-tight">
                      {alert.headline}
                    </h2>
                  </div>

                  {alert.is_verified_by_authority ? (
                    <span className="flex items-center gap-1 bg-emerald-950/80 border border-emerald-800 text-emerald-300 text-[11px] font-bold px-2.5 py-1 rounded-full">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      Verified: {alert.verified_by}
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 bg-amber-950/80 border border-amber-800 text-amber-300 text-[11px] font-bold px-2.5 py-1 rounded-full">
                      <AlertOctagon className="w-3.5 h-3.5 text-amber-400" />
                      Pending Authority Sign-off
                    </span>
                  )}
                </div>

                {/* Body Content */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                  {/* Left: Time Windows & Roads */}
                  <div className="space-y-2.5 bg-slate-950/80 p-3.5 rounded-xl border border-slate-800">
                    <div>
                      <span className="text-[11px] text-slate-400 block font-semibold">
                        0–6h Rain Nowcast Window:
                      </span>
                      <span className="font-bold text-sky-400 text-sm">
                        {alert.rainfall_time_window}
                      </span>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-400 block font-semibold">
                        6–24h Inundation Window:
                      </span>
                      <span className="font-bold text-rose-400 text-sm">
                        {alert.inundation_time_window}
                      </span>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-400 block font-semibold">
                        {t.affectedRoads}:
                      </span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {alert.affected_roads?.map((road, i) => (
                          <span key={i} className="bg-slate-800 text-slate-300 text-[10px] px-2 py-0.5 rounded border border-slate-700">
                            🚧 {road}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Center & Right: Instructions and Action Guidance */}
                  <div className="md:col-span-2 space-y-3 bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 flex flex-col justify-between">
                    <div>
                      <span className="text-[11px] text-slate-400 block font-semibold mb-1">
                        Action Directive & Public Guidance:
                      </span>
                      <p className="text-sm font-medium text-slate-200 leading-relaxed bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                        {alert.instruction}
                      </p>
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800/80">
                      <span className="text-[11px] text-slate-400">
                        Target Geo-Zone: <strong className="text-slate-200">{alert.area_desc}</strong>
                      </span>

                      <div className="flex flex-wrap items-center gap-2">
                        {/* Send SMS Alert to Registered Mobile */}
                        <button
                          onClick={() => onTriggerSmsForAlert && onTriggerSmsForAlert(alert)}
                          className="flex items-center gap-1.5 bg-gradient-to-r from-red-600 via-rose-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white text-xs px-3.5 py-1.5 rounded-lg font-bold transition-all shadow-lg hover:shadow-red-500/25 active:scale-95 cursor-pointer ring-1 ring-red-400/40"
                          title={`Transmit official flood warning SMS to ${currentUser?.phone || 'registered handset'}`}
                        >
                          <Smartphone className="w-3.5 h-3.5 text-white animate-bounce" />
                          <span>{currentUser?.phone ? `Send SMS to ${currentUser.phone}` : "Send SMS to My Phone"}</span>
                        </button>

                        <button
                          onClick={() => onNavigateToLocation && onNavigateToLocation(alert)}
                          className="flex items-center gap-1.5 bg-gradient-to-r from-sky-600 to-cyan-600 hover:from-sky-500 hover:to-cyan-500 text-white text-xs px-3.5 py-1.5 rounded-lg font-bold transition-all shadow-lg hover:shadow-cyan-500/25 active:scale-95 cursor-pointer ring-1 ring-cyan-400/40"
                          title="Open GIS Dashboard at this alert location"
                        >
                          <MapPin className="w-3.5 h-3.5 text-cyan-200" />
                          <span>{t.viewInGisDashboard || "View on GIS Map →"}</span>
                        </button>

                        <button
                          onClick={() => setSelectedAlertForPreview(alert)}
                          className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700 text-xs px-3.5 py-1.5 rounded-lg font-bold transition-all shadow cursor-pointer"
                        >
                          <Smartphone className="w-3.5 h-3.5 text-cyan-400" />
                          {t.testBroadcastModal}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Mock Emergency Broadcast Simulator Modal */}
      {selectedAlertForPreview && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="bg-slate-950 p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-cyan-400 block">
                  PUBLIC NOTIFICATION SIMULATOR
                </span>
                <h3 className="text-sm font-bold text-white">
                  Multi-Channel Emergency Alert Preview
                </h3>
              </div>
              <button
                onClick={() => setSelectedAlertForPreview(null)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Channel Tabs */}
            <div className="flex border-b border-slate-800 bg-slate-950/60 p-1 text-xs">
              <button
                onClick={() => setPreviewChannel('cell_broadcast')}
                className={`flex-1 py-2 font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-colors ${
                  previewChannel === 'cell_broadcast'
                    ? 'bg-red-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Radio className="w-3.5 h-3.5" />
                Cell Broadcast (Siren)
              </button>
              <button
                onClick={() => setPreviewChannel('whatsapp')}
                className={`flex-1 py-2 font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-colors ${
                  previewChannel === 'whatsapp'
                    ? 'bg-emerald-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5" />
                WhatsApp
              </button>
              <button
                onClick={() => setPreviewChannel('sms')}
                className={`flex-1 py-2 font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-colors ${
                  previewChannel === 'sms'
                    ? 'bg-sky-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Smartphone className="w-3.5 h-3.5" />
                SMS Blast
              </button>
            </div>

            {/* Channel Simulation Canvas */}
            <div className="p-6 bg-slate-950 flex items-center justify-center min-h-[320px]">
              {/* Option 1: Cell Broadcast Emergency Alarm */}
              {previewChannel === 'cell_broadcast' && (
                <div className="w-full max-w-sm bg-red-950/90 border-2 border-red-600 rounded-2xl p-5 text-center shadow-2xl space-y-3 animate-bounce-short">
                  <div className="w-12 h-12 rounded-full bg-red-600 mx-auto flex items-center justify-center text-white text-2xl shadow-lg">
                    ⚠️
                  </div>
                  <h4 className="text-red-300 text-xs font-black tracking-widest uppercase">
                    GOVERNMENT EMERGENCY ALERT
                  </h4>
                  <p className="text-sm font-black text-white leading-snug">
                    {selectedAlertForPreview.headline}
                  </p>
                  <p className="text-xs text-red-200/90 bg-red-900/60 p-3 rounded-lg border border-red-700/60 text-left">
                    {selectedAlertForPreview.instruction}
                  </p>
                  <div className="text-[10px] text-red-400 font-mono">
                    High Priority Geo-Fence Broadcast | Dispatched by SDMA
                  </div>
                </div>
              )}

              {/* Option 2: WhatsApp Flash Message */}
              {previewChannel === 'whatsapp' && (
                <div className="w-full max-w-sm bg-[#0b141a] rounded-xl p-4 text-xs space-y-2 border border-slate-800 shadow-2xl">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center text-white font-bold">
                      AA
                    </div>
                    <div>
                      <span className="font-bold text-white text-xs block">AquaAlert AI Verified</span>
                      <span className="text-[10px] text-emerald-400">Official Government Channel</span>
                    </div>
                  </div>
                  <div className="bg-[#1f2c34] p-3 rounded-xl rounded-tl-none text-slate-200 space-y-1.5">
                    <div className="font-bold text-amber-300">
                      🚨 {selectedAlertForPreview.headline}
                    </div>
                    <p className="text-[11px] text-slate-300 leading-relaxed">
                      {selectedAlertForPreview.instruction}
                    </p>
                    <div className="text-[10px] text-slate-400 border-t border-slate-700 pt-1 mt-1">
                      Helpline: <strong>112 / 1916</strong> | Area: {selectedAlertForPreview.area_desc}
                    </div>
                    <span className="text-[9px] text-slate-400 block text-right">Just now ✓✓</span>
                  </div>
                </div>
              )}

              {/* Option 3: SMS */}
              {previewChannel === 'sms' && (
                <div className="w-full max-w-sm bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs space-y-2 shadow-2xl">
                  <div className="text-slate-400 text-[10px] text-center border-b border-slate-800 pb-1 font-mono">
                    Sender: <strong>VM-GOVAQU</strong> | Indian Carrier SMS Gateway
                  </div>
                  <div className="bg-sky-950/60 border border-sky-800/80 p-3.5 rounded-xl text-sky-100 text-xs leading-relaxed">
                    {selectedAlertForPreview.sms_preview}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="bg-slate-950 p-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedAlertForPreview(null)}
                className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-4 py-1.5 rounded-lg font-semibold transition-colors"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
