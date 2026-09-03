"""
AquaAlert AI - Sensors Telemetry & Scenario Simulation Routes
Provides real-time telemetry from Automated Weather Stations (AWS),
Doppler Weather Radars (DWR), River & Canal Gauges, and crisis scenario selection.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
from backend.database import SENSOR_STATIONS
from backend.ingestion import ingestion_manager

router = APIRouter(prefix="/api", tags=["Sensors & Telemetry"])

class ScenarioSelectRequest(BaseModel):
    scenario_id: str

@router.get("/sensors")
def get_sensors():
    """
    Returns full sensor telemetry network with readings calibrated
    to the currently active hydrometeorological scenario.
    """
    scenario = ingestion_manager.get_current_scenario()
    params = scenario["params"]
    multiplier = params.get("rain_intensity_multiplier", 1.0)
    surge_m = params.get("river_surge_m", 0.0)

    calibrated_sensors = []
    for s in SENSOR_STATIONS:
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
    """Switches the active simulation scenario across the entire platform."""
    res = ingestion_manager.set_scenario(req.scenario_id)
    return {
        "status": "success",
        "message": f"Active meteorological scenario switched to '{res['name']}'",
        "scenario": res
    }

@router.get("/ingestion/telemetry")
def get_ingestion_layers():
    """Returns live telemetry payloads from Satellite, Radar, and NWP feeds."""
    return {
        "satellite": ingestion_manager.get_satellite_telemetry(),
        "radar": ingestion_manager.get_radar_telemetry(),
        "nwp": ingestion_manager.get_nwp_telemetry()
    }
