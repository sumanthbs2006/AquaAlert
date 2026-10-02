import React, { useState } from 'react';
import { 
  X, 
  Smartphone, 
  ShieldAlert, 
  CheckCheck, 
  Send, 
  History, 
  Radio, 
  AlertTriangle,
  RefreshCw,
  PhoneCall
} from 'lucide-react';

export default function SmsInboxModal({ 
  isOpen, 
  onClose, 
  currentUser, 
  smsHistory = [], 
  onTriggerTestSms,
  currentRegion
}) {
  const [sendingTest, setSendingTest] = useState(false);
  const [testSuccessMsg, setTestSuccessMsg] = useState('');

  if (!isOpen) return null;

  const phoneDisplay = currentUser?.phone || '+91 98765 43210';

  const handleTestClick = async () => {
    try {
      setSendingTest(true);
      setTestSuccessMsg('');
      await onTriggerTestSms();
      setSendingTest(false);
      setTestSuccessMsg('Test emergency SMS dispatched to ' + phoneDisplay);
      setTimeout(() => setTestSuccessMsg(''), 4000);
    } catch {
      setSendingTest(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center p-3 sm:p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div 
        className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl text-slate-100 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-5 py-4 bg-slate-950/90 border-b border-slate-800 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500/20 to-amber-500/20 border border-red-500/40 flex items-center justify-center text-red-400 shrink-0">
              <Smartphone className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white">Emergency SMS Alerts</h3>
                <span className="text-[11px] bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded-full font-bold">
                  {smsHistory.length} {smsHistory.length === 1 ? 'Message' : 'Messages'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Active alerts sent to signed-in number: <strong className="text-cyan-300 font-semibold">{phoneDisplay}</strong>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
            title="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Action Bar (Test Trigger & Carrier info) */}
        <div className="bg-slate-950/60 px-5 py-3 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Gateway: <strong className="text-slate-200">Infobip Global SMS Gateway (API Key Active)</strong></span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleTestClick}
              disabled={sendingTest}
              className="px-3 py-1.5 bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white rounded-lg font-semibold flex items-center gap-1.5 shadow-md shadow-red-950/50 transition-all cursor-pointer disabled:opacity-50"
            >
              <Send className={`w-3.5 h-3.5 ${sendingTest ? 'animate-spin' : ''}`} />
              <span>{sendingTest ? 'Dispatching via Infobip...' : 'Test Send Flood Alert SMS'}</span>
            </button>
          </div>
        </div>

        {testSuccessMsg && (
          <div className="bg-emerald-950/60 border-b border-emerald-700/60 px-5 py-2 text-xs text-emerald-300 flex items-center gap-2 animate-in fade-in">
            <CheckCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{testSuccessMsg}</span>
          </div>
        )}

        {/* SMS List Body */}
        <div className="p-5 flex-1 overflow-y-auto space-y-4">
          {smsHistory.length === 0 ? (
            <div className="text-center py-12 px-4 space-y-3">
              <div className="w-14 h-14 rounded-2xl bg-slate-800/60 border border-slate-700 mx-auto flex items-center justify-center text-slate-500">
                <History className="w-7 h-7" />
              </div>
              <h4 className="text-sm font-semibold text-slate-300">No Emergency SMS Sent Yet</h4>
              <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">
                Emergency SMS alerts are strictly restricted to heavy rainfall (&gt;= 25 mm/h) or flood conditions near <span className="text-cyan-300 font-medium">{currentRegion?.name || "your area"}</span>. When triggered, the alert is simultaneously dispatched to <span className="text-white font-mono">{phoneDisplay}</span> and the nearby rescue authority (NDRF / SDRF) via Infobip.
              </p>
              <button
                onClick={handleTestClick}
                className="mt-2 inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-semibold shadow-md transition-all cursor-pointer"
              >
                <Radio className="w-3.5 h-3.5" />
                <span>Simulate Flood Hazard &amp; Dispatch SMS</span>
              </button>
            </div>
          ) : (
            smsHistory.map((msg, index) => {
              const isAuthority = msg.recipient_type === 'rescue_authority';
              return (
                <div 
                  key={msg.id || index}
                  className={`bg-slate-950/90 border rounded-xl p-4 space-y-2.5 shadow-md transition-colors ${
                    isAuthority ? 'border-amber-700/60 bg-gradient-to-br from-slate-950 via-slate-950 to-amber-950/30' : 'border-slate-800 hover:border-slate-700'
                  }`}
                >
                  {/* Meta Header */}
                  <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] pb-2 border-b border-slate-800/80">
                    <div className="flex items-center gap-2">
                      <span className={`font-mono font-bold px-2 py-0.5 rounded border ${
                        isAuthority 
                          ? 'text-amber-400 bg-amber-950/80 border-amber-700/60'
                          : 'text-red-400 bg-red-950/80 border-red-800/60'
                      }`}>
                        {isAuthority ? 'RESCUE AUTHORITY COPY' : (msg.severity || 'SEVERE')}
                      </span>
                      <span className="text-slate-300 font-semibold">
                        {isAuthority ? (msg.authority_name || 'Nearby Disaster Response Force') : (msg.hazard_type || 'Heavy Rainfall & Flood Threat')}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-slate-400 font-mono text-[10px]">
                      <span>{msg.formatted_time || 'Recent'}</span>
                      <span className="flex items-center gap-1 text-emerald-400 font-medium">
                        <CheckCheck className="w-3.5 h-3.5" />
                        {msg.delivery_status || 'DELIVERED'}
                      </span>
                    </div>
                  </div>

                  {/* Recipient banner */}
                  <div className="text-[11px] text-slate-400 flex flex-wrap items-center justify-between gap-2">
                    <div>
                      Target Handset: <strong className="text-cyan-300 font-mono">{msg.recipient_phone || phoneDisplay}</strong>
                      {isAuthority && msg.station && (
                        <span className="ml-2 text-slate-400">• Station: <span className="text-amber-300">{msg.station}</span></span>
                      )}
                    </div>
                    {msg.infobip_message_id && (
                      <div className="font-mono text-[10px] text-emerald-400/90">
                        Infobip ID: {msg.infobip_message_id.slice(-8)}
                      </div>
                    )}
                  </div>

                  {/* Message Body (Realistic Mobile SMS bubble) */}
                  <div className="p-3 bg-slate-900/90 rounded-lg border border-slate-800 text-xs text-amber-100 font-sans leading-relaxed select-all">
                    {msg.message}
                  </div>

                  {/* Technical Telecom Details */}
                  <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400 pt-1">
                    <div>
                      Area: <strong className="text-slate-200">{msg.area_name || currentRegion?.name}</strong>
                      {msg.rainfall_mm_hr && (
                        <span className="ml-2 font-mono text-sky-300">
                          • Rain: {msg.rainfall_mm_hr} mm/h
                        </span>
                      )}
                      {!isAuthority && msg.rescue_authority_alerted && (
                        <span className="ml-2 text-emerald-400 font-medium">
                          • Alerted: {msg.rescue_authority_alerted.split('&')[0]}
                        </span>
                      )}
                    </div>
                    <div className="font-mono text-[10px] text-slate-400">
                      Gateway: <span className="text-slate-300">{msg.carrier_gateway || 'Infobip Global SMS Gateway'}</span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 bg-slate-950 border-t border-slate-800 flex items-center justify-between gap-2 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <PhoneCall className="w-3.5 h-3.5 text-red-400" />
            <span>State Emergency Disaster Helpline: <strong className="text-white">112</strong> / <strong className="text-white">1070</strong></span>
          </div>

          <button
            onClick={onClose}
            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
