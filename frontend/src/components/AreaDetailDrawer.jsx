import React, { useEffect, useState } from 'react';
import { 
  X, 
  AlertTriangle, 
  Droplets, 
  TrendingUp, 
  HelpCircle, 
  ShieldCheck, 
  Building, 
  MapPin, 
  Navigation, 
  PhoneCall, 
  Sliders, 
  CheckCircle2,
  Info
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { getTranslation } from '../i18n';

export default function AreaDetailDrawer({ 
  wardId, 
  onClose,
  activeScenario,
  activeScenarioName,
  currentLang = 'en',
  isNavigating = false,
  onStartNavigation
}) {
  const t = getTranslation(currentLang);
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('hydrograph'); // 'hydrograph' or 'xai'

  useEffect(() => {
    if (!wardId) return;
    setLoading(true);

    fetch(`/api/forecasts/${wardId}`)
      .then((res) => {
        if (!res.ok) throw new Error('Network error');
        return res.json();
      })
      .then((data) => {
        setForecastData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching ward forecast:', err);
        setLoading(false);
      });
  }, [wardId, activeScenario?.id, activeScenarioName]);

  if (!wardId) return null;

  const pred = forecastData?.prediction;
  const ward = forecastData?.ward_info;

  const getRiskBadge = (level) => {
    switch (level) {
      case 'Severe':
        return { bg: 'bg-red-500/20 text-red-400 border-red-500/40', text: t.riskSevere };
      case 'High':
        return { bg: 'bg-orange-500/20 text-orange-400 border-orange-500/40', text: t.riskHigh };
      case 'Moderate':
        return { bg: 'bg-amber-500/20 text-amber-400 border-amber-500/40', text: t.riskModerate };
      default:
        return { bg: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40', text: t.riskLow };
    }
  };

  const badge = getRiskBadge(pred?.risk_level);

  return (
    <aside className="fixed sm:absolute bottom-0 sm:bottom-auto sm:top-0 right-0 left-0 sm:left-auto w-full sm:max-w-md max-h-[85vh] sm:max-h-none sm:h-full bg-slate-900/98 sm:bg-slate-900/95 backdrop-blur-2xl border-t sm:border-t-0 sm:border-l border-slate-700/80 sm:border-slate-800 rounded-t-3xl sm:rounded-none shadow-2xl z-40 sm:z-30 flex flex-col transition-transform duration-300 mobile-bottom-sheet sm:animate-none safe-bottom">
      {/* Mobile Swipe Handle Indicator */}
      <div className="w-12 h-1.5 bg-slate-700/80 rounded-full mx-auto mt-2.5 mb-0.5 sm:hidden shrink-0"></div>

      {/* Drawer Header */}
      <div className="p-3.5 sm:p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/80 shrink-0">
        <div className="min-w-0 mr-2">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] sm:text-xs font-mono font-bold text-cyan-400 bg-cyan-950 px-1.5 py-0.5 rounded border border-cyan-800">
              {ward?.code || 'WARD'}
            </span>
            <h2 className="text-sm sm:text-base font-bold text-white tracking-tight truncate">
              {ward?.name || 'Loading Area...'}
            </h2>
          </div>
          <p className="text-[11px] sm:text-xs text-slate-400 mt-0.5 truncate">
            Zone: {ward?.zone} | Pop: {ward?.population?.toLocaleString()}
          </p>
          {forecastData?.is_outside_basin && (
            <div className="mt-1.5 flex items-center gap-1.5 text-[10px] text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/60 w-fit">
              <ShieldCheck className="w-3 h-3 text-emerald-400 shrink-0" />
              <span>Outside Mumbai Pilot Basin &bull; Live Regional Weather</span>
            </div>
          )}
        </div>

        <button
          onClick={onClose}
          className="p-2 sm:p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors shrink-0"
          aria-label="Close drawer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-cyan-500 mb-2"></div>
          <span className="ml-3">{t.runningInference}</span>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Primary Alert Banner */}
          <div className={`p-3 rounded-xl border ${badge.bg} flex items-center justify-between shadow-lg`}>
            <div>
              <span className="text-xs font-black tracking-wide uppercase block">
                {badge.text}
              </span>
              <span className="text-2xl font-black text-white">
                {pred?.risk_score} <span className="text-xs font-normal text-slate-400">/ 100 {t.riskIndex}</span>
              </span>
            </div>
            <div className="text-right">
              <span className="text-[11px] text-slate-300 block">{t.estInundationDepth}</span>
              <span className="text-xl font-bold text-white">
                {pred?.predicted_depth_cm} cm
              </span>
              <span className="text-[10px] text-slate-400 block font-mono">
                (Range: {pred?.depth_range_cm})
              </span>
            </div>
          </div>

          {/* AI Decision Support & Confidence Telemetry */}
          <div className="grid grid-cols-2 gap-2 bg-slate-950 p-3 rounded-xl border border-slate-800/80 text-xs">
            <div>
              <span className="text-slate-400 block text-[11px]">{t.modelConfidence}</span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span className="font-bold text-emerald-300 text-sm">{pred?.confidence_pct}%</span>
              </div>
              <span className="text-[10px] text-slate-500">{t.treeAgreement}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">{t.rainfallNowcast6h}</span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <Droplets className="w-4 h-4 text-sky-400" />
                <span className="font-bold text-sky-300 text-sm">{pred?.rainfall_nowcast_6h_mm} mm</span>
              </div>
              <span className="text-[10px] text-slate-500">{t.peakExpectedAt} {pred?.peak_rainfall_hr}</span>
            </div>
          </div>

          {/* Sub-Tabs: 24h Hydrograph vs AI Explainability */}
          <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setActiveTab('hydrograph')}
              className={`flex-1 py-1.5 rounded-md font-semibold transition-all ${
                activeTab === 'hydrograph'
                  ? 'bg-cyan-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {t.tabHydrograph}
            </button>
            <button
              onClick={() => setActiveTab('xai')}
              className={`flex-1 py-1.5 rounded-md font-semibold transition-all ${
                activeTab === 'xai'
                  ? 'bg-cyan-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {t.tabXai}
            </button>
          </div>

          {/* Tab 1: 24-Hr Forecast Charts */}
          {activeTab === 'hydrograph' && (
            <div className="space-y-3">
              {/* Rainfall Projection Chart */}
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <Droplets className="w-3.5 h-3.5 text-sky-400" />
                    {t.hourlyPrecipitation}
                  </span>
                  <span className="text-[10px] text-sky-400 font-mono">0-24h</span>
                </div>
                <div className="h-32 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={pred?.hourly_forecast || []} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                      <defs>
                        <linearGradient id="rainColor" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#0284c7" stopOpacity={0.8}/>
                          <stop offset="95%" stopColor="#0284c7" stopOpacity={0.0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="time_label" stroke="#64748b" fontSize={9} interval={3} />
                      <YAxis stroke="#64748b" fontSize={9} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                        formatter={(val) => [`${val} mm`, 'Rainfall']}
                      />
                      <Area type="monotone" dataKey="rainfall_mm" stroke="#38bdf8" fillOpacity={1} fill="url(#rainColor)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Inundation Depth Curve */}
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-rose-400" />
                    {t.floodDepthCurve}
                  </span>
                  <span className="text-[10px] text-rose-400 font-mono">Hydrograph</span>
                </div>
                <div className="h-32 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={pred?.hourly_forecast || []} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="time_label" stroke="#64748b" fontSize={9} interval={3} />
                      <YAxis stroke="#64748b" fontSize={9} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                        formatter={(val) => [`${val} cm`, 'Water Depth']}
                      />
                      <ReferenceLine y={50} stroke="#ef4444" strokeDasharray="3 3" label={{ value: t.dangerThreshold, fill: '#ef4444', fontSize: 9 }} />
                      <Line type="monotone" dataKey="inundation_depth_cm" stroke="#f43f5e" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Explainable AI (XAI) Feature Attribution */}
          {activeTab === 'xai' && (
            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                  <Sliders className="w-4 h-4 text-cyan-400" />
                  {t.topDriversTitle}
                </span>
                <span className="text-[10px] text-cyan-400 font-medium">Hydrological Attribution</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Machine learning model attribution highlights which geophysical and meteorological signals contribute most to the predicted flood risk:
              </p>

              <div className="space-y-2.5">
                {pred?.explainability_factors?.map((factor, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-300 font-medium">{factor.label}</span>
                      <span className="text-cyan-400 font-bold font-mono">+{factor.contribution_pct}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-cyan-500 to-blue-600 h-full rounded-full transition-all duration-500"
                        style={{ width: `${factor.contribution_pct}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
                <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                <span>
                  Physical drivers are evaluated against the digital elevation model (DEM slope: {ward?.terrain_slope_deg}°), built-up surface ({ward?.impervious_surface_pct}%), and active CWC river gauges.
                </span>
              </div>
            </div>
          )}

          {/* Vulnerable Infrastructure in Ward */}
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <h3 className="text-xs font-bold text-slate-300 mb-2 flex items-center gap-1.5">
              <Building className="w-3.5 h-3.5 text-amber-400" />
              Critical Assets at Risk ({ward?.vulnerable_assets?.length || 0})
            </h3>
            <div className="space-y-1.5">
              {ward?.vulnerable_assets?.map((asset, idx) => (
                <div key={idx} className="flex items-center justify-between bg-slate-900/80 px-2.5 py-1.5 rounded-lg border border-slate-800/80 text-xs">
                  <div className="flex items-center gap-2">
                    <span>{asset.type === 'hospital' ? '🏥' : (asset.type === 'transit' ? '🚇' : '🏘️')}</span>
                    <span className="text-slate-200 font-medium">{asset.name}</span>
                  </div>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                    asset.vulnerability === 'Severe' || asset.vulnerability === 'Critical'
                      ? 'bg-red-500/20 text-red-400'
                      : 'bg-amber-500/20 text-amber-400'
                  }`}>
                    {asset.vulnerability}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Nearest Emergency Shelter & Evacuation */}
          {ward?.nearest_shelter ? (
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-2">
              <h3 className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                <Navigation className="w-3.5 h-3.5 text-emerald-400" />
                {t.designatedShelter}
              </h3>
              <div className="bg-emerald-950/40 border border-emerald-800/50 p-2.5 rounded-lg">
                <div className="flex items-center justify-between">
                  <strong className="text-xs text-emerald-300 font-bold">
                    {ward?.nearest_shelter?.name}
                  </strong>
                  <span className="text-[10px] bg-emerald-800/80 text-emerald-200 px-1.5 py-0.5 rounded font-mono">
                    {t.capacity}: {ward?.nearest_shelter?.capacity}
                  </span>
                </div>
                <p className="text-[11px] text-emerald-400/90 mt-1">
                  Occupancy: {ward?.nearest_shelter?.occupied} / {ward?.nearest_shelter?.capacity} beds occupied (Open for public admission)
                </p>
              </div>

              {/* Live GPS Evacuation Navigation Button */}
              <button
                type="button"
                onClick={() => {
                  if (onStartNavigation) onStartNavigation();
                }}
                className="w-full py-2.5 bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 active:scale-98 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-teal-950/60 transition-all cursor-pointer border border-teal-400/30"
              >
                <Navigation className="w-4 h-4 text-cyan-200 animate-pulse shrink-0" />
                <span>{isNavigating ? t.gpsNavActive : t.startGpsNav}</span>
              </button>
              
              <a
                href="tel:1916"
                className="w-full py-2 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded-lg flex items-center justify-center gap-2 transition-colors shadow-lg"
              >
                <PhoneCall className="w-3.5 h-3.5" />
                Dial Disaster Control Room (1916 / 112)
              </a>
            </div>
          ) : (
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center gap-2 text-emerald-400">
                <ShieldCheck className="w-4 h-4" />
                <span className="text-xs font-bold">Safe Operations Zone</span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                {forecastData?.evacuation_advice?.advisory_notes || "Normal municipal operations active. No emergency flood evacuation required."}
              </p>
              <a
                href="tel:112"
                className="w-full py-2 bg-slate-850 hover:bg-slate-800 text-slate-300 text-xs font-bold rounded-lg flex items-center justify-center gap-2 transition-colors border border-slate-700/80"
              >
                <PhoneCall className="w-3.5 h-3.5" />
                National Emergency Helpline (112)
              </a>
            </div>
          )}
        </div>
      )}
    </aside>
  );
}
