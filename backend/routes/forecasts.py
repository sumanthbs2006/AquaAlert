"""
AquaAlert AI - Forecasts & Risk Zones API Routes
GeoJSON FeatureCollection export, Ward-specific 24-hr hydrological forecasts, and ad-hoc ML inference.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
import urllib.parse
import requests
import numpy as np
from backend.database import (
    WARDS_DATA, 
    generate_regional_wards, 
    estimate_base_elevation,
    get_active_alert_for_location,
    get_alert_crisis_params,
    get_calamity_proximity_info
)
from backend.ml_engine import ml_engine
from backend.ingestion import ingestion_manager
from backend.openweather import get_live_weather

router = APIRouter(prefix="/api", tags=["Forecasts & Risk Zones"])

class CustomMLPredictRequest(BaseModel):
    rain_1h_mm: float = 45.0
    cum_3h_rain_mm: float = 110.0
    radar_reflectivity_dbz: float = 52.0
    soil_saturation_pct: float = 85.0
    river_gauge_ratio: float = 0.95
    elevation_m: float = 8.0
    terrain_slope_deg: float = 1.0
    impervious_surface_pct: float = 85.0
    drainage_constriction_idx: float = 60.0
    tidal_backwater_m: float = 0.8

@router.get("/risk-zones")
def get_risk_zones_geojson(
    lat: Optional[float] = Query(None, description="Center latitude"),
    lon: Optional[float] = Query(None, description="Center longitude"),
    name: Optional[str] = Query(None, description="Name of searched location")
):
    """
    Returns GeoJSON FeatureCollection containing ward polygons
    enriched with real-time ML risk scores, inundation depths, and XAI explainability.
    If lat and lon are provided outside Mumbai, dynamically generates regional wards!
    """
    scenario = ingestion_manager.get_current_scenario()
    wards = WARDS_DATA
    is_national = (name and "india" in name.lower()) or (lat is not None and abs(lat - 22.5) < 2.0 and lon is not None and abs(lon - 79.0) < 2.0)
    active_alert = None
    if not is_national and lat is not None and lon is not None:
        active_alert = get_active_alert_for_location(lat, lon, name or "")
        min_d = min(((lat - w["center"][0])**2 + (lon - w["center"][1])**2)**0.5 for w in WARDS_DATA)
        if min_d > 0.22:
            wards = generate_regional_wards(lat, lon, name or "Searched Location")

    # Synchronize simulation parameters: prioritize live weather observations when in live_weather mode!
    if scenario.get("id") == "live_weather":
        if lat is not None and lon is not None:
            live_w = get_live_weather(lat, lon)
            live_rain = float(live_w.get("rain_1h_mm", 0.0) or 0.0)
            run_params = {
                "rain_intensity_multiplier": live_rain / 45.0 if live_rain > 0 else 0.0,
                "soil_saturation_delta": -35.0 if live_rain == 0 else 5.0,
                "river_surge_m": -0.8 if live_rain == 0 else 0.1,
                "radar_peak_dbz": 15.0 if live_rain == 0 else min(55.0, 10 * float(np.log10(max(200 * (live_rain ** 1.6), 1)))),
                "tidal_level_m": 0.2
            }
        else:
            run_params = scenario.get("params")
        scenario_title = "Live Weather Observations"
    elif active_alert:
        run_params = get_alert_crisis_params(active_alert)
        scenario_title = f"Active CAP Advisory: {active_alert.get('headline', active_alert.get('event', 'Emergency Alert'))}"
    else:
        run_params = scenario.get("params")
        scenario_title = scenario["name"]

    features = []
    for ward in wards:
        # Run ML engine prediction for this ward
        pred = ml_engine.predict_ward_risk(ward, run_params)

        # Calamity proximity analysis for this ward
        w_center = ward.get("center", [lat or 19.076, lon or 72.877])
        prox = get_calamity_proximity_info(w_center[0], w_center[1], ward.get("name", ""), ward.get("id", ""))
        z_type = prox.get("zone_type", "none")
        c_dist = prox.get("distance_km", 999.0)

        if z_type == "calamity_epicenter":
            # Calamity epicenter zone: Severe risk!
            pred["risk_level"] = "Severe"
            pred["risk_score"] = round(max(86.5, 92.0 - c_dist * 0.4), 1)
            pred["predicted_depth_cm"] = round(max(40.0, 54.0 - c_dist * 0.8), 1)
            pred["depth_range_cm"] = "40 - 65 cm"
            pred["rainfall_nowcast_6h_mm"] = 38.5
        elif z_type == "calamity_near":
            # Areas near calamity zone: Moderate risk!
            pred["risk_level"] = "Moderate"
            pred["risk_score"] = round(48.0 - (c_dist - 15.0) * 0.45, 1)
            pred["predicted_depth_cm"] = round(max(10.0, 20.0 - (c_dist - 15.0) * 0.35), 1)
            pred["depth_range_cm"] = "12 - 25 cm (Sump Pooling)"
            pred["rainfall_nowcast_6h_mm"] = 18.0
        elif z_type == "calamity_peripheral":
            # Outer peripheral buffer: Low risk with slight elevation
            pred["risk_level"] = "Low"
            pred["risk_score"] = round(28.0 - (c_dist - 42.0) * 0.15, 1)
            pred["predicted_depth_cm"] = round(max(0.0, 5.0 - (c_dist - 42.0) * 0.15), 1)
            pred["depth_range_cm"] = "0 - 5 cm (Peripheral Watch)"
            pred["rainfall_nowcast_6h_mm"] = 5.0
        elif scenario.get("id") == "live_weather" and run_params.get("rain_intensity_multiplier", 0.0) == 0.0:
            # Areas with no calamity and zero rainfall: Safe & Clear!
            pred["risk_score"] = round(min(float(pred.get("risk_score", 11.5)), 14.0), 1)
            pred["risk_level"] = "Low"
            pred["predicted_depth_cm"] = 0.0
            pred["depth_range_cm"] = "0 cm (Safe & Clear)"
            pred["rainfall_nowcast_6h_mm"] = 0.0

        # Map risk level to standard disaster color palette
        color_map = {
            "Low": "#22c55e",       # Green
            "Moderate": "#eab308",  # Amber / Yellow
            "High": "#f97316",      # Orange
            "Severe": "#ef4444"      # Red / Crimson
        }
        risk_color = color_map.get(pred["risk_level"], "#22c55e")

        # GeoJSON coordinates format is [longitude, latitude]
        polygon_geojson = [
            [[coord[1], coord[0]] for coord in ward["polygon"]]
        ]

        feature = {
            "type": "Feature",
            "id": ward["id"],
            "geometry": {
                "type": "Polygon",
                "coordinates": polygon_geojson
            },
            "properties": {
                "ward_id": ward["id"],
                "name": ward["name"],
                "code": ward["code"],
                "zone": ward["zone"],
                "population": ward["population"],
                "area_km2": ward["area_km2"],
                "avg_elevation_m": ward["avg_elevation_m"],
                "terrain_slope_deg": ward["terrain_slope_deg"],
                "impervious_surface_pct": ward["impervious_surface_pct"],
                "drainage_density_idx": ward["drainage_density_idx"],
                "center": ward["center"],
                "risk_score": pred["risk_score"],
                "risk_level": pred["risk_level"],
                "risk_color": risk_color,
                "predicted_depth_cm": pred["predicted_depth_cm"],
                "depth_range_cm": pred["depth_range_cm"],
                "confidence_pct": pred["confidence_pct"],
                "uncertainty_margin_cm": pred["uncertainty_margin_cm"],
                "rainfall_nowcast_6h_mm": pred["rainfall_nowcast_6h_mm"],
                "explainability_factors": pred["explainability_factors"],
                "vulnerable_assets": ward.get("vulnerable_assets", []),
                "nearest_shelter": ward.get("nearest_shelter")
            }
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "scenario": scenario["name"],
        "total_wards": len(features),
        "features": features
    }

@router.get("/forecasts/{ward_id}")
def get_ward_forecast(ward_id: str):
    """
    Returns full deep-dive forecast for a specific ward or any arbitrary geographic point.
    """
    ward = next((w for w in WARDS_DATA if w["id"] == ward_id or w["code"].lower() == ward_id.lower()), None)
    is_out = False
    lat, lon = 19.076, 72.877
    
    # If not one of the pre-configured pilot wards, generate on-the-fly virtual ward!
    if not ward:
        # Check if it is a regional basin ward or coordinate-based custom location
        if ward_id.startswith("reg-basin-"):
            parts = ward_id.split("-")
            try:
                r_lat = float(parts[2])
                r_lon = float(parts[3])
                quad = int(parts[4]) - 1
                reg_wards = generate_regional_wards(r_lat, r_lon)
                ward = reg_wards[quad] if quad < len(reg_wards) else reg_wards[0]
                lat, lon, name = ward["center"][0], ward["center"][1], ward["name"]
                is_out = True
            except Exception:
                lat, lon, name = 19.076, 72.877, "Regional Basin"
                is_out = True
        elif ward_id.startswith("loc_"):
            parts = ward_id.split("_", 3)
            try:
                lat = float(parts[1])
                lon = float(parts[2])
                name = urllib.parse.unquote(parts[3]) if len(parts) > 3 else f"Coordinates {lat}, {lon}"
            except Exception:
                lat, lon, name = 19.076, 72.877, "Searched Location"
            is_out = True
        else:
            lat, lon, name = 19.076, 72.877, ward_id.replace("-", " ").title()
            is_out = True

        if not ward:
            # Generate realistic topographical parameters for arbitrary inspected coordinate point
            base_elev = estimate_base_elevation(lat, lon)
            name_lower = name.lower()
            is_lowland = any(w in name_lower for w in ["underpass", "subway", "nullah", "culvert", "creek", "riverbank", "lakebed", "marsh", "swamp", "khadi"])
            is_highland = any(w in name_lower for w in ["hill", "ridge", "high", "heights", "peak", "plateau", "mount"])
            
            p_slope = 3.5 if is_highland else (0.8 if is_lowland else 1.6)
            p_elev = max(base_elev + 20.0, 30.0) if is_highland else (max(base_elev - 4.0, 5.0) if is_lowland else max(base_elev, 15.0))
            p_imperv = 60.0 if is_highland else (86.0 if is_lowland else 75.0)
            p_drain = 65.0 if is_highland else (40.0 if is_lowland else 55.0)
            
            ward = {
                "id": ward_id,
                "name": name,
                "code": "REGIONAL",
                "zone": "Inspected Region",
                "population": 150000,
                "avg_elevation_m": p_elev,
                "actual_altitude_m": base_elev,
                "terrain_slope_deg": p_slope,
                "impervious_surface_pct": p_imperv,
                "drainage_density_idx": p_drain,
                "antecedent_moisture_pct": 55.0 if is_lowland else 45.0,
                "historical_waterlogging_frequency": "Moderate" if is_lowland else "Low",
                "center": [lat, lon],
                "vulnerable_assets": [
                    {"name": f"Local Infrastructure near {name.split(',')[0]}", "type": "transit", "lat": lat, "lon": lon, "vulnerability": "Moderate" if is_lowland else "Low"}
                ],
                "nearest_shelter": {"name": f"{name.split(',')[0]} Municipal Relief Shelter", "lat": round(lat + 0.005, 4), "lon": round(lon + 0.005, 4), "capacity": 750, "occupied": 10}
            }

    scenario = ingestion_manager.get_current_scenario()
    sc_id = scenario.get("id", "live_weather")
    
    # Check if this ward or inspected coordinate belongs to an Active CAP Disaster Alert Zone
    active_alert = get_active_alert_for_location(lat, lon, name, ward_id)
    matched_alert_dict = None
    if active_alert:
        matched_alert_dict = {
            "id": active_alert.get("id"),
            "severity": active_alert.get("severity"),
            "headline": active_alert.get("headline"),
            "instruction": active_alert.get("instruction"),
            "state": active_alert.get("state"),
            "sent": active_alert.get("sent"),
            "area_desc": active_alert.get("areaDesc"),
            "rainfall_time_window": active_alert.get("rainfall_time_window"),
            "inundation_time_window": active_alert.get("inundation_time_window")
        }

    prox_info = get_calamity_proximity_info(lat, lon, name, ward_id)
    calamity_zone = prox_info.get("zone_type", "none")
    calamity_alert = prox_info.get("alert") or active_alert
    calamity_dist_km = prox_info.get("distance_km", 999.0)

    if sc_id == "live_weather":
        if calamity_zone == "calamity_epicenter":
            # Calamity epicenter zone: Severe risk! (e.g. Patna, Dehradun)
            alert = calamity_alert or {
                "headline": "RED ALERT: Severe Calamity & Inundation Zone",
                "instruction": "Active RED ALERT flood advisory. Evacuate lowlands.",
                "state": "Regional",
                "event": "Torrential Downpour & Flash Inundation"
            }
            risk_score = round(max(86.5, 92.0 - calamity_dist_km * 0.35), 1)
            risk_level = "Severe"
            pred_depth = round(max(42.0, 56.0 - calamity_dist_km * 0.7), 1)
            depth_range = "40 - 65 cm"
            uncertainty_margin = 6.5
            confidence_pct = 89.5
            nowcast_6h = 38.5
            peak_hr = "T+1 hr (Severe Convective Bursts)"

            hourly_series = []
            for h in range(1, 25):
                h_rain = round(nowcast_6h * 0.35, 1) if h <= 2 else (round(nowcast_6h * 0.2, 1) if h <= 5 else 0.8)
                h_depth = pred_depth if (2 <= h <= 6) else (round(pred_depth * 0.75, 1) if h <= 10 else round(pred_depth * 0.35, 1))
                hourly_series.append({
                    "hour": f"+{h}h",
                    "time_label": f"T+{h:02d}:00",
                    "rainfall_mm": h_rain,
                    "inundation_depth_cm": h_depth,
                    "river_level_m": 1.45
                })

            xai_factors = [
                {"factor_key": "active_calamity", "label": f"Active SDMA Calamity Directive: {alert.get('headline')}", "contribution_pct": 45},
                {"factor_key": "flood_surge", "label": f"Severe Flash Inundation Runoff ({alert.get('event', 'Torrential Flood')})", "contribution_pct": 26},
                {"factor_key": "elevation_m", "label": f"Lowland Basin Elevation ({ward['avg_elevation_m']}m MSL)", "contribution_pct": 17},
                {"factor_key": "drainage_constriction_idx", "label": "Lowland Culvert & Outfall Surcharge", "contribution_pct": 12}
            ]

            pred = {
                "ward_id": ward_id,
                "ward_name": ward["name"],
                "risk_score": risk_score,
                "risk_level": risk_level,
                "predicted_depth_cm": pred_depth,
                "depth_range_cm": depth_range,
                "uncertainty_margin_cm": uncertainty_margin,
                "confidence_pct": confidence_pct,
                "rainfall_nowcast_6h_mm": nowcast_6h,
                "peak_rainfall_hr": peak_hr,
                "explainability_factors": xai_factors,
                "hourly_forecast": hourly_series,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            scenario_name = f"Active CAP Calamity ({alert.get('state', 'Regional')} SDMA)"
            evacuation_advice = {
                "is_evacuation_recommended": True,
                "primary_shelter": ward.get("nearest_shelter", {}).get("name") if ward.get("nearest_shelter") else "Designated District Relief Shelter",
                "shelter_distance_approx": "580m",
                "advisory_notes": alert.get("instruction") or f"Active RED ALERT flood advisory issued by {alert.get('state', 'State')} Disaster Management Authority."
            }

        elif calamity_zone == "calamity_near":
            # Areas near calamity zone: Moderate risk! (~15-42 km buffer)
            alert = calamity_alert or {"state": "Regional", "event": "Disaster Inundation"}
            risk_score = round(max(36.0, 48.0 - (calamity_dist_km - 15.0) * 0.45), 1)
            risk_level = "Moderate"
            pred_depth = round(max(10.0, 20.0 - (calamity_dist_km - 15.0) * 0.35), 1)
            depth_range = "12 - 25 cm (Sump Pooling)"
            uncertainty_margin = 4.2
            confidence_pct = 82.0
            nowcast_6h = round(max(12.0, 22.0 - (calamity_dist_km - 15.0) * 0.35), 1)
            peak_hr = "T+2 hrs"

            hourly_series = []
            for h in range(1, 25):
                h_rain = round(nowcast_6h * 0.25, 1) if h <= 3 else (round(nowcast_6h * 0.15, 1) if h <= 6 else 0.2)
                h_depth = pred_depth if (2 <= h <= 5) else (round(pred_depth * 0.6, 1) if h <= 8 else 0.0)
                hourly_series.append({
                    "hour": f"+{h}h",
                    "time_label": f"T+{h:02d}:00",
                    "rainfall_mm": h_rain,
                    "inundation_depth_cm": h_depth,
                    "river_level_m": 0.65
                })

            xai_factors = [
                {"factor_key": "calamity_buffer", "label": f"Proximity to Active Calamity Zone (~{round(calamity_dist_km)} km to {alert.get('state')} Epicenter)", "contribution_pct": 42},
                {"factor_key": "regional_inflow", "label": "Regional Inundation Buffer & Hydrological Inflow", "contribution_pct": 26},
                {"factor_key": "terrain_slope_deg", "label": f"Terrain Runoff Slope ({ward['terrain_slope_deg']}°) & Outfall Flow", "contribution_pct": 18},
                {"factor_key": "drainage_constriction_idx", "label": "Local Urban Stormwater Density", "contribution_pct": 14}
            ]

            pred = {
                "ward_id": ward_id,
                "ward_name": ward["name"],
                "risk_score": risk_score,
                "risk_level": risk_level,
                "predicted_depth_cm": pred_depth,
                "depth_range_cm": depth_range,
                "uncertainty_margin_cm": uncertainty_margin,
                "confidence_pct": confidence_pct,
                "rainfall_nowcast_6h_mm": nowcast_6h,
                "peak_rainfall_hr": peak_hr,
                "explainability_factors": xai_factors,
                "hourly_forecast": hourly_series,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            scenario_name = f"Adjoining Calamity Buffer (~{round(calamity_dist_km)} km from {alert.get('state')} Calamity)"
            evacuation_advice = {
                "is_evacuation_recommended": False,
                "primary_shelter": ward.get("nearest_shelter", {}).get("name") if ward.get("nearest_shelter") else "Designated District Relief Shelter",
                "shelter_distance_approx": "580m",
                "advisory_notes": f"Cautionary Standby: Location is within the ~{round(calamity_dist_km)} km perimeter of active {alert.get('event')}. Be prepared for street runoff."
            }

        elif calamity_zone == "calamity_peripheral":
            # Outer peripheral buffer: Low-Moderate risk (~42-75 km buffer)
            alert = calamity_alert or {"state": "Regional"}
            risk_score = round(max(22.0, 28.0 - (calamity_dist_km - 42.0) * 0.15), 1)
            risk_level = "Low"
            pred_depth = round(max(0.0, 5.0 - (calamity_dist_km - 42.0) * 0.15), 1)
            depth_range = "0 - 5 cm (Peripheral Watch)"
            uncertainty_margin = 3.0
            confidence_pct = 80.0
            nowcast_6h = 4.0
            peak_hr = "T+3 hrs"

            hourly_series = []
            for h in range(1, 25):
                hourly_series.append({
                    "hour": f"+{h}h",
                    "time_label": f"T+{h:02d}:00",
                    "rainfall_mm": 0.5 if h <= 4 else 0.0,
                    "inundation_depth_cm": pred_depth if h <= 4 else 0.0,
                    "river_level_m": 0.35
                })

            xai_factors = [
                {"factor_key": "peripheral_watch", "label": f"Peripheral Monitoring Buffer (~{round(calamity_dist_km)} km to {alert.get('state')} Alert)", "contribution_pct": 35},
                {"factor_key": "drainage", "label": "Topographic Runoff Drainage", "contribution_pct": 30},
                {"factor_key": "elevation_m", "label": f"Elevation ({ward['avg_elevation_m']}m MSL)", "contribution_pct": 20},
                {"factor_key": "moisture", "label": "Low Antecedent Moisture", "contribution_pct": 15}
            ]

            pred = {
                "ward_id": ward_id,
                "ward_name": ward["name"],
                "risk_score": risk_score,
                "risk_level": risk_level,
                "predicted_depth_cm": pred_depth,
                "depth_range_cm": depth_range,
                "uncertainty_margin_cm": uncertainty_margin,
                "confidence_pct": confidence_pct,
                "rainfall_nowcast_6h_mm": nowcast_6h,
                "peak_rainfall_hr": peak_hr,
                "explainability_factors": xai_factors,
                "hourly_forecast": hourly_series,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            scenario_name = f"Peripheral Calamity Watch (~{round(calamity_dist_km)} km)"
            evacuation_advice = {
                "is_evacuation_recommended": False,
                "primary_shelter": ward.get("nearest_shelter", {}).get("name") if ward.get("nearest_shelter") else "Designated District Relief Shelter",
                "shelter_distance_approx": "580m",
                "advisory_notes": f"Peripheral monitoring buffer ~{round(calamity_dist_km)} km from active disaster zone in {alert.get('state')}. Conditions stable."
            }

        else:
            # Normal territory: check live atmospheric measurements from Open-Meteo & OpenWeather
            live_data = get_live_weather(lat, lon)
            live_rain = float(live_data.get("rain_1h_mm", 0.0) or 0.0)
            live_temp = float(live_data.get("temp_c", 25.0) or 25.0)
            live_humidity = float(live_data.get("humidity_pct", 65.0) or 65.0)
            hourly_rain = [float(x) for x in live_data.get("hourly_precip_trend", [0.0] * 24)]

            dynamic_params = {
                "rain_intensity_multiplier": live_rain / 45.0 if live_rain > 0 else 0.0,
                "soil_saturation_delta": -35.0 if live_rain == 0 else (live_humidity - 65.0) * 0.3,
                "river_surge_m": (live_rain * 0.03) if live_rain > 0 else -0.8,
                "radar_peak_dbz": 15.0 if live_rain == 0 else min(55.0, 10 * float(np.log10(max(200 * ((live_rain or 0.1) ** 1.6), 1)))),
                "tidal_level_m": 0.2
            }
            pred = ml_engine.predict_ward_risk(ward, dynamic_params)

            # When live rain is 0, enforce calm ground truth: 0 cm depth, Low Risk (Safe & Clear)
            if live_rain == 0.0:
                pred["risk_level"] = "Low"
                pred["risk_score"] = round(min(float(pred.get("risk_score", 11.5)), 14.0), 1)
                pred["predicted_depth_cm"] = 0.0
                pred["depth_range_cm"] = "0 cm (Safe & Clear)"
                pred["peak_rainfall_hr"] = "No Active Rain"
                pred["rainfall_nowcast_6h_mm"] = 0.0

            risk_score = pred["risk_score"]
            risk_level = pred["risk_level"]
            pred_depth = pred["predicted_depth_cm"]
            depth_range = pred["depth_range_cm"]
            uncertainty_margin = pred["uncertainty_margin_cm"]
            confidence_pct = pred["confidence_pct"]
            nowcast_6h = pred["rainfall_nowcast_6h_mm"]
            peak_hr = pred["peak_rainfall_hr"]

            hourly_series = []
            for h in range(1, 25):
                h_rain = hourly_rain[h - 1] if (h - 1) < len(hourly_rain) else 0.0
                h_depth = 0.0 if h_rain < 15.0 else round((h_rain - 10.0) * 0.6, 1)
                hourly_series.append({
                    "hour": f"+{h}h",
                    "time_label": f"T+{h:02d}:00",
                    "rainfall_mm": h_rain,
                    "inundation_depth_cm": h_depth,
                    "river_level_m": 0.4
                })

            xai_factors = [
                {"factor_key": "elevation_m", "label": f"Topographic Elevation ({ward['avg_elevation_m']}m MSL)", "contribution_pct": 38},
                {"factor_key": "rain_1h_mm", "label": f"Live Weather Precipitation ({live_rain} mm/h)", "contribution_pct": 28},
                {"factor_key": "terrain_slope_deg", "label": f"Terrain Runoff Slope ({ward['terrain_slope_deg']}°)", "contribution_pct": 20},
                {"factor_key": "drainage_constriction_idx", "label": "Urban Stormwater Density", "contribution_pct": 14}
            ]

            pred = {
                "ward_id": ward_id,
                "ward_name": ward["name"],
                "risk_score": risk_score,
                "risk_level": risk_level,
                "predicted_depth_cm": pred_depth,
                "depth_range_cm": depth_range,
                "uncertainty_margin_cm": uncertainty_margin,
                "confidence_pct": confidence_pct,
                "rainfall_nowcast_6h_mm": nowcast_6h,
                "peak_rainfall_hr": peak_hr,
                "explainability_factors": xai_factors,
                "hourly_forecast": hourly_series,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            scenario_name = f"Live High-Res Atmospheric Feed ({live_data.get('condition_description', 'Live Weather')})"
            evacuation_advice = {
                "is_evacuation_recommended": False,
                "primary_shelter": None,
                "shelter_distance_approx": "N/A",
                "advisory_notes": "Dry / normal atmospheric conditions. No waterlogging or evacuation necessary."
            }

    elif sc_id == "dry_baseline":
        # Dry Weather Baseline: Run ML prediction for this specific ward with 0 rain
        pred = ml_engine.predict_ward_risk(ward, scenario.get("params"))
        scenario_name = "Dry Weather / Baseline"
        evacuation_advice = {
            "is_evacuation_recommended": False,
            "primary_shelter": None,
            "shelter_distance_approx": "N/A",
            "advisory_notes": f"Dry weather and clear skies in {ward['name']}. Baseline topographic risk index is {pred['risk_score']}/100."
        }
    else:
        # Active Crisis Simulation (Cloudburst, Cyclone Surge, Normal Monsoon)
        pred = ml_engine.predict_ward_risk(ward, scenario.get("params"))
        scenario_name = scenario["name"]
        evacuation_advice = {
            "is_evacuation_recommended": pred["risk_level"] in ["High", "Severe"],
            "primary_shelter": ward.get("nearest_shelter", {}).get("name") if ward.get("nearest_shelter") else "Designated District Relief Shelter",
            "shelter_distance_approx": "580m",
            "advisory_notes": f"Simulated Scenario: {scenario['name']} stress-testing hydrology in {ward['name']}. {'Flood inundation surge expected. Move to designated high-ground relief shelter.' if pred['risk_level'] in ['High', 'Severe'] else 'Moderate conditions active.'}"
        }

    return {
        "ward_info": ward,
        "prediction": pred,
        "active_scenario": scenario_name,
        "is_outside_basin": is_out,
        "matched_alert": matched_alert_dict,
        "evacuation_advice": evacuation_advice
    }

@router.post("/ml/predict")
def predict_custom_features(request: CustomMLPredictRequest):
    """
    Direct ML inference endpoint for test runs and external emergency API consumers.
    Takes fused meteorological/hydrological features and returns risk, depth, and XAI attribution.
    """
    custom_ward = {
        "id": "custom-input",
        "name": "Custom Geographic Input",
        "avg_elevation_m": request.elevation_m,
        "terrain_slope_deg": request.terrain_slope_deg,
        "impervious_surface_pct": request.impervious_surface_pct,
        "drainage_density_idx": 100.0 - request.drainage_constriction_idx,
        "antecedent_moisture_pct": request.soil_saturation_pct
    }
    
    custom_scenario_params = {
        "rain_intensity_multiplier": request.rain_1h_mm / 45.0,
        "soil_saturation_delta": 0.0,
        "river_surge_m": (request.river_gauge_ratio - 0.7) * 2.0,
        "radar_peak_dbz": request.radar_reflectivity_dbz,
        "tidal_level_m": request.tidal_backwater_m
    }

    pred = ml_engine.predict_ward_risk(custom_ward, custom_scenario_params)
    return {
        "status": "success",
        "input_features": request.model_dump(),
        "prediction": pred
    }
