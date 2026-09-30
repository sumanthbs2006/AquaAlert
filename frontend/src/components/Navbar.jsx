import React, { useState } from 'react';
import { 
  ShieldAlert, 
  MapPin, 
  BellRing, 
  PhoneCall, 
  Radio, 
  UserCheck, 
  Menu, 
  X, 
  Globe, 
  Droplets, 
  ChevronDown,
  LogOut,
  LogIn,
  User
} from 'lucide-react';
import { getTranslation } from '../i18n';

export default function Navbar({ 
  currentPage, 
  setCurrentPage, 
  userRole, 
  setUserRole, 
  currentLang, 
  setCurrentLang,
  activeScenario,
  onSelectScenario,
  scenarios = [],
  sensorsSummary,
  currentUser,
  onLogout,
  onOpenLogin
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const t = getTranslation(currentLang);

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'hi', name: 'हिन्दी' },
    { code: 'kn', name: 'ಕನ್ನಡ' }
  ];

  const handleNavClick = (page) => {
    setCurrentPage(page);
    setMobileMenuOpen(false);
  };

  const getScenarioName = (sc) => {
    if (!sc) return '';
    const id = sc.id || '';
    if (id.includes('live')) return t.scenarioLiveWeather;
    if (id === 'cloudburst') return t.scenarioCloudburst;
    if (id === 'cyclone_surge' || id === 'cyclone') return t.scenarioCyclone;
    if (id === 'normal_monsoon' || id === 'normal') return t.scenarioNormal;
    if (id === 'dry_baseline' || id === 'baseline') return t.scenarioBaseline;
    return sc.name || '';
  };

  return (
    <header className="bg-slate-950 border-b border-slate-800 sticky top-0 z-50 shadow-xl safe-top">
      {/* 1. Top Emergency Telemetry Status Bar */}
      <div className="bg-slate-900/90 px-3 sm:px-4 py-1.5 text-[11px] sm:text-xs text-slate-300 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-2 overflow-x-auto no-scrollbar">
          {/* Live Status Indicators */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            <span className="flex items-center gap-1.5 font-bold text-emerald-400">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span>{t.telemetryLive}</span>
            </span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-300">
              {t.basinRain}: <strong className="text-sky-300">{sensorsSummary?.avg_basin_rain_mm_hr ?? 45.0} mm/h</strong>
            </span>
            <span className="hidden sm:inline text-slate-600">|</span>
            <span className="hidden sm:inline text-slate-300">
              {t.riverStage}: <strong className={sensorsSummary?.peak_river_danger_status === 'DANGER' ? 'text-red-400' : 'text-amber-300'}>
                {sensorsSummary?.peak_river_danger_status ?? 'WARNING'}
              </strong>
            </span>
          </div>

          {/* Emergency Helpline Direct Dialer (Compact on Mobile) */}
          <div className="flex items-center gap-2 shrink-0">
            <a 
              href="tel:112"
              className="flex items-center gap-1 bg-red-950/70 hover:bg-red-900/80 border border-red-700/60 px-2 py-0.5 rounded text-[11px] font-bold text-red-200 transition-colors shadow-sm"
              title="Tap to call emergency helpline 112"
            >
              <PhoneCall className="w-3 h-3 text-red-400 animate-pulse" />
              <span>{t.sosHelpline}</span>
            </a>

            {/* Scenario Picker (Desktop Only, in mobile menu for phones) */}
            <div className="hidden md:flex items-center gap-1.5">
              <span className="text-slate-400 text-[10px] flex items-center gap-1">
                <Radio className="w-3 h-3 text-indigo-400" />
                {t.scenario}:
              </span>
              <select
                value={activeScenario?.id || 'cloudburst'}
                onChange={(e) => onSelectScenario(e.target.value)}
                className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded px-2 py-0.5 focus:outline-none focus:border-cyan-500 cursor-pointer font-medium"
              >
                {scenarios.map((sc) => (
                  <option key={sc.id} value={sc.id}>
                    {getScenarioName(sc)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Main Navigation Bar */}
      <div className="max-w-7xl mx-auto px-3 sm:px-4 py-2 flex items-center justify-between gap-2">
        {/* Brand & Emblem */}
        <div 
          onClick={() => handleNavClick('dashboard')}
          className="flex items-center gap-2.5 cursor-pointer group shrink-0"
        >
          <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-700 p-0.5 flex items-center justify-center shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-slate-950 rounded-[7px] flex items-center justify-center">
              <ShieldAlert className="w-5 h-5 sm:w-6 sm:h-6 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-base sm:text-lg text-white tracking-tight">AquaAlert</span>
              <span className="text-[10px] sm:text-xs px-1.5 py-0.2 rounded font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">AI</span>
              <span className="hidden sm:inline text-[9px] uppercase font-semibold text-slate-400 bg-slate-800 px-1 py-0.2 rounded border border-slate-700">SIH26071</span>
            </div>
            <p className="hidden xs:block text-[10px] sm:text-[11px] text-slate-400 tracking-wide font-medium">
              {t.platformSubtitle}
            </p>
          </div>
        </div>

        {/* Desktop Navigation Tabs (Hidden on mobile < 768px) */}
        <nav className="hidden md:flex items-center gap-1">
          <button
            onClick={() => handleNavClick('dashboard')}
            className={`px-3 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-colors flex items-center gap-1.5 ${
              currentPage === 'dashboard'
                ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30'
                : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <MapPin className="w-4 h-4" />
            {t.gisDashboard}
          </button>

          <button
            onClick={() => handleNavClick('alerts')}
            className={`px-3 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-colors flex items-center gap-1.5 ${
              currentPage === 'alerts'
                ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <BellRing className="w-4 h-4" />
            {t.activeAlerts}
            <span className="bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full animate-pulse">
              3
            </span>
          </button>
        </nav>

        {/* Right Tools: Language Picker & Mobile Menu Button */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Language Picker (Desktop) */}
          <div className="hidden sm:block relative">
            <select
              value={currentLang}
              onChange={(e) => setCurrentLang(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-md px-2.5 py-1.5 focus:outline-none focus:border-cyan-500 cursor-pointer font-medium"
            >
              {languages.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.name}
                </option>
              ))}
            </select>
          </div>

          {/* User Auth Status / Action (Desktop) */}
          {currentUser ? (
            <div className="hidden sm:flex items-center gap-1.5 bg-slate-900/90 border border-slate-700 rounded-lg p-1">
              <div className="flex items-center gap-1.5 px-2 py-0.5 text-xs">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span className="font-semibold text-[11px] text-cyan-300">
                  {currentUser.phone || currentUser.name}
                </span>
              </div>
              <button
                onClick={onLogout}
                title="Log out"
                className="px-2 py-1 rounded bg-slate-800 hover:bg-red-950/80 hover:text-red-300 text-slate-400 text-[11px] font-semibold flex items-center gap-1 transition-colors cursor-pointer"
              >
                <LogOut className="w-3 h-3 text-red-400" />
                <span className="hidden lg:inline">Logout</span>
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenLogin}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-600/30 transition-all cursor-pointer"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Login</span>
            </button>
          )}

          {/* Mobile Hamburger Menu Button (Visible on mobile < 768px) */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5 text-cyan-400" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* 3. Mobile Slide-Down Menu Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-slate-900/98 backdrop-blur-xl border-b border-slate-800 p-4 space-y-3 shadow-2xl animate-in slide-in-from-top-2">
          {/* Mobile Navigation Links */}
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => handleNavClick('dashboard')}
              className={`p-2.5 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                currentPage === 'dashboard'
                  ? 'bg-cyan-600 text-white'
                  : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800'
              }`}
            >
              <MapPin className="w-4 h-4" />
              {t.gisDashboard}
            </button>

            <button
              onClick={() => handleNavClick('alerts')}
              className={`p-2.5 rounded-xl text-xs font-semibold flex items-center justify-between transition-all ${
                currentPage === 'alerts'
                  ? 'bg-amber-600 text-white'
                  : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800'
              }`}
            >
              <div className="flex items-center gap-2">
                <BellRing className="w-4 h-4" />
                <span>{t.activeAlerts}</span>
              </div>
              <span className="bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full">
                3
              </span>
            </button>
          </div>

          {/* Scenario & Language Pickers for Mobile */}
          <div className="pt-2 border-t border-slate-800/80 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Globe className="w-3.5 h-3.5 text-cyan-400" />
                {t.language}:
              </span>
              <select
                value={currentLang}
                onChange={(e) => setCurrentLang(e.target.value)}
                className="bg-slate-800 border border-slate-700 text-white rounded-lg px-2.5 py-1 focus:outline-none"
              >
                {languages.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Radio className="w-3.5 h-3.5 text-indigo-400" />
                {t.scenario}:
              </span>
              <select
                value={activeScenario?.id || 'cloudburst'}
                onChange={(e) => onSelectScenario(e.target.value)}
                className="bg-slate-800 border border-slate-700 text-white rounded-lg px-2.5 py-1 focus:outline-none max-w-[180px] truncate"
              >
                {scenarios.map((sc) => (
                  <option key={sc.id} value={sc.id}>
                    {getScenarioName(sc)}
                  </option>
                ))}
              </select>
            </div>

            {/* Direct Emergency Helpline Call Buttons */}
            <div className="pt-2 flex items-center justify-between gap-2">
              <span className="text-slate-400 text-[11px]">{t.emergencyCalls}:</span>
              <div className="flex gap-1.5">
                <a href="tel:112" className="px-2 py-1 bg-red-900/60 border border-red-700 text-red-200 rounded font-bold text-xs">
                  📞 112
                </a>
                <a href="tel:1070" className="px-2 py-1 bg-amber-900/60 border border-amber-700 text-amber-200 rounded font-bold text-xs">
                  📞 1070
                </a>
                <a href="tel:1916" className="px-2 py-1 bg-blue-900/60 border border-blue-700 text-blue-200 rounded font-bold text-xs">
                  📞 1916
                </a>
              </div>
            </div>

            {/* User Profile / Auth Status (Mobile) */}
            <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
              {currentUser ? (
                <>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span className="text-xs font-bold text-cyan-300">
                      {currentUser.phone || currentUser.name}
                    </span>
                  </div>
                  <button
                    onClick={() => {
                      setMobileMenuOpen(false);
                      onLogout();
                    }}
                    className="px-2.5 py-1 bg-red-950/80 border border-red-700/80 hover:bg-red-900 text-red-200 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-colors"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Logout</span>
                  </button>
                </>
              ) : (
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onOpenLogin();
                  }}
                  className="w-full py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg text-xs font-bold flex items-center justify-center gap-2 shadow-md transition-all"
                >
                  <LogIn className="w-4 h-4" />
                  <span>Citizen Login with Mobile</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
