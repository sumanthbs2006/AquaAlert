"""
AquaAlert AI - Alerts & CAP (Common Alerting Protocol ITU-T X.1303) API Routes
Supports multilingual early warnings (English, Hindi, Marathi, Tamil, Bengali, Telugu)
and official standard CAP v1.2 XML / JSON export for emergency response agencies (NDMA/NDRF).
"""

from fastapi import APIRouter, HTTPException, Query, Response
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from backend.database import ACTIVE_ALERTS, WARDS_DATA

router = APIRouter(prefix="/api/alerts", tags=["Alerts & CAP Protocols"])

@router.get("")
def get_active_alerts(
    severity: Optional[str] = None,
    lang: str = "en",
    ward_id: Optional[str] = None
):
    """
    Returns active heavy rainfall and flood inundation warnings
    with localized multilingual headlines, instructions, and mock SMS previews.
    """
    results = []
    for alert in ACTIVE_ALERTS:
        # Filter by severity if specified
        if severity and alert["severity"].lower() != severity.lower():
            continue

        # Filter by ward if specified
        if ward_id and ward_id not in alert.get("affected_wards", []):
            continue

        # Extract language translation if available
        translation = alert.get("translations", {}).get(lang, alert.get("translations", {}).get("en", {}))
        
        item = {
            "id": alert["id"],
            "identifier": alert["identifier"],
            "sender": alert["sender"],
            "sent": alert["sent"],
            "urgency": alert["urgency"],
            "severity": alert["severity"],
            "certainty": alert["certainty"],
            "event": alert["event"],
            "headline": translation.get("headline", alert["headline"]),
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

@router.get("/{alert_id}")
def get_alert_detail(alert_id: str):
    """Returns single alert detail including full multilingual translations."""
    alert = next((a for a in ACTIVE_ALERTS if a["id"] == alert_id or a["identifier"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return alert

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
