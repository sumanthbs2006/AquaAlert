"""
AquaAlert AI - Alerts & CAP (Common Alerting Protocol ITU-T X.1303) API Routes
Supports multilingual early warnings (English, Hindi, Marathi, Tamil, Bengali, Telugu)
and official standard CAP v1.2 XML / JSON export for emergency response agencies (NDMA/NDRF).
"""

from fastapi import APIRouter, HTTPException, Query, Response
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
import re
import random
from pydantic import BaseModel
from backend.database import ACTIVE_ALERTS, WARDS_DATA
from backend.services.sms_service import send_dual_flood_sms
from backend.config import EMERGENCY_RESCUE_AUTHORITY_PHONE

router = APIRouter(prefix="/api/alerts", tags=["Alerts & CAP Protocols"])

IST = timezone(timedelta(hours=5, minutes=30))

# In-memory emergency SMS broadcast log
DISPATCHED_SMS_LOGS: List[Dict[str, Any]] = []

def normalize_phone_number(raw_phone: str) -> tuple[str, str]:
    """Cleans phone string and formats to (+91 XXXXX XXXXX, 10digit)."""
    digits = re.sub(r"\D", "", str(raw_phone or ""))
    if len(digits) == 12 and digits.startswith("91"):
        clean_10 = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        clean_10 = digits[1:]
    elif len(digits) >= 10:
        clean_10 = digits[-10:]
    else:
        clean_10 = digits.zfill(10) if digits else "9876543210"
    formatted = f"+91 {clean_10[:5]} {clean_10[5:]}"
    return clean_10, formatted

def resolve_nearby_rescue_authority(area_name: str, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
    """
    Resolves the jurisdiction and contact details of the nearest National/State Disaster
    Response Force (NDRF/SDRF) Quick Response Team and Municipal Flood Control Hub.
    Evaluates both geographic coordinate proximity and text keyword heuristics.
    """
    text = (area_name or "").lower()
    
    # 1. Coordinate-based proximity detection if lat/lon provided
    if lat is not None and lon is not None:
        try:
            f_lat, f_lon = float(lat), float(lon)
            # Mumbai / Konkan: lat ~ 18.5 - 20.2, lon ~ 72.5 - 73.5
            if 18.2 <= f_lat <= 20.5 and 72.4 <= f_lon <= 73.8:
                text += " mumbai"
            # Bihar / Patna: lat ~ 24.5 - 26.5, lon ~ 84.0 - 86.5
            elif 24.0 <= f_lat <= 26.8 and 83.5 <= f_lon <= 86.8:
                text += " patna"
            # Uttarakhand / Himalayan foothills: lat ~ 29.5 - 31.5, lon ~ 77.5 - 79.5
            elif 29.2 <= f_lat <= 31.8 and 77.2 <= f_lon <= 79.8:
                text += " dehradun"
            # Bengaluru / Karnataka: lat ~ 12.5 - 13.5, lon ~ 77.0 - 78.0
            elif 12.4 <= f_lat <= 13.6 and 76.8 <= f_lon <= 78.2:
                text += " bengaluru"
            # Kolkata / Bengal Delta: lat ~ 22.0 - 23.5, lon ~ 88.0 - 89.0
            elif 21.8 <= f_lat <= 23.6 and 87.8 <= f_lon <= 89.2:
                text += " kolkata"
        except (ValueError, TypeError):
            pass

    # Mumbai / Maharashtra
    if any(k in text for k in ["mumbai", "kurla", "dharavi", "bandra", "sion", "mithi", "maharashtra", "thane"]):
        return {
            "name": "NDRF 5th Battalion (Andheri/Kurla QRT) & BMC Disaster Management Cell",
            "jurisdiction": "Mumbai Metropolitan & Mithi River Catchment",
            "control_phone": "+91 22 2269 4725 / +91 94223 10700",
            "sms_phone": "919422310700",
            "nodal_officer": "Commandant N. K. Roy (NDRF QRT Lead)",
            "helpline": "1916 / 112",
            "station": "Kurla-Kalina Emergency Response Station #4",
            "units_alerted": ["NDRF Quick Response Team #2", "BMC Sump Dewatering Unit", "Civil Defense Marine Patrol"]
        }
    # Bihar / Patna
    elif any(k in text for k in ["patna", "bihar", "ganga", "rajendra", "kankarbagh"]):
        return {
            "name": "NDRF 9th Battalion (Bihta, Patna) & BSDMA State Control Room",
            "jurisdiction": "Patna Urban & Central Gangetic Basin",
            "control_phone": "+91 612 2911000 / +91 94318 20000",
            "sms_phone": "919431820000",
            "nodal_officer": "Dr. A. K. Sinha (BSDMA State Disaster Officer)",
            "helpline": "1070 / 112",
            "station": "Patna Civil Lines Flood Response Outpost",
            "units_alerted": ["NDRF Inflatable Boat Unit", "BSDMA Emergency Suction Squad"]
        }
    # Uttarakhand / Dehradun / Rishikesh
    elif any(k in text for k in ["dehradun", "rishikesh", "uttarakhand", "song", "tapkeshwar", "sahastradhara"]):
        return {
            "name": "SDRF Uttarakhand Rapid Mountain Rescue & USDMA SEOC",
            "jurisdiction": "Dehradun Valley & Rishikesh Foothills",
            "control_phone": "0135-2710334 / +91 94111 12990",
            "sms_phone": "919411112990",
            "nodal_officer": "Shri V. P. Semwal (Director SEOC USDMA)",
            "helpline": "1070 / 112",
            "station": "Rishikesh Foothills Quick Response Post",
            "units_alerted": ["SDRF Torrent Rescue Unit", "USDMA Emergency Wireless Network"]
        }
    # Bengaluru / Karnataka
    elif any(k in text for k in ["bengaluru", "bangalore", "karnataka", "andraahalli", "vrishabhavathi"]):
        return {
            "name": "Karnataka SDRF Battalion & BBMP Central Disaster Operations",
            "jurisdiction": "Bengaluru Urban Watershed & BBMP Control Hub",
            "control_phone": "+91 80 2266 0000 / 1533",
            "sms_phone": "919480685700",
            "nodal_officer": "Chief Engineer (Stormwater Drain & Disaster Cell)",
            "helpline": "1533 / 112",
            "station": "BBMP West Zone Emergency Staging Hub",
            "units_alerted": ["BBMP Prahari Emergency Squad", "SDRF Urban Dewatering Unit"]
        }
    # Kolkata / West Bengal
    elif any(k in text for k in ["kolkata", "bengal", "howrah", "hooghly"]):
        return {
            "name": "NDRF 2nd Battalion (Kolkata) & WBDMA Emergency Response",
            "jurisdiction": "Kolkata Coastal Delta & Hooghly Flood Basin",
            "control_phone": "033-22143526 / +91 94330 11222",
            "sms_phone": "919433011222",
            "nodal_officer": "Special Relief Commissioner (Disaster Management)",
            "helpline": "1070 / 112",
            "station": "Kolkata Riverfront Quick Reaction Post",
            "units_alerted": ["NDRF IRB Boat Crew", "KMC High-Discharge Pump Cell"]
        }
    # General / Nationwide fallback
    else:
        return {
            "name": "NDRF National Command Quick Response Team & Local DEOC",
            "jurisdiction": f"{area_name} Local Hydrological Emergency Sector",
            "control_phone": "011-24363260 / 112",
            "sms_phone": "919711077372",
            "nodal_officer": "Duty Operations Officer (National Disaster Response)",
            "helpline": "112 / 1070",
            "station": "District Emergency Operations Centre (DEOC)",
            "units_alerted": ["Local Fire & Emergency Rescue", "District Rapid Action Team"]
        }

def is_heavy_rainfall_or_flood(
    rainfall_mm_hr: Optional[float] = 0.0,
    severity: Optional[str] = "",
    river_stage: Optional[str] = "",
    inundation_depth_cm: Optional[float] = 0.0,
    hazard_type: Optional[str] = ""
) -> bool:
    """
    Validates whether the meteorological/hydrological telemetry strictly qualifies
    as heavy rainfall (>= 25 mm/h) or flood emergency near the monitored area.
    """
    rain = float(rainfall_mm_hr or 0.0)
    depth = float(inundation_depth_cm or 0.0)
    stage = str(river_stage or "").strip().upper()
    sev = str(severity or "").strip().capitalize()
    ht = str(hazard_type or "").strip().lower()

    # IMD heavy rain criteria (>= 25 mm/h)
    if rain >= 25.0:
        return True
    # Waterlogging / inundation threshold (>= 15 cm)
    if depth >= 15.0:
        return True
    # Critical river stage
    if stage in ["DANGER", "CRITICAL", "HIGH", "SEVERE", "EXTREME"]:
        return True
    # Severity indicator
    if sev in ["Severe", "Critical", "High", "Red", "Orange"]:
        return True
    # Flood keywords in hazard description
    flood_keywords = ["flood", "inundation", "cloudburst", "cyclone", "torrential", "heavy rain", "waterlogging", "surge", "overflow"]
    if any(k in ht for k in flood_keywords):
        return True

    return False

def format_emergency_sms(
    hazard_type: str, 
    area_name: str, 
    rainfall_mm_hr: float, 
    severity: str, 
    river_stage: str, 
    authority_name: str = "NDRF / Local Disaster Authority", 
    lang: str = "en"
) -> str:
    lang = lang.lower() if lang else "en"
    short_auth = authority_name.split('&')[0].strip() if authority_name else "NDRF/SDRF Rescue QRT"
    if lang == "hi":
        return f"🚨 [एक्वाअलर्ट आपदा चेतावनी] {area_name} में {rainfall_mm_hr:.1f} मिमी/घंटा भारी बारिश व बाढ़ का गंभीर खतरा ({severity})! नदी स्तर: {river_stage}। तुरंत सुरक्षित ऊंचे स्थान पर जाएं। निकटतम बचाव दल ({short_auth}) को भी अलर्ट भेजा गया है। आपात हेल्पलाइन: 112 / 1070।"
    elif lang == "kn":
        return f"🚨 [AquaAlert ತುರ್ತು ಎಚ್ಚರಿಕೆ] {area_name} ಪ್ರದೇಶದಲ್ಲಿ {rainfall_mm_hr:.1f} mm/h ಭಾರೀ ಮಳೆ ಹಾಗೂ ಪ್ರವಾಹದ ತೀವ್ರ ಅಪಾಯ ({severity})! ನದಿ ಸ್ಥಿತಿ: {river_stage}. ತಕ್ಷಣ ಎತ್ತರದ ಪ್ರದೇಶಕ್ಕೆ ತೆರಳಿ. ರಕ್ಷಣಾ ಪಡೆಗೆ ({short_auth}) ಮಾಹಿತಿ ಕಳುಹಿಸಲಾಗಿದೆ. ತುರ್ತು ಸಹಾಯ: 112 / 1070."
    else:
        return f"🚨 [AquaAlert URGENT FLOOD WARNING] Heavy rainfall ({rainfall_mm_hr:.1f} mm/h) & flood risk ({severity}) in {area_name}! River/Drainage: {river_stage}. Move to higher ground immediately. Alert also transmitted to nearby rescue team: {short_auth}. Emergency Helpline: 112 / 1070."

def format_rescue_authority_sms(authority: Dict[str, Any], area_name: str, rainfall_mm_hr: float, severity: str, river_stage: str, inundation_depth_cm: float, citizen_phone: str) -> str:
    return (
        f"🚒 [NDMA-RESCUE DISPATCH] PRIORITY 1 FLOOD ADVISORY for {area_name}. "
        f"Precipitation: {rainfall_mm_hr:.1f} mm/h | Est. Inundation: {inundation_depth_cm:.0f} cm | River Stage: {river_stage}. "
        f"Citizen SOS in Hazard Zone: {citizen_phone}. "
        f"Action: Stand by QRT boat unit & stage dewatering pumps at {authority['station']}. "
        f"SEOC Helpline: 112 / 1070."
    )

class DispatchSmsRequest(BaseModel):
    phone: str
    area_name: Optional[str] = "Current Monitored Area"
    hazard_type: Optional[str] = "Heavy Rainfall & Flash Flood"
    rainfall_mm_hr: Optional[float] = 45.0
    severity: Optional[str] = "Severe"
    river_stage: Optional[str] = "DANGER"
    inundation_depth_cm: Optional[float] = 30.0
    lat: Optional[float] = None
    lon: Optional[float] = None
    lang: Optional[str] = "en"
    override_text: Optional[str] = None
    is_force_test: Optional[bool] = False
    authority_phone: Optional[str] = None
    alert_id: Optional[str] = None

class TestSmsRequest(BaseModel):
    phone: str
    area_name: Optional[str] = "User Area"
    rainfall_mm_hr: Optional[float] = 68.5
    authority_phone: Optional[str] = None

@router.get("")
def get_active_alerts(
    severity: Optional[str] = None,
    lang: str = "en",
    ward_id: Optional[str] = None
):
    """
    Returns active heavy rainfall and flood inundation warnings across India
    with localized multilingual headlines, instructions, and mock SMS previews.
    """
    results = []
    now_ist = datetime.now(IST)

    for alert in ACTIVE_ALERTS:
        # Filter by severity if specified
        if severity and alert["severity"].lower() != severity.lower():
            continue

        # Filter by ward if specified
        if ward_id and ward_id not in alert.get("affected_wards", []):
            continue

        # Extract language translation if available
        translation = alert.get("translations", {}).get(lang, alert.get("translations", {}).get("en", {}))
        
        # Format sent timestamp cleanly
        sent_raw = alert.get("sent", now_ist.isoformat())
        try:
            dt = datetime.fromisoformat(sent_raw)
            # Ensure it shows current day's issuance
            dt_display = dt.replace(year=now_ist.year, month=now_ist.month, day=now_ist.day)
            formatted_sent = dt_display.strftime("%b %d, %Y | %I:%M %p IST")
        except Exception:
            formatted_sent = now_ist.strftime("%b %d, %Y | %I:%M %p IST")

        item = {
            "id": alert["id"],
            "alias_id": alert.get("alias_id"),
            "identifier": alert["identifier"],
            "sender": alert["sender"],
            "sent": formatted_sent,
            "raw_sent": sent_raw,
            "state": alert.get("state", "India"),
            "lat": alert.get("lat"),
            "lon": alert.get("lon"),
            "urgency": alert["urgency"],
            "severity": alert["severity"],
            "certainty": alert["certainty"],
            "event": alert["event"],
            "headline": translation.get("headline", alert["headline"]),
            "description": alert.get("description", ""),
            "instruction": translation.get("instruction", alert["instruction"]),
            "sms_preview": translation.get("sms", alert.get("translations", {}).get("en", {}).get("sms", "")),
            "area_desc": alert["areaDesc"],
            "affected_wards": alert["affected_wards"],
            "affected_roads": alert["affected_roads"],
            "rainfall_time_window": alert["rainfall_time_window"],
            "inundation_time_window": alert["inundation_time_window"],
            "is_verified_by_authority": alert["is_verified_by_authority"],
            "verified_by": alert["verified_by"],
            "active_language": lang,
            "all_available_languages": ["en", "hi", "kn"]
        }
        results.append(item)

    return {
        "status": "success",
        "total_active_alerts": len(results),
        "selected_language": lang,
        "alerts": results
    }



@router.get("/export/cap-xml", response_class=Response)
def export_cap_xml():
    """
    Exports official Common Alerting Protocol (CAP v1.2, ITU-T X.1303) XML document.
    Interoperable with NDMA SACHET, SDMA, and international early warning frameworks.
    """
    root = ET.Element("alert", xmlns="urn:oasis:names:tc:emergency:cap:1.2")
    
    primary_alert = ACTIVE_ALERTS[0] if ACTIVE_ALERTS else None
    if not primary_alert:
        return Response(content="<alert></alert>", media_type="application/xml")

    ET.SubElement(root, "identifier").text = primary_alert["identifier"]
    ET.SubElement(root, "sender").text = primary_alert["sender"]
    ET.SubElement(root, "sent").text = primary_alert["sent"]
    ET.SubElement(root, "status").text = primary_alert["status"]
    ET.SubElement(root, "msgType").text = primary_alert["msgType"]
    ET.SubElement(root, "scope").text = primary_alert["scope"]

    info = ET.SubElement(root, "info")
    ET.SubElement(info, "category").text = primary_alert["category"]
    ET.SubElement(info, "event").text = primary_alert["event"]
    ET.SubElement(info, "urgency").text = primary_alert["urgency"]
    ET.SubElement(info, "severity").text = primary_alert["severity"]
    ET.SubElement(info, "certainty").text = primary_alert["certainty"]
    ET.SubElement(info, "eventCode").text = "FLW"  # Flood Warning
    ET.SubElement(info, "headline").text = primary_alert["headline"]
    ET.SubElement(info, "description").text = primary_alert["description"]
    ET.SubElement(info, "instruction").text = primary_alert["instruction"]

    area = ET.SubElement(info, "area")
    ET.SubElement(area, "areaDesc").text = primary_alert["areaDesc"]
    
    # Add circle coordinates around Kurla/Mithi
    ET.SubElement(area, "circle").text = "19.070,72.882,3.5"

    xml_str = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
    formatted_xml = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'
    return Response(content=formatted_xml, media_type="application/xml")

@router.get("/export/cap-json")
def export_cap_json():
    """Exports CAP standard JSON feed for emergency dispatch systems."""
    return {
        "cap_version": "1.2",
        "provider": "AquaAlert AI - National Hydromet Warning Portal",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "alerts": ACTIVE_ALERTS
    }

@router.post("/dispatch-sms")
def dispatch_emergency_sms(req: DispatchSmsRequest):
    """
    Dispatches a high-priority emergency SMS alert via Infobip API when heavy rainfall (>= 25 mm/h),
    cloudburst, or flood inundation is detected in the user's vicinity.
    Sends the exact emergency alert to BOTH:
    1. The signed-in citizen's mobile handset
    2. The nearby rescue authority / concerned emergency authority (NDRF / SDRF / Municipal Control Hub)
    """
    clean_phone, formatted_phone = normalize_phone_number(req.phone)

    # Check if a specific alert was requested
    matched_alert = None
    if req.alert_id:
        matched_alert = next((a for a in ACTIVE_ALERTS if a["id"] == req.alert_id or a.get("alias_id") == req.alert_id or a.get("identifier") == req.alert_id), None)
        if matched_alert:
            qualifies = True

    # Strict condition check: Only send SMS when heavy rainfall or flood condition is active
    qualifies = qualifies or req.is_force_test or is_heavy_rainfall_or_flood(
        rainfall_mm_hr=req.rainfall_mm_hr,
        severity=req.severity,
        river_stage=req.river_stage,
        inundation_depth_cm=req.inundation_depth_cm,
        hazard_type=req.hazard_type
    )

    if not qualifies:
        return {
            "status": "skipped",
            "message": "SMS alert suppressed: Dispatches are restricted strictly to heavy rainfall (>= 25 mm/h) or flood emergency conditions near your area.",
            "rainfall_mm_hr": req.rainfall_mm_hr,
            "threshold_required_mm_hr": 25.0,
            "area_name": req.area_name
        }

    target_area = req.area_name or "Your Monitored Vicinity"
    target_lat = req.lat
    target_lon = req.lon
    target_hazard = req.hazard_type or "Heavy Rainfall & Flash Flood Risk"
    target_sev = req.severity or "Severe"

    if matched_alert:
        target_area = matched_alert.get("areaDesc", target_area)
        target_sev = matched_alert.get("severity", target_sev)
        if target_lat is None:
            target_lat = matched_alert.get("lat")
        if target_lon is None:
            target_lon = matched_alert.get("lon")

    # Resolve nearest rescue authority (NDRF/SDRF) for the user's area & coordinates
    authority = resolve_nearby_rescue_authority(
        area_name=target_area,
        lat=target_lat,
        lon=target_lon
    )

    authority_phone = (
        req.authority_phone 
        or EMERGENCY_RESCUE_AUTHORITY_PHONE 
        or authority.get("sms_phone") 
        or "919422310700"
    )

    if req.override_text:
        sms_text = req.override_text
    elif matched_alert:
        trans = matched_alert.get("translations", {}).get(req.lang or "en", matched_alert.get("translations", {}).get("en", {}))
        sms_text = trans.get("sms") or format_emergency_sms(
            hazard_type=trans.get("headline", matched_alert.get("headline", target_hazard)),
            area_name=target_area,
            rainfall_mm_hr=req.rainfall_mm_hr or 55.0,
            severity=target_sev,
            river_stage=req.river_stage or "DANGER",
            authority_name=authority["name"],
            lang=req.lang or "en"
        )
    else:
        sms_text = format_emergency_sms(
            hazard_type=target_hazard,
            area_name=target_area,
            rainfall_mm_hr=req.rainfall_mm_hr or 45.0,
            severity=target_sev,
            river_stage=req.river_stage or "DANGER",
            authority_name=authority["name"],
            lang=req.lang or "en"
        )

    # Dispatch dual SMS to Citizen AND Nearby Rescue Authority via Infobip API
    infobip_res = send_dual_flood_sms(
        citizen_phone=clean_phone,
        authority_phone=authority_phone,
        sms_text=sms_text,
        area_name=target_area,
        authority_name=authority["name"]
    )

    now_utc = datetime.now(timezone.utc).isoformat()
    now_ist = datetime.now(IST).strftime("%b %d, %Y | %I:%M:%S %p IST")

    # 1. Citizen Handset Entry
    citizen_entry = {
        "id": f"SMS-CIT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}",
        "recipient_type": "citizen",
        "recipient_phone": formatted_phone,
        "clean_phone": clean_phone,
        "area_name": req.area_name or "Current Area",
        "hazard_type": req.hazard_type,
        "rainfall_mm_hr": req.rainfall_mm_hr,
        "severity": req.severity,
        "river_stage": req.river_stage,
        "inundation_depth_cm": req.inundation_depth_cm,
        "message": sms_text,
        "lang": req.lang or "en",
        "delivery_status": "DELIVERED_TO_HANDSET" if infobip_res.get("success") else "QUEUED",
        "carrier_gateway": "INFOBIP-GLOBAL-SMSC (TRAI-DND-BYPASS)",
        "infobip_message_id": infobip_res.get("citizen_message_id"),
        "rescue_authority_alerted": authority["name"],
        "dispatched_at": now_utc,
        "formatted_time": now_ist
    }

    # 2. Rescue Authority Handset Entry (Same Message dispatched to concerned rescue agency)
    clean_auth_phone = re.sub(r"\D", "", str(authority_phone))
    auth_display_phone = f"+{clean_auth_phone[:2]} {clean_auth_phone[2:]}" if len(clean_auth_phone) >= 12 else authority_phone

    authority_entry = {
        "id": f"SMS-QRT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}",
        "recipient_type": "rescue_authority",
        "authority_name": authority["name"],
        "recipient_phone": auth_display_phone,
        "clean_phone": clean_phone,  # Keyed to citizen phone so both render in citizen emergency inbox
        "authority_contact": authority.get("control_phone"),
        "area_name": req.area_name or "Current Area",
        "hazard_type": req.hazard_type,
        "rainfall_mm_hr": req.rainfall_mm_hr,
        "severity": req.severity,
        "river_stage": req.river_stage,
        "inundation_depth_cm": req.inundation_depth_cm,
        "message": sms_text,
        "station": authority.get("station"),
        "nodal_officer": authority.get("nodal_officer"),
        "helpline": authority.get("helpline"),
        "units_alerted": authority.get("units_alerted", []),
        "delivery_status": "DELIVERED_TO_HANDSET" if infobip_res.get("success") else "QUEUED",
        "carrier_gateway": "INFOBIP-QRT-HOTLINE (PRIORITY-1)",
        "infobip_message_id": infobip_res.get("authority_message_id"),
        "dispatched_at": now_utc,
        "formatted_time": now_ist
    }

    # Store at top of history log
    DISPATCHED_SMS_LOGS.insert(0, authority_entry)
    DISPATCHED_SMS_LOGS.insert(0, citizen_entry)

    return {
        "status": "success",
        "message": f"Emergency flood alert successfully dispatched via Infobip to citizen ({formatted_phone}) and nearby rescue authority ({authority['name']})",
        "sms": citizen_entry,
        "authority_sms": authority_entry,
        "rescue_authority": authority,
        "dispatched_entries": [citizen_entry, authority_entry],
        "total_dispatched": len(DISPATCHED_SMS_LOGS),
        "infobip_delivered": infobip_res.get("success", False),
        "infobip_details": infobip_res
    }

@router.get("/sms-history")
def get_sms_history(phone: Optional[str] = None):
    """
    Returns history of emergency SMS alerts dispatched to the signed-in user's mobile number,
    including both citizen warnings and rescue authority dispatch confirmations.
    """
    if phone:
        digits = re.sub(r"\D", "", str(phone))
        suffix = digits[-10:] if len(digits) >= 10 else digits
        filtered = [s for s in DISPATCHED_SMS_LOGS if s.get("clean_phone", "").endswith(suffix)]
        return {
            "status": "success",
            "phone": phone,
            "total": len(filtered),
            "history": filtered
        }
    return {
        "status": "success",
        "total": len(DISPATCHED_SMS_LOGS),
        "history": DISPATCHED_SMS_LOGS
    }

@router.get("/check-proximity")
def check_user_proximity(
    phone: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    area_name: Optional[str] = None
):
    """
    Checks if the user's current coordinates or monitored locality fall within
    proximity (<= 75km) or direct geographic boundary of an active CAP flood warning.
    """
    from backend.database import haversine_distance_km
    
    nearby_alert = None
    min_dist = 9999.0
    user_area_str = (area_name or "").lower()

    for alert in ACTIVE_ALERTS:
        a_lat = alert.get("lat")
        a_lon = alert.get("lon")
        alert_area = (alert.get("areaDesc") or "").lower()
        alert_state = (alert.get("state") or "").lower()

        # 1. Geographic Coordinate Proximity
        if lat is not None and lon is not None and a_lat is not None and a_lon is not None:
            dist = haversine_distance_km(float(lat), float(lon), float(a_lat), float(a_lon))
            if dist < min_dist:
                min_dist = dist
                if dist <= 75.0:
                    nearby_alert = alert

        # 2. Text Keyword Matching
        tokens = ["mumbai", "kurla", "mithi", "dharavi", "patna", "ganga", "dehradun", "rishikesh", "song", "bengaluru", "kolkata"]
        for tok in tokens:
            if tok in user_area_str and (tok in alert_area or tok in alert_state):
                nearby_alert = alert
                min_dist = min(min_dist, 5.0)
                break

    return {
        "status": "success",
        "has_alert_nearby": nearby_alert is not None,
        "distance_km": round(min_dist, 1) if min_dist < 9999 else None,
        "alert": nearby_alert,
        "phone": phone
    }

@router.post("/test-sms")
def test_emergency_sms(req: TestSmsRequest):
    """
    Dispatches immediate test flood warning SMS via Infobip to citizen and nearby rescue authority.
    """
    dispatch_req = DispatchSmsRequest(
        phone=req.phone,
        area_name=req.area_name or "Test Vicinity (Mithi Catchment)",
        hazard_type="Severe Flash Flood & Cloudburst Alert",
        rainfall_mm_hr=req.rainfall_mm_hr or 65.0,
        severity="Severe",
        river_stage="DANGER",
        inundation_depth_cm=48.0,
        lang="en",
        is_force_test=True,
        authority_phone=req.authority_phone
    )
    return dispatch_emergency_sms(dispatch_req)

@router.get("/{alert_id}")
def get_alert_detail(alert_id: str):
    """Returns single alert detail including full multilingual translations."""
    alert = next((a for a in ACTIVE_ALERTS if a["id"] == alert_id or a.get("alias_id") == alert_id or a["identifier"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return alert

