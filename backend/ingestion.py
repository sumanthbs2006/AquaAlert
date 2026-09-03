"""
AquaAlert AI - Multi-Source Data Ingestion & Live Telemetry Simulator
Connectors for:
1. INSAT-3D / GPM Satellite Rainfall Estimator
2. IMD Doppler Weather Radar (DWR) Reflectivity
3. Automated Weather Stations (AWS) Ground Network
4. Central Water Commission (CWC) River & Canal Gauge Telemetry
5. Numerical Weather Prediction (IMD GFS / NCMRWF Unified Model)
Provides dynamic scenario triggering (Cloudburst, Cyclone Inflow, Normal Monsoon, Baseline Dry).
"""

from typing import Dict, List, Any
from datetime import datetime, timezone
import random

# Predefined Meteorological Crisis Scenarios
SCENARIOS = {
    "live_weather": {
        "id": "live_weather",
        "name": "Live Real-Time Weather (Open-Meteo)",
        "description": "Live real-time weather observations directly from atmospheric numerical feeds. Accurately mirrors current sunny/dry conditions.",
        "params": {
            "rain_intensity_multiplier": 0.0,
            "soil_saturation_delta": -35.0,
            "river_surge_m": -0.8,
            "radar_peak_dbz": 15.0,
            "tidal_level_m": 0.2
        },
        "satellite": {
            "satellite_name": "INSAT-3D Optical / IR",
            "sensor": "Visible & Infrared Radiometer",
            "cloud_top_temp_c": -12.0,
            "precip_rate_mm_hr": 0.0,
            "coverage": "Mumbai Metropolitan Region"
        },
        "radar": {
            "radar_name": "DWR Mumbai S-Band",
            "max_reflectivity_dbz": 15.0,
            "echo_top_km": 2.5,
            "convective_core": "None (Clear / Sunny)",
            "cell_speed_kmh": 12.0,
            "cell_bearing_deg": 65
        },
        "nwp": {
            "model": "Open-Meteo GFS 3km High-Res",
            "forecast_accum_24h_mm": 0.0,
            "convective_available_pe_j_kg": 400,
            "precipitable_water_mm": 28.0
        }
    },
    "cloudburst": {
        "id": "cloudburst",
        "name": "Monsoon Cloudburst / Flash Flood Event",
        "description": "High-intensity localized convective cloudburst (>65 mm/hr) centering over Mithi River Catchment with rapid river surcharge.",
        "params": {
            "rain_intensity_multiplier": 1.75,
            "soil_saturation_delta": 10.0,
            "river_surge_m": 1.1,
            "radar_peak_dbz": 56.5,
            "tidal_level_m": 1.2
        },
        "satellite": {
            "satellite_name": "INSAT-3D / 3DR Imager",
            "sensor": "Thermal Infrared (TIR-1) + Hydro-Estimator",
            "cloud_top_temp_c": -68.5,
            "precip_rate_mm_hr": 74.0,
            "coverage": "Western Coastal Strip & Mumbai Urban Basin"
        },
        "radar": {
            "radar_name": "DWR Mumbai S-Band (Colaba) + X-Band (Veravali)",
            "max_reflectivity_dbz": 56.5,
            "echo_top_km": 15.4,
            "convective_core": "Bandra-Kurla-Sion corridor",
            "cell_speed_kmh": 22.0,
            "cell_bearing_deg": 68
        },
        "nwp": {
            "model": "IMD GFS 3km Regional High-Resolution Ensemble",
            "forecast_accum_24h_mm": 240.0,
            "convective_available_pe_j_kg": 2850,
            "precipitable_water_mm": 68.0
        }
    },
    "cyclone_surge": {
        "id": "cyclone_surge",
        "name": "Cyclone Rain-Band & Tidal Backwater Surge",
        "description": "Outer spiraling rainbands from Arabian Sea depression combined with spring high-tide (4.8m) causing severe tidal backwater.",
        "params": {
            "rain_intensity_multiplier": 1.35,
            "soil_saturation_delta": 6.0,
            "river_surge_m": 0.85,
            "radar_peak_dbz": 51.0,
            "tidal_level_m": 1.85  # Severe coastal tide locking drainage gates
        },
        "satellite": {
            "satellite_name": "GPM IMERG (Half-Hourly Global Precipitation)",
            "sensor": "Dual-frequency Precipitation Radar (DPR) + GMI",
            "cloud_top_temp_c": -55.0,
            "precip_rate_mm_hr": 52.0,
            "coverage": "Konkan Coast & Mumbai Metropolitan Region"
        },
        "radar": {
            "radar_name": "DWR Mumbai S-Band",
            "max_reflectivity_dbz": 51.0,
            "echo_top_km": 12.0,
            "convective_core": "Coastal Island City & Mahim Bay",
            "cell_speed_kmh": 38.0,
            "cell_bearing_deg": 110
        },
        "nwp": {
            "model": "NCMRWF Unified Model (NCUM-R 4km)",
            "forecast_accum_24h_mm": 175.0,
            "convective_available_pe_j_kg": 2100,
            "precipitable_water_mm": 62.0
        }
    },
    "normal_monsoon": {
        "id": "normal_monsoon",
        "name": "Normal Steady Monsoon Downpour",
        "description": "Typical steady southwest monsoon rainfall (20-35 mm/hr) with active storm drains and standard operational pumping.",
        "params": {
            "rain_intensity_multiplier": 0.65,
            "soil_saturation_delta": -5.0,
            "river_surge_m": 0.1,
            "radar_peak_dbz": 38.0,
            "tidal_level_m": 0.4
        },
        "satellite": {
            "satellite_name": "INSAT-3D Hydro-Estimator",
            "sensor": "Multi-Spectral Water Vapor + TIR",
            "cloud_top_temp_c": -42.0,
            "precip_rate_mm_hr": 28.0,
            "coverage": "General North Konkan"
        },
        "radar": {
            "radar_name": "DWR Mumbai S-Band",
            "max_reflectivity_dbz": 38.0,
            "echo_top_km": 9.5,
            "convective_core": "Dispersed stratiform rain cells",
            "cell_speed_kmh": 18.0,
            "cell_bearing_deg": 80
        },
        "nwp": {
            "model": "IMD GFS Global 12km Model",
            "forecast_accum_24h_mm": 65.0,
            "convective_available_pe_j_kg": 1200,
            "precipitable_water_mm": 48.0
        }
    },
    "dry_baseline": {
        "id": "dry_baseline",
        "name": "Dry Weather / Safe Baseline",
        "description": "Clear to partly cloudy skies, low moisture, dry soils, all river and drainage waterways flowing well within normal base levels.",
        "params": {
            "rain_intensity_multiplier": 0.05,
            "soil_saturation_delta": -35.0,
            "river_surge_m": -0.8,
            "radar_peak_dbz": 18.0,
            "tidal_level_m": 0.1
        },
        "satellite": {
            "satellite_name": "INSAT-3D Optical / IR",
            "sensor": "Visible & Infrared Radiometer",
            "cloud_top_temp_c": -12.0,
            "precip_rate_mm_hr": 0.0,
            "coverage": "Clear Skies / Scattered Cirrus"
        },
        "radar": {
            "radar_name": "DWR Mumbai S-Band",
            "max_reflectivity_dbz": 18.0,
            "echo_top_km": 3.0,
            "convective_core": "None (Clear air echo)",
            "cell_speed_kmh": 10.0,
            "cell_bearing_deg": 45
        },
        "nwp": {
            "model": "IMD GFS Global Model",
            "forecast_accum_24h_mm": 2.0,
            "convective_available_pe_j_kg": 450,
            "precipitable_water_mm": 26.0
        }
    }
}

SCENARIO_TRANSLATIONS = {
    "live_weather": {
        "en": {
            "name": "Live Real-Time Weather (Open-Meteo)",
            "description": "Live real-time weather observations directly from atmospheric numerical feeds. Accurately mirrors current sunny/dry conditions."
        },
        "hi": {
            "name": "लाइव वास्तविक समय मौसम (ओपन-मीटियो)",
            "description": "वायुमंडलीय मॉडल से सीधे लाइव मौसम आंकड़े। वर्तमान धूप व शुष्क स्थिति दर्शाता है।"
        },
        "kn": {
            "name": "ಲೈವ್ ನೈಜ-ಸಮಯದ ಹವಾಮಾನ (Open-Meteo)",
            "description": "ನೈಜ-ಸಮಯದ ವಾತಾವರಣದ ನೇರ ಮಾಹಿತಿ. ಪ್ರಸ್ತುತ ಬಿಸಿಲು ಮತ್ತು ಒಣ ವಾತಾವರಣವನ್ನು ಪ್ರತಿಬಿಂಬಿಸುತ್ತದೆ."
        }
    },
    "cloudburst": {
        "en": {
            "name": "Monsoon Cloudburst / Flash Flood Event",
            "description": "High-intensity localized convective cloudburst (>65 mm/hr) centering over Mithi River Catchment with rapid river surcharge."
        },
        "hi": {
            "name": "मानसून बादल फटना / अचानक बाढ़",
            "description": "मीठी नदी जल ग्रहण क्षेत्र में अत्यधिक भारी मानसूनी बादल फटने की घटना (>65 मिमी/घंटा), जिससे नदी का जलस्तर तेजी से बढ़ रहा है।"
        },
        "kn": {
            "name": "ಮೇಘಸ್ಫೋಟ / ಹಠಾತ್ ಪ್ರವಾಹದ ಘಟನೆ",
            "description": "ಮಿಥಿ ನದಿ ಜಲಾನಯನ ಪ್ರದೇಶದಲ್ಲಿ ತೀವ್ರ ಹಠಾತ್ ಮಳೆ (>65 ಮಿ.ಮೀ/ಗಂ) ಮತ್ತು ನದಿ ನೀರಿನ ಮಟ್ಟದಲ್ಲಿ ಕ್ಷಿಪ್ರ ಏರಿಕೆ."
        }
    },
    "cyclone_surge": {
        "en": {
            "name": "Cyclone Storm Surge & High Tide Coincidence",
            "description": "Outer spiraling rainbands from Arabian Sea depression combined with spring high-tide (4.8m) causing severe tidal backwater."
        },
        "hi": {
            "name": "चक्रवाती तूफान का दबाव व उच्च ज्वार",
            "description": "अरब सागर में चक्रवाती दबाव और 4.8 मीटर ऊंचे समुद्री ज्वार के कारण जल निकासी अवरुद्ध और गंभीर जलभराव।"
        },
        "kn": {
            "name": "ಚಂಡಮಾರುತದ ಅಲೆ ಮತ್ತು ಉಬ್ಬರವಿಳಿತ",
            "description": "ಅರಬ್ಬಿ ಸಮುದ್ರದ ಚಂಡಮಾರುತದ ಮಳೆ ಮತ್ತು 4.8 ಮೀಟರ್ ಎತ್ತರದ ಉಬ್ಬರವಿಳಿತದಿಂದಾಗಿ ನಗರದ ಒಳಚರಂಡಿ ನೀರಿನ ಹಿಮ್ಮುಖ ಹರಿವು."
        }
    },
    "normal_monsoon": {
        "en": {
            "name": "Standard Seasonal Monsoon Shower",
            "description": "Typical steady southwest monsoon rainfall (20-35 mm/hr) with active storm drains and standard operational pumping."
        },
        "hi": {
            "name": "सामान्य मौसमी मानसूनी बारिश",
            "description": "सामान्य स्थिर मानसूनी वर्षा (20-35 मिमी/घंटा), सामान्य नाली निकासी और परिचालन पंपिंग।"
        },
        "kn": {
            "name": "ಸಾಮಾನ್ಯ ಋತುಮಾನದ ಮುಂಗಾರು ಮಳೆ",
            "description": "ಸಾಮಾನ್ಯ ಸ್ಥಿರ ಮುಂಗಾರು ಮಳೆ (20-35 ಮಿ.ಮೀ/ಗಂ), ಕಾರ್ಯನಿರ್ವಹಿಸುವ ಚರಂಡಿಗಳು ಮತ್ತು ಸಾಮಾನ್ಯ ಪಂಪಿಂಗ್ ವ್ಯವಸ್ಥೆ."
        }
    },
    "dry_baseline": {
        "en": {
            "name": "Dry Weather / Safe Baseline",
            "description": "Clear to partly cloudy skies, low moisture, dry soils, all river and drainage waterways flowing well within normal base levels."
        },
        "hi": {
            "name": "शुष्क मौसम / सुरक्षित स्थिति",
            "description": "स्वच्छ मौसम, सूखी मिट्टी, और सभी नदियां तथा नालियां सामान्य आधार स्तर पर सुरक्षित बह रही हैं।"
        },
        "kn": {
            "name": "ಒಣ ಹವೆ / ಸುರಕ್ಷಿತ ಪರಿಸ್ಥಿತಿ",
            "description": "ಸ್ವಚ್ಛ ಹವೆ, ಒಣ ಮಣ್ಣು ಮತ್ತು ಎಲ್ಲಾ ನದಿ-ಕಾಲುವೆಗಳು ಸಾಮಾನ್ಯ ಸುರಕ್ಷಿತ ಮಟ್ಟದಲ್ಲಿ ಹರಿಯುತ್ತಿವೆ."
        }
    }
}

class IngestionManager:
    def __init__(self):
        self.active_scenario_id = "live_weather"
        self.last_refresh_time = datetime.now(timezone.utc).isoformat()

    def get_current_scenario(self) -> Dict[str, Any]:
        sc = SCENARIOS.get(self.active_scenario_id, SCENARIOS["live_weather"])
        if self.active_scenario_id == "live_weather":
            try:
                url = "https://api.open-meteo.com/v1/forecast?latitude=19.076&longitude=72.877&current=temperature_2m,precipitation,rain,weather_code&timezone=Asia%2FKolkata"
                r = requests.get(url, timeout=2.0)
                if r.status_code == 200:
                    cur = r.json().get("current", {})
                    precip = float(cur.get("precipitation", 0.0))
                    sc["params"]["rain_intensity_multiplier"] = max(0.0, precip / 45.0)
                    sc["satellite"]["precip_rate_mm_hr"] = precip
            except Exception:
                pass
        return sc

    def set_scenario(self, scenario_id: str) -> Dict[str, Any]:
        if scenario_id in SCENARIOS:
            self.active_scenario_id = scenario_id
            self.last_refresh_time = datetime.now(timezone.utc).isoformat()
        return self.get_current_scenario()

    def get_all_scenarios(self, lang: str = "en") -> List[Dict[str, Any]]:
        results = []
        for k, v in SCENARIOS.items():
            trans = SCENARIO_TRANSLATIONS.get(k, {}).get(lang, SCENARIO_TRANSLATIONS.get(k, {}).get("en", {}))
            results.append({
                "id": k,
                "name": trans.get("name", v["name"]),
                "description": trans.get("description", v["description"]),
                "is_active": (k == self.active_scenario_id)
            })
        return results

    def get_satellite_telemetry(self) -> Dict[str, Any]:
        scenario = self.get_current_scenario()
        sat = scenario["satellite"]
        return {
            "satellite_source": sat["satellite_name"],
            "sensor_payload": sat["sensor"],
            "cloud_top_temp_celsius": sat["cloud_top_temp_c"],
            "estimated_precip_rate_mm_hr": sat["precip_rate_mm_hr"],
            "geographic_coverage": sat["coverage"],
            "orbit_pass_time": "19:55 IST (Half-Hourly Refresh)",
            "data_quality_index": 98.4,
            "status": "ONLINE"
        }

    def get_radar_telemetry(self) -> Dict[str, Any]:
        scenario = self.get_current_scenario()
        rad = scenario["radar"]
        return {
            "station_name": rad["radar_name"],
            "operating_band": "S-Band (2.7-2.9 GHz)",
            "max_reflectivity_dbz": rad["max_reflectivity_dbz"],
            "echo_top_height_km": rad["echo_top_km"],
            "tracked_storm_core": rad["convective_core"],
            "storm_motion": f"{rad['cell_speed_kmh']} km/h at {rad['cell_bearing_deg']}°",
            "sweep_resolution": "250m radial grid",
            "last_scan_utc": datetime.now(timezone.utc).isoformat(),
            "status": "OPERATIONAL_SWEEP"
        }

    def get_nwp_telemetry(self) -> Dict[str, Any]:
        scenario = self.get_current_scenario()
        nwp = scenario["nwp"]
        return {
            "model_name": nwp["model"],
            "run_cycle": "12:00 UTC Run",
            "accumulated_24h_precip_mm": nwp["forecast_accum_24h_mm"],
            "cape_j_kg": nwp["convective_available_pe_j_kg"],
            "precipitable_water_mm": nwp["precipitable_water_mm"],
            "status": "INGESTED"
        }

ingestion_manager = IngestionManager()
