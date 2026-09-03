import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { 
  Search, 
  Crosshair, 
  Layers, 
  Clock, 
  ShieldAlert, 
  CloudRain, 
  RotateCcw,
  Navigation,
  Wind,
  Thermometer,
  Play,
  Pause,
  SlidersHorizontal,
  ChevronRight,
  Sun,
  Moon,
  Compass,
  Map as MapIcon,
  Sparkles
} from 'lucide-react';
import { getTranslation } from '../i18n';

const CARTO_KEY = import.meta.env.VITE_CARTO_API_KEY || '';

const BASEMAP_TILES = {
  dark_matter: {
    name: 'CARTO Dark Matter',
    url: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?key=${CARTO_KEY}`,
    subdomains: 'abcd',
    attribution: '&copy; CARTO &copy; OpenStreetMap'
  },
  voyager: {
    name: 'CARTO Voyager (Streets & Water)',
    url: `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=${CARTO_KEY}`,
    subdomains: 'abcd',
    attribution: '&copy; CARTO &copy; OpenStreetMap'
  },
  positron: {
    name: 'CARTO Positron (High-Contrast)',
    url: `https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=${CARTO_KEY}`,
    subdomains: 'abcd',
    attribution: '&copy; CARTO &copy; OpenStreetMap'
  },
  satellite: {
    name: 'Satellite Hybrid Terrain',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    subdomains: 'abc',
    attribution: 'Tiles &copy; Esri, Maxar'
  }
};

export default function MapView({ 
  riskZones, 
  sensors, 
  selectedWardId, 
  onSelectWard,
  currentLang = 'en'
}) {
  const t = getTranslation(currentLang);
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layersRef = useRef({
    tileLayer: null,
    polygons: null,
    radar: null,
    radarSweep: null,
    gauges: null,
    aws: null,
    assets: null,
    evacuation: null,
    userGps: null
  });

  // Basemap & Viewport State
  const [selectedBasemap, setSelectedBasemap] = useState('dark_matter');
  const [showBasemapMenu, setShowBasemapMenu] = useState(false);
  const [timeHorizon, setTimeHorizon] = useState('6-24h');
  
  // Search & Geolocation State
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isLocating, setIsLocating] = useState(false);

  // Layers Visibility
  const [layerVisibility, setLayerVisibility] = useState({
    floodZones: true,
    weatherRadar: true,
    riverGauges: true,
    awsStations: true,
    vulnerableAssets: true,
    evacuationCorridors: true
  });
  const [showLayerMenu, setShowLayerMenu] = useState(false);

  // Dynamic Surge Simulator (+0mm to +100mm)
  const [surgeDelta, setSurgeDelta] = useState(0);
  const [showSurgeSimulator, setShowSurgeSimulator] = useState(false);
  const [mobileLegendOpen, setMobileLegendOpen] = useState(false);

  // Radar Animation State
  const [radarPlaying, setRadarPlaying] = useState(true);
  const [radarSweepAngle, setRadarSweepAngle] = useState(45);

  // Live Open-Meteo Weather
  const [liveMet, setLiveMet] = useState(null);
  const [activeEvacuationInfo, setActiveEvacuationInfo] = useState(null);

  // 1. Initialize Leaflet Map with CARTO Basemap
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [19.065, 72.875],
      zoom: 13,
      zoomControl: false,
      attributionControl: false
    });

    const baseConfig = BASEMAP_TILES[selectedBasemap];
    const initialTileLayer = L.tileLayer(baseConfig.url, {
      maxZoom: 20,
      subdomains: baseConfig.subdomains,
      attribution: baseConfig.attribution
    }).addTo(map);

    layersRef.current.tileLayer = initialTileLayer;

    // Zoom controls bottom-right
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Allow clicking anywhere on the map to inspect hyperlocal flood risk & hydrograph
    map.on('click', (e) => {
      const lat = parseFloat(e.latlng.lat.toFixed(4));
      const lon = parseFloat(e.latlng.lng.toFixed(4));
      const locId = `loc_${lat}_${lon}_Inspection Point (${lat}, ${lon})`;
      onSelectWard(locId);
    });

    mapInstanceRef.current = map;

    // Fetch live atmospheric conditions
    fetch('/api/carto/live-weather')
      .then(r => r.json())
      .then(data => setLiveMet(data))
      .catch(console.error);

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 2. Basemap Switcher Effect
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    const baseConfig = BASEMAP_TILES[selectedBasemap];
    if (layersRef.current.tileLayer) {
      map.removeLayer(layersRef.current.tileLayer);
    }

    const newTileLayer = L.tileLayer(baseConfig.url, {
      maxZoom: 20,
      subdomains: baseConfig.subdomains,
      attribution: baseConfig.attribution
    }).addTo(map);

    layersRef.current.tileLayer = newTileLayer;

    // Ensure GeoJSON & other overlays stay on top of the new tile layer
    if (layersRef.current.polygons) layersRef.current.polygons.bringToFront();
  }, [selectedBasemap]);

  // 3. Render & Update GeoJSON Flood Risk Choropleth Wards (With Dynamic Surge Delta)
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !riskZones?.features) return;

    if (layersRef.current.polygons) {
      map.removeLayer(layersRef.current.polygons);
    }

    if (!layerVisibility.floodZones) return;

    const geoJsonLayer = L.geoJSON(riskZones, {
      style: (feature) => {
        const props = feature.properties;
        const isSelected = selectedWardId === props.ward_id;

        // Dynamic depth & risk calibration based on surge simulator
        const dynamicDepth = Math.round(props.predicted_depth_cm + (surgeDelta * 0.45));
        let dynamicColor = props.risk_color;
        let dynamicLevel = props.risk_level;

        if (dynamicDepth > 70) {
          dynamicColor = '#ef4444';
          dynamicLevel = 'Severe';
        } else if (dynamicDepth > 40) {
          dynamicColor = '#f97316';
          dynamicLevel = 'High';
        } else if (dynamicDepth > 15) {
          dynamicColor = '#eab308';
          dynamicLevel = 'Moderate';
        }

        return {
          color: isSelected ? '#38bdf8' : dynamicColor,
          weight: isSelected ? 3.5 : (dynamicLevel === 'Severe' ? 2.5 : 1.5),
          opacity: 0.95,
          fillColor: dynamicColor,
          fillOpacity: isSelected ? 0.65 : (timeHorizon === '0-6h' ? 0.35 : 0.50),
          dashArray: isSelected ? '4, 4' : null
        };
      },
      onEachFeature: (feature, layer) => {
        const props = feature.properties;
        const dynamicDepth = Math.round(props.predicted_depth_cm + (surgeDelta * 0.45));

        layer.bindTooltip(`
          <div style="font-family: inherit; padding: 4px 6px;">
            <div style="font-weight: 700; font-size: 13px; color: #fff; margin-bottom: 2px;">${props.name}</div>
            <div style="display: flex; gap: 8px; font-size: 11px; margin-bottom: 2px;">
              <span style="color: ${props.risk_color}; font-weight: 600;">● ${props.risk_level} Risk (${props.risk_score}/100)</span>
            </div>
            <div style="font-size: 11px; color: #94a3b8;">
              Est. Inundation: <strong style="color: #f1f5f9;">${dynamicDepth} cm</strong> ${surgeDelta > 0 ? `(+${Math.round(surgeDelta * 0.45)}cm surge)` : ''}
            </div>
            <div style="font-size: 11px; color: #94a3b8;">
              6h Rain Nowcast: <strong style="color: #38bdf8;">${props.rainfall_nowcast_6h_mm + surgeDelta} mm</strong>
            </div>
            <div style="font-size: 10px; color: #64748b; margin-top: 4px; border-top: 1px solid #334155; padding-top: 2px;">
              Click to view detailed hydrograph & evacuation route
            </div>
          </div>
        `, { sticky: true, className: 'leaflet-custom-tooltip' });

        layer.on({
          click: () => {
            onSelectWard(props.ward_id);
            map.flyTo(props.center, 14, { duration: 0.8 });
          },
          mouseover: (e) => {
            e.target.setStyle({ fillOpacity: 0.75, weight: 3 });
          },
          mouseout: (e) => {
            geoJsonLayer.resetStyle(e.target);
          }
        });
      }
    }).addTo(map);

    layersRef.current.polygons = geoJsonLayer;
  }, [riskZones, selectedWardId, timeHorizon, layerVisibility.floodZones, surgeDelta]);

  // 4. Render Weather Radar Doppler Reflectivity Clouds & Animated Sweep Beam
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (layersRef.current.radar) map.removeLayer(layersRef.current.radar);
    if (!layerVisibility.weatherRadar) return;

    const radarGroup = L.layerGroup();

    // S-Band Doppler Radar Range Rings (Colaba)
    L.circle([18.910, 72.820], {
      radius: 45000,
      color: '#0284c7',
      weight: 1,
      dashArray: '4, 8',
      fillColor: '#0284c7',
      fillOpacity: 0.02
    }).addTo(radarGroup);

    // Convective Storm Cloud Core 1 (Mithi Basin - >54 dBZ)
    L.circle([19.070, 72.875], {
      radius: 5500,
      color: '#ef4444',
      weight: 1.5,
      fillColor: '#dc2626',
      fillOpacity: 0.32,
      dashArray: '3, 4'
    }).bindPopup(`
      <div style="font-size: 12px;">
        <strong style="color: #ef4444;">DWR Doppler Radar Convective Core</strong><br/>
        Reflectivity: <strong>54.5 dBZ</strong> (Intense Rain Band)<br/>
        Cloud Top Height: <strong>14.2 km</strong><br/>
        Motion: <strong>22 km/h ENE</strong>
      </div>
    `).addTo(radarGroup);

    // Secondary Rain Band (Sion-Dadar - 48 dBZ)
    L.circle([19.035, 72.860], {
      radius: 3800,
      color: '#f97316',
      weight: 1,
      fillColor: '#ea580c',
      fillOpacity: 0.25
    }).addTo(radarGroup);

    // Tertiary Rain Band (Andheri Subway Corridor - 42 dBZ)
    L.circle([19.115, 72.855], {
      radius: 3200,
      color: '#eab308',
      weight: 1,
      fillColor: '#ca8a04',
      fillOpacity: 0.22
    }).addTo(radarGroup);

    radarGroup.addTo(map);
    layersRef.current.radar = radarGroup;
  }, [layerVisibility.weatherRadar]);

  // 5. Radar Sweep Line Animation Interval
  useEffect(() => {
    if (!radarPlaying) return;
    const interval = setInterval(() => {
      setRadarSweepAngle((prev) => (prev + 15) % 360);
    }, 200);
    return () => clearInterval(interval);
  }, [radarPlaying]);

  // 6. Render High-Ground Evacuation Route Polyline for Selected Ward
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (layersRef.current.evacuation) {
      map.removeLayer(layersRef.current.evacuation);
      layersRef.current.evacuation = null;
    }

    if (!selectedWardId || !layerVisibility.evacuationCorridors) {
      setActiveEvacuationInfo(null);
      return;
    }

    fetch(`/api/carto/evacuation-route/${selectedWardId}`)
      .then(r => r.json())
      .then(data => {
        if (data.status !== 'success' || !data.route) return;
        const route = data.route;
        setActiveEvacuationInfo(route);

        const evacGroup = L.layerGroup();

        // Pulsing Glowing Green Safe Corridor Polyline
        const polyline = L.polyline(route.waypoints, {
          color: '#10b981',
          weight: 5,
          opacity: 0.9,
          dashArray: '8, 10',
          className: 'evac-pulsing-path'
        }).addTo(evacGroup);

        // Origin Lowland Vulnerability Node Marker
        const originIcon = L.divIcon({
          className: 'evac-origin-icon',
          html: `
            <div class="w-6 h-6 rounded-full bg-red-600 border-2 border-white shadow-xl flex items-center justify-center text-[10px] animate-bounce">
              ⚠️
            </div>
          `,
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        });

        L.marker(route.origin_point.coords, { icon: originIcon })
          .bindPopup(`
            <div style="font-size: 12px;">
              <strong style="color: #ef4444;">Flooding Hazard Origin</strong><br/>
              ${route.origin_point.name}<br/>
              <span style="color: #94a3b8;">Evacuate via marked high-ground pathway</span>
            </div>
          `)
          .addTo(evacGroup);

        // Safe Relief Shelter Destination Marker
        const shelterIcon = L.divIcon({
          className: 'evac-shelter-icon',
          html: `
            <div class="w-7 h-7 rounded-lg bg-emerald-600 border-2 border-white shadow-2xl flex items-center justify-center text-xs">
              ⛺
            </div>
          `,
          iconSize: [28, 28],
          iconAnchor: [14, 14]
        });

        L.marker(route.destination_shelter.coords, { icon: shelterIcon })
          .bindPopup(`
            <div style="font-size: 12px;">
              <strong style="color: #10b981; font-size: 13px;">Designated Relief Shelter</strong><br/>
              ${route.destination_shelter.name}<br/>
              Distance: <strong>${route.distance_m}m (~${route.est_evacuation_time_mins} min walk)</strong><br/>
              Elevation Gain: <strong style="color: #38bdf8;">+${route.elevation_gain_m}m above flood level</strong>
            </div>
          `)
          .addTo(evacGroup)
          .openPopup();

        evacGroup.addTo(map);
        layersRef.current.evacuation = evacGroup;
      })
      .catch(console.error);
  }, [selectedWardId, layerVisibility.evacuationCorridors]);

  // 7. Render River Gauges & AWS Stations
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !sensors?.sensors) return;

    if (layersRef.current.gauges) map.removeLayer(layersRef.current.gauges);
    if (layersRef.current.aws) map.removeLayer(layersRef.current.aws);

    const gaugeGroup = L.layerGroup();
    const awsGroup = L.layerGroup();

    sensors.sensors.forEach((s) => {
      if (s.type === 'river_gauge' && layerVisibility.riverGauges) {
        const isDanger = s.status === 'danger';
        const isWarning = s.status === 'warning';
        const badgeColor = isDanger ? 'bg-red-600 ring-red-400' : (isWarning ? 'bg-amber-600 ring-amber-400' : 'bg-emerald-600 ring-emerald-400');

        const gaugeIcon = L.divIcon({
          className: 'custom-gauge-icon',
          html: `
            <div class="relative flex items-center justify-center cursor-pointer group">
              <div class="w-8 h-8 rounded-full ${badgeColor} ring-4 ring-opacity-40 text-white flex items-center justify-center shadow-lg transform group-hover:scale-110 transition-transform">
                <span class="text-[11px] font-extrabold">🌊</span>
              </div>
              <div class="absolute -bottom-4 bg-slate-900/90 text-[10px] text-white font-bold px-1.5 py-0.2 rounded border border-slate-700 whitespace-nowrap shadow">
                ${s.current_level_m}m
              </div>
            </div>
          `,
          iconSize: [32, 32],
          iconAnchor: [16, 16]
        });

        const marker = L.marker([s.lat, s.lon], { icon: gaugeIcon })
          .bindPopup(`
            <div style="font-size: 12px; font-family: inherit;">
              <strong style="color: ${isDanger ? '#ef4444' : '#f59e0b'}; font-size: 13px;">${s.name}</strong><br/>
              Code: <span style="color: #94a3b8;">${s.code}</span><br/>
              Current Water Level: <strong style="color: #fff; font-size: 14px;">${s.current_level_m} m</strong><br/>
              Warning: <strong>${s.warning_mark_m}m</strong> | Danger: <strong style="color: #ef4444;">${s.danger_mark_m}m</strong><br/>
              Discharge: <strong>${s.discharge_cumec} m³/s</strong><br/>
              <span style="font-size: 10px; color: ${isDanger ? '#ef4444' : '#10b981'}; font-weight: 700; text-transform: uppercase;">
                ● Status: ${s.status}
              </span>
            </div>
          `);
        gaugeGroup.addLayer(marker);
      }

      if (s.type === 'aws' && layerVisibility.awsStations) {
        const awsIcon = L.divIcon({
          className: 'custom-aws-icon',
          html: `
            <div class="relative flex items-center justify-center cursor-pointer group">
              <div class="w-7 h-7 rounded-full bg-cyan-600 ring-2 ring-cyan-400 text-white flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                <span class="text-[10px] font-bold">☁️</span>
              </div>
              <div class="absolute -bottom-4 bg-slate-950 text-[9px] text-cyan-300 font-bold px-1 rounded border border-cyan-800 whitespace-nowrap shadow">
                ${s.current_rain_mm_hr}mm/h
              </div>
            </div>
          `,
          iconSize: [28, 28],
          iconAnchor: [14, 14]
        });

        const marker = L.marker([s.lat, s.lon], { icon: awsIcon })
          .bindPopup(`
            <div style="font-size: 12px;">
              <strong style="color: #38bdf8;">${s.name}</strong><br/>
              Rain Rate: <strong style="font-size: 13px; color: #fff;">${s.current_rain_mm_hr} mm/hr</strong><br/>
              3-Hr Cumulative: <strong>${s.cum_3hr_rain_mm} mm</strong><br/>
              Soil Moisture: <strong>${s.soil_moisture_pct}%</strong><br/>
              Temp / Humidity: <strong>${s.temp_c}°C / ${s.humidity_pct}%</strong>
            </div>
          `);
        awsGroup.addLayer(marker);
      }
    });

    gaugeGroup.addTo(map);
    awsGroup.addTo(map);
    layersRef.current.gauges = gaugeGroup;
    layersRef.current.aws = awsGroup;
  }, [sensors, layerVisibility.riverGauges, layerVisibility.awsStations]);

  // 8. Render Vulnerable Assets
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !riskZones?.features) return;

    if (layersRef.current.assets) map.removeLayer(layersRef.current.assets);
    if (!layerVisibility.vulnerableAssets) return;

    const assetGroup = L.layerGroup();

    riskZones.features.forEach((feat) => {
      const assets = feat.properties.vulnerable_assets || [];
      assets.forEach((asset) => {
        let iconEmoji = '⚠️';
        let bgColor = 'bg-amber-600';
        if (asset.type === 'hospital') {
          iconEmoji = '🏥';
          bgColor = 'bg-rose-600';
        } else if (asset.type === 'transit' || asset.type === 'road') {
          iconEmoji = '🚧';
          bgColor = 'bg-orange-600';
        } else if (asset.type === 'settlement') {
          iconEmoji = '🏘️';
          bgColor = 'bg-red-700';
        }

        const icon = L.divIcon({
          className: 'asset-marker',
          html: `
            <div class="w-6 h-6 rounded-md ${bgColor} text-white flex items-center justify-center text-[11px] shadow-md border border-slate-300/40 hover:scale-125 transition-transform" title="${asset.name}">
              ${iconEmoji}
            </div>
          `,
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        });

        const marker = L.marker([asset.lat, asset.lon], { icon })
          .bindPopup(`
            <div style="font-size: 12px;">
              <strong style="color: #f8fafc; font-size: 13px;">${asset.name}</strong><br/>
              Type: <span style="text-transform: capitalize; color: #94a3b8;">${asset.type}</span><br/>
              Vulnerability: <strong style="color: #ef4444;">${asset.vulnerability}</strong><br/>
              Ward: <span>${feat.properties.name}</span>
            </div>
          `);
        assetGroup.addLayer(marker);
      });
    });

    assetGroup.addTo(map);
    layersRef.current.assets = assetGroup;
  }, [riskZones, layerVisibility.vulnerableAssets]);

  // Debounced Search via /api/location/search
  useEffect(() => {
    if (!searchQuery || searchQuery.trim().length < 2) {
      setSuggestions([]);
      return;
    }

    const timer = setTimeout(() => {
      setIsSearching(true);
      fetch(`/api/location/search?q=${encodeURIComponent(searchQuery)}`)
        .then(r => r.json())
        .then(data => {
          setSuggestions(data.results || []);
          setIsSearching(false);
        })
        .catch(err => {
          console.error(err);
          setIsSearching(false);
        });
    }, 250);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleSelectSuggestion = (item) => {
    setSearchQuery(item.title);
    setSuggestions([]);

    const map = mapInstanceRef.current;
    if (!map) return;

    map.flyTo([item.lat, item.lon], 15, { duration: 1.2 });

    const locId = item.ward_id || `loc_${item.lat}_${item.lon}_${encodeURIComponent(item.title)}`;
    onSelectWard(locId);

    const pinIcon = L.divIcon({
      className: 'search-pin-icon',
      html: `
        <div class="flex flex-col items-center cursor-pointer animate-bounce">
          <div class="bg-cyan-500 text-slate-950 font-black text-xs px-2 py-0.5 rounded-md shadow-xl border border-white whitespace-nowrap">
            📍 ${item.title}
          </div>
          <div class="w-3 h-3 bg-cyan-500 rotate-45 -mt-1 shadow-md"></div>
        </div>
      `,
      iconSize: [120, 40],
      iconAnchor: [60, 40]
    });

    L.marker([item.lat, item.lon], { icon: pinIcon })
      .addTo(map)
      .bindPopup(`
        <div style="font-size: 12px; padding: 4px;">
          <strong style="color: #38bdf8; font-size: 13px;">${item.title}</strong><br/>
          <span style="color: #94a3b8;">${item.subtitle}</span><br/>
          Source: <strong style="color: #a855f7;">${item.source}</strong><br/>
          Flood Risk: <strong style="color: ${item.risk_level === 'Severe' ? '#ef4444' : '#f59e0b'};">${item.risk_level} (${item.risk_score}/100)</strong><br/>
          Est. Water Depth: <strong>${item.predicted_depth_cm} cm</strong>
        </div>
      `)
      .openPopup();
  };

  // Real Browser GPS Geolocation "Locate Me"
  const handleLocateMe = () => {
    setIsLocating(true);

    if (!('geolocation' in navigator)) {
      fallbackLocate();
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude, accuracy } = position.coords;
        const map = mapInstanceRef.current;

        fetch(`/api/location/reverse?lat=${latitude}&lon=${longitude}`)
          .then(r => r.json())
          .then(data => {
            setIsLocating(false);
            if (map) {
              map.flyTo([latitude, longitude], 15, { duration: 1.2 });

              const gpsIcon = L.divIcon({
                className: 'user-gps-icon',
                html: `
                  <div class="relative flex items-center justify-center">
                    <div class="w-6 h-6 rounded-full bg-cyan-500 ring-4 ring-cyan-300/50 animate-ping absolute"></div>
                    <div class="w-5 h-5 rounded-full bg-cyan-600 border-2 border-white shadow-xl flex items-center justify-center text-[10px]">
                      📍
                    </div>
                  </div>
                `,
                iconSize: [24, 24],
                iconAnchor: [12, 12]
              });

              L.marker([latitude, longitude], { icon: gpsIcon })
                .addTo(map)
                .bindPopup(`
                  <div style="font-size: 12px; padding: 2px;">
                    <strong style="color: #06b6d4; font-size: 13px;">📍 ${data.place_name || 'Your Location'}</strong><br/>
                    GPS: <code>${latitude.toFixed(4)}, ${longitude.toFixed(4)}</code> (±${Math.round(accuracy)}m)<br/>
                    Region: <strong>${data.city || 'Monitored Region'}</strong><br/>
                    Status: <strong style="color: #22c55e;">${data.matched_flood_ward?.risk_level || 'Low'} (0 cm flood depth)</strong><br/>
                    <span style="font-size: 10px; color: #94a3b8; display: block; margin-top: 3px;">${data.advice}</span>
                  </div>
                `)
                .openPopup();

              if (data.loc_id) {
                onSelectWard(data.loc_id);
              }
            }
          })
          .catch(() => fallbackLocate("Failed to parse GPS coordinates"));
      },
      (err) => {
        console.warn('Geolocation fallback:', err);
        fallbackLocate(err?.message || "Location access denied");
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
    );
  };

  const fallbackLocate = (reason) => {
    setIsLocating(false);
    const targetWard = riskZones?.features?.find(f => f.properties.ward_id === 'ward-L-kurla-w') || riskZones?.features?.[0];
    if (targetWard && mapInstanceRef.current) {
      onSelectWard(targetWard.properties.ward_id);
      mapInstanceRef.current.flyTo([19.070, 72.882], 14, { duration: 1.2 });
    }

    if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      alert("GPS Permission Notice:\n\nMobile browsers (Chrome / Safari) disable device GPS on unencrypted HTTP.\n\nPlease open the HTTPS link to enable real GPS positioning in Bengaluru:\nhttps://directory-rough-cinema-amplifier.trycloudflare.com");
    }
  };

  const handleResetView = () => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([19.065, 72.875], 13, { duration: 0.8 });
    }
  };

  return (
    <div className="relative w-full h-[calc(100dvh-80px)] sm:h-[calc(100vh-90px)] bg-slate-950 overflow-hidden">
      {/* Leaflet Map Canvas */}
      <div ref={mapContainerRef} className="w-full h-full z-0" />

      {/* Top Floating Control Deck / HUD */}
      <div className="absolute top-2 sm:top-4 left-2 sm:left-4 right-2 sm:right-4 z-20 flex flex-col sm:flex-row items-stretch sm:items-center justify-between pointer-events-none gap-2">
        {/* Search Bar with Mappls / Local Autocomplete */}
        <div className="pointer-events-auto relative w-full sm:max-w-md">
          <div className="flex items-center gap-1.5 bg-slate-900/95 backdrop-blur-md p-1.5 rounded-xl border border-slate-700/80 shadow-2xl">
            <form onSubmit={(e) => { e.preventDefault(); if (suggestions[0]) handleSelectSuggestion(suggestions[0]); }} className="flex-1 flex items-center gap-1.5 px-2 min-w-0">
              <Search className={`w-3.5 h-3.5 shrink-0 ${isSearching ? 'text-cyan-400 animate-spin' : 'text-slate-400'}`} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t.searchPlaceholder}
                className="w-full bg-transparent text-xs text-white placeholder-slate-400 focus:outline-none min-w-0"
              />
              {searchQuery && (
                <button type="button" onClick={() => { setSearchQuery(''); setSuggestions([]); }} className="text-slate-400 hover:text-white text-xs px-1">
                  ✕
                </button>
              )}
            </form>
            <button
              type="button"
              onClick={handleLocateMe}
              disabled={isLocating}
              className="flex items-center gap-1 bg-cyan-600 hover:bg-cyan-500 text-white text-[11px] sm:text-xs px-2.5 py-1.5 rounded-lg font-semibold transition-all shadow shrink-0"
              title="Detect precise GPS location"
            >
              <Crosshair className={`w-3.5 h-3.5 ${isLocating ? 'animate-spin' : ''}`} />
              <span>{isLocating ? t.locating : t.gpsLocate}</span>
            </button>
          </div>

          {/* Autocomplete Dropdown */}
          {suggestions.length > 0 && (
            <div className="absolute left-0 right-0 mt-1.5 bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-xl shadow-2xl overflow-hidden z-30 divide-y divide-slate-800 max-h-60 overflow-y-auto">
              {suggestions.map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => handleSelectSuggestion(item)}
                  className="p-2.5 hover:bg-slate-800/80 cursor-pointer transition-colors flex items-center justify-between gap-2"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-white truncate">{item.title}</span>
                      <span className="text-[9px] bg-purple-950/80 border border-purple-800 text-purple-300 px-1 rounded font-mono">
                        {item.source}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-400 block truncate">{item.subtitle}</span>
                  </div>
                  <div className="text-right shrink-0">
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      item.risk_level === 'Severe'
                        ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                        : (item.risk_level === 'High'
                        ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                        : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30')
                    }`}>
                      {item.risk_level} ({item.predicted_depth_cm}cm)
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Secondary Tool Row (Horizon + Tools) */}
        <div className="pointer-events-auto flex items-center justify-between sm:justify-end gap-1.5 w-full sm:w-auto relative z-30">
          {/* Time Horizon Switcher */}
          <div className="flex items-center bg-slate-900/95 backdrop-blur-md p-0.5 rounded-xl border border-slate-700/80 shadow-2xl shrink-0">
            <button
              onClick={() => setTimeHorizon('0-6h')}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                timeHorizon === '0-6h'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {t.horizonRain}
            </button>
            <button
              onClick={() => setTimeHorizon('6-24h')}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                timeHorizon === '6-24h'
                  ? 'bg-gradient-to-r from-orange-600 to-red-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {t.horizonFlood}
            </button>
          </div>

          {/* Dynamic Surge Simulator Button */}
          <button
            onClick={() => {
              setShowSurgeSimulator(!showSurgeSimulator);
              setShowBasemapMenu(false);
              setShowLayerMenu(false);
            }}
            className={`flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-[11px] font-semibold border shadow-2xl transition-all shrink-0 ${
              surgeDelta > 0 || showSurgeSimulator
                ? 'bg-amber-600 text-white border-amber-400 ring-2 ring-amber-500/30'
                : 'bg-slate-900/95 text-slate-200 border-slate-700/80 hover:bg-slate-800'
            }`}
            title="Simulate extreme rainfall storm surge"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span className="hidden xs:inline">{t.surgeSim}</span> {surgeDelta > 0 ? `+${surgeDelta}mm` : ''}
          </button>

          {/* CARTO Basemap Switcher */}
          <div className="relative shrink-0">
            <button
              onClick={() => {
                setShowBasemapMenu(!showBasemapMenu);
                setShowLayerMenu(false);
                setShowSurgeSimulator(false);
              }}
              className="flex items-center gap-1 bg-slate-900/95 backdrop-blur-md px-2.5 py-1.5 rounded-xl border border-slate-700/80 text-[11px] font-semibold text-slate-200 hover:bg-slate-800 transition-colors shadow-2xl cursor-pointer"
              title="CARTO Basemap Switcher"
            >
              <MapIcon className="w-3.5 h-3.5 text-cyan-400" />
              <span>{t.cartoMap}</span>
            </button>

            {showBasemapMenu && (
              <>
                <div className="fixed inset-0 z-40 bg-transparent" onClick={() => setShowBasemapMenu(false)} />
                <div className="absolute right-0 top-full mt-2 w-56 bg-slate-900/98 backdrop-blur-xl border border-slate-700 rounded-xl p-2.5 shadow-2xl z-50 space-y-1.5 text-xs animate-in fade-in slide-in-from-top-1">
                  <div className="font-bold text-slate-300 px-2 py-1 border-b border-slate-800 flex items-center justify-between text-[11px]">
                    <span>{t.cartoBasemaps}</span>
                    <span className="text-[9px] text-emerald-400 font-mono">{t.activeLayerTag}</span>
                  </div>
                  {Object.entries(BASEMAP_TILES).map(([key, style]) => (
                    <button
                      key={key}
                      onClick={() => {
                        setSelectedBasemap(key);
                        setShowBasemapMenu(false);
                      }}
                      className={`w-full text-left px-2.5 py-2 rounded-lg text-xs font-medium transition-colors flex items-center justify-between cursor-pointer ${
                        selectedBasemap === key
                          ? 'bg-cyan-600 text-white font-bold'
                          : 'text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      <span>{style.name}</span>
                      {selectedBasemap === key && <span>✓</span>}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* GIS Layers Toggle Menu */}
          <div className="relative shrink-0">
            <button
              onClick={() => {
                setShowLayerMenu(!showLayerMenu);
                setShowBasemapMenu(false);
                setShowSurgeSimulator(false);
              }}
              className="flex items-center gap-1 bg-slate-900/95 backdrop-blur-md px-2.5 py-1.5 rounded-xl border border-slate-700/80 text-[11px] font-semibold text-slate-200 hover:bg-slate-800 transition-colors shadow-2xl cursor-pointer"
            >
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>{t.layers}</span>
            </button>

            {showLayerMenu && (
              <>
                <div className="fixed inset-0 z-40 bg-transparent" onClick={() => setShowLayerMenu(false)} />
                <div className="absolute right-0 top-full mt-2 w-60 bg-slate-900/98 backdrop-blur-xl border border-slate-700 rounded-xl p-3.5 shadow-2xl z-50 text-xs space-y-2.5 animate-in fade-in slide-in-from-top-1">
                  <div className="font-bold text-slate-300 border-b border-slate-800 pb-1.5 flex items-center justify-between">
                    <span>{t.toggleGisLayers}</span>
                    <span className="text-[10px] text-slate-400 font-normal">{t.activeLayerTag}</span>
                  </div>
                  
                  <label className="flex items-center gap-2.5 cursor-pointer text-slate-200 hover:text-white transition-colors">
                    <input
                      type="checkbox"
                      checked={layerVisibility.floodZones}
                      onChange={(e) => setLayerVisibility({ ...layerVisibility, floodZones: e.target.checked })}
                      className="accent-cyan-500 rounded w-4 h-4 cursor-pointer"
                    />
                    <span>{t.layerFloodPolygons}</span>
                  </label>

                  <label className="flex items-center gap-2.5 cursor-pointer text-slate-200 hover:text-white transition-colors">
                    <input
                      type="checkbox"
                      checked={layerVisibility.weatherRadar}
                      onChange={(e) => setLayerVisibility({ ...layerVisibility, weatherRadar: e.target.checked })}
                      className="accent-cyan-500 rounded w-4 h-4 cursor-pointer"
                    />
                    <span>{t.layerDopplerRadar}</span>
                  </label>

                  <label className="flex items-center gap-2.5 cursor-pointer text-slate-200 hover:text-white transition-colors">
                    <input
                      type="checkbox"
                      checked={layerVisibility.riverGauges}
                      onChange={(e) => setLayerVisibility({ ...layerVisibility, riverGauges: e.target.checked })}
                      className="accent-cyan-500 rounded w-4 h-4 cursor-pointer"
                    />
                    <span>{t.layerRiverGauges}</span>
                  </label>

                  <label className="flex items-center gap-2.5 cursor-pointer text-slate-200 hover:text-white transition-colors">
                    <input
                      type="checkbox"
                      checked={layerVisibility.awsStations}
                      onChange={(e) => setLayerVisibility({ ...layerVisibility, awsStations: e.target.checked })}
                      className="accent-cyan-500 rounded w-4 h-4 cursor-pointer"
                    />
                    <span>{t.layerAwsStations}</span>
                  </label>

                  <label className="flex items-center gap-2.5 cursor-pointer text-slate-200 hover:text-white transition-colors">
                    <input
                      type="checkbox"
                      checked={layerVisibility.vulnerableAssets}
                      onChange={(e) => setLayerVisibility({ ...layerVisibility, vulnerableAssets: e.target.checked })}
                      className="accent-cyan-500 rounded w-4 h-4 cursor-pointer"
                    />
                    <span>{t.layerRoadsSubways}</span>
                  </label>

                  <label className="flex items-center gap-2.5 cursor-pointer text-emerald-400 font-semibold hover:text-emerald-300 transition-colors">
                    <input
                      type="checkbox"
                      checked={layerVisibility.evacuationCorridors}
                      onChange={(e) => setLayerVisibility({ ...layerVisibility, evacuationCorridors: e.target.checked })}
                      className="accent-emerald-500 rounded w-4 h-4 cursor-pointer"
                    />
                    <span>{t.layerEvacRoutes}</span>
                  </label>
                </div>
              </>
            )}
          </div>

          {/* Reset View */}
          <button
            onClick={handleResetView}
            className="bg-slate-900/95 backdrop-blur-md p-1.5 rounded-xl border border-slate-700/80 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors shadow-2xl shrink-0 cursor-pointer"
            title="Reset Map Center"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Interactive Storm Surge Simulator Drawer / Modal */}
      {showSurgeSimulator && (
        <div className="absolute top-28 sm:top-20 left-2 right-2 sm:left-auto sm:right-4 z-30 sm:w-80 bg-slate-900/98 backdrop-blur-xl p-3.5 rounded-2xl border border-amber-500/60 shadow-2xl text-xs space-y-2.5 animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
            <span className="font-bold text-amber-400 flex items-center gap-1.5 text-xs">
              <SlidersHorizontal className="w-3.5 h-3.5" />
              Dynamic Inundation Surge Sim
            </span>
            <button onClick={() => setShowSurgeSimulator(false)} className="text-slate-400 hover:text-white p-1">✕</button>
          </div>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            Simulate convective storm downpour over the catchment:
          </p>

          <div className="space-y-1">
            <div className="flex items-center justify-between font-mono text-xs">
              <span className="text-slate-400">Added Rainfall:</span>
              <strong className="text-amber-400 text-sm">+{surgeDelta} mm</strong>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="10"
              value={surgeDelta}
              onChange={(e) => setSurgeDelta(Number(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer h-2"
            />
            <div className="flex justify-between text-[9px] text-slate-500 font-mono">
              <span>0mm</span>
              <span>+50mm</span>
              <span>+100mm Cloudburst</span>
            </div>
          </div>

          <div className="bg-slate-950 p-2 rounded-lg border border-slate-800 text-[10px] sm:text-[11px] text-slate-300">
            Est. Inundation: <strong className="text-red-400">+{Math.round(surgeDelta * 0.45)} cm</strong> water depth across basins.
          </div>
        </div>
      )}

      {/* Active Evacuation Path HUD Alert (Appears when route is shown) */}
      {activeEvacuationInfo && (
        <div className="absolute top-28 sm:top-20 left-2 right-2 sm:right-auto sm:left-4 z-20 bg-emerald-950/95 backdrop-blur-md border border-emerald-500/70 p-2.5 sm:p-3 rounded-xl shadow-2xl text-xs max-w-none sm:max-w-sm flex items-start gap-2 animate-in fade-in">
          <Navigation className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5 min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <strong className="text-emerald-300 text-xs font-bold">{t.safeCorridorActive}</strong>
              <span className="text-[9px] bg-emerald-800 text-white px-1 rounded font-mono">
                ~{activeEvacuationInfo.est_evacuation_time_mins} {t.walkTime}
              </span>
            </div>
            <p className="text-[11px] text-emerald-200 leading-snug truncate">
              {activeEvacuationInfo.distance_m}m to {activeEvacuationInfo.destination_shelter.name}
            </p>
            <span className="text-[10px] text-cyan-300 font-mono block">
              {t.elevationGain}: +{activeEvacuationInfo.elevation_gain_m}m
            </span>
          </div>
        </div>
      )}

      {/* Floating Bottom-Left GIS Map Legend & Radar Controls (Responsive Collapsible on Mobile) */}
      <div className="absolute bottom-4 left-2 sm:left-4 z-20">
        {/* Mobile Toggle Pill Button */}
        <button
          onClick={() => setMobileLegendOpen(!mobileLegendOpen)}
          className="sm:hidden flex items-center gap-1.5 bg-slate-900/95 backdrop-blur-md border border-slate-700 px-3 py-1.5 rounded-full text-[11px] font-bold text-slate-200 shadow-2xl"
        >
          <ShieldAlert className="w-3.5 h-3.5 text-cyan-400" />
          <span>{t.legendRadar}</span>
          <span className="text-[9px] text-slate-400">{mobileLegendOpen ? '▼' : '▲'}</span>
        </button>

        {/* Legend Content Card (Always visible on desktop sm:block, toggleable on mobile) */}
        <div className={`${mobileLegendOpen ? 'block' : 'hidden'} sm:block mt-1 sm:mt-0 bg-slate-900/95 backdrop-blur-md p-3 rounded-2xl border border-slate-800 shadow-2xl text-xs w-[calc(100vw-1rem)] max-w-[280px] sm:w-72 space-y-2`}>
          <div className="flex items-center justify-between border-b border-slate-800 pb-1">
            <span className="font-bold text-slate-200 flex items-center gap-1.5 text-xs">
              <ShieldAlert className="w-3.5 h-3.5 text-cyan-400" />
              {t.legendTitle}
            </span>
            <span className="text-[9px] bg-cyan-950 border border-cyan-800 text-cyan-300 px-1 py-0.2 rounded font-mono">
              CARTO
            </span>
          </div>

          {/* Risk Palette */}
          <div className="grid grid-cols-2 gap-1 text-[10px] sm:text-[11px]">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 inline-block shadow"></span>
              <span className="text-slate-300">{t.riskLow}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-yellow-500 inline-block shadow"></span>
              <span className="text-slate-300">{t.riskModerate}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-orange-500 inline-block shadow"></span>
              <span className="text-slate-300">{t.riskHigh}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-red-500 inline-block shadow animate-pulse"></span>
              <span className="text-red-300 font-semibold">{t.riskSevere}</span>
            </div>
          </div>

          {/* Radar Loop Control Bar */}
          <div className="border-t border-slate-800 pt-1.5 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setRadarPlaying(!radarPlaying)}
                className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 transition-colors"
                title={radarPlaying ? 'Pause Radar' : 'Play Radar'}
              >
                {radarPlaying ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
              </button>
              <span className="text-[10px] text-slate-400 font-mono">
                {t.radarSweep}: {radarPlaying ? t.radarSweepLive : t.radarPaused}
              </span>
            </div>
            <span className="text-[10px] text-red-400 font-bold font-mono">54.5 dBZ</span>
          </div>

          {/* Live Open-Meteo Telemetry Badge */}
          {liveMet && (
            <div className="bg-slate-950 p-1.5 rounded-lg border border-slate-800/80 text-[10px] text-slate-400 flex items-center justify-between">
              <div className="flex items-center gap-1">
                <Thermometer className="w-3 h-3 text-amber-400" />
                <span>{liveMet.current_temperature_c}°C</span>
              </div>
              <div className="flex items-center gap-1">
                <CloudRain className="w-3 h-3 text-sky-400" />
                <span>{liveMet.current_precipitation_mm}mm/h</span>
              </div>
              <div className="flex items-center gap-1">
                <Wind className="w-3 h-3 text-cyan-400" />
                <span>{liveMet.wind_speed_kmh}km/h</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
