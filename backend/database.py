"""
AquaAlert AI - Geospatial Database & Telemetry Store
Provides realistic GeoJSON boundaries, sensor stations, vulnerable assets,
emergency resources, and active alerts for urban flood testbeds (e.g., Mithi River Catchment & Mumbai Metropolitan Basin).
Includes PostGIS migration DDL script for production deployments.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# --- WARDS GEOSPATIAL TESTBED DATA (MITHI RIVER & SURROUNDING BASIN) ---
WARDS_DATA = [
    {
        "id": "ward-L-kurla-w",
        "name": "Kurla West (Mithi River Basin)",
        "code": "L-01",
        "zone": "Eastern Suburbs",
        "area_km2": 4.8,
        "population": 185000,
        "avg_elevation_m": 8.5,
        "terrain_slope_deg": 0.8,  # Very flat, high waterlogging risk
        "impervious_surface_pct": 82,  # Heavy concrete / built-up
        "drainage_density_idx": 38,  # Choked or constrained drainage
        "antecedent_moisture_pct": 88,
        "historical_waterlogging_frequency": "Very High",
        "polygon": [
            [19.062, 72.868],
            [19.075, 72.872],
            [19.082, 72.885],
            [19.078, 72.896],
            [19.065, 72.892],
            [19.058, 72.879],
            [19.062, 72.868]
        ],
        "center": [19.070, 72.882],
        "vulnerable_assets": [
            {"name": "Kurla Railway Station Subway", "type": "transit", "lat": 19.065, "lon": 72.879, "vulnerability": "Severe"},
            {"name": "Bhabha Municipal Hospital Kurla", "type": "hospital", "lat": 19.068, "lon": 72.886, "vulnerability": "High"},
            {"name": "Kranti Nagar Slum Cluster", "type": "settlement", "lat": 19.072, "lon": 72.874, "vulnerability": "Severe"}
        ],
        "nearest_shelter": {"name": "Kurla Urdu Municipal High School", "lat": 19.071, "lon": 72.889, "capacity": 650, "occupied": 45}
    },
    {
        "id": "ward-GN-dharavi",
        "name": "Dharavi - Mahim Creek Estuary",
        "code": "GN-02",
        "zone": "Island City North",
        "area_km2": 3.2,
        "population": 290000,
        "avg_elevation_m": 4.2,  # Low-lying coastal tidal backwater
        "terrain_slope_deg": 0.4,
        "impervious_surface_pct": 92,
        "drainage_density_idx": 30,
        "antecedent_moisture_pct": 94,
        "historical_waterlogging_frequency": "Critical",
        "polygon": [
            [19.038, 72.848],
            [19.048, 72.852],
            [19.055, 72.861],
            [19.049, 72.869],
            [19.039, 72.865],
            [19.034, 72.855],
            [19.038, 72.848]
        ],
        "center": [19.044, 72.859],
        "vulnerable_assets": [
            {"name": "90 Feet Road Transit Corridor", "type": "road", "lat": 19.042, "lon": 72.858, "vulnerability": "Severe"},
            {"name": "Chhotani Road Health Center", "type": "hospital", "lat": 19.046, "lon": 72.854, "vulnerability": "High"},
            {"name": "Kumbharwada Lowland Settlement", "type": "settlement", "lat": 19.040, "lon": 72.862, "vulnerability": "Critical"}
        ],
        "nearest_shelter": {"name": "Mahim Causeway Relief Camp", "lat": 19.047, "lon": 72.845, "capacity": 800, "occupied": 120}
    },
    {
        "id": "ward-HE-bkc-bandra",
        "name": "Bandra-Kurla Complex & Kalina",
        "code": "HE-03",
        "zone": "Western Suburbs South",
        "area_km2": 5.1,
        "population": 120000,
        "avg_elevation_m": 7.0,
        "terrain_slope_deg": 1.1,
        "impervious_surface_pct": 86,
        "drainage_density_idx": 52,
        "antecedent_moisture_pct": 79,
        "historical_waterlogging_frequency": "High",
        "polygon": [
            [19.058, 72.855],
            [19.070, 72.858],
            [19.076, 72.868],
            [19.066, 72.875],
            [19.054, 72.866],
            [19.058, 72.855]
        ],
        "center": [19.063, 72.864],
        "vulnerable_assets": [
            {"name": "BKC Diamond Bourse Underpass", "type": "road", "lat": 19.065, "lon": 72.865, "vulnerability": "High"},
            {"name": "Mumbai University Kalina Campus Lowland", "type": "education", "lat": 19.073, "lon": 72.868, "vulnerability": "Moderate"},
            {"name": "Asian Heart Institute Hospital", "type": "hospital", "lat": 19.061, "lon": 72.862, "vulnerability": "Low"}
        ],
        "nearest_shelter": {"name": "Kalina Municipal Sports Complex", "lat": 19.074, "lon": 72.861, "capacity": 500, "occupied": 10}
    },
    {
        "id": "ward-FN-sion-matunga",
        "name": "Sion Circle & Matunga East",
        "code": "FN-04",
        "zone": "Island City Central",
        "area_km2": 4.0,
        "population": 210000,
        "avg_elevation_m": 5.5,
        "terrain_slope_deg": 0.6,
        "impervious_surface_pct": 89,
        "drainage_density_idx": 41,
        "antecedent_moisture_pct": 85,
        "historical_waterlogging_frequency": "Severe",
        "polygon": [
            [19.030, 72.855],
            [19.043, 72.860],
            [19.046, 72.873],
            [19.035, 72.878],
            [19.025, 72.868],
            [19.030, 72.855]
        ],
        "center": [19.036, 72.866],
        "vulnerable_assets": [
            {"name": "Sion Circle Flyover Junction", "type": "transit", "lat": 19.039, "lon": 72.863, "vulnerability": "Critical"},
            {"name": "Lokmanya Tilak Municipal General Hospital (Sion)", "type": "hospital", "lat": 19.034, "lon": 72.860, "vulnerability": "High"},
            {"name": "Gandhi Market Chronic Waterlogging Spot", "type": "road", "lat": 19.031, "lon": 72.859, "vulnerability": "Critical"}
        ],
        "nearest_shelter": {"name": "Sion Community Kalyan Kendra", "lat": 19.041, "lon": 72.870, "capacity": 600, "occupied": 90}
    },
    {
        "id": "ward-KE-andheri-e",
        "name": "Andheri East & Chakala",
        "code": "KE-05",
        "zone": "Western Suburbs North",
        "area_km2": 6.5,
        "population": 310000,
        "avg_elevation_m": 12.8,
        "terrain_slope_deg": 2.2,
        "impervious_surface_pct": 84,
        "drainage_density_idx": 48,
        "antecedent_moisture_pct": 74,
        "historical_waterlogging_frequency": "Moderate",
        "polygon": [
            [19.108, 72.845],
            [19.125, 72.850],
            [19.130, 72.872],
            [19.112, 72.875],
            [19.102, 72.855],
            [19.108, 72.845]
        ],
        "center": [19.115, 72.860],
        "vulnerable_assets": [
            {"name": "Andheri Subway (Underpass)", "type": "transit", "lat": 19.118, "lon": 72.846, "vulnerability": "Critical"},
            {"name": "Holy Spirit Hospital", "type": "hospital", "lat": 19.124, "lon": 72.862, "vulnerability": "Moderate"},
            {"name": "Western Express Highway Chakala Crossing", "type": "road", "lat": 19.113, "lon": 72.855, "vulnerability": "High"}
        ],
        "nearest_shelter": {"name": "Andheri Sports Complex Relief Wing", "lat": 19.128, "lon": 72.836, "capacity": 900, "occupied": 0}
    },
    {
        "id": "ward-S-bhandup-vikhroli",
        "name": "Vikhroli & Powai Catchment",
        "code": "S-06",
        "zone": "Eastern Suburbs North",
        "area_km2": 7.8,
        "population": 240000,
        "avg_elevation_m": 18.5,  # Higher upstream hilly catchment
        "terrain_slope_deg": 4.5,
        "impervious_surface_pct": 65,
        "drainage_density_idx": 60,
        "antecedent_moisture_pct": 71,
        "historical_waterlogging_frequency": "Low",
        "polygon": [
            [19.115, 72.900],
            [19.135, 72.908],
            [19.140, 72.935],
            [19.118, 72.938],
            [19.108, 72.915],
            [19.115, 72.900]
        ],
        "center": [19.124, 72.918],
        "vulnerable_assets": [
            {"name": "LBS Marg Vikhroli Depot", "type": "road", "lat": 19.112, "lon": 72.920, "vulnerability": "Moderate"},
            {"name": "Godrej Memorial Hospital", "type": "hospital", "lat": 19.105, "lon": 72.926, "vulnerability": "Low"}
        ],
        "nearest_shelter": {"name": "Powai Lake High School Auditorium", "lat": 19.128, "lon": 72.908, "capacity": 550, "occupied": 0}
    },
    {
        "id": "ward-M-chembur-trombay",
        "name": "Chembur East & Govandi",
        "code": "M-07",
        "zone": "Eastern Suburbs South",
        "area_km2": 5.4,
        "population": 275000,
        "avg_elevation_m": 9.2,
        "terrain_slope_deg": 1.4,
        "impervious_surface_pct": 81,
        "drainage_density_idx": 44,
        "antecedent_moisture_pct": 80,
        "historical_waterlogging_frequency": "High",
        "polygon": [
            [19.048, 72.888],
            [19.062, 72.895],
            [19.065, 72.918],
            [19.042, 72.922],
            [19.038, 72.902],
            [19.048, 72.888]
        ],
        "center": [19.052, 72.905],
        "vulnerable_assets": [
            {"name": "Chembur Naka Road Underpass", "type": "road", "lat": 19.058, "lon": 72.898, "vulnerability": "High"},
            {"name": "Shatabdi Hospital Govandi", "type": "hospital", "lat": 19.050, "lon": 72.915, "vulnerability": "High"},
            {"name": "Deonar Lowland Settlement", "type": "settlement", "lat": 19.045, "lon": 72.919, "vulnerability": "Severe"}
        ],
        "nearest_shelter": {"name": "Chembur Gymkhana Relief Ground", "lat": 19.056, "lon": 72.902, "capacity": 700, "occupied": 40}
    },
    {
        "id": "ward-GS-dadar-prabhadevi",
        "name": "Dadar West & Prabhadevi",
        "code": "GS-08",
        "zone": "Island City South",
        "area_km2": 4.1,
        "population": 195000,
        "avg_elevation_m": 6.8,
        "terrain_slope_deg": 1.0,
        "impervious_surface_pct": 88,
        "drainage_density_idx": 55,
        "antecedent_moisture_pct": 77,
        "historical_waterlogging_frequency": "Moderate",
        "polygon": [
            [19.008, 72.825],
            [19.025, 72.830],
            [19.028, 72.845],
            [19.015, 72.848],
            [19.005, 72.838],
            [19.008, 72.825]
        ],
        "center": [19.016, 72.836],
        "vulnerable_assets": [
            {"name": "Hindmata Cinema Junction", "type": "road", "lat": 19.012, "lon": 72.842, "vulnerability": "Severe"},
            {"name": "KEM Hospital Parel (Adjacent)", "type": "hospital", "lat": 19.004, "lon": 72.841, "vulnerability": "Moderate"},
            {"name": "Dadar TT Circle Underpass", "type": "transit", "lat": 19.019, "lon": 72.844, "vulnerability": "High"}
        ],
        "nearest_shelter": {"name": "Shivaji Park Municipal Pavilion", "lat": 19.024, "lon": 72.838, "capacity": 1000, "occupied": 15}
    }
]

# --- SENSOR STATIONS (AWS, RADAR, RIVER GAUGES) ---
SENSOR_STATIONS = [
    # River / Drainage Gauges (CWC & Municipal SCADA)
    {
        "id": "gauge-mithi-01",
        "type": "river_gauge",
        "name": "Mithi River - Kranti Nagar Gauge",
        "code": "CWC-MR-01",
        "lat": 19.073,
        "lon": 72.875,
        "danger_mark_m": 3.8,
        "warning_mark_m": 2.7,
        "current_level_m": 3.45,
        "discharge_cumec": 142.0,
        "status": "warning",  # safe, warning, danger
        "last_updated": "2 mins ago"
    },
    {
        "id": "gauge-mithi-02",
        "type": "river_gauge",
        "name": "Mithi River - CST Road Bridge Gauge",
        "code": "CWC-MR-02",
        "lat": 19.066,
        "lon": 72.871,
        "danger_mark_m": 4.2,
        "warning_mark_m": 3.0,
        "current_level_m": 4.10,
        "discharge_cumec": 210.5,
        "status": "danger",
        "last_updated": "1 min ago"
    },
    {
        "id": "gauge-mahim-creek",
        "type": "river_gauge",
        "name": "Mahim Creek Tidal Outfall Gauge",
        "code": "CWC-MC-03",
        "lat": 19.043,
        "lon": 72.847,
        "danger_mark_m": 4.5,
        "warning_mark_m": 3.5,
        "current_level_m": 4.25,  # Tidal surge compounding river outflow
        "discharge_cumec": 180.0,
        "status": "warning",
        "last_updated": "3 mins ago"
    },
    {
        "id": "gauge-powai-overflow",
        "type": "river_gauge",
        "name": "Powai Lake Weir Outflow Gauge",
        "code": "CWC-PL-04",
        "lat": 19.122,
        "lon": 72.905,
        "danger_mark_m": 3.0,
        "warning_mark_m": 2.2,
        "current_level_m": 2.15,
        "discharge_cumec": 45.0,
        "status": "safe",
        "last_updated": "5 mins ago"
    },
    # National CWC River Gauges across Indian River Basins
    {
        "id": "gauge-ganga-rishikesh",
        "type": "river_gauge",
        "name": "Ganga River - Rishikesh / Haridwar Gauge",
        "code": "CWC-UK-01",
        "lat": 30.086,
        "lon": 78.288,
        "danger_mark_m": 294.0,
        "warning_mark_m": 293.0,
        "current_level_m": 293.45,
        "discharge_cumec": 1820.0,
        "status": "warning",
        "basin": "Upper Ganga Basin",
        "last_updated": "5 mins ago"
    },
    {
        "id": "gauge-ganga-patna",
        "type": "river_gauge",
        "name": "Ganga River - Digha Ghat Gauge (Patna)",
        "code": "CWC-BR-01",
        "lat": 25.642,
        "lon": 85.105,
        "danger_mark_m": 50.45,
        "warning_mark_m": 49.50,
        "current_level_m": 50.15,
        "discharge_cumec": 2450.0,
        "status": "warning",
        "basin": "Middle Ganga Basin",
        "last_updated": "3 mins ago"
    },
    {
        "id": "gauge-hooghly-kolkata",
        "type": "river_gauge",
        "name": "Hooghly River - Garden Reach Gauge (Kolkata)",
        "code": "CWC-WB-01",
        "lat": 22.545,
        "lon": 88.305,
        "danger_mark_m": 6.2,
        "warning_mark_m": 5.4,
        "current_level_m": 5.85,
        "discharge_cumec": 980.0,
        "status": "warning",
        "basin": "Lower Gangetic Delta Basin",
        "last_updated": "4 mins ago"
    },
    {
        "id": "gauge-bengaluru-valley",
        "type": "river_gauge",
        "name": "Vrishabhavathi River Basin Gauge (Bengaluru)",
        "code": "KSNDMC-KA-01",
        "lat": 12.925,
        "lon": 77.535,
        "danger_mark_m": 3.8,
        "warning_mark_m": 2.8,
        "current_level_m": 2.45,
        "discharge_cumec": 65.0,
        "status": "safe",
        "basin": "Cauvery - Vrishabhavathi Valley",
        "last_updated": "2 mins ago"
    },
    {
        "id": "gauge-mahanadi-cuttack",
        "type": "river_gauge",
        "name": "Mahanadi River - Naraj Weir Gauge (Cuttack)",
        "code": "CWC-OD-01",
        "lat": 20.485,
        "lon": 85.765,
        "danger_mark_m": 26.5,
        "warning_mark_m": 25.4,
        "current_level_m": 25.10,
        "discharge_cumec": 3100.0,
        "status": "safe",
        "basin": "Mahanadi Delta Basin",
        "last_updated": "6 mins ago"
    },
    {
        "id": "gauge-yamuna-delhi",
        "type": "river_gauge",
        "name": "Yamuna River - Old Railway Bridge (Delhi)",
        "code": "CWC-DL-01",
        "lat": 28.662,
        "lon": 77.245,
        "danger_mark_m": 205.33,
        "warning_mark_m": 204.50,
        "current_level_m": 204.85,
        "discharge_cumec": 850.0,
        "status": "warning",
        "basin": "Upper Yamuna Basin",
        "last_updated": "1 min ago"
    },
    {
        "id": "gauge-brahmaputra-guwahati",
        "type": "river_gauge",
        "name": "Brahmaputra River - Saraighat Gauge (Guwahati)",
        "code": "CWC-AS-01",
        "lat": 26.172,
        "lon": 91.715,
        "danger_mark_m": 49.68,
        "warning_mark_m": 48.68,
        "current_level_m": 48.20,
        "discharge_cumec": 14200.0,
        "status": "safe",
        "basin": "Brahmaputra Valley Basin",
        "last_updated": "8 mins ago"
    },

    # Automated Weather Stations (AWS)
    {
        "id": "aws-santacruz",
        "type": "aws",
        "name": "IMD Santacruz Observatory (AWS-01)",
        "code": "IMD-AWS-SCZ",
        "lat": 19.088,
        "lon": 72.855,
        "current_rain_mm_hr": 48.5,
        "cum_3hr_rain_mm": 112.0,
        "cum_24hr_rain_mm": 194.0,
        "soil_moisture_pct": 89,
        "temp_c": 26.2,
        "humidity_pct": 96,
        "status": "operational",
        "last_updated": "Just now"
    },
    {
        "id": "aws-kurla",
        "type": "aws",
        "name": "Kurla Municipal Telemetry AWS",
        "code": "MCGM-AWS-KRL",
        "lat": 19.068,
        "lon": 72.880,
        "current_rain_mm_hr": 56.0,
        "cum_3hr_rain_mm": 134.0,
        "cum_24hr_rain_mm": 218.0,
        "soil_moisture_pct": 94,
        "temp_c": 25.8,
        "humidity_pct": 98,
        "status": "operational",
        "last_updated": "Just now"
    },
    {
        "id": "aws-colaba",
        "type": "aws",
        "name": "IMD Colaba Coastal AWS",
        "code": "IMD-AWS-CLB",
        "lat": 18.905,
        "lon": 72.815,
        "current_rain_mm_hr": 24.0,
        "cum_3hr_rain_mm": 62.0,
        "cum_24hr_rain_mm": 98.0,
        "soil_moisture_pct": 76,
        "temp_c": 27.5,
        "humidity_pct": 92,
        "status": "operational",
        "last_updated": "4 mins ago"
    },
    {
        "id": "aws-vikhroli",
        "type": "aws",
        "name": "Eastern Hills Telemetry Station",
        "code": "MCGM-AWS-VKH",
        "lat": 19.110,
        "lon": 72.925,
        "current_rain_mm_hr": 32.5,
        "cum_3hr_rain_mm": 84.0,
        "cum_24hr_rain_mm": 142.0,
        "soil_moisture_pct": 82,
        "temp_c": 26.0,
        "humidity_pct": 95,
        "status": "operational",
        "last_updated": "2 mins ago"
    },
    {
        "id": "aws-dehradun",
        "type": "aws",
        "name": "IMD Dehradun Forest Observatory (AWS)",
        "code": "IMD-AWS-DDN",
        "lat": 30.335,
        "lon": 78.045,
        "current_rain_mm_hr": 35.0,
        "cum_3hr_rain_mm": 88.0,
        "cum_24hr_rain_mm": 145.0,
        "soil_moisture_pct": 92,
        "temp_c": 21.4,
        "humidity_pct": 98,
        "status": "operational",
        "last_updated": "Just now"
    },
    {
        "id": "aws-patna",
        "type": "aws",
        "name": "IMD Patna Airport Observatory (AWS)",
        "code": "IMD-AWS-PAT",
        "lat": 25.591,
        "lon": 85.088,
        "current_rain_mm_hr": 28.5,
        "cum_3hr_rain_mm": 64.0,
        "cum_24hr_rain_mm": 96.0,
        "soil_moisture_pct": 86,
        "temp_c": 27.2,
        "humidity_pct": 94,
        "status": "operational",
        "last_updated": "Just now"
    },
    {
        "id": "aws-kolkata",
        "type": "aws",
        "name": "IMD Alipore Observatory (AWS)",
        "code": "IMD-AWS-CCU",
        "lat": 22.533,
        "lon": 88.324,
        "current_rain_mm_hr": 22.0,
        "cum_3hr_rain_mm": 52.0,
        "cum_24hr_rain_mm": 84.0,
        "soil_moisture_pct": 84,
        "temp_c": 28.6,
        "humidity_pct": 91,
        "status": "operational",
        "last_updated": "Just now"
    },
    {
        "id": "aws-bengaluru",
        "type": "aws",
        "name": "IMD Bengaluru City Observatory (AWS)",
        "code": "IMD-AWS-BLR",
        "lat": 12.972,
        "lon": 77.585,
        "current_rain_mm_hr": 14.0,
        "cum_3hr_rain_mm": 32.0,
        "cum_24hr_rain_mm": 48.0,
        "soil_moisture_pct": 72,
        "temp_c": 25.0,
        "humidity_pct": 82,
        "status": "operational",
        "last_updated": "Just now"
    },
    {
        "id": "aws-delhi",
        "type": "aws",
        "name": "IMD Safdarjung Observatory (AWS)",
        "code": "IMD-AWS-DEL",
        "lat": 28.585,
        "lon": 77.206,
        "current_rain_mm_hr": 18.0,
        "cum_3hr_rain_mm": 42.0,
        "cum_24hr_rain_mm": 68.0,
        "soil_moisture_pct": 75,
        "temp_c": 29.1,
        "humidity_pct": 85,
        "status": "operational",
        "last_updated": "Just now"
    },

    # Doppler Weather Radars (DWR)
    {
        "id": "radar-dwr-colaba",
        "type": "dwr_radar",
        "name": "IMD Mumbai DWR (S-Band Doppler Radar)",
        "code": "DWR-MUMBAI-01",
        "lat": 18.910,
        "lon": 72.820,
        "range_km": 250,
        "max_reflectivity_dbz": 54.5,  # Convective intense rain band
        "echo_top_height_km": 14.2,
        "cloud_motion_deg": 75,  # Moving ENE
        "cloud_speed_kmh": 28,
        "status": "active_sweep",
        "last_updated": "Sweep #148 at 20:00 IST"
    },
    {
        "id": "radar-dwr-veravali",
        "type": "dwr_radar",
        "name": "Veravali X-Band Urban Hydrological Radar",
        "code": "DWR-VERAVALI-X",
        "lat": 19.120,
        "lon": 72.870,
        "range_km": 80,
        "max_reflectivity_dbz": 52.0,
        "echo_top_height_km": 12.8,
        "cloud_motion_deg": 70,
        "cloud_speed_kmh": 26,
        "status": "active_sweep",
        "last_updated": "Sweep #312 at 20:01 IST"
    }
]

# --- EMERGENCY RESOURCES INVENTORY (FOR SDMA / NDRF PRE-POSITIONING) ---
RESOURCE_INVENTORY = [
    {
        "id": "res-pump-01",
        "name": "High-Capacity Dewatering Pump 500 m³/hr (Submersible)",
        "category": "dewatering_pump",
        "total_available": 14,
        "deployed": 8,
        "allocated_wards": ["ward-L-kurla-w", "ward-GN-dharavi", "ward-FN-sion-matunga", "ward-KE-andheri-e"],
        "standby": 6
    },
    {
        "id": "res-boat-02",
        "name": "NDRF Inflatable Rescue Boats (IRBs) with OBM Engine",
        "category": "rescue_boat",
        "total_available": 18,
        "deployed": 10,
        "allocated_wards": ["ward-L-kurla-w", "ward-GN-dharavi"],
        "standby": 8
    },
    {
        "id": "res-amb-03",
        "name": "ALS 4x4 Flood Ambulances (High Ground Clearance)",
        "category": "ambulance",
        "total_available": 25,
        "deployed": 16,
        "allocated_wards": ["ward-L-kurla-w", "ward-GN-dharavi", "ward-FN-sion-matunga", "ward-M-chembur-trombay"],
        "standby": 9
    },
    {
        "id": "res-shelter-04",
        "name": "Activated Community Relief Shelters",
        "category": "shelter",
        "total_available": 12,
        "deployed": 8,
        "total_bed_capacity": 5200,
        "current_occupancy": 325,
        "standby": 4
    },
    {
        "id": "res-sandbags-05",
        "name": "Pre-filled Heavy Sandbag Bunds (50kg units)",
        "category": "flood_barrier",
        "total_available": 20000,
        "deployed": 12500,
        "allocated_wards": ["ward-L-kurla-w", "ward-GN-dharavi", "ward-GS-dadar-prabhadevi"],
        "standby": 7500
    }
]
# --- COMMON ALERTING PROTOCOL (CAP v1.2) LIVE ACTIVE ALERTS ACROSS INDIA ---
ACTIVE_ALERTS = [
    {
        "id": "ALERT-LIVE-UK-001",
        "alias_id": "ALERT-20260901-001",
        "identifier": "IN-UK-USDMA-2026-AQ-001",
        "state": "Uttarakhand",
        "lat": 30.12,
        "lon": 78.30,
        "sender": "seoc-usdma@uk.gov.in",
        "sent": "2026-09-26T14:45:00+05:30",
        "status": "Actual",
        "msgType": "Alert",
        "scope": "Public",
        "category": "Met",
        "event": "Heavy Rainfall & Foothill Torrent Inundation Advisory",
        "urgency": "Immediate",
        "severity": "Severe",
        "certainty": "Observed",
        "headline": "RED ALERT: Heavy Rainfall & Riverine Runoff along Dehradun-Rishikesh Foothills & Song River Basin",
        "description": "Continuous precipitation (IMD Code 63, 43.1 mm 24h forecast, current rate 1.1 mm/h). Song and Bindal torrents experiencing rapid runoff. Potential culvert choking and water accumulation across Sahastradhara, Tapkeshwar, and Rishikesh foothill corridors.",
        "instruction": "Residents in low-lying valley pockets and near seasonal streams should relocate to designated multi-purpose cyclone/flood shelters. Avoid navigating NH-7 foothill stretches and low bridges during active downpours. Dial 112 / 1070 for State Disaster Helpline.",
        "areaDesc": "Dehradun Valley, Sahastradhara Lowlands, Rishikesh Foothill Drainage Basin, and Tapkeshwar Riverbanks",
        "affected_wards": ["ward-L-kurla-w", "ward-GN-dharavi", "zone-dehradun-foothills"],
        "affected_roads": ["NH-7 (Rishikesh - Badrinath Corridor)", "Sahastradhara Bypass Road", "Rajpur Road Foothill Stretches"],
        "rainfall_time_window": "0–6 hrs: 25–40 mm nowcast (Current rate 1.1 mm/h, 43.1 mm 24h accumulated)",
        "inundation_time_window": "2–12 hrs (Peak runoff depth 40–65 cm along culverts)",
        "is_verified_by_authority": True,
        "verified_by": "Shri V. P. Semwal (Director, State Emergency Operations Centre, USDMA Uttarakhand & IMD Dehradun)",
        "translations": {
            "en": {
                "headline": "RED ALERT: Heavy Rainfall & Riverine Runoff along Dehradun-Rishikesh Foothills & Song River Basin",
                "instruction": "Residents along foothill streams should avoid crossing swollen drainage nullahs. Stay away from unpaved riverbanks along NH-7. Keep emergency essentials ready.",
                "sms": "AquaAlert RED WARNING: Heavy rainfall active in Dehradun & foothill streams (43mm 24h). Avoid riverbanks & low bridges. Dial 112 / 1070 for USDMA emergency rescue."
            },
            "hi": {
                "headline": "लाल चेतावनी: देहरादून-ऋषिकेश तलहटी और सोंग नदी बेसिन में भारी बारिश और जलप्रवाह का खतरा",
                "instruction": "नदी किनारों और निचले इलाकों के निवासी सतर्क रहें। NH-7 और जलमग्न पुलियों से गुजरने से बचें। राज्य आपातकालीन नंबर 112 या 1070 पर संपर्क करें।",
                "sms": "एक्वाअलर्ट लाल चेतावनी: देहरादून और सोंग नदी क्षेत्र में भारी बारिश (43 मिमी/24 घंटे)। नदी किनारों से दूर रहें। राज्य आपदा हेल्पलाइन: 112 / 1070."
            },
            "kn": {
                "headline": "ತೀವ್ರ ಕೆಂಪು ಎಚ್ಚರಿಕೆ (ರೆಡ್ ಅಲರ್ಟ್): ಡೆಹ್ರಾಡೂನ್-ಋಷಿಕೇಶ ತಪ್ಪಲು ಮತ್ತು ಸೋಂಗ್ ನದಿ ಕಣಿವೆಯಲ್ಲಿ ಭಾರೀ ಮಳೆ ಹಾಗೂ ಪ್ರವಾಹ ಭೀತಿ",
                "instruction": "ತಪ್ಪಲು ಮತ್ತು ನದಿ ತೀರದ ನಿವಾಸಿಗಳು ತಕ್ಷಣ ಎಚ್ಚರಿಕೆ ವಹಿಸಬೇಕು. NH-7 ಹೆದ್ದಾರಿಯ ಮುಳುಗಡೆ ಪ್ರದೇಶಗಳು ಮತ್ತು ಸೇತುವೆಗಳಿಂದ ದೂರವಿರಿ. ತುರ್ತು ಸಹಾಯಕ್ಕಾಗಿ 112 / 1070 ಗೆ ಕರೆ ಮಾಡಿ.",
                "sms": "AquaAlert ರೆಡ್ ಅಲರ್ಟ್: ಡೆಹ್ರಾಡೂನ್ ಮತ್ತು ಸುತ್ತಮುತ್ತಲಿನ ಕಣಿವೆಗಳಲ್ಲಿ ಭಾರೀ ಮಳೆ (43 ಮಿ.ಮೀ/24 ಗಂ). ನದಿ ದಂಡೆಗಳಿಂದ ದೂರವಿರಿ. ತುರ್ತು ರಕ್ಷಣೆಗೆ 112 / 1070 ಗೆ ಕರೆ ಮಾಡಿ."
            }
        }
    },
    {
        "id": "ALERT-LIVE-BR-002",
        "alias_id": "ALERT-20260901-002",
        "identifier": "IN-BR-BSDMA-2026-AQ-002",
        "state": "Bihar",
        "lat": 25.61,
        "lon": 85.14,
        "sender": "controlroom@bsdma.org",
        "sent": "2026-09-26T14:55:00+05:30",
        "status": "Actual",
        "msgType": "Alert",
        "scope": "Public",
        "category": "Met",
        "event": "Severe Convective Thunderstorm, Lightning & Urban Waterlogging Nowcast",
        "urgency": "Expected",
        "severity": "High",
        "certainty": "Likely",
        "headline": "ORANGE ALERT: Intense Thunderstorm, Lightning Strikes & Urban Waterlogging across Patna & Central Gangetic Basin",
        "description": "Severe convective storm cells active (IMD Weather Code 96, 25.6 mm 24h rainfall, current rate 0.8 mm/h). Strong cloud-to-ground lightning discharge accompanied by short-duration intense precipitation causing surface waterlogging.",
        "instruction": "Stay strictly indoors during lightning and gusty winds. Avoid open fields, metallic structures, and electrical transformers. Municipal drainage suction units engaged at Bailey Road and Rajendra Nagar sumps.",
        "areaDesc": "Patna Urban Lowlands, Rajendra Nagar, Kankarbagh, and Central Gangetic Floodplains",
        "affected_wards": ["ward-FN-sion-matunga", "zone-patna-central"],
        "affected_roads": ["Bailey Road Sag-Point Underpass", "Ashok Rajpath Riverfront Arterial", "Patna Junction Approach Corridor"],
        "rainfall_time_window": "0–6 hrs: 20–35 mm localized convective bursts (Thunderstorm Code 96, 25.6 mm 24h forecast)",
        "inundation_time_window": "1–6 hrs (Temporary street waterlogging 30–50 cm in sump basins)",
        "is_verified_by_authority": True,
        "verified_by": "Dr. Anil K. Sinha (Disaster Management Authority Officer, BSDMA Bihar & IMD Patna)",
        "translations": {
            "en": {
                "headline": "ORANGE ALERT: Intense Thunderstorm, Lightning Strikes & Urban Waterlogging across Patna & Central Gangetic Basin",
                "instruction": "Stay indoors during thunderstorm activity. Avoid sheltering under trees or metal structures. Do not drive through submerged underpasses like Bailey Road sag points.",
                "sms": "AquaAlert ORANGE: Severe thunderstorm & lightning active across Patna/Gangetic basin (25.6mm rain). Take shelter immediately. BSDMA Helpline: 1070 / 112."
            },
            "hi": {
                "headline": "ऑरेंज अलर्ट: पटना और मध्य गंगा बेसिन में तीव्र गरज-चमक, आकाशीय बिजली और जलभराव की चेतावनी",
                "instruction": "तेज आंधी-तूफान के दौरान घरों के अंदर रहें। पेड़ों और बिजली के खंभों के नीचे शरण न लें। बेली रोड और जलमग्न अंडरपास से वाहन न निकालें।",
                "sms": "एक्वाअलर्ट ऑरेंज: पटना और गंगा तटवर्ती इलाकों में आकाशीय बिजली व भारी बारिश का अलर्ट। खुले में न रहें। आपदा प्रबंधन हेल्पलाइन: 1070 / 112."
            },
            "kn": {
                "headline": "ಕಿತ್ತಳೆ ಎಚ್ಚರಿಕೆ (ಆರೆಂಜ್ ಅಲರ್ಟ್): ಪಾಟ್ನಾ ಮತ್ತು ಗಂಗಾ ಬಯಲಿನಲ್ಲಿ ತೀವ್ರ ಗುಡುಗು-ಮಿಂಚು ಹಾಗೂ ಜಲಾವೃತ ಭೀತಿ",
                "instruction": "ಗುಡುಗು-ಮಿಂಚಿನ ಸಮಯದಲ್ಲಿ ಮನೆಯೊಳಗೇ ಇರಿ. ಮರಗಳು ಅಥವಾ ವಿದ್ಯುತ್ ಕಂಬಗಳ ಕೆಳಗೆ ನಿಲ್ಲಬೇಡಿ. ಮುಳುಗಿದ ಸಬ್‌ವೇಗಳಲ್ಲಿ ವಾಹನ ಚಾಲನೆ ಮಾಡಬೇಡಿ.",
                "sms": "AquaAlert ಆರೆಂಜ್ ಅಲರ್ಟ್: ಪಾಟ್ನಾ ಮತ್ತು ಸುತ್ತಮುತ್ತಲಿನ ಪ್ರದೇಶಗಳಲ್ಲಿ ತೀವ್ರ ಗುಡುಗು ಮಿಂಚು ಸಹಿತ ಮಳೆ. ಜಾಗರೂಕರಾಗಿರಿ. ಸಹಾಯವಾಣಿ: 1070 / 112."
            }
        }
    },
    {
        "id": "ALERT-LIVE-WB-003",
        "alias_id": "ALERT-20260901-003",
        "identifier": "IN-WB-SDMA-2026-AQ-003",
        "state": "West Bengal",
        "lat": 22.57,
        "lon": 88.36,
        "sender": "wbeoc@wb.gov.in",
        "sent": "2026-09-26T15:05:00+05:30",
        "status": "Actual",
        "msgType": "Alert",
        "scope": "Public",
        "category": "Met",
        "event": "Convective Thunderstorm, Squally Winds & Urban Waterlogging Advisory",
        "urgency": "Expected",
        "severity": "High",
        "certainty": "Likely",
        "headline": "ORANGE ALERT: Convective Thunderstorm, Squally Winds & Traffic Disruption in Kolkata Metropolitan Area",
        "description": "Active squall line from North Bay of Bengal (IMD Weather Code 95, 12.8 mm 24h precipitation). Heavy gusty winds (45-55 km/h) and localized waterlogging along arterial corridors.",
        "instruction": "Commuters should avoid low-lying underpasses on EM Bypass. Secure loose rooftop objects. Lock gates at canal outfalls to prevent tidal backflow.",
        "areaDesc": "Kolkata Core, Salt Lake Sector V, Chingrighata Basin, and South 24 Parganas Lowlands",
        "affected_wards": ["ward-KE-andheri-e", "zone-kolkata-delta"],
        "affected_roads": ["EM Bypass (Chingrighata Underpass)", "VIP Road Airport Stretch", "Park Circus 7-Point Crossing"],
        "rainfall_time_window": "0–6 hrs: 15–25 mm sharp convective downpours (Code 95 Thunderstorm, 12.8 mm 24h forecast)",
        "inundation_time_window": "2–8 hrs (Canal backflow & street submergence 25–40 cm)",
        "is_verified_by_authority": True,
        "verified_by": "Smt. M. Ghosh (Executive Director, Disaster Management Department, Govt of West Bengal)",
        "translations": {
            "en": {
                "headline": "ORANGE ALERT: Convective Thunderstorm, Squally Winds & Traffic Disruption in Kolkata Metropolitan Area",
                "instruction": "Expect gusty winds (40-50 km/h) and rapid street waterlogging along EM Bypass and low-lying transit corridors. High-capacity dewatering pumps deployed at pumping stations.",
                "sms": "AquaAlert ORANGE: Convective storm with gusty winds impacting Kolkata & Delta next 2-4 hrs. Avoid waterlogged arterial roads. WB Disaster Helpline: 1070."
            },
            "hi": {
                "headline": "ऑरेंज अलर्ट: कोलकाता महानगर क्षेत्र में गरज-चमक के साथ आंधी, बारिश और जलभराव का अलर्ट",
                "instruction": "ईएम बाईपास और निचले इलाकों में 40-50 किमी/घंटे की रफ्तार से तेज हवाएं और जलभराव संभव। अनावश्यक यात्रा से बचें। नगर निगम पंप सक्रिय हैं।",
                "sms": "एक्वाअलर्ट ऑरेंज: कोलकाता में तेज आंधी और बारिश (12.8 मिमी)। जलमग्न सड़कों से बचें। राज्य आपदा हेल्पलाइन: 1070 / 112."
            },
            "kn": {
                "headline": "ಕಿತ್ತಳೆ ಎಚ್ಚರಿಕೆ (ಆರೆಂಜ್ ಅಲರ್ಟ್): ಕೋಲ್ಕತ್ತಾ ಮಹಾನಗರದಲ್ಲಿ ತೀವ್ರ ಬಿರುಗಾಳಿ ಸಹಿತ ಗುಡುಗು ಮಳೆ ಹಾಗೂ ಸಂಚಾರ ವ್ಯತ್ಯಯ",
                "instruction": "ಗಂಟೆಗೆ 40-50 ಕಿ.ಮೀ ವೇಗದ ಬಿರುಗಾಳಿ ಮತ್ತು ಇ.ಎಂ ಬೈಪಾಸ್ ರಸ್ತೆಗಳಲ್ಲಿ ನೀರು ನಿಲ್ಲುವ ಸಾಧ್ಯತೆ. ನಾಗರಿಕರು ಜಾಗರೂಕರಾಗಿರಲು ಮತ್ತು ಜಲಾವೃತ ರಸ್ತೆಗಳನ್ನು ತಪ್ಪಿಸಲು ಸೂಚಿಸಲಾಗಿದೆ.",
                "sms": "AquaAlert ಆರೆಂಜ್: ಕೋಲ್ಕತ್ತಾ ಮತ್ತು ಕರಾವಳಿ ಡೆಲ್ಟಾದಲ್ಲಿ ಬಿರುಗಾಳಿ ಸಹಿತ ಮಳೆ. ಜಾಗರೂಕರಾಗಿರಿ. ಸಹಾಯವಾಣಿ: 1070."
            }
        }
    },
    {
        "id": "ALERT-LIVE-KA-004",
        "identifier": "IN-KA-KSDMA-2026-AQ-004",
        "state": "Karnataka",
        "lat": 12.97,
        "lon": 77.59,
        "sender": "ksndmc-alert@karnataka.gov.in",
        "sent": "2026-09-26T15:15:00+05:30",
        "status": "Actual",
        "msgType": "Alert",
        "scope": "Public",
        "category": "Met",
        "event": "Urban Drainage Congestion & Underpass Precautionary Watch",
        "urgency": "Future",
        "severity": "Moderate",
        "certainty": "Possible",
        "headline": "YELLOW ADVISORY: Afternoon Convective Cloud Build-up & Lowland Underpass Watch across Bengaluru Urban",
        "description": "Afternoon thermal convective clouds developing over South Interior Karnataka (28.2°C, 68% relative humidity, Weather Code 3). Potential short-lived localized showers capable of ponding in low-lying railway underpasses and valley sections.",
        "instruction": "BBMP emergency rapid response teams on standby. Commuters on Outer Ring Road (ORR), Silk Board, and Hebbal underpass advised to exercise caution during evening commute. Report clogged grates to BBMP Sahaya (1533).",
        "areaDesc": "Bengaluru Urban Basin (Mahadevapura, Bellandur, Silk Board, and Hebbal Lake Valleys)",
        "affected_wards": ["ward-S-bhandup-vikhroli", "zone-bengaluru-valley"],
        "affected_roads": ["Bellandur - Marathahalli Outer Ring Road (ORR)", "Silk Board Junction Basin", "Hebbal Flyover Grade-Separators"],
        "rainfall_time_window": "0–6 hrs: 5–15 mm localized convective showers (Afternoon Cloud Cover, 28.2°C)",
        "inundation_time_window": "4–12 hrs (Sump pooling 15–25 cm in low-lying valley underpasses)",
        "is_verified_by_authority": True,
        "verified_by": "Shri Ramesh K. (Senior Hydrometeorological Analyst, KSNDMC & BBMP Stormwater Management Cell)",
        "translations": {
            "en": {
                "headline": "YELLOW ADVISORY: Afternoon Convective Cloud Build-up & Lowland Underpass Watch across Bengaluru Urban",
                "instruction": "BBMP emergency rapid response teams on standby. Commuters on Outer Ring Road (ORR) and Silk Board advise caution around underpass dips during localized shower bursts.",
                "sms": "AquaAlert YELLOW: Afternoon convective cloud watch in Bengaluru Urban. Sump pooling possible at major underpasses. BBMP Helpline: 1533 / 112."
            },
            "hi": {
                "headline": "येलो एडवाइजरी: बेंगलुरु शहरी क्षेत्र में दोपहर की बादलों की सक्रियता और अंडरपास जलभराव निगरानी",
                "instruction": "बीबीएमपी आपातकालीन टीमें अलर्ट पर हैं। आउटर रिंग रोड (ओआरआर) और सिल्क बोर्ड अंडरपास से गुजरते समय सावधानी बरतें।",
                "sms": "एक्वाअलर्ट येलो: बेंगलुरु में गरज वाले बादलों की सक्रियता। निचले अंडरपासों में धीमी गति से वाहन चलाएं। बीबीएमपी हेल्पलाइन: 1533 / 112."
            },
            "kn": {
                "headline": "ಹಳದಿ ಎಚ್ಚರಿಕೆ (ಯೆಲ್ಲೋ ವಾಚ್): ಬೆಂಗಳೂರು ನಗರ ವ್ಯಾಪ್ತಿಯಲ್ಲಿ ಮಧ್ಯಾಹ್ನದ ಮೋಡ ಕವಿದ ವಾತಾವರಣ ಮತ್ತು ಸಬ್‌ವೇ ನಿಗಾ",
                "instruction": "ಬಿಬಿಎಂಪಿ ತುರ್ತು ಸ್ಪಂದನಾ ತಂಡಗಳು ಸನ್ನದ್ಧವಾಗಿವೆ. ಹೊರ ವರ್ತುಲ ರಸ್ತೆ (ORR) ಮತ್ತು ಸಿಲ್ಕ್ ಬೋರ್ಡ್ ಜಂಕ್ಷನ್ ವ್ಯಾಪ್ತಿಯಲ್ಲಿ ವಾಹನ ಸವಾರರು ಎಚ್ಚರಿಕೆಯಿಂದ ಸಂಚರಿಸಲು ಕೋರಲಾಗಿದೆ.",
                "sms": "AquaAlert ಯೆಲ್ಲೋ ವಾಚ್: ಬೆಂಗಳೂರಿನ ತಗ್ಗು ಪ್ರದೇಶಗಳು ಮತ್ತು ಅಂಡರ್‌ಪಾಸ್‌ಗಳಲ್ಲಿ ನೀರು ನಿಲ್ಲುವ ಸಾಧ್ಯತೆ. ಜಾಗರೂಕರಾಗಿರಿ. ಬಿಬಿಎಂಪಿ ಸಹಾಯವಾಣಿ: 1533 / 112."
            }
        }
    },
    {
        "id": "ALERT-LIVE-OD-005",
        "identifier": "IN-OD-OSDMA-2026-AQ-005",
        "state": "Odisha",
        "lat": 20.30,
        "lon": 85.82,
        "sender": "eoc-osdma@odisha.gov.in",
        "sent": "2026-09-26T15:20:00+05:30",
        "status": "Actual",
        "msgType": "Alert",
        "scope": "Public",
        "category": "Met",
        "event": "Coastal Moisture Convergence & Scattered Shower Advisory",
        "urgency": "Future",
        "severity": "Moderate",
        "certainty": "Possible",
        "headline": "YELLOW ADVISORY: Coastal Moisture Incursion & Scattered Heavy Spells across Bhubaneswar-Cuttack Delta",
        "description": "Low-level easterly wind convergence from the Bay of Bengal bringing intermittent rain spells (30.6°C, 5.3 mm 24h rain). Drainage outfalls in Daya and Kuakhai river systems operating within nominal buffer limits.",
        "instruction": "Maintain normal traffic movement along NH-16. Suction tankers stationed at low-lying crossings near Vani Vihar and Rasulgarh. Avoid water stagnation near building foundations.",
        "areaDesc": "Bhubaneswar Smart City Lowlands, Rasulgarh Junction, and Mahanadi Southern Spillway",
        "affected_wards": ["ward-M-chembur-trombay", "zone-odisha-coastal"],
        "affected_roads": ["NH-16 (Khandagiri - Vani Vihar Urban Stretch)", "Puri-Bhubaneswar Expressway Low-Lying Stretches"],
        "rainfall_time_window": "0–6 hrs: 8–18 mm intermittent rain spells (30.6°C, Bay of Bengal Moisture)",
        "inundation_time_window": "6–18 hrs (Surface pooling 10–20 cm)",
        "is_verified_by_authority": True,
        "verified_by": "Dr. P. K. Mohapatra (General Manager, Odisha State Disaster Management Authority - OSDMA)",
        "translations": {
            "en": {
                "headline": "YELLOW ADVISORY: Coastal Moisture Incursion & Scattered Heavy Spells across Bhubaneswar-Cuttack Delta",
                "instruction": "Monitored coastal flow from North Bay of Bengal. Lowland transit points along NH-16 to maintain normal flow with municipal suction pumps deployed.",
                "sms": "AquaAlert YELLOW: Coastal rain spells likely across Bhubaneswar-Cuttack corridor. Drive cautiously. OSDMA Helpline: 1070 / 112."
            },
            "hi": {
                "headline": "येलो एडवाइजरी: भुवनेश्वर-कटक डेल्टा क्षेत्र में तटीय नमी और छिटपुट बारिश का अलर्ट",
                "instruction": "बंगाल की खाड़ी से आ रही नमी के कारण छिटपुट बारिश की संभावना। एनएच-16 पर वाहन सावधानी से चलाएं।",
                "sms": "एक्वाअलर्ट येलो: भुवनेश्वर-कटक में बारिश की संभावना। यात्रा के दौरान सतर्क रहें। ओडिशा आपदा हेल्पलाइन: 1070."
            },
            "kn": {
                "headline": "ಹಳದಿ ಎಚ್ಚರಿಕೆ (ಯೆಲ್ಲೋ ವಾಚ್): ಭುವನೇಶ್ವರ-ಕಟಕ್ ಕರಾವಳಿ ಪ್ರದೇಶದಲ್ಲಿ ಮಳೆ ಹಾಗೂ ತೇವಾಂಶ ಸಾಂದ್ರತೆ ನಿಗಾ",
                "instruction": "ಬಂಗಾಳಕೊಲ್ಲಿಯ ತೇವಾಂಶದಿಂದ ಸಾಧಾರಣ ಮಳೆಯಾಗುವ ಮುನ್ಸೂಚನೆ. NH-16 ಹೆದ್ದಾರಿಯಲ್ಲಿ ಚಾಲಕರು ಎಚ್ಚರಿಕೆ ವಹಿಸಲು ಸೂಚಿಸಲಾಗಿದೆ.",
                "sms": "AquaAlert ಯೆಲ್ಲೋ: ಭುವನೇಶ್ವರ-ಕಟಕ್ ಮಾರ್ಗದಲ್ಲಿ ಮಳೆಯಾಗುವ ಸಾಧ್ಯತೆ. ಸುರಕ್ಷಿತವಾಗಿ ಸಂಚರಿಸಿ. ಸಹಾಯವಾಣಿ: 1070."
            }
        }
    },
    {
        "id": "ALERT-LIVE-MH-006",
        "identifier": "IN-MH-MCGM-2026-AQ-006",
        "state": "Maharashtra",
        "lat": 19.076,
        "lon": 72.877,
        "sender": "mcgm-sdma-aquaalert@gov.in",
        "sent": "2026-09-26T15:25:00+05:30",
        "status": "Actual",
        "msgType": "Alert",
        "scope": "Public",
        "category": "Met",
        "event": "Monsoon Transition Hydrological Watch & River Stage Baseline",
        "urgency": "Future",
        "severity": "Moderate",
        "certainty": "Observed",
        "headline": "YELLOW WATCH: Controlled Drainage Baseline & Coastal Breeze Monitoring across Mumbai Metropolitan Basin",
        "description": "Live coastal radar and weather telemetry show light intermittent coastal drizzle (29.5°C, 0.1 mm/h, Weather Code 51). Mithi River level holding at 1.15m (completely safe, well below warning mark of 2.70m). Drainage sluice gates functioning normally.",
        "instruction": "Normal civic operations across Mumbai. Subways (Andheri, Milan, Khar) open to all traffic. Pumping stations in standby readiness for incoming tidal phases.",
        "areaDesc": "Mumbai Island City & Suburbs (Kurla, Dadar, Andheri, and Mithi River Estuary)",
        "affected_roads": ["LBS Marg (Normal Flow)", "Hindmata Flyover Corridor", "Milan Subway (Pumps on Standby)"],
        "affected_wards": ["ward-GS-dadar-prabhadevi", "zone-mumbai-basin"],
        "rainfall_time_window": "0–6 hrs: 0–3 mm light coastal drizzle (Normal Drainage Flow, 29.5°C)",
        "inundation_time_window": "Normal river stages (Mithi 1.15m, Safe Baseline below 2.7m warning)",
        "is_verified_by_authority": True,
        "verified_by": "Dr. R. K. Sharma (Deputy Municipal Commissioner, MCGM Disaster Management Cell)",
        "translations": {
            "en": {
                "headline": "YELLOW WATCH: Controlled Drainage Baseline & Coastal Breeze Monitoring across Mumbai Metropolitan Basin",
                "instruction": "All major river stages (Mithi, Poisar, Dahisar) currently in safe normal bands. Stormwater pumping stations on standard operational standby.",
                "sms": "AquaAlert ADVISORY: Normal drainage flow across Mumbai. Mithi river level 1.15m (Safe). MCGM Control Room: 1916 / 112."
            },
            "hi": {
                "headline": "येलो निगरानी: मुंबई महानगर क्षेत्र में नियंत्रित जल निकासी और सामान्य नदी जलस्तर निगरानी",
                "instruction": "मीठी नदी का जलस्तर 1.15 मीटर (सामान्य और सुरक्षित) है। सभी पंपिंग स्टेशन अलर्ट मोड पर हैं। स्थिति पूरी तरह सामान्य है।",
                "sms": "एक्वाअलर्ट सूचना: मुंबई में सामान्य जल निकासी और सुरक्षित स्थिति। मीठी नदी सामान्य स्तर पर। आपातकालीन संपर्क: 1916 / 112."
            },
            "kn": {
                "headline": "ಹಳದಿ ನಿಗಾ (ಯೆಲ್ಲೋ ವಾಚ್): ಮುಂಬೈ ಮಹಾನಗರ ಕಣಿವೆಯಲ್ಲಿ ಸುರಕ್ಷಿತ ನದಿ ಹರಿವು ಹಾಗೂ ಕರಾವಳಿ ಹವಾಮಾನ ನಿಗಾ",
                "instruction": "ಮಿಥಿ ನದಿಯ ನೀರಿನ ಮಟ್ಟ 1.15 ಮೀಟರ್ ಇದ್ದು ಸಂಪೂರ್ಣ ಸುರಕ್ಷಿತ ಮಟ್ಟದಲ್ಲಿದೆ. ಪಂಪಿಂಗ್ ಸ್ಟೇಷನ್‌ಗಳು ಸನ್ನದ್ಧ ಸ್ಥಿತಿಯಲ್ಲಿವೆ.",
                "sms": "AquaAlert ಮಾಹಿತಿ: ಮುಂಬೈ ಕರಾವಳಿಯಲ್ಲಿ ಸ್ಥಿತಿ ಸಹಜ ಮತ್ತು ಸುರಕ್ಷಿತವಾಗಿದೆ. ಮಿಥಿ ನದಿ ಮಟ್ಟ ಸುರಕ್ಷಿತ. ಸಹಾಯವಾಣಿ: 1916 / 112."
            }
        }
    }
]

def get_active_alert_for_location(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    name: str = "",
    ward_id: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Identifies if a geographic location (lat, lon) or ward identifier belongs to an active CAP alert zone.
    Matches by coordinate proximity (< 0.85 degrees ~ 90km) or location text keywords.
    """
    if not ACTIVE_ALERTS:
        return None

    # 1. Coordinate Proximity Matching
    if lat is not None and lon is not None:
        for alert in ACTIVE_ALERTS:
            a_lat = alert.get("lat")
            a_lon = alert.get("lon")
            if a_lat is not None and a_lon is not None:
                d = ((lat - a_lat) ** 2 + (lon - a_lon) ** 2) ** 0.5
                if d <= 0.85:
                    return alert

    # 2. Text Keyword Matching
    search_str = f"{name} {ward_id}".lower()
    for alert in ACTIVE_ALERTS:
        state = alert.get("state", "").lower()
        if state and state in search_str:
            return alert
        area = alert.get("areaDesc", "").lower()
        if area and any(word in search_str for word in area.replace(",", " ").split() if len(word) > 4):
            return alert
        for token in ["dehradun", "rishikesh", "song river", "patna", "ganga", "kolkata", "bengaluru", "odisha", "bhubaneswar", "mumbai"]:
            if token in search_str and (token in area or token in state):
                return alert

    return None


def get_alert_crisis_params(alert: Dict[str, Any]) -> Dict[str, float]:
    """
    Translates an active CAP alert's meteorological severity and nowcast windows
    into physics-guided dynamic parameters for the ML engine.
    """
    sev = alert.get("severity", "Severe").capitalize()
    if sev == "Severe":
        return {
            "rain_intensity_multiplier": 1.95,
            "soil_saturation_delta": 15.0,
            "river_surge_m": 1.35,
            "radar_peak_dbz": 56.0,
            "tidal_level_m": 1.1
        }
    elif sev == "High":
        return {
            "rain_intensity_multiplier": 1.40,
            "soil_saturation_delta": 8.0,
            "river_surge_m": 0.90,
            "radar_peak_dbz": 49.5,
            "tidal_level_m": 0.8
        }
    elif sev == "Moderate":
        return {
            "rain_intensity_multiplier": 0.85,
            "soil_saturation_delta": 2.0,
            "river_surge_m": 0.35,
            "radar_peak_dbz": 38.5,
            "tidal_level_m": 0.4
        }
    return {
        "rain_intensity_multiplier": 0.3,
        "soil_saturation_delta": -10.0,
        "river_surge_m": -0.4,
        "radar_peak_dbz": 20.0,
        "tidal_level_m": 0.2
    }


# --- ADMIN DISPATCH LOG & AUDIT HISTORY ---
DISPATCH_HISTORY = [
    {
        "id": "disp-001",
        "timestamp": "2026-09-01T19:30:10+05:30",
        "resource_name": "High-Capacity Dewatering Pump 500 m³/hr",
        "quantity": 2,
        "destination_ward": "Kurla West (Mithi River Basin)",
        "destination_location": "Kranti Nagar Outfall",
        "status": "In Transit",
        "authorized_by": "Deputy Commissioner K. Patil"
    },
    {
        "id": "disp-002",
        "timestamp": "2026-09-01T19:35:45+05:30",
        "resource_name": "NDRF Inflatable Rescue Boats (IRBs)",
        "quantity": 3,
        "destination_ward": "Dharavi - Mahim Creek Estuary",
        "destination_location": "90 Feet Road Staging Post",
        "status": "Staged On-Site",
        "authorized_by": "NDRF Commandant S. Verma"
    },
    {
        "id": "disp-003",
        "timestamp": "2026-09-01T19:42:00+05:30",
        "resource_name": "ALS 4x4 Flood Ambulance",
        "quantity": 2,
        "destination_ward": "Sion Circle & Matunga East",
        "destination_location": "Sion Hospital Emergency Gate",
        "status": "Active On-Site",
        "authorized_by": "Chief Medical Officer"
    }
]

# --- POSTGIS DDL SCHEMA SCRIPT ---
POSTGIS_DDL_SCHEMA = """
-- AquaAlert AI - PostGIS Production Migration Schema
-- Compatible with PostgreSQL 15+ with PostGIS 3.3+

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Administrative Wards / Basins
CREATE TABLE IF NOT EXISTS wards (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(32) NOT NULL,
    zone VARCHAR(100),
    area_km2 NUMERIC(8,2),
    population INTEGER,
    avg_elevation_m NUMERIC(6,2),
    terrain_slope_deg NUMERIC(5,2),
    impervious_surface_pct NUMERIC(5,2),
    drainage_density_idx NUMERIC(5,2),
    antecedent_moisture_pct NUMERIC(5,2),
    historical_waterlogging_frequency VARCHAR(50),
    geom GEOMETRY(Polygon, 4326),
    center_geom GEOMETRY(Point, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wards_geom ON wards USING GIST (geom);

-- 2. Sensor Stations (AWS, CWC Gauges, Doppler Radar)
CREATE TABLE IF NOT EXISTS sensor_stations (
    id VARCHAR(64) PRIMARY KEY,
    type VARCHAR(50) NOT NULL, -- aws, river_gauge, dwr_radar
    name VARCHAR(255) NOT NULL,
    code VARCHAR(64) UNIQUE NOT NULL,
    danger_mark_m NUMERIC(6,2),
    warning_mark_m NUMERIC(6,2),
    current_reading NUMERIC(8,2),
    unit VARCHAR(20),
    status VARCHAR(30) DEFAULT 'operational',
    location GEOMETRY(Point, 4326) NOT NULL,
    last_telemetry_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sensors_geom ON sensor_stations USING GIST (location);

-- 3. Telemetry Stream Time-Series
CREATE TABLE IF NOT EXISTS telemetry_records (
    id BIGSERIAL PRIMARY KEY,
    station_id VARCHAR(64) REFERENCES sensor_stations(id),
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    rainfall_1hr_mm NUMERIC(6,2),
    rainfall_3hr_mm NUMERIC(6,2),
    water_level_m NUMERIC(6,2),
    discharge_cumec NUMERIC(8,2),
    radar_reflectivity_dbz NUMERIC(5,2),
    soil_moisture_pct NUMERIC(5,2)
);

CREATE INDEX IF NOT EXISTS idx_telemetry_station_time ON telemetry_records (station_id, recorded_at DESC);

-- 4. ML Predictions & Inundation Risk Map
CREATE TABLE IF NOT EXISTS ward_predictions (
    id BIGSERIAL PRIMARY KEY,
    ward_id VARCHAR(64) REFERENCES wards(id),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    horizon_hrs INTEGER NOT NULL, -- 6 or 24
    rainfall_forecast_mm NUMERIC(6,2),
    flood_risk_score NUMERIC(5,2), -- 0 to 100
    risk_level VARCHAR(20), -- Low, Moderate, High, Severe
    predicted_depth_cm NUMERIC(6,2),
    model_confidence_pct NUMERIC(5,2),
    uncertainty_margin_cm NUMERIC(5,2),
    explainability_factors JSONB
);

-- 5. Common Alerting Protocol (CAP) Active Alerts
CREATE TABLE IF NOT EXISTS cap_alerts (
    id VARCHAR(64) PRIMARY KEY,
    identifier VARCHAR(100) UNIQUE NOT NULL,
    sender VARCHAR(150) NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'Actual',
    msg_type VARCHAR(20) DEFAULT 'Alert',
    category VARCHAR(50) DEFAULT 'Met',
    event VARCHAR(150) NOT NULL,
    urgency VARCHAR(30) NOT NULL,
    severity VARCHAR(30) NOT NULL,
    certainty VARCHAR(30) NOT NULL,
    headline TEXT NOT NULL,
    description TEXT,
    instruction TEXT,
    affected_wards JSONB,
    affected_roads JSONB,
    translations JSONB,
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by VARCHAR(150)
);

-- 6. Emergency Resources & Pre-Positioning
CREATE TABLE IF NOT EXISTS emergency_resources (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    total_available INTEGER NOT NULL,
    deployed INTEGER NOT NULL DEFAULT 0,
    standby INTEGER NOT NULL DEFAULT 0,
    allocated_wards JSONB
);
"""


def estimate_base_elevation(lat: float, lon: float) -> float:
    """Estimates typical baseline elevation in meters for Indian geographic coordinates."""
    # Bengaluru & Mysore Plateau (lat 12.0 - 13.5, lon 75.5 - 77.9)
    if 12.0 <= lat <= 13.5 and 76.5 <= lon <= 77.9:
        return 910.0
    # Deccan Plateau (Hyderabad, Pune, Solapur, etc.)
    if 16.5 <= lat <= 19.5 and 73.8 <= lon <= 79.5:
        return 550.0
    # Coastal plains & lowlands (Mumbai, Chennai, Kolkata, Kochi, Surat, Goa, etc.)
    if 12.5 <= lat <= 13.5 and 79.9 <= lon <= 80.4:  # Chennai / Tambaram
        return 12.0
    if 18.8 <= lat <= 19.4 and 72.7 <= lon <= 73.2:  # Mumbai MMR
        return 8.0
    if 22.0 <= lat <= 23.0 and 88.0 <= lon <= 88.8:  # Kolkata
        return 9.0
    if (lon < 73.4 or lon > 80.0) and lat < 21.0:
        return 8.0
    # Northern Gangetic Plains (Delhi, Kanpur, Lucknow, Patna)
    if 25.0 <= lat <= 29.0 and 76.5 <= lon <= 86.0:
        return 190.0
    # Himalayas / Hills (lat > 29.5 or Western Ghats)
    if lat > 29.5:
        return 1200.0
    return 150.0


def generate_regional_wards(lat: float, lon: float, name: str = "Searched Location") -> List[Dict[str, Any]]:
    """Generates 4 contiguous flood wards with distinct topographic & drainage features around any searched GPS location."""
    clean_name = name.split(",")[0].strip()
    r_lat = round(lat, 4)
    r_lon = round(lon, 4)
    base_elev = estimate_base_elevation(lat, lon)

    return [
        {
            "id": f"reg-basin-{r_lat}-{r_lon}-1",
            "name": f"{clean_name} (Central Runoff Basin)",
            "code": "REG-01",
            "zone": "Lowland Runoff Basin",
            "population": 165000,
            "area_km2": 3.6,
            "avg_elevation_m": 4.5,
            "actual_altitude_m": base_elev,
            "terrain_slope_deg": 0.8,
            "impervious_surface_pct": 85,
            "drainage_density_idx": 36,
            "antecedent_moisture_pct": 82,
            "historical_waterlogging_frequency": "Very High",
            "center": [round(lat + 0.007, 4), round(lon + 0.007, 4)],
            "polygon": [
                [round(lat + 0.001, 4), round(lon + 0.001, 4)],
                [round(lat + 0.013, 4), round(lon + 0.001, 4)],
                [round(lat + 0.015, 4), round(lon + 0.014, 4)],
                [round(lat + 0.008, 4), round(lon + 0.016, 4)],
                [round(lat + 0.001, 4), round(lon + 0.010, 4)],
                [round(lat + 0.001, 4), round(lon + 0.001, 4)]
            ],
            "vulnerable_assets": [
                {"name": f"{clean_name} Transit Underpass", "type": "transit", "lat": round(lat + 0.007, 4), "lon": round(lon + 0.006, 4), "vulnerability": "Severe"},
                {"name": f"{clean_name} General Hospital", "type": "hospital", "lat": round(lat + 0.009, 4), "lon": round(lon + 0.008, 4), "vulnerability": "High"}
            ],
            "nearest_shelter": {"name": f"{clean_name} Community Relief Center", "lat": round(lat + 0.011, 4), "lon": round(lon + 0.010, 4), "capacity": 650, "occupied": 20}
        },
        {
            "id": f"reg-basin-{r_lat}-{r_lon}-2",
            "name": f"{clean_name} (Commercial & Transit Sector)",
            "code": "REG-02",
            "zone": "Commercial Corridor",
            "population": 145000,
            "area_km2": 2.9,
            "avg_elevation_m": 8.0,
            "actual_altitude_m": base_elev,
            "terrain_slope_deg": 1.4,
            "impervious_surface_pct": 88,
            "drainage_density_idx": 45,
            "antecedent_moisture_pct": 74,
            "historical_waterlogging_frequency": "High",
            "center": [round(lat - 0.007, 4), round(lon + 0.007, 4)],
            "polygon": [
                [round(lat - 0.001, 4), round(lon + 0.001, 4)],
                [round(lat - 0.001, 4), round(lon + 0.014, 4)],
                [round(lat - 0.013, 4), round(lon + 0.015, 4)],
                [round(lat - 0.014, 4), round(lon + 0.002, 4)],
                [round(lat - 0.001, 4), round(lon + 0.001, 4)]
            ],
            "vulnerable_assets": [
                {"name": f"{clean_name} Metro Station", "type": "transit", "lat": round(lat - 0.006, 4), "lon": round(lon + 0.007, 4), "vulnerability": "High"}
            ],
            "nearest_shelter": {"name": f"{clean_name} Sports Complex Relief Hub", "lat": round(lat - 0.008, 4), "lon": round(lon + 0.008, 4), "capacity": 850, "occupied": 15}
        },
        {
            "id": f"reg-basin-{r_lat}-{r_lon}-3",
            "name": f"{clean_name} (Drainage Canal & Lowland Sump)",
            "code": "REG-03",
            "zone": "Canal Outfall Basin",
            "population": 180000,
            "area_km2": 4.2,
            "avg_elevation_m": 2.5,
            "actual_altitude_m": base_elev,
            "terrain_slope_deg": 0.4,
            "impervious_surface_pct": 82,
            "drainage_density_idx": 28,
            "antecedent_moisture_pct": 88,
            "historical_waterlogging_frequency": "Severe",
            "center": [round(lat - 0.007, 4), round(lon - 0.007, 4)],
            "polygon": [
                [round(lat - 0.001, 4), round(lon - 0.001, 4)],
                [round(lat - 0.013, 4), round(lon - 0.002, 4)],
                [round(lat - 0.015, 4), round(lon - 0.014, 4)],
                [round(lat - 0.003, 4), round(lon - 0.015, 4)],
                [round(lat - 0.001, 4), round(lon - 0.001, 4)]
            ],
            "vulnerable_assets": [
                {"name": f"{clean_name} Lowland Settlement", "type": "settlement", "lat": round(lat - 0.007, 4), "lon": round(lon - 0.008, 4), "vulnerability": "Severe"}
            ],
            "nearest_shelter": {"name": f"{clean_name} Secondary School Pavilion", "lat": round(lat - 0.005, 4), "lon": round(lon - 0.006, 4), "capacity": 500, "occupied": 25}
        },
        {
            "id": f"reg-basin-{r_lat}-{r_lon}-4",
            "name": f"{clean_name} (Elevated Ridge / High Ground)",
            "code": "REG-04",
            "zone": "Elevated Plateau",
            "population": 115000,
            "area_km2": 3.3,
            "avg_elevation_m": 18.0,
            "actual_altitude_m": base_elev,
            "terrain_slope_deg": 3.8,
            "impervious_surface_pct": 62,
            "drainage_density_idx": 68,
            "antecedent_moisture_pct": 55,
            "historical_waterlogging_frequency": "Low",
            "center": [round(lat + 0.007, 4), round(lon - 0.007, 4)],
            "polygon": [
                [round(lat + 0.001, 4), round(lon - 0.001, 4)],
                [round(lat + 0.002, 4), round(lon - 0.014, 4)],
                [round(lat + 0.014, 4), round(lon - 0.013, 4)],
                [round(lat + 0.014, 4), round(lon - 0.001, 4)],
                [round(lat + 0.001, 4), round(lon - 0.001, 4)]
            ],
            "vulnerable_assets": [],
            "nearest_shelter": {"name": f"{clean_name} Government College Ground", "lat": round(lat + 0.008, 4), "lon": round(lon - 0.006, 4), "capacity": 1200, "occupied": 0}
        }
    ]


def generate_regional_sensors(lat: float, lon: float, name: str = "Searched Location") -> List[Dict[str, Any]]:
    """Generates localized river/drainage gauges and AWS weather stations around any searched coordinates."""
    clean_name = name.split(",")[0].strip()
    return [
        {
            "id": "reg-gauge-1",
            "type": "river_gauge",
            "name": f"{clean_name} - Main Outfall Canal Gauge",
            "code": "CWC-REG-01",
            "lat": round(lat + 0.004, 4),
            "lon": round(lon + 0.005, 4),
            "current_level_m": 2.2,
            "warning_mark_m": 2.8,
            "danger_mark_m": 3.8,
            "discharge_cumec": 85.0,
            "status": "safe",
            "basin": f"{clean_name} Urban Drainage Basin"
        },
        {
            "id": "reg-gauge-2",
            "type": "river_gauge",
            "name": f"{clean_name} - Lowland Creek Gauge",
            "code": "CWC-REG-02",
            "lat": round(lat - 0.005, 4),
            "lon": round(lon - 0.004, 4),
            "current_level_m": 1.9,
            "warning_mark_m": 2.5,
            "danger_mark_m": 3.4,
            "discharge_cumec": 62.0,
            "status": "safe",
            "basin": f"{clean_name} Creek Valley"
        },
        {
            "id": "reg-aws-1",
            "type": "aws",
            "name": f"{clean_name} - North Met AWS Station",
            "code": "AWS-REG-N",
            "lat": round(lat + 0.009, 4),
            "lon": round(lon - 0.005, 4),
            "current_rain_mm_hr": 25.0,
            "cum_3hr_rain_mm": 62.0,
            "cum_24hr_rain_mm": 115.0,
            "soil_moisture_pct": 78,
            "temp_c": 25.5,
            "humidity_pct": 86,
            "status": "online"
        },
        {
            "id": "reg-aws-2",
            "type": "aws",
            "name": f"{clean_name} - South AWS Station",
            "code": "AWS-REG-S",
            "lat": round(lat - 0.007, 4),
            "lon": round(lon + 0.008, 4),
            "current_rain_mm_hr": 30.0,
            "cum_3hr_rain_mm": 74.0,
            "cum_24hr_rain_mm": 130.0,
            "soil_moisture_pct": 82,
            "temp_c": 25.0,
            "humidity_pct": 89,
            "status": "online"
        },
        {
            "id": "reg-dwr-1",
            "type": "dwr_radar",
            "name": f"{clean_name} - Regional Doppler Radar",
            "code": "DWR-REG",
            "lat": round(lat - 0.030, 4),
            "lon": round(lon - 0.030, 4),
            "max_reflectivity_dbz": 45.0,
            "beam_elevation_deg": 0.5,
            "range_km": 45,
            "status": "online"
        }
    ]
