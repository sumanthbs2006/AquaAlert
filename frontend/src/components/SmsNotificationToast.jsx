import React, { useEffect } from 'react';
import { MessageSquareWarning, X, Smartphone, CheckCheck, ExternalLink, ShieldAlert, ArrowRight } from 'lucide-react';

export default function SmsNotificationToast({ sms, onDismiss, onViewInbox }) {
  useEffect(() => {
    if (!sms) return;
    const timer = setTimeout(() => {
      if (onDismiss) onDismiss();
    }, 12000);
    return () => clearTimeout(timer);
  }, [sms, onDismiss]);

  if (!sms) return null;

  return (
    <aside 
      aria-label="Emergency SMS Alert"
      className="fixed top-16 right-3 sm:right-6 z-[100] max-w-md w-[calc(100vw-1.5rem)] animate-in slide-in-from-top-4 fade-in duration-300"
    >
      <div className="bg-slate-900/98 backdrop-blur-xl border-2 border-red-500/80 rounded-2xl p-4 shadow-2xl shadow-red-950/60 text-white relative overflow-hidden">
        {/* Top Emergency Indicator Strip */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-red-600 via-amber-500 to-red-600 animate-pulse" />

        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-2.5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-red-500/20 border border-red-500/50 flex items-center justify-center text-red-400 shrink-0">
              <Smartphone className="w-4 h-4 animate-bounce" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] font-extrabold uppercase tracking-wider text-red-400 bg-red-950/80 px-2 py-0.5 rounded border border-red-800/60 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-ping inline-block"></span>
                  Emergency SMS Alert Output
                </span>
                <span className="text-[10px] text-slate-400 font-mono">
                  {sms.formatted_time || 'Just Now'}
                </span>
              </div>
              <p className="text-xs text-slate-300 font-medium mt-0.5">
                Sent to Registered Phone: <strong className="text-cyan-300 font-bold font-mono">{sms.recipient_phone || sms.phone}</strong>
              </p>
              {sms.rescue_authority_alerted && (
                <p className="text-[11px] text-emerald-400 flex items-center gap-1 mt-0.5 font-medium truncate max-w-[280px]">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0"></span>
                  <span className="truncate">Rescue QRT: <strong className="text-white">{sms.rescue_authority_alerted}</strong></span>
                </p>
              )}
            </div>
          </div>

          <button
            onClick={onDismiss}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
            title="Dismiss notification"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* SMS Message Bubble */}
        <div className="bg-slate-950/90 border border-slate-800 rounded-xl p-3 mb-3 shadow-inner">
          <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1.5 pb-1 border-b border-slate-800/60 font-mono">
            <span className="flex items-center gap-1 text-red-400 font-semibold">
              <ShieldAlert className="w-3 h-3" />
              INFOBIP GATEWAY • AQUAALERT
            </span>
            <span className="flex items-center gap-1 text-emerald-400">
              <CheckCheck className="w-3 h-3" />
              {sms.delivery_status || 'Delivered'}
            </span>
          </div>
          <p className="text-xs sm:text-[13px] leading-relaxed text-amber-100 font-sans select-all">
            {sms.message}
          </p>
          <div className="mt-2 flex items-center justify-between text-[10px] text-slate-400">
            <span className="truncate max-w-[200px]">
              Area: <strong className="text-slate-300">{sms.area_name}</strong>
            </span>
            <span className="font-mono text-cyan-400">
              {sms.rainfall_mm_hr ? `${sms.rainfall_mm_hr} mm/h` : 'Heavy Rain'}
            </span>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between gap-2 pt-1 border-t border-slate-800/70 text-xs">
          <span className="text-[11px] text-slate-400 flex items-center gap-1 truncate max-w-[220px]">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block shrink-0"></span>
            Carrier: <span className="font-mono text-[10px] text-slate-300 truncate">{sms.carrier_gateway || 'Infobip Global SMSC'}</span>
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                onViewInbox();
                onDismiss();
              }}
              className="px-2.5 py-1 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition-all shadow-md shadow-cyan-600/20 cursor-pointer"
            >
              <span>View All SMS</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
