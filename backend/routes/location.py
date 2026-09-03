"""
AquaAlert AI - Location & Geocoding Service
Integrates Mappls (MapmyIndia) Developer REST API with graceful fallback to Nominatim
and local ward spatial matching for Smart India Hackathon 2026.
"""

import os
import requests
from fastapi import APIRouter, Query
from typing import Dict, Any, List, Optional
from backend.database import WARDS_DATA
from backend.ml_engine import ml_engine
from backend.ingestion import ingestion_manager

router = APIRouter(prefix="/api/location", tags=["Location & Geocoding"])

# Mappls Developer API Key (Configurable via environment or default key)
MAPPLS_REST_KEY = os.environ.get("MAPPLS_REST_KEY", "")

@router.get("/search")
def search_location(
    q: str = Query(..., description="Search address, landmark, PIN code, or ward name"),
    limit: int = 5
):
    """
    Hyperlocal search endpoint:
    1. Matches against local high-resolution flood testbed wards & critical assets first.
    2. Calls Mappls / MapmyIndia Geocoding API using the user's static REST key.
    3. Falls back seamlessly to OpenStreetMap Nominatim for all Indian localities.
    4. Automatically calculates hydrological flood risk for the resulting coordinates!
    """
    query = q.strip()
    if not query:
        return {"status": "success", "results": []}

    results = []

    # Step 1: Check if matching local pilot wards or vulnerable assets
    q_lower = query.lower()
    for ward in WARDS_DATA:
        if q_lower in ward["name"].lower() or q_lower in ward["zone"].lower() or q_lower in ward["code"].lower():
            scenario = ingestion_manager.get_current_scenario()
            pred = ml_engine.predict_ward_risk(ward, scenario.get("params"))
            results.append({
                "source": "AquaAlert Ward GIS",
                "title": ward["name"],
                "subtitle": f"{ward['zone']} ({ward['code']}) - Monitored Flood Basin",
                "lat": ward["center"][0],
                "lon": ward["center"][1],
                "ward_id": ward["id"],
                "risk_level": pred["risk_level"],
                "risk_score": pred["risk_score"],
                "predicted_depth_cm": pred["predicted_depth_cm"]
            })

    # Step 2: Query Mappls API with user's key
    mappls_success = False
    if MAPPLS_REST_KEY:
        try:
            mappls_url = f"https://apis.mappls.com/advancedmaps/v1/{MAPPLS_REST_KEY}/geo_code?addr={requests.utils.quote(query)}"
            m_resp = requests.get(mappls_url, timeout=3)
            if m_resp.status_code == 200:
                m_data = m_resp.json()
                items = m_data.get("copResults", []) if isinstance(m_data, dict) else []
                for item in items[:limit]:
                    lat = float(item.get("latitude", 0))
                    lon = float(item.get("longitude", 0))
                    if lat and lon:
                        mappls_success = True
                        nearest_ward = find_nearest_ward(lat, lon)
                        results.append({
                            "source": "Mappls (MapmyIndia)",
                            "title": item.get("formatted_address", query),
                            "subtitle": f"District: {item.get('district', 'India')}",
                            "lat": lat,
                            "lon": lon,
                            "ward_id": nearest_ward["id"] if nearest_ward else None,
                            "risk_level": nearest_ward["risk_level"] if nearest_ward else "Moderate",
                            "risk_score": nearest_ward["risk_score"] if nearest_ward else 45.0,
                            "predicted_depth_cm": nearest_ward["predicted_depth_cm"] if nearest_ward else 20.0
                        })
        except Exception:
            pass

    # Step 3: High-accuracy Nominatim Fallback if needed
    if len(results) < 2:
        try:
            nom_url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(query)}&format=json&countrycodes=in&limit={limit}"
            nom_headers = {"User-Agent": "AquaAlertAI-SIH2026/1.0"}
            nom_resp = requests.get(nom_url, headers=nom_headers, timeout=3)
            if nom_resp.status_code == 200:
                for place in nom_resp.json():
                    lat = float(place.get("lat", 0))
                    lon = float(place.get("lon", 0))
                    if lat and lon:
                        nearest_ward = find_nearest_ward(lat, lon)
                        results.append({
                            "source": "OpenStreetMap",
                            "title": place.get("display_name", "").split(",")[0],
                            "subtitle": ", ".join(place.get("display_name", "").split(",")[1:4]).strip(),
                            "lat": lat,
                            "lon": lon,
                            "ward_id": nearest_ward["id"] if nearest_ward else None,
                            "risk_level": nearest_ward["risk_level"] if nearest_ward else "Moderate",
                            "risk_score": nearest_ward["risk_score"] if nearest_ward else 45.0,
                            "predicted_depth_cm": nearest_ward["predicted_depth_cm"] if nearest_ward else 25.0
                        })
        except Exception:
            pass

    return {
        "status": "success",
        "query": query,
        "mappls_active": bool(MAPPLS_REST_KEY),
        "total_results": len(results),
        "results": results[:limit]
    }

@router.get("/reverse")
def reverse_geocode(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """
    Reverse geocodes GPS coordinates into real user address (e.g. Bengaluru, Karnataka)
    and maps to nearest flood zone or creates an on-the-fly local inspection area.
    """
    place_name = f"Location ({round(lat, 3)}, {round(lon, 3)})"
    city = "India"
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {"User-Agent": "AquaAlertAI-SIH2026/1.0"}
        r = requests.get(url, headers=headers, timeout=2.5)
        if r.status_code == 200:
            addr = r.json().get("address", {})
            city = addr.get("city") or addr.get("town") or addr.get("suburb") or addr.get("state_district") or addr.get("state") or "Local Area"
            road = addr.get("road") or addr.get("suburb") or addr.get("neighbourhood") or ""
            place_name = f"{road}, {city}".strip(", ") if road else city
    except Exception:
        pass

    nearest = find_nearest_ward(lat, lon)
    is_in_mumbai = nearest and nearest.get("id") is not None
    
    loc_id = nearest["id"] if is_in_mumbai else f"loc_{lat}_{lon}_{requests.utils.quote(place_name)}"

    return {
        "status": "success",
        "coordinates": {"lat": lat, "lon": lon},
        "place_name": place_name,
        "city": city,
        "loc_id": loc_id,
        "is_in_pilot_catchment": is_in_mumbai,
        "matched_flood_ward": nearest,
        "advice": f"You are within a monitored Mumbai drainage basin ({nearest['name']})." if is_in_mumbai else f"Monitoring live weather in {city} (Outside Mumbai pilot catchment)."
    }

def find_nearest_ward(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """Calculates closest ward center to coordinates and returns calibrated ML risk."""
    scenario = ingestion_manager.get_current_scenario()
    best_ward = None
    min_dist = float("inf")

    for ward in WARDS_DATA:
        clat, clon = ward["center"]
        dist = ((lat - clat) ** 2 + (lon - clon) ** 2) ** 0.5
        if dist < min_dist:
            min_dist = dist
            best_ward = ward

    if best_ward:
        # If coordinates are outside Mumbai urban basin (> 0.22 degrees, ~24km away):
        if min_dist > 0.22:
            return {
                "id": None,
                "name": "Outside Catchment Area",
                "code": "OUT-BASIN",
                "zone": "Non-Vulnerable Region",
                "distance_degrees": round(min_dist, 4),
                "risk_level": "Low",
                "risk_score": 8.0,
                "predicted_depth_cm": 0.0,
                "nearest_shelter": None
            }

        pred = ml_engine.predict_ward_risk(best_ward, scenario.get("params"))
        return {
            "id": best_ward["id"],
            "name": best_ward["name"],
            "code": best_ward["code"],
            "zone": best_ward["zone"],
            "distance_degrees": round(min_dist, 4),
            "risk_level": pred["risk_level"],
            "risk_score": pred["risk_score"],
            "predicted_depth_cm": pred["predicted_depth_cm"],
            "nearest_shelter": best_ward.get("nearest_shelter")
        }
    return None
