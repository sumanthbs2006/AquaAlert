import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar';
import MapView from './components/MapView';
import AreaDetailDrawer from './components/AreaDetailDrawer';
import SmsNotificationToast from './components/SmsNotificationToast';
import SmsInboxModal from './components/SmsInboxModal';
import AlertsPage from './pages/AlertsPage';
import AdminControlRoom from './pages/AdminControlRoom';
import AboutPage from './pages/AboutPage';
import LoginPage from './pages/LoginPage';
import { getTranslation } from './i18n';

// Web Audio API Emergency Alert Chime
const playEmergencySmsChime = () => {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    if (ctx.state === 'suspended') {
      ctx.resume();
    }
    const now = ctx.currentTime;
    
    // First Alert Beep (F5 - 698Hz)
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(698.46, now);
    gain1.gain.setValueAtTime(0.2, now);
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
    osc1.connect(gain1);
    gain1.connect(ctx.destination);
    osc1.start(now);
    osc1.stop(now + 0.22);

    // Second Higher Alert Beep (A5 - 880Hz)
    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.type = 'sine';
    osc2.frequency.setValueAtTime(880.00, now + 0.16);
    gain2.gain.setValueAtTime(0.25, now + 0.16);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
    osc2.connect(gain2);
    gain2.connect(ctx.destination);
    osc2.start(now + 0.16);
    osc2.stop(now + 0.5);
  } catch (e) {
    console.warn('Audio chime blocked or unsupported:', e);
  }
};

const getScenarioSmsMessage = (scenarioId, areaName, lang = 'en', rain = 75.0) => {
  const l = (lang || 'en').toLowerCase();
  const area = areaName || 'Local Monitored Area';

  if (scenarioId === 'cloudburst') {
    if (l === 'hi') {
      return `🚨 [एक्वाअलर्ट लाल चेतावनी] ${area} में भारी बादल फटना (${rain.toFixed(1)} मिमी/घंटा) व भीषण बाढ़ की स्थिति! नदियां खतरे के निशान से ऊपर। तुरंत सुरक्षित ऊंचे स्थान पर जाएं। NDRF QRT तैनात। आपातकालीन: 112 / 1070।`;
    }
    if (l === 'kn') {
      return `🚨 [AquaAlert ರೆಡ್ ಅಲರ್ಟ್] ${area} ಪ್ರದೇಶದಲ್ಲಿ ಮೇಘಸ್ಫೋಟ (${rain.toFixed(1)} mm/h) ಮತ್ತು ಪ್ರವಾಹ! ತಕ್ಷಣ ಎತ್ತರದ ಪ್ರದೇಶಗಳಿಗೆ ತೆರಳಿ. NDRF ರಕ್ಷಣಾ ಪಡೆ ಸನ್ನದ್ಧವಾಗಿದೆ. ತುರ್ತು ಸಹಾಯ: 112 / 1070.`;
    }
    return `🚨 [AquaAlert RED FLOOD ALERT] Severe Cloudburst (${rain.toFixed(1)} mm/h) active over ${area}! Critical river surcharge & street inundation (40–70cm). Relocate to higher ground immediately. NDRF Quick Response Team deployed. Emergency: 112 / 1070.`;
  }

  if (scenarioId === 'cyclone_surge' || scenarioId === 'cyclone') {
    if (l === 'hi') {
      return `🚨 [एक्वाअलर्ट चक्रवाती चेतावनी] ${area} में भारी चक्रवाती बारिश (${rain.toFixed(1)} मिमी/घंटा) और 4.8 मीटर समुद्री ज्वार! तटीय सड़कों व सबवे से दूर रहें। DEOC आपातकालीन: 112 / 1916।`;
    }
    if (l === 'kn') {
      return `🚨 [AquaAlert ಚಂಡಮಾರುತ ಎಚ್ಚರಿಕೆ] ${area} ಕರಾವಳಿಯಲ್ಲಿ ಭಾರಿ ಮಳೆ (${rain.toFixed(1)} mm/h) ಮತ್ತು 4.8m ಉಬ್ಬರವಿಳಿತದ ಅಲೆಗಳು! ಕರಾವಳಿ ಮಾರ್ಗಗಳನ್ನು ತಪ್ಪಿಸಿ. DEOC ತುರ್ತು: 112 / 1916.`;
    }
    return `🚨 [AquaAlert CYCLONIC SURGE WARNING] Heavy outer rainbands (${rain.toFixed(1)} mm/h) & 4.8m tidal storm surge in ${area}! Sea outfalls locked. Avoid coastal corridors and subways. DEOC Emergency: 112 / 1916.`;
  }

  if (scenarioId === 'normal_monsoon' || scenarioId === 'normal') {
    if (l === 'hi') {
      return `⚠️ [एक्वाअलर्ट मानसूनी सूचना] ${area} में सामान्य मध्यम मानसूनी बारिश (${rain.toFixed(1)} मिमी/घंटा)। नगर निगम पंप सक्रिय हैं। निचले जलभराव वाले रास्तों पर सावधानी बरतें। हेल्पलाइन: 1916 / 112।`;
    }
    if (l === 'kn') {
      return `⚠️ [AquaAlert ಮುಂಗಾರು ಮಾಹಿತಿ] ${area} ಪ್ರದೇಶದಲ್ಲಿ ಸಾಧಾರಣ ಮುಂಗಾರು ಮಳೆ (${rain.toFixed(1)} mm/h). ನೀರು ಹೊರಹಾಕುವ ಪಂಪ್‌ಗಳು ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತಿವೆ. ತಗ್ಗು ಪ್ರದೇಶಗಳಲ್ಲಿ ಜಾಗರೂಕರಾಗಿರಿ. ಸಹಾಯವಾಣಿ: 1916 / 112.`;
    }
    return `⚠️ [AquaAlert MONSOON ADVISORY] Moderate steady monsoon rain (${rain.toFixed(1)} mm/h) recorded in ${area}. Municipal suction pumps deployed. Proceed with caution near railway dips and lowlands. Helpline: 1916 / 112.`;
  }

  if (l === 'hi') {
    return `⚠️ [एक्वाअलर्ट लाइव मौसम सूचना] लाइव मौसम रडार ने ${area} में ${rain.toFixed(1)} मिमी/घंटा बारिश दर्ज की है। जल निकासी निगरानी जारी। हेल्पलाइन: 112 / 1916।`;
  }
  if (l === 'kn') {
    return `⚠️ [AquaAlert ಲೈವ್ ಹವಾಮಾನ ಮಾಹಿತಿ] ಲೈವ್ ರಾಡಾರ್ ${area} ಪ್ರದೇಶದಲ್ಲಿ ${rain.toFixed(1)} mm/h ಮಳೆಯನ್ನು ದಾಖಲಿಸಿದೆ. ನಿಗಾ ಇರಿಸಲಾಗಿದೆ. ಸಹಾಯವಾಣಿ: 112 / 1916.`;
  }
  return `⚠️ [AquaAlert LIVE WEATHER ALERT] Live atmospheric telemetry detects ${rain.toFixed(1)} mm/h rainfall in ${area}. Drainage and river monitoring active. Helpline: 112 / 1916.`;
};

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('aquaalert_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  // Always show login page first whenever the website is opened
  const [currentPage, setCurrentPage] = useState('login');

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
  const [activeAlerts, setActiveAlerts] = useState([]);
  const [selectedWardId, setSelectedWardId] = useState(null);
  const [isNavigating, setIsNavigating] = useState(false);
  const [currentRegion, setCurrentRegion] = useState({
    lat: 19.076,
    lon: 72.877,
    name: 'Mumbai Metropolitan Basin',
    isRegional: false
  });
  const [loading, setLoading] = useState(true);
  const [latestSmsToast, setLatestSmsToast] = useState(null);
  const [smsInboxOpen, setSmsInboxOpen] = useState(false);
  const [smsHistory, setSmsHistory] = useState([]);
  const dispatchedHazardKeys = useRef(new Set());

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

  // Initial Load: Scenarios, Risk Zones, Sensors, Active Alerts
  useEffect(() => {
    loadInitialData();
  }, [currentLang]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [scenariosRes, rzRes, sensorsRes, summaryRes, alertsRes] = await Promise.all([
        fetch('/api/scenarios').then(r => r.json()).catch(() => ({ scenarios: [] })),
        fetch('/api/risk-zones').then(r => r.json()).catch(() => ({})),
        fetch('/api/sensors').then(r => r.json()).catch(() => ({})),
        fetch('/api/sensors/summary').then(r => r.json()).catch(() => ({})),
        fetch(`/api/alerts?lang=${currentLang}`).then(r => r.json()).catch(() => ({ alerts: [] }))
      ]);

      setScenarios(scenariosRes.scenarios || []);
      const currentSc = scenariosRes.scenarios?.find(s => s.is_active) || scenariosRes.scenarios?.[0];
      setActiveScenario(currentSc);
      setRiskZones(rzRes);
      setSensors(sensorsRes);
      setSensorsSummary(summaryRes);
      if (Array.isArray(alertsRes?.alerts)) {
        setActiveAlerts(alertsRes.alerts);
      }
      setLoading(false);
    } catch (err) {
      console.error('Failed to load telemetry:', err);
      setLoading(false);
    }
  };

  // Handle User Search or Geolocation Anywhere
  const handleLocationChange = async ({ lat, lon, name, isUserAction = false, source = 'unknown' }) => {
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

      // Trigger automatic SMS alert whenever user explicitly gives location (Search, GPS, or Basin)
      // corresponding to the active meteorological scenario (Cloudburst, Cyclone Surge, Normal Monsoon, or Live Weather)
      if (isUserAction) {
        const regPhone = localStorage.getItem('aquaalert_registered_phone');
        const targetPhone = currentUser?.phone || currentUser?.clean_phone || regPhone || '+91 98765 43210';
        const scId = activeScenario?.id || 'live_weather';
        const locName = name || 'Your Monitored Location';
        const locDedupeKey = `${targetPhone}_${scId}_${locName}`;

        if (!dispatchedHazardKeys.current.has(locDedupeKey)) {
          dispatchedHazardKeys.current.add(locDedupeKey);

          if (scId === 'cloudburst') {
            const customMsg = getScenarioSmsMessage('cloudburst', locName, currentLang, 85.0);
            await handleTriggerSmsForAlert(null, {
              phone: targetPhone,
              area_name: locName,
              hazard_type: 'Monsoon Cloudburst & Flash Flood Surge Emergency',
              rainfall_mm_hr: 85.0,
              severity: 'Severe',
              river_stage: 'DANGER',
              lat,
              lon,
              custom_message: customMsg
            });
          } else if (scId === 'cyclone_surge' || scId === 'cyclone') {
            const customMsg = getScenarioSmsMessage('cyclone_surge', locName, currentLang, 55.0);
            await handleTriggerSmsForAlert(null, {
              phone: targetPhone,
              area_name: locName,
              hazard_type: 'Cyclonic Rain-Band & Tidal Backwater Surge Advisory',
              rainfall_mm_hr: 55.0,
              severity: 'Severe',
              river_stage: 'DANGER',
              lat,
              lon,
              custom_message: customMsg
            });
          } else if (scId === 'normal_monsoon' || scId === 'normal') {
            const customMsg = getScenarioSmsMessage('normal_monsoon', locName, currentLang, 28.0);
            await handleTriggerSmsForAlert(null, {
              phone: targetPhone,
              area_name: locName,
              hazard_type: 'Steady Seasonal Monsoon Downpour Advisory',
              rainfall_mm_hr: 28.0,
              severity: 'Moderate',
              river_stage: 'WARNING',
              lat,
              lon,
              custom_message: customMsg
            });
          } else if (scId === 'live_weather') {
            await checkAndDispatchProximitySms(lat, lon, locName, source);
          }
          // If dry_baseline: dry weather / safe conditions, so no flood warning SMS is dispatched
        }
      }
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

  // Central Dispatcher: Sends emergency SMS alert output to user's registered phone number
  const handleTriggerSmsForAlert = async (alert, customDetails = {}) => {
    const regPhone = localStorage.getItem('aquaalert_registered_phone');
    const targetPhone = currentUser?.phone || currentUser?.clean_phone || regPhone || customDetails.phone || '+91 98765 43210';
    if (!targetPhone) return;

    const areaName = customDetails.area_name || alert?.area_desc || currentRegion?.name || 'Monitored Basin';
    const hazardType = customDetails.hazard_type || alert?.headline || 'High Flood Inundation & Heavy Rainfall Warning';
    const severity = customDetails.severity || alert?.severity || 'Severe';
    const rainfall = customDetails.rainfall_mm_hr || (severity === 'Severe' ? 75.0 : (severity === 'Moderate' ? 28.0 : 45.0));
    const cleanPhone = currentUser?.clean_phone || (regPhone ? regPhone.replace(/\D/g, '') : targetPhone.replace(/\D/g, ''));

    // 1. Play immediate emergency sound chime
    playEmergencySmsChime();

    // 2. Build immediate visible output for registered handset
    const localSmsId = `SMS-CIT-${Date.now()}`;
    const shortAuth = 'NDRF 5th Battalion & Local DEOC';
    const localizedText = customDetails.custom_message || alert?.sms_preview || 
      `🚨 [AquaAlert URGENT FLOOD WARNING] Heavy rainfall (${rainfall.toFixed(1)} mm/h) & flood risk (${severity}) in ${areaName}! River/Drainage: DANGER. Move to higher ground immediately. Alert also transmitted to nearby rescue team: ${shortAuth}. Emergency Helpline: 112 / 1070.`;

    const citizenSms = {
      id: localSmsId,
      recipient_phone: targetPhone,
      clean_phone: cleanPhone,
      area_name: areaName,
      hazard_type: hazardType,
      rainfall_mm_hr: rainfall,
      severity: severity,
      river_stage: customDetails.river_stage || (severity === 'Severe' ? 'DANGER' : 'WARNING'),
      message: localizedText,
      delivery_status: 'DELIVERED_TO_HANDSET',
      carrier_gateway: 'INFOBIP GLOBAL SMSC (TRAI-DND-BYPASS)',
      rescue_authority_alerted: shortAuth,
      formatted_time: 'Just now'
    };

    setLatestSmsToast(citizenSms);
    setSmsHistory(prev => [citizenSms, ...prev.filter(p => p.id !== localSmsId)]);

    // 3. Dispatch to backend API
    try {
      const res = await fetch('/api/alerts/dispatch-sms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: targetPhone,
          area_name: areaName,
          hazard_type: hazardType,
          rainfall_mm_hr: rainfall,
          severity: severity,
          alert_id: alert?.id,
          lat: alert?.lat || currentRegion?.lat,
          lon: alert?.lon || currentRegion?.lon,
          lang: currentLang,
          override_text: customDetails.custom_message || localizedText,
          is_force_test: true
        })
      });
      const data = await res.json();
      if (data?.status === 'success' && data.sms) {
        setLatestSmsToast(data.sms);
        const entries = data.authority_sms ? [data.sms, data.authority_sms] : [data.sms];
        setSmsHistory(prev => {
          const existingIds = new Set(prev.map(p => p.id));
          const fresh = entries.filter(e => !existingIds.has(e.id));
          return [...fresh, ...prev.filter(p => p.id !== localSmsId)];
        });
      }
    } catch (err) {
      console.warn('Backend SMS dispatch notice:', err);
    }
  };

  // Scenario Selection Handler with Live Demo Emergency SMS Broadcast
  const handleSelectScenario = async (scenarioId) => {
    try {
      dispatchedHazardKeys.current.clear();
      const regPhone = localStorage.getItem('aquaalert_registered_phone');
      const targetPhone = currentUser?.phone || currentUser?.clean_phone || regPhone || '+91 98765 43210';
      const targetArea = currentRegion?.name || 'Mumbai Metropolitan Basin';

      const res = await fetch('/api/scenarios/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: scenarioId,
          phone: targetPhone,
          lang: currentLang,
          area_name: targetArea,
          lat: currentRegion?.lat,
          lon: currentRegion?.lon
        })
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

        // DEMO TRIGGER: When scenario has heavy, severe, or moderate rainfall, backend dispatches SMS
        if (res.sms_dispatched && res.sms) {
          playEmergencySmsChime();
          setLatestSmsToast(res.sms);
          const entries = res.authority_sms ? [res.sms, res.authority_sms] : [res.sms];
          setSmsHistory(prev => {
            const existingIds = new Set(prev.map(p => p.id));
            const fresh = entries.filter(e => !existingIds.has(e.id));
            return [...fresh, ...prev];
          });
        }
      }
    } catch (err) {
      console.error('Failed to switch scenario:', err);
    }
  };

  // Fetch past SMS alerts sent to signed-in user's phone number
  useEffect(() => {
    if (!currentUser?.phone) return;
    const cleanPhone = currentUser.clean_phone || currentUser.phone.replace(/\D/g, '');
    fetch(`/api/alerts/sms-history?phone=${encodeURIComponent(cleanPhone)}`)
      .then(r => r.json())
      .then(data => {
        if (data.status === 'success' && Array.isArray(data.history)) {
          setSmsHistory(data.history);
        }
      })
      .catch(err => console.error('Failed to load SMS history:', err));
  }, [currentUser?.phone]);

  // Proximity Alert Dispatcher: ONLY triggered when user provides their location or uses GPS and an alert is nearby
  const checkAndDispatchProximitySms = async (targetLat, targetLon, targetName, actionSource = 'unknown') => {
    if (!currentUser?.phone) return;

    try {
      // 1. Query the backend proximity intelligence endpoint (evaluates active calamities, coordinates, active scenarios)
      const proxRes = await fetch(
        `/api/alerts/check-proximity?phone=${encodeURIComponent(currentUser.phone)}&lat=${targetLat}&lon=${targetLon}&area_name=${encodeURIComponent(targetName || '')}`
      ).then(r => r.json());

      let alertToTrigger = null;
      if (proxRes?.has_alert_nearby && proxRes.alert) {
        alertToTrigger = proxRes.alert;
      } else {
        // Fallback client check: Haversine distance (<= 75km) or matching disaster tokens
        const haversineDistKm = (lat1, lon1, lat2, lon2) => {
          const R = 6371;
          const dLat = (lat2 - lat1) * Math.PI / 180;
          const dLon = (lon2 - lon1) * Math.PI / 180;
          const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
          return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        };
        const normName = (targetName || '').toLowerCase();
        for (const a of activeAlerts) {
          if (a.severity === 'Severe' || a.severity === 'High') {
            if (typeof a.lat === 'number' && typeof a.lon === 'number' && typeof targetLat === 'number') {
              const d = haversineDistKm(targetLat, targetLon, a.lat, a.lon);
              if (d <= 75.0) {
                alertToTrigger = a;
                break;
              }
            }
            const aDesc = (a.area_desc || '').toLowerCase();
            const aState = (a.state || '').toLowerCase();
            const tokens = ['dehradun', 'rishikesh', 'song', 'tapkeshwar', 'patna', 'ganga', 'kankarbagh', 'rajendra nagar', 'kolkata'];
            if (tokens.some(tok => normName.includes(tok) && (aDesc.includes(tok) || aState.includes(tok)))) {
              alertToTrigger = a;
              break;
            }
          }
        }
      }

      // If NO alert near user's location, DO NOT SEND ANY SMS!
      if (!alertToTrigger) {
        console.log(`[AquaAlert Location Check] ${targetName} (${targetLat}, ${targetLon}) has NO active flood alert within 75km. No SMS dispatched.`);
        return;
      }

      // Proximity match found: Dispatch emergency SMS alert to user's registered phone
      const alertId = alertToTrigger.id || alertToTrigger.identifier || 'alert';
      const dedupeKey = `${currentUser.phone}_${alertId}_${targetName}`;
      if (dispatchedHazardKeys.current.has(dedupeKey)) return;
      dispatchedHazardKeys.current.add(dedupeKey);

      await handleTriggerSmsForAlert(alertToTrigger, {
        area_name: targetName || alertToTrigger.area_desc || 'Your Monitored Location',
        hazard_type: alertToTrigger.headline || 'Active Flood Warning',
        rainfall_mm_hr: alertToTrigger.rainfall_mm_hr || (alertToTrigger.severity === 'Severe' ? 75.0 : 50.0),
        severity: alertToTrigger.severity || 'Severe'
      });
    } catch (err) {
      console.warn('Error evaluating proximity SMS:', err);
    }
  };

  // Test button action inside SMS Inbox dialog
  const handleTriggerTestSms = async () => {
    if (!currentUser?.phone) return;
    const areaName = currentRegion?.name || 'Local Basin';
    await handleTriggerSmsForAlert(null, {
      area_name: areaName,
      hazard_type: 'Severe Flash Flood & Cloudburst Alert',
      rainfall_mm_hr: 75.5,
      severity: 'Severe'
    });
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
        onOpenSmsInbox={() => setSmsInboxOpen(true)}
        smsHistoryCount={smsHistory.length}
      />

      {/* Emergency SMS Real-Time Toast Notification */}
      <SmsNotificationToast
        sms={latestSmsToast}
        onDismiss={() => setLatestSmsToast(null)}
        onViewInbox={() => setSmsInboxOpen(true)}
      />

      {/* Emergency SMS Inbox & History Modal */}
      <SmsInboxModal
        isOpen={smsInboxOpen}
        onClose={() => setSmsInboxOpen(false)}
        currentUser={currentUser}
        smsHistory={smsHistory}
        onTriggerTestSms={handleTriggerTestSms}
        currentRegion={currentRegion}
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
                currentUser={currentUser}
              />
            )}
          </div>
        )}

        {currentPage === 'alerts' && (
          <AlertsPage
            currentLang={currentLang}
            setCurrentLang={setCurrentLang}
            onNavigateToLocation={handleNavigateToAlertLocation}
            currentUser={currentUser}
            onTriggerSmsForAlert={handleTriggerSmsForAlert}
            currentRegion={currentRegion}
            smsHistory={smsHistory}
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
