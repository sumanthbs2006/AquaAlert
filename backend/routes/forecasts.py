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
from backend.database import WARDS_DATA, generate_regional_wards, estimate_base_elevation
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

    if lat is not None and lon is not None:
        min_d = min(((lat - w["center"][0])**2 + (lon - w["center"][1])**2)**0.5 for w in WARDS_DATA)
        if min_d > 0.22:
            wards = generate_regional_wards(lat, lon, name or "Searched Location")

    features = []
    for ward in wards:
        # Run ML engine prediction for this ward
        pred = ml_engine.predict_ward_risk(ward, scenario.get("params"))

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
            is_lowland = any(w in name_lower for w in ["low", "underpass", "chawl", "slum", "lake", "basin", "river", "canal", "road", "main"])
            is_highland = any(w in name_lower for w in ["hill", "ridge", "high", "heights", "peak", "plateau", "mount"])
            
            p_slope = 3.5 if is_highland else (0.7 if is_lowland else 1.6)
            p_elev = base_elev + (10.0 if is_highland else (-4.0 if is_lowland else 0.0))
            p_imperv = 60.0 if is_highland else (86.0 if is_lowland else 75.0)
            p_drain = 65.0 if is_highland else (32.0 if is_lowland else 48.0)
            
            ward = {
                "id": ward_id,
                "name": name,
                "code": "REGIONAL",
                "zone": "Inspected Region",
                "population": 150000,
                "avg_elevation_m": round(max(3.0, p_elev), 1),
                "terrain_slope_deg": p_slope,
                "impervious_surface_pct": p_imperv,
                "drainage_density_idx": p_drain,
                "antecedent_moisture_pct": 70.0,
                "historical_waterlogging_frequency": "Very High" if is_lowland else ("Low" if is_highland else "Moderate"),
                "center": [lat, lon],
                "vulnerable_assets": [
                    {"name": f"Local Infrastructure near {name.split(',')[0]}", "type": "transit", "lat": lat, "lon": lon, "vulnerability": "Moderate"}
                ],
                "nearest_shelter": {"name": f"{name.split(',')[0]} Municipal Relief Shelter", "lat": round(lat + 0.005, 4), "lon": round(lon + 0.005, 4), "capacity": 750, "occupied": 10}
            }

    scenario = ingestion_manager.get_current_scenario()
    sc_id = scenario.get("id", "live_weather")

    if is_out:
        if sc_id == "live_weather":
            # Real-time atmospheric measurements from OpenWeatherMap (with resilient gateway fallback)
            live_data = get_live_weather(lat, lon)
            live_rain = float(live_data.get("rain_1h_mm", 0.0) or 0.0)
            live_temp = float(live_data.get("temp_c", 25.0) or 25.0)
            live_humidity = float(live_data.get("humidity_pct", 65.0) or 65.0)
            hourly_rain = [float(x) for x in live_data.get("hourly_precip_trend", [0.0] * 24)]

            dynamic_params = {
                "rain_intensity_multiplier": live_rain / 45.0 if live_rain > 0 else 0.0,
                "soil_saturation_delta": (live_humidity - 65.0) * 0.3,
                "river_surge_m": (live_rain * 0.03) if live_rain > 0 else -0.6,
                "radar_peak_dbz": min(55.0, 10 * float(np.log10(max(200 * ((live_rain or 0.1) ** 1.6), 1)))),
                "tidal_level_m": 0.3
            }
            pred = ml_engine.predict_ward_risk(ward, dynamic_params)
            risk_score = pred["risk_score"]
            risk_level = pred["risk_level"]
            pred_depth = pred["predicted_depth_cm"]
            depth_range = pred["depth_range_cm"]
            uncertainty_margin = pred["uncertainty_margin_cm"]
            confidence_pct = pred["confidence_pct"]
            nowcast_6h = round(sum(hourly_rain[:6]), 1) if hourly_rain else 0.0
            peak_hr = "Dry / Normal" if nowcast_6h == 0.0 else "T+2 hrs"

            hourly_series = []
            for h in range(1, 25):
                h_rain = hourly_rain[h - 1] if (h - 1) < len(hourly_rain) else 0.0
                hourly_series.append({
                    "hour": f"+{h}h",
                    "time_label": f"T+{h:02d}:00",
                    "rainfall_mm": h_rain,
                    "inundation_depth_cm": round(pred_depth * (0.8 if h > 6 else 1.0), 1),
                    "river_level_m": 0.4
                })

            xai_factors = pred.get("explainability_factors", [
                {"factor_key": "elevation_m", "label": f"Topographic Elevation ({ward['avg_elevation_m']}m)", "contribution_pct": 35},
                {"factor_key": "terrain_slope_deg", "label": f"Terrain Runoff Slope ({ward['terrain_slope_deg']}°)", "contribution_pct": 30},
                {"factor_key": "rain_1h_mm", "label": f"OpenWeather Live Precipitation ({live_rain} mm/h)", "contribution_pct": 20},
                {"factor_key": "drainage_constriction_idx", "label": "Drainage Outfall Density", "contribution_pct": 15}
            ])

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
            scenario_name = "Live Regional Weather (OpenWeather API)"
            evacuation_advice = {
                "is_evacuation_recommended": pred["risk_level"] in ["High", "Severe"],
                "primary_shelter": ward.get("nearest_shelter", {}).get("name") if ward.get("nearest_shelter") else None,
                "shelter_distance_approx": "580m",
                "advisory_notes": f"Real-time conditions in {ward['name']}. Topographic baseline vulnerability index: {risk_score}/100. Monitored via OpenWeather atmospheric feeds."
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
                "primary_shelter": ward.get("nearest_shelter", {}).get("name") if ward.get("nearest_shelter") else None,
                "shelter_distance_approx": "580m",
                "advisory_notes": f"Simulated Scenario: {scenario['name']} stress-testing hydrology in {ward['name']}. {'Flood inundation surge expected. Move to designated high-ground relief shelter.' if pred['risk_level'] in ['High', 'Severe'] else 'Moderate conditions active.'}"
            }
    else:
        # Monitored Mumbai catchment
        pred = ml_engine.predict_ward_risk(ward, scenario.get("params"))
        scenario_name = scenario["name"]
        evacuation_advice = {
            "is_evacuation_recommended": pred["risk_level"] in ["High", "Severe"],
            "primary_shelter": ward.get("nearest_shelter"),
            "shelter_distance_approx": "450 meters",
            "advisory_notes": "Avoid flooded basements and lower elevation corridors. Use marked high-ground pedestrian walkways."
        }

    return {
        "ward_info": ward,
        "prediction": pred,
        "active_scenario": scenario_name,
        "is_outside_basin": is_out,
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
