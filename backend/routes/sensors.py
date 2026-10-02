"""
AquaAlert AI - Sensors Telemetry & Scenario Simulation Routes
Provides real-time telemetry from Automated Weather Stations (AWS),
Doppler Weather Radars (DWR), River & Canal Gauges, and crisis scenario selection.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from backend.database import SENSOR_STATIONS, generate_regional_sensors
from backend.ingestion import ingestion_manager

router = APIRouter(prefix="/api", tags=["Sensors & Telemetry"])

class ScenarioSelectRequest(BaseModel):
    scenario_id: str
    phone: Optional[str] = None
    lang: Optional[str] = "en"
    area_name: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    authority_phone: Optional[str] = None
    override_text: Optional[str] = None

@router.get("/sensors")
def get_sensors(
    lat: Optional[float] = Query(None, description="Center latitude"),
    lon: Optional[float] = Query(None, description="Center longitude"),
    name: Optional[str] = Query(None, description="Name of searched location")
):
    """
    Returns sensor telemetry network with readings calibrated
    to the currently active hydrometeorological scenario.
    If lat and lon are provided outside Mumbai, dynamically generates regional sensors!
    """
    scenario = ingestion_manager.get_current_scenario()
    params = scenario["params"]
    multiplier = params.get("rain_intensity_multiplier", 1.0)
    surge_m = params.get("river_surge_m", 0.0)

    sensor_list = SENSOR_STATIONS
    is_national = (name and "india" in name.lower()) or (lat is not None and abs(lat - 22.5) < 2.0 and lon is not None and abs(lon - 79.0) < 2.0)
    if not is_national and lat is not None and lon is not None:
        min_d = min(((lat - s["lat"])**2 + (lon - s["lon"])**2)**0.5 for s in SENSOR_STATIONS)
        if min_d > 0.22:
            sensor_list = generate_regional_sensors(lat, lon, name or "Searched Location")

    calibrated_sensors = []
    for s in sensor_list:
        item = dict(s)
        if s["type"] == "aws":
            item["current_rain_mm_hr"] = round(s["current_rain_mm_hr"] * multiplier, 1)
            item["cum_3hr_rain_mm"] = round(s["cum_3hr_rain_mm"] * multiplier, 1)
            item["cum_24hr_rain_mm"] = round(s["cum_24hr_rain_mm"] * multiplier, 1)
        elif s["type"] == "river_gauge":
            new_level = round(s["current_level_m"] + surge_m, 2)
            item["current_level_m"] = new_level
            # Update status based on danger mark
            if new_level >= s["danger_mark_m"]:
                item["status"] = "danger"
            elif new_level >= s["warning_mark_m"]:
                item["status"] = "warning"
            else:
                item["status"] = "safe"
        elif s["type"] == "dwr_radar":
            item["max_reflectivity_dbz"] = params.get("radar_peak_dbz", s["max_reflectivity_dbz"])

        calibrated_sensors.append(item)

    return {
        "status": "success",
        "active_scenario": scenario["name"],
        "total_sensors": len(calibrated_sensors),
        "sensors": calibrated_sensors
    }

@router.get("/sensors/summary")
def get_sensors_summary():
    """Returns top-level metric counters for dashboard header ribbon."""
    scenario = ingestion_manager.get_current_scenario()
    params = scenario["params"]
    multiplier = params.get("rain_intensity_multiplier", 1.0)

    avg_basin_rain = round(42.5 * multiplier, 1)
    peak_gauge_ratio = round(min(1.25, 0.92 + (params.get("river_surge_m", 0.0) * 0.18)), 2)
    max_dbz = params.get("radar_peak_dbz", 52.0)

    return {
        "active_scenario_id": scenario["id"],
        "active_scenario_name": scenario["name"],
        "avg_basin_rain_mm_hr": avg_basin_rain,
        "peak_river_level_ratio": peak_gauge_ratio,
        "peak_river_danger_status": "DANGER" if peak_gauge_ratio >= 1.0 else ("WARNING" if peak_gauge_ratio >= 0.85 else "NORMAL"),
        "max_radar_reflectivity_dbz": max_dbz,
        "active_radar_stations": 2,
        "active_aws_stations": 4,
        "active_river_gauges": 4,
        "total_sensors_online": 10
    }

@router.get("/scenarios")
def list_scenarios(lang: str = "en"):
    """Returns list of selectable weather/flood simulation scenarios."""
    return {
        "current_active_id": ingestion_manager.active_scenario_id,
        "scenarios": ingestion_manager.get_all_scenarios(lang=lang)
    }

@router.post("/scenarios/select")
def select_scenario(req: ScenarioSelectRequest):
    """
    Switches the active simulation scenario across the entire platform.
    Automatically dispatches corresponding emergency SMS alert to citizen and nearby rescue authority
    whenever the switched scenario involves heavy, severe, or moderate rainfall for live demo & warning.
    """
    res = ingestion_manager.set_scenario(req.scenario_id)
    sc_id = req.scenario_id.lower()

    # Determine meteorological parameters for this scenario
    params = res.get("params", {})
    multiplier = params.get("rain_intensity_multiplier", 1.0)
    basin_rain = round(42.5 * multiplier, 1)

    is_sms_eligible = False
    rainfall_rate = basin_rain
    severity = "Moderate"
    river_stage = "WARNING"
    hazard_type = "Monsoon Telemetry Advisory"

    if sc_id == "cloudburst":
        is_sms_eligible = True
        rainfall_rate = max(basin_rain, 75.0)
        severity = "Severe"
        river_stage = "DANGER"
        hazard_type = "Monsoon Cloudburst & Flash Flood Surge Emergency"
    elif sc_id in ["cyclone_surge", "cyclone"]:
        is_sms_eligible = True
        rainfall_rate = max(basin_rain, 55.0)
        severity = "Severe"
        river_stage = "DANGER"
        hazard_type = "Cyclone Storm Surge & Tidal Backwater Warning"
    elif sc_id in ["normal_monsoon", "normal"]:
        is_sms_eligible = True
        rainfall_rate = basin_rain if basin_rain >= 15.0 else 28.0
        severity = "Moderate"
        river_stage = "WARNING"
        hazard_type = "Standard Seasonal Monsoon Downpour Advisory"
    elif sc_id == "live_weather":
        sat_precip = res.get("satellite", {}).get("precip_rate_mm_hr", 0.0)
        eff_rain = max(basin_rain, sat_precip)
        if eff_rain >= 65.0:
            is_sms_eligible = True
            rainfall_rate = eff_rain
            severity = "Severe"
            river_stage = "DANGER"
            hazard_type = "Live Convective Cloudburst Advisory"
        elif eff_rain >= 25.0:
            is_sms_eligible = True
            rainfall_rate = eff_rain
            severity = "Severe"
            river_stage = "DANGER"
            hazard_type = "Live Heavy Rainfall Advisory"
        elif eff_rain >= 15.0:
            is_sms_eligible = True
            rainfall_rate = eff_rain
            severity = "Moderate"
            river_stage = "WARNING"
            hazard_type = "Live Moderate Rain Advisory"
        else:
            is_sms_eligible = False
    elif sc_id in ["dry_baseline", "baseline"]:
        is_sms_eligible = False

    target_area = req.area_name or "Mumbai Metropolitan Basin"
    lang = (req.lang or "en").lower()

    sms_result = None
    if is_sms_eligible:
        from backend.routes.alerts import dispatch_emergency_sms, DispatchSmsRequest, DISPATCHED_SMS_LOGS

        # Determine target phone: user requested phone, or most recent logged citizen phone, or default
        target_phone = req.phone
        if not target_phone and DISPATCHED_SMS_LOGS:
            for item in DISPATCHED_SMS_LOGS:
                if item.get("recipient_type") == "citizen" and item.get("clean_phone"):
                    target_phone = item["clean_phone"]
                    break
        if not target_phone:
            target_phone = "919876543210"

        # Construct customized, high-fidelity localized emergency SMS message for this scenario
        if req.override_text:
            sms_text = req.override_text
        elif sc_id == "cloudburst":
            if lang == "hi":
                sms_text = f"🚨 [एक्वाअलर्ट लाल चेतावनी] {target_area} में भारी बादल फटना ({rainfall_rate:.1f} मिमी/घंटा) व भीषण बाढ़! नदियां खतरे के निशान से ऊपर। तुरंत ऊंचे स्थान पर जाएं। NDRF QRT तैनात। आपातकालीन: 112 / 1070।"
            elif lang == "kn":
                sms_text = f"🚨 [AquaAlert ರೆಡ್ ಅಲರ್ಟ್] {target_area} ಪ್ರದೇಶದಲ್ಲಿ ಮೇಘಸ್ಫೋಟ ({rainfall_rate:.1f} mm/h) ಮತ್ತು ಪ್ರವಾಹ! ತಕ್ಷಣ ಎತ್ತರದ ಪ್ರದೇಶಗಳಿಗೆ ತೆರಳಿ. NDRF ರಕ್ಷಣಾ ಪಡೆ ಸನ್ನದ್ಧವಾಗಿದೆ. ತುರ್ತು ಸಹಾಯ: 112 / 1070."
            else:
                sms_text = f"🚨 [AquaAlert RED FLOOD ALERT] Severe Cloudburst ({rainfall_rate:.1f} mm/h) active over {target_area}! Critical river surcharge & street inundation (40–70cm). Relocate to higher ground immediately. NDRF Quick Response Team deployed. Emergency: 112 / 1070."
        elif sc_id in ["cyclone_surge", "cyclone"]:
            if lang == "hi":
                sms_text = f"🚨 [एक्वाअलर्ट चक्रवाती चेतावनी] {target_area} में भारी चक्रवाती बारिश ({rainfall_rate:.1f} मिमी/घंटा) और 4.8 मीटर समुद्री ज्वार! तटीय सड़कों व सबवे से दूर रहें। DEOC आपातकालीन: 112 / 1916।"
            elif lang == "kn":
                sms_text = f"🚨 [AquaAlert ಚಂಡಮಾರುತ ಎಚ್ಚರಿಕೆ] {target_area} ಕರಾವಳಿಯಲ್ಲಿ ಭಾರಿ ಮಳೆ ({rainfall_rate:.1f} mm/h) ಮತ್ತು 4.8m ಉಬ್ಬರವಿಳಿತದ ಅಲೆಗಳು! ಕರಾವಳಿ ಮಾರ್ಗಗಳನ್ನು ತಪ್ಪಿಸಿ. DEOC ತುರ್ತು: 112 / 1916."
            else:
                sms_text = f"🚨 [AquaAlert CYCLONIC SURGE WARNING] Heavy outer rainbands ({rainfall_rate:.1f} mm/h) & 4.8m tidal storm surge in {target_area}! Sea outfalls locked. Avoid coastal corridors and subways. DEOC Emergency: 112 / 1916."
        elif sc_id in ["normal_monsoon", "normal"]:
            if lang == "hi":
                sms_text = f"⚠️ [एक्वाअलर्ट मानसूनी सूचना] {target_area} में सामान्य मध्यम मानसूनी बारिश ({rainfall_rate:.1f} मिमी/घंटा)। नगर निगम पंप सक्रिय हैं। निचले जलभराव वाले रास्तों पर सावधानी बरतें। हेल्पलाइन: 1916 / 112।"
            elif lang == "kn":
                sms_text = f"⚠️ [AquaAlert ಮುಂಗಾರು ಮಾಹಿತಿ] {target_area} ಪ್ರದೇಶದಲ್ಲಿ ಸಾಧಾರಣ ಮುಂಗಾರು ಮಳೆ ({rainfall_rate:.1f} mm/h). ನೀರು ಹೊರಹಾಕುವ ಪಂಪ್‌ಗಳು ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತಿವೆ. ತಗ್ಗು ಪ್ರದೇಶಗಳಲ್ಲಿ ಜಾಗರೂಕರಾಗಿರಿ. ಸಹಾಯವಾಣಿ: 1916 / 112."
            else:
                sms_text = f"⚠️ [AquaAlert MONSOON ADVISORY] Moderate steady monsoon rain ({rainfall_rate:.1f} mm/h) recorded in {target_area}. Municipal suction pumps deployed. Proceed with caution near railway dips and lowlands. Helpline: 1916 / 112."
        else:
            if lang == "hi":
                sms_text = f"⚠️ [एक्वाअलर्ट लाइव मौसम सूचना] लाइव मौसम रडार ने {target_area} में {rainfall_rate:.1f} मिमी/घंटा बारिश दर्ज की है। जल निकासी निगरानी जारी। हेल्पलाइन: 112 / 1916।"
            elif lang == "kn":
                sms_text = f"⚠️ [AquaAlert ಲೈವ್ ಹವಾಮಾನ ಮಾಹಿತಿ] ಲೈವ್ ರಾಡಾರ್ {target_area} ಪ್ರದೇಶದಲ್ಲಿ {rainfall_rate:.1f} mm/h ಮಳೆಯನ್ನು ದಾಖಲಿಸಿದೆ. ನಿಗಾ ಇರಿಸಲಾಗಿದೆ. ಸಹಾಯವಾಣಿ: 112 / 1916."
            else:
                sms_text = f"⚠️ [AquaAlert LIVE WEATHER ALERT] Live atmospheric telemetry detects {rainfall_rate:.1f} mm/h rainfall in {target_area}. Drainage and river monitoring active. Helpline: 112 / 1916."

        dispatch_req = DispatchSmsRequest(
            phone=target_phone,
            area_name=target_area,
            hazard_type=hazard_type,
            rainfall_mm_hr=rainfall_rate,
            severity=severity,
            river_stage=river_stage,
            inundation_depth_cm=45.0 if severity == "Severe" else 15.0,
            lat=req.lat,
            lon=req.lon,
            lang=lang,
            override_text=sms_text,
            is_force_test=True,
            authority_phone=req.authority_phone
        )
        sms_result = dispatch_emergency_sms(dispatch_req)

    return {
        "status": "success",
        "message": f"Active meteorological scenario switched to '{res['name']}'",
        "scenario": res,
        "sms_dispatched": is_sms_eligible,
        "rainfall_mm_hr": rainfall_rate if is_sms_eligible else 0.0,
        "severity": severity if is_sms_eligible else "Safe",
        "sms": sms_result.get("sms") if sms_result else None,
        "authority_sms": sms_result.get("authority_sms") if sms_result else None,
        "dispatched_entries": sms_result.get("dispatched_entries", []) if sms_result else [],
        "infobip_delivered": sms_result.get("infobip_delivered", False) if sms_result else False,
        "reason": None if is_sms_eligible else "Dry baseline / safe weather condition: Emergency SMS suppressed as rainfall is not heavy, severe, or moderate."
    }

@router.get("/ingestion/telemetry")
def get_ingestion_layers():
    """Returns live telemetry payloads from Satellite, Radar, and NWP feeds."""
    return {
        "satellite": ingestion_manager.get_satellite_telemetry(),
        "radar": ingestion_manager.get_radar_telemetry(),
        "nwp": ingestion_manager.get_nwp_telemetry()
    }
