"""
AquaAlert AI - Forecasts & Risk Zones API Routes
GeoJSON FeatureCollection export, Ward-specific 24-hr hydrological forecasts, and ad-hoc ML inference.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from backend.database import WARDS_DATA
from backend.ml_engine import ml_engine
from backend.ingestion import ingestion_manager

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
def get_risk_zones_geojson():
    """
    Returns GeoJSON FeatureCollection containing all ward polygons
    enriched with real-time ML risk scores, inundation depths, and XAI explainability.
    """
    scenario = ingestion_manager.get_current_scenario()
    features = []

    for ward in WARDS_DATA:
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

import urllib.parse

@router.get("/forecasts/{ward_id}")
def get_ward_forecast(ward_id: str):
    """
    Returns full deep-dive forecast for a specific ward or any arbitrary geographic point.
    """
    ward = next((w for w in WARDS_DATA if w["id"] == ward_id or w["code"].lower() == ward_id.lower()), None)
    
    # If not one of the pre-configured pilot wards, generate on-the-fly virtual ward!
    if not ward:
        # Check if it is a coordinate-based custom location: loc_lat_lon_name
        if ward_id.startswith("loc_"):
            parts = ward_id.split("_", 3)
            try:
                lat = float(parts[1])
                lon = float(parts[2])
                name = urllib.parse.unquote(parts[3]) if len(parts) > 3 else f"Coordinates {lat}, {lon}"
            except Exception:
                lat, lon, name = 19.076, 72.877, "Searched Location"
        else:
            lat, lon, name = 19.076, 72.877, ward_id.replace("-", " ").title()

        # Find nearest pilot ward for demographic / baseline topography proxy
        nearest = None
        min_d = float("inf")
        for w in WARDS_DATA:
            clat, clon = w["center"]
            d = ((lat - clat) ** 2 + (lon - clon) ** 2) ** 0.5
            if d < min_d:
                min_d = d
                nearest = w

        is_out = min_d > 0.22
        ward = {
            "id": ward_id,
            "name": name,
            "code": "HYPERLOCAL" if not is_out else "REGIONAL",
            "zone": nearest["zone"] if nearest and not is_out else "Searched Location Basin",
            "population": nearest["population"] if nearest else 125000,
            "avg_elevation_m": nearest["avg_elevation_m"] if nearest else 10.0,
            "terrain_slope_deg": nearest["terrain_slope_deg"] if nearest else 1.2,
            "impervious_surface_pct": nearest["impervious_surface_pct"] if nearest else 78.0,
            "drainage_density_idx": nearest["drainage_density_idx"] if nearest else 45.0,
            "antecedent_moisture_pct": nearest["antecedent_moisture_pct"] if nearest else 65.0,
            "center": [lat, lon],
            "vulnerable_assets": [
                {"name": f"Main Transit Corridor near {name}", "type": "transit", "lat": lat, "lon": lon, "vulnerability": "Moderate"}
            ] if not is_out else [],
            "nearest_shelter": nearest.get("nearest_shelter") if nearest else {
                "name": "Designated Community Relief Center", "lat": lat + 0.004, "lon": lon + 0.004, "capacity": 500, "occupied": 0
            }
        }

    scenario = ingestion_manager.get_current_scenario()
    pred = ml_engine.predict_ward_risk(ward, scenario.get("params"))

    return {
        "ward_info": ward,
        "prediction": pred,
        "active_scenario": scenario["name"],
        "evacuation_advice": {
            "is_evacuation_recommended": pred["risk_level"] in ["High", "Severe"],
            "primary_shelter": ward.get("nearest_shelter"),
            "shelter_distance_approx": "450 meters",
            "advisory_notes": "Avoid flooded basements and lower elevation corridors. Use marked high-ground pedestrian walkways."
        }
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
