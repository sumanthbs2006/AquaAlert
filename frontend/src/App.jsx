import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import MapView from './components/MapView';
import AreaDetailDrawer from './components/AreaDetailDrawer';
import AlertsPage from './pages/AlertsPage';
import AdminControlRoom from './pages/AdminControlRoom';
import AboutPage from './pages/AboutPage';
import LoginPage from './pages/LoginPage';
import { getTranslation } from './i18n';

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('aquaalert_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [currentPage, setCurrentPage] = useState(() => {
    try {
      const saved = localStorage.getItem('aquaalert_user');
      return saved ? 'dashboard' : 'login';
    } catch {
      return 'login';
    }
  });

  const [userRole, setUserRole] = useState(() => {
    try {
      const saved = localStorage.getItem('aquaalert_user');
      const u = saved ? JSON.parse(saved) : null;
      return u?.role || 'citizen';
    } catch {
      return 'citizen';
    }
  });
  const [currentLang, setCurrentLang] = useState('en'); // 'en', 'hi', 'kn'
  const t = getTranslation(currentLang);
  
  const [scenarios, setScenarios] = useState([]);
  const [activeScenario, setActiveScenario] = useState(null);
  const [riskZones, setRiskZones] = useState(null);
  const [sensors, setSensors] = useState(null);
  const [sensorsSummary, setSensorsSummary] = useState(null);
  const [selectedWardId, setSelectedWardId] = useState(null);
  const [isNavigating, setIsNavigating] = useState(false);
  const [currentRegion, setCurrentRegion] = useState({
    lat: 19.076,
    lon: 72.877,
    name: 'Mumbai Metropolitan Basin',
    isRegional: false
  });
  const [loading, setLoading] = useState(true);

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

  // Initial Load: Scenarios, Risk Zones, Sensors
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [scenariosRes, rzRes, sensorsRes, summaryRes] = await Promise.all([
        fetch('/api/scenarios').then(r => r.json()),
        fetch('/api/risk-zones').then(r => r.json()),
        fetch('/api/sensors').then(r => r.json()),
        fetch('/api/sensors/summary').then(r => r.json())
      ]);

      setScenarios(scenariosRes.scenarios || []);
      const currentSc = scenariosRes.scenarios?.find(s => s.is_active) || scenariosRes.scenarios?.[0];
      setActiveScenario(currentSc);
      setRiskZones(rzRes);
      setSensors(sensorsRes);
      setSensorsSummary(summaryRes);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load telemetry:', err);
      setLoading(false);
    }
  };

  // Handle User Search or Geolocation Anywhere
  const handleLocationChange = async ({ lat, lon, name }) => {
    try {
      const isRegional = Math.hypot(lat - 19.076, lon - 72.877) > 0.22;
      setCurrentRegion({ lat, lon, name, isRegional });
      const query = isRegional ? `?lat=${lat}&lon=${lon}&name=${encodeURIComponent(name || 'Searched Area')}` : '';
      const [rzRes, sensorsRes] = await Promise.all([
        fetch(`/api/risk-zones${query}`).then(r => r.json()),
        fetch(`/api/sensors${query}`).then(r => r.json())
      ]);
      setRiskZones(rzRes);
      setSensors(sensorsRes);
    } catch (e) {
      console.error('Failed to load regional telemetry:', e);
    }
  };

  // Navigate directly from Alert Card to GIS Dashboard at Alert Coordinates
  const handleNavigateToAlertLocation = (alert) => {
    setCurrentPage('dashboard');
    if (alert?.lat && alert?.lon) {
      const targetName = alert.area_desc || `${alert.state} Alert Zone`;
      handleLocationChange({
        lat: alert.lat,
        lon: alert.lon,
        name: targetName
      });
      const alertWardId = `loc_${alert.lat}_${alert.lon}_${encodeURIComponent(targetName)}`;
      setSelectedWardId(alertWardId);
    }
  };

  // Scenario Selection Handler
  const handleSelectScenario = async (scenarioId) => {
    try {
      const res = await fetch('/api/scenarios/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: scenarioId })
      }).then(r => r.json());

      if (res.status === 'success') {
        setActiveScenario(res.scenario);
        // Refresh risk zones & sensor telemetry for current region
        const query = currentRegion.isRegional ? `?lat=${currentRegion.lat}&lon=${currentRegion.lon}&name=${encodeURIComponent(currentRegion.name)}` : '';
        const [rzRes, sensorsRes, summaryRes] = await Promise.all([
          fetch(`/api/risk-zones${query}`).then(r => r.json()),
          fetch(`/api/sensors${query}`).then(r => r.json()),
          fetch('/api/sensors/summary').then(r => r.json())
        ]);
        setRiskZones(rzRes);
        setSensors(sensorsRes);
        setSensorsSummary(summaryRes);
      }
    } catch (err) {
      console.error('Failed to switch scenario:', err);
    }
  };

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    if (user?.role) setUserRole(user.role);
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('aquaalert_user');
    localStorage.removeItem('aquaalert_token');
    setCurrentUser(null);
    setCurrentPage('login');
  };

  if (currentPage === 'login') {
    return (
      <LoginPage 
        onLoginSuccess={handleLoginSuccess}
        currentLang={currentLang}
      />
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
      {/* Navigation & Header */}
      <Navbar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        userRole={userRole}
        setUserRole={setUserRole}
        currentLang={currentLang}
        setCurrentLang={setCurrentLang}
        activeScenario={activeScenario}
        onSelectScenario={handleSelectScenario}
        scenarios={scenarios}
        sensorsSummary={sensorsSummary}
        currentUser={currentUser}
        onLogout={handleLogout}
        onOpenLogin={() => setCurrentPage('login')}
      />

      {/* Main Content Area */}
      <main className="flex-1 relative overflow-hidden">
        {currentPage === 'dashboard' && (
          <div className="relative w-full h-full">
            <MapView
              riskZones={riskZones}
              sensors={sensors}
              selectedWardId={selectedWardId}
              onSelectWard={(wardId) => setSelectedWardId(wardId)}
              activeScenario={activeScenario}
              currentRegion={currentRegion}
              onLocationChange={handleLocationChange}
              currentLang={currentLang}
              isNavigating={isNavigating}
              setIsNavigating={setIsNavigating}
            />
            {selectedWardId && (
              <AreaDetailDrawer
                wardId={selectedWardId}
                onClose={() => {
                  setSelectedWardId(null);
                  setIsNavigating(false);
                }}
                activeScenario={activeScenario}
                activeScenarioName={getScenarioName(activeScenario)}
                currentLang={currentLang}
                isNavigating={isNavigating}
                onStartNavigation={() => setIsNavigating(true)}
              />
            )}
          </div>
        )}

        {currentPage === 'alerts' && (
          <AlertsPage
            currentLang={currentLang}
            setCurrentLang={setCurrentLang}
            onNavigateToLocation={handleNavigateToAlertLocation}
          />
        )}

        {currentPage === 'admin' && (
          <AdminControlRoom
            activeScenario={activeScenario}
            sensorsSummary={sensorsSummary}
            currentLang={currentLang}
          />
        )}

        {currentPage === 'about' && (
          <AboutPage currentLang={currentLang} />
        )}
      </main>

      {/* Bottom Ticker & Quick Status */}
      <footer className="bg-slate-950 border-t border-slate-800/80 px-4 py-2 text-[11px] text-slate-400 flex flex-wrap items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-slate-300">
            AquaAlert AI &copy; 2026 | SIH26071
          </span>
          <span className="text-slate-600">|</span>
          <span>
            {t.pilotCatchment}
          </span>
          <span className="text-slate-600">|</span>
          <span className="text-emerald-400 font-medium">
            {t.capFeedOnline}
          </span>
        </div>

        <div className="flex items-center gap-3 text-slate-500">
          <span>{t.decisionSupport}</span>
        </div>
      </footer>
    </div>
  );
}
