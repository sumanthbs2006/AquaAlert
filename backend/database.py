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

# --- COMMON ALERTING PROTOCOL (CAP v1.2) INITIAL ACTIVE ALERTS ---
ACTIVE_ALERTS = [
    {
        "id": "ALERT-20260901-001",
        "identifier": "IN-MH-MCGM-2026-AQ-001",
        "sender": "mcgm-sdma-aquaalert@gov.in",
        "sent": "2026-09-01T19:45:00+05:30",
        "status": "Actual",
        "msgType": "Alert",
        "scope": "Public",
        "category": "Met",
        "event": "Severe Flash Flood & Inundation Warning",
        "urgency": "Immediate",
        "severity": "Severe",  # Severe, High, Moderate, Minor
        "certainty": "Observed",
        "headline": "RED ALERT: Severe Riverbank Overtopping & Inundation in Kurla West & Dharavi Basin",
        "description": "Fusing DWR radar reflectivity (>54 dBZ) and CWC Mithi River Gauge (3.45m, above warning mark 2.7m). Expect 60-90cm water inundation in next 2-6 hours across Kranti Nagar, Bail Bazar, and 90 Feet Road.",
        "instruction": "Residents of ground floors and low-lying chawls should immediately move to Kurla Urdu High School Shelter or Mahim Camp. Avoid LBS Road and Kurla Railway Subway. Keep emergency go-bags ready.",
        "areaDesc": "Kurla West, Dharavi Lowland, and Kranti Nagar Chawls",
        "affected_wards": ["ward-L-kurla-w", "ward-GN-dharavi"],
        "affected_roads": ["LBS Marg (Kurla Stretch)", "90 Feet Road Dharavi", "Kurla Subway"],
        "rainfall_time_window": "0–6 hrs (Expected 75–110 mm)",
        "inundation_time_window": "6–24 hrs (Peak depth 85 cm)",
        "is_verified_by_authority": True,
        "verified_by": "Dr. R. K. Sharma (Deputy Municipal Commissioner, Disaster Mgmt)",
        "translations": {
            "en": {
                "headline": "RED ALERT: Severe Flash Flood & Inundation in Kurla & Dharavi Basin",
                "instruction": "Ground floor residents must relocate to upper floors or nearby relief centers immediately. Stay away from Mithi River embankments and flooded subways.",
                "sms": "AquaAlert RED WARNING: Severe flood inundation expected in Kurla W/Dharavi next 2-6 hrs. Move to designated municipal shelters. Dial 1916 / 112 for rescue."
            },
            "hi": {
                "headline": "लाल चेतावनी: कुर्ला पश्चिम और धारावी बेसिन में गंभीर बाढ़ और जलभराव का खतरा",
                "instruction": "निचली मंजिलों के निवासी तुरंत ऊपरी मंजिलों या नजदीकी राहत शिविरों (कुर्ला उर्दू स्कूल/माहिम कैंप) में जाएं। मीठी नदी के किनारों और सबवे से दूर रहें।",
                "sms": "एक्वाअलर्ट लाल चेतावनी: अगले 2-6 घंटों में कुर्ला/धारावी में गंभीर बाढ़ की संभावना। सुरक्षित आश्रय स्थलों में जाएं। आपातकालीन हेल्पलाइन 1916 / 112 पर कॉल करें।"
            },
            "mr": {
                "headline": "रेड अलर्ट: कुर्ला पश्चिम व धारावी भागात अतिवृष्टीमुळे पूर आणि पाणी साचण्याचा गंभीर इशारा",
                "instruction": "तळमजल्यावरील रहिवाशांनी तातडीने सुरक्षित ठिकाणी किंवा पालिकेच्या निवारक केंद्रात हलवावे. मिठी नदी किनारा व सबवेकडे जाणे टाळावे.",
                "sms": "अ‍ॅक्वाअलर्ट रेड अलर्ट: कुर्ला व धारावीमध्ये पुढील २-६ तासांत तीव्र पुराचा धोका. तत्काळ महापालिका निवारा केंद्रात पोहोचा. आपत्कालीन कक्ष: १९१६ / ११२."
            },
            "ta": {
                "headline": "ரெட் அலர்ட்: குர்லா மேற்கு மற்றும் தாராவியில் கடுமையான வெள்ள அபாயம்",
                "instruction": "தரைத்தளத்தில் வசிப்பவர்கள் உடனடியாக நிவாரண முகாம்களுக்கு செல்லவும். மிதி நதி மற்றும் சுரங்கப்பாதைகளைத் தவிர்க்கவும்.",
                "sms": "AquaAlert ரெட் அலர்ட்: அடுத்த 2-6 மணி நேரத்தில் குர்லா/தாராவியில் வெள்ளப்பெருக்கு ஏற்படும். உதவிக்கு 1916 / 112 அழைக்கவும்."
            },
            "bn": {
                "headline": "রেড অ্যালার্ট: কুরলা ও ধারাভিতে তীব্র আকস্মিক বন্যা ও জলমগ্নতার সতর্কতা",
                "instruction": "নিচতলার বাসিন্দারা অবিলম্বে নিকটবর্তী ত্রাণ কেন্দ্রে যান। নদী তীর এবং সাবওয়ে এড়িয়ে চলুন।",
                "sms": "অ্যাকুয়াঅ্যালার্ট রেড সতর্কতা: আগামী ২-৬ ঘন্টায় কুরলা/ধারাভিতে তীব্র বন্যার আশঙ্কা। জরুরি সহায়তার জন্য ১৯১৬ / ১১২ নম্বরে যোগাযোগ করুন।"
            },
            "te": {
                "headline": "రెడ్ అలర్ట్: కుర్లా వెస్ట్ మరియు ధారవి బేసిన్‌లో తీవ్ర వరద ప్రమాదం",
                "instruction": "కింది అంతస్తుల్లోని ప్రజలు వెంటనే పై అంతస్తులకు లేదా పునరావాస కేంద్రాలకు వెళ్లాలి. వరద ప్రవాహాలకు దూరంగా ఉండండి.",
                "sms": "AquaAlert రెడ్ అలర్ట్: వచ్చే 2-6 గంటల్లో కుర్లా/ధారవిలో తీవ్ర వరదలు. సహాయం కోసం 1916 / 112 కి కాల్ చేయండి."
            },
            "kn": {
                "headline": "ಕೆಂಪು ಎಚ್ಚರಿಕೆ (ರೆಡ್ ಅಲರ್ಟ್): ಕುರ್ಲಾ ಪಶ್ಚಿಮ ಮತ್ತು ಧಾರಾವಿ ಕಣಿವೆಯಲ್ಲಿ ತೀವ್ರ ಪ್ರವಾಹ ಮತ್ತು ಮುಳುಗಡೆ ಭೀತಿ",
                "instruction": "ನೆಲಮಹಡಿಯ ನಿವಾಸಿಗಳು ತಕ್ಷಣ ಮೇಲಿನ ಮಹಡಿಗಳಿಗೆ ಅಥವಾ ಹತ್ತಿರದ ಪುರಸಭೆಯ ಪರಿಹಾರ ಕೇಂದ್ರಗಳಿಗೆ ತೆರಳಬೇಕು. ಮಿಥಿ ನದಿಯ ದಂಡೆಗಳು ಮತ್ತು ಮುಳುಗಿದ ಸಬ್‌ವೇಗಳಿಂದ ದೂರವಿರಿ.",
                "sms": "AquaAlert ರೆಡ್ ಅಲರ್ಟ್: ಮುಂದಿನ 2-6 ಗಂಟೆಗಳಲ್ಲಿ ಕುರ್ಲಾ/ಧಾರಾವಿಯಲ್ಲಿ ತೀವ್ರ ಪ್ರವಾಹದ ಸಾಧ್ಯತೆ. ಸುರಕ್ಷಿತ ಆಶ್ರಯ ತಾಣಗಳಿಗೆ ತೆರಳಿ. ರಕ್ಷಣಾ ಸಹಾಯಕ್ಕಾಗಿ 1916 / 112 ಗೆ ಕರೆ ಮಾಡಿ."
            }
        }
    },
    {
        "id": "ALERT-20260901-002",
        "identifier": "IN-MH-MCGM-2026-AQ-002",
        "sender": "mcgm-sdma-aquaalert@gov.in",
        "sent": "2026-09-01T19:50:00+05:30",
        "status": "Actual",
        "msgType": "Alert",
        "scope": "Public",
        "category": "Met",
        "event": "High Risk Urban Waterlogging Warning",
        "urgency": "Expected",
        "severity": "High",
        "certainty": "Likely",
        "headline": "ORANGE ALERT: Chronic Waterlogging & Transit Disruption in Sion & Gandhi Market",
        "description": "Antecedent moisture at 85% with continuous 35mm/hr precipitation. Sion Circle and Gandhi Market roads predicted to submerge up to 45cm within 1-3 hours.",
        "instruction": "Vehicular traffic on Sion flyover junction diverted. Commuters advised to avoid King's Circle and Matunga East corridors. Dewatering pumps active.",
        "areaDesc": "Sion Circle, Matunga East, Gandhi Market, King's Circle",
        "affected_wards": ["ward-FN-sion-matunga"],
        "affected_roads": ["Gandhi Market Road", "Sion Circle Underpass", "King's Circle Railway Bridge"],
        "rainfall_time_window": "0–6 hrs (Expected 50–75 mm)",
        "inundation_time_window": "3–12 hrs (Peak depth 45 cm)",
        "is_verified_by_authority": True,
        "verified_by": "Control Room Officer Patil (DDMA Mumbai)",
        "translations": {
            "en": {
                "headline": "ORANGE ALERT: Chronic Waterlogging in Sion & Gandhi Market",
                "instruction": "Avoid driving through Sion Circle and King's Circle. Use alternate elevated arterial routes.",
                "sms": "AquaAlert ORANGE: Heavy waterlogging likely at Sion Circle & Gandhi Market. Traffic diverted. Stay indoors where possible."
            },
            "hi": {
                "headline": "ऑरेंज अलर्ट: सायन सर्कल और गांधी मार्केट में भीषण जलभराव की चेतावनी",
                "instruction": "सायन सर्कल और किंग्स सर्कल से गुजरने से बचें। वैकल्पिक एलिवेटेड मार्गों का उपयोग करें।",
                "sms": "एक्वाअलर्ट ऑरेंज: सायन व गांधी मार्केट में 45 सेमी तक पानी भरने की संभावना। अनावश्यक यात्रा से बचें।"
            },
            "mr": {
                "headline": "ऑरेंज अलर्ट: सायन सर्कल आणि गांधी मार्केट भागात पाणी साचण्याचा इशारा",
                "instruction": "सायन सर्कल व गांधी मार्केट मार्गावरील वाहतूक वळवण्यात आली आहे. आवश्यक असल्यासच घराबाहेर पडावे.",
                "sms": "अ‍ॅक्वाअलर्ट ऑरेंज: सायन भागात रस्त्यावर पाणी साचण्याची शक्यता. पर्यायी मार्गांचा वापर करा."
            },
            "ta": {
                "headline": "ஆரஞ்சு அலர்ட்: சியோன் மற்றும் காந்தி சந்தையில் கடுமையான நீர் தேக்கம்",
                "instruction": "சியோன் வட்டாரப் பாதையைத் தவிர்க்கவும். மாற்றுப் பாதைகளைப் பயன்படுத்தவும்.",
                "sms": "AquaAlert ஆரஞ்சு: சியோன் பகுதியில் வெள்ளநீர் தேங்க வாய்ப்புள்ளது. பயணத்தைத் தவிர்க்கவும்."
            },
            "bn": {
                "headline": "অরেঞ্জ অ্যালার্ট: সায়ন ও গান্ধী মার্কেটে ভারী জলজট",
                "instruction": "সায়ন সার্কেল এলাকায় যাতায়াত এড়িয়ে চলুন। সাবধানে থাকুন।",
                "sms": "অ্যাকুয়াঅ্যালার্ট অরেঞ্জ: সায়ন অঞ্চলে তীব্র জলজটের সম্ভাবনা। অপ্রয়োজনীয় ভ্রমণ এড়িয়ে চলুন।"
            },
            "te": {
                "headline": "ఆరెంజ్ అలర్ట్: సియోన్ మరియు గాంధీ మార్కెట్‌లో నీటి నిల్వ హెచ్చరిక",
                "instruction": "సియోన్ సర్కిల్ గుండా ప్రయాణించవద్దు. ప్రత్యామ్నాయ మార్గాలను వాడండి.",
                "sms": "AquaAlert ఆరెంజ్: సియోన్ ప్రాంతంలో భారీగా నీరు నిలిచే అవకాశం ఉంది. అప్రమత్తంగా ఉండండి."
            },
            "kn": {
                "headline": "ಕಿತ್ತಳೆ ಎಚ್ಚರಿಕೆ (ಆರೆಂಜ್ ಅಲರ್ಟ್): ಸಿಯಾನ್ ಸರ್ಕಲ್ ಮತ್ತು ಗಾಂಧಿ ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ ತೀವ್ರ ಜಲಾವೃತ ಭೀತಿ",
                "instruction": "ಸಿಯಾನ್ ಸರ್ಕಲ್ ಮತ್ತು ಕಿಂಗ್ಸ್ ಸರ್ಕಲ್ ಮೂಲಕ ಸಂಚರಿಸುವುದನ್ನು ತಪ್ಪಿಸಿ. ಪರ್ಯಾಯ ಮೇಲ್ಸೇತುವೆ ಮಾರ್ಗಗಳನ್ನು ಬಳಸಿ.",
                "sms": "AquaAlert ಆರೆಂಜ್ ಅಲರ್ಟ್: ಸಿಯಾನ್ ಮತ್ತು ಗಾಂಧಿ ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ 45 ಸೆಂ.ಮೀ ವರೆಗೆ ನೀರು ನಿಲ್ಲುವ ಸಾಧ್ಯತೆ. ಅನಗತ್ಯ ಸಂಚಾರ ತಪ್ಪಿಸಿ."
            }
        }
    },
    {
        "id": "ALERT-20260901-003",
        "identifier": "IN-MH-MCGM-2026-AQ-003",
        "sender": "mcgm-sdma-aquaalert@gov.in",
        "sent": "2026-09-01T20:00:00+05:30",
        "status": "Actual",
        "msgType": "Alert",
        "scope": "Public",
        "category": "Met",
        "event": "Moderate Flash Waterlogging Advisory",
        "urgency": "Future",
        "severity": "Moderate",
        "certainty": "Possible",
        "headline": "YELLOW ADVISORY: Andheri Subway Closure & Flash Ponding Expected",
        "description": "Doppler radar shows convective rain cell shifting towards Western Suburbs. Andheri subway pump sump at 75% capacity.",
        "instruction": "Andheri Subway vehicular gates will close if water exceeds 25cm. Pedestrians advised to take Gokhale Bridge route.",
        "areaDesc": "Andheri East, Andheri Subway, Western Express Highway Crossing",
        "affected_wards": ["ward-KE-andheri-e"],
        "affected_roads": ["Andheri Subway", "Sahar Road Junction"],
        "rainfall_time_window": "0–6 hrs (Expected 35–50 mm)",
        "inundation_time_window": "2–8 hrs (Subway depth 30 cm)",
        "is_verified_by_authority": False,
        "verified_by": "Pending Authority Verification (AI Auto-Flagged)",
        "translations": {
            "en": {
                "headline": "YELLOW ADVISORY: Andheri Subway Flood Watch",
                "instruction": "Subway may be closed to traffic. Use Gokhale Bridge connector.",
                "sms": "AquaAlert YELLOW: Andheri subway flood watch active. Drive cautiously and monitor live updates."
            },
            "hi": {
                "headline": "येलो एडवाइजरी: अंधेरी सबवे में जलभराव की संभावना",
                "instruction": "अंधेरी सबवे में जलस्तर बढ़ने पर यातायात रोका जा सकता है। गोखले ब्रिज का उपयोग करें।",
                "sms": "एक्वाअलर्ट येलो: अंधेरी सबवे में जलभराव की चेतावनी। गोखले ओवरब्रिज का प्रयोग करें।"
            },
            "mr": {
                "headline": "येलो अलर्ट: अंधेरी सबवेमध्ये पाणी साचण्याची शक्यता",
                "instruction": "अंधेरी सबवे वाहतुकीसाठी बंद होऊ शकतो. गोखले पुलाचा वापर करावा.",
                "sms": "अ‍ॅक्वाअलर्ट येलो: अंधेरी सबवे सतर्कता इशारा. वाहन चालकांनी पर्यायी पूल वापरावा."
            },
            "ta": {
                "headline": "மஞ்சள் எச்சரிக்கை: அந்தேரி சுரங்கப்பாதையில் நீர் தேங்கும் வாய்ப்பு",
                "instruction": "கோகலே பாலத்தை மாற்றுப்பாதையாகப் பயன்படுத்தவும்.",
                "sms": "AquaAlert மஞ்சள்: அந்தேரி சுரங்கப்பாதையில் எச்சரிக்கையுடன் பயணிக்கவும்."
            },
            "bn": {
                "headline": "হলুদ সতর্কতা: আন্ধেরি সাবওয়েতে জল জমার সতর্কতা",
                "instruction": "সাবওয়ে বন্ধ হতে পারে, গোখলে ওভারব্রিজ ব্যবহার করুন।",
                "sms": "অ্যাকুয়াঅ্যালার্ট হলুদ: আন্ধেরি সাবওয়েতে জল জমতে পারে, বিকল্প রাস্তা ব্যবহার করুন।"
            },
            "te": {
                "headline": "ఎల్లో హెచ్చరిక: అంధేరీ సబ్వేలో నీరు చేరే ప్రమాదం",
                "instruction": "గోఖలే వంతెనను ప్రత్యామ్నాయంగా ఉపయోగించండి.",
                "sms": "AquaAlert ఎల్లో: అంధేరీ సబ్వే ప్రాంతంలో జాగ్రత్తగా ప్రయాణించండి."
            },
            "kn": {
                "headline": "ಹಳದಿ ಎಚ್ಚರಿಕೆ (ಯೆಲ್ಲೋ ಅಲರ್ಟ್): ಅಂಧೇರಿ ಸಬ್‌ವೇ ಮುಳುಗಡೆ ಮತ್ತು ನೀರು ನಿಲ್ಲುವ ನಿಗಾ",
                "instruction": "ಅಂಧೇರಿ ಸಬ್‌ವೇ ಸಂಚಾರಕ್ಕೆ ಮುಚ್ಚಲ್ಪಡಬಹುದು. ಗೋಖಲೆ ಮೇಲ್ಸೇತುವೆ ಪರ್ಯಾಯ ಸಂಪರ್ಕ ರಸ್ತೆಯನ್ನು ಬಳಸಿ.",
                "sms": "AquaAlert ಯೆಲ್ಲೋ ವಾಚ್: ಅಂಧೇರಿ ಸಬ್‌ವೇ ಮುಳುಗಡೆ ನಿಗಾ ಸಕ್ರಿಯವಾಗಿದೆ. ಜಾಗರೂಕರಾಗಿ ವಾಹನ ಚಲಾಯಿಸಿ."
            }
        }
    }
]

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
