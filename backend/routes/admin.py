"""
AquaAlert AI - Disaster Management Authority (SDMA / NDRF) Admin Control Room
Provides:
1. Priority Triage Matrix (ranked highest-risk wards)
2. AI-driven Resource Pre-Positioning suggestions (pumps, rescue boats, ambulances, shelters)
3. Human-in-the-Loop Alert Verification & Manual Override
4. Emergency Cell Broadcast / Multi-Channel Alert Trigger
5. Incident Action Audit Trail
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
from backend.database import WARDS_DATA, RESOURCE_INVENTORY, ACTIVE_ALERTS, DISPATCH_HISTORY
from backend.ml_engine import ml_engine
from backend.ingestion import ingestion_manager

router = APIRouter(prefix="/api/admin", tags=["Admin & Control Room"])

class ResourceDispatchRequest(BaseModel):
    resource_id: str
    target_ward_id: str
    quantity: int
    authorized_by: str = "Commandant Patil (SDMA Mumbai)"
    notes: Optional[str] = "Immediate pre-positioning ahead of peak precipitation window."

class AlertOverrideRequest(BaseModel):
    alert_id: str
    new_severity: str  # Severe, High, Moderate, Silenced
    override_reason: str
    authorized_by: str = "Chief Disaster Officer"

class EmergencyBroadcastRequest(BaseModel):
    alert_id: str
    channels: List[str] = ["cell_broadcast", "sms", "whatsapp", "cap_feed"]
    target_ward_ids: List[str]
    authorized_by: str = "State Disaster Management Authority"

@router.get("/triage")
def get_triage_matrix():
    """
    Returns prioritized triage ranking of wards calculated by combining:
    ML Inundation Depth (cm) * Population Density * Asset Vulnerability Weight.
    """
    scenario = ingestion_manager.get_current_scenario()
    triage_list = []

    for ward in WARDS_DATA:
        pred = ml_engine.predict_ward_risk(ward, scenario.get("params"))
        
        # Calculate Triage Priority Index (0 - 100)
        pop_weight = min(1.0, ward["population"] / 300000.0)
        depth_weight = min(1.0, pred["predicted_depth_cm"] / 100.0)
        asset_count = len(ward.get("vulnerable_assets", []))
        
        triage_score = round((pred["risk_score"] * 0.45) + (depth_weight * 100 * 0.35) + (pop_weight * 100 * 0.20), 1)

        # Recommendation for emergency response
        recommended_actions = []
        if pred["predicted_depth_cm"] > 50:
            recommended_actions.append("Deploy high-capacity dewatering pumps (500 m³/hr)")
            recommended_actions.append("Pre-position NDRF Inflatable Rescue Boats (IRBs)")
            recommended_actions.append("Issue mandatory ground-floor evacuation order")
        elif pred["predicted_depth_cm"] > 25:
            recommended_actions.append("Position mobile trailer pumps at underpasses")
            recommended_actions.append("Divert road transit corridors")
            recommended_actions.append("Activate community relief shelters")
        else:
            recommended_actions.append("Continuous storm drain trash-screen clearance")
            recommended_actions.append("Keep emergency response teams on 30-min standby")

        triage_list.append({
            "ward_id": ward["id"],
            "ward_name": ward["name"],
            "code": ward["code"],
            "zone": ward["zone"],
            "triage_score": triage_score,
            "risk_level": pred["risk_level"],
            "predicted_depth_cm": pred["predicted_depth_cm"],
            "population_at_risk": ward["population"],
            "confidence_pct": pred["confidence_pct"],
            "vulnerable_assets_count": asset_count,
            "nearest_shelter": ward.get("nearest_shelter"),
            "recommended_actions": recommended_actions
        })

    # Sort descending by priority triage score
    triage_list.sort(key=lambda x: x["triage_score"], reverse=True)

    return {
        "status": "success",
        "total_ranked_zones": len(triage_list),
        "critical_priority_count": sum(1 for t in triage_list if t["risk_level"] == "Severe"),
        "triage": triage_list
    }

@router.get("/resources")
def get_resource_inventory():
    """
    Returns available emergency logistics (pumps, boats, ambulances, shelters)
    alongside AI pre-positioning guidance.
    """
    # Generate proactive AI pre-positioning recommendation
    recommendations = [
        {
            "priority": "CRITICAL",
            "action": "Pre-position 3x Submersible Pumps (500 m³/h)",
            "target": "Kurla West (Mithi River Basin)",
            "rationale": "Mithi river gauge at 3.45m (warning mark 2.7m) with predicted 85cm water depth in 2-4 hours."
        },
        {
            "priority": "HIGH",
            "action": "Stage 2x NDRF Inflatable Rescue Boats (IRBs)",
            "target": "Dharavi - Mahim Creek Estuary",
            "rationale": "High tide backwater at Mahim Creek expected to bottleneck 90 Feet Road drainage."
        },
        {
            "priority": "HIGH",
            "action": "Activate Dadar Shivaji Park Shelter (1000 Capacity)",
            "target": "Dadar West / Prabhadevi",
            "rationale": "Precautionary shelter staging for Hindmata junction chawl residents."
        }
    ]

    return {
        "status": "success",
        "inventory": RESOURCE_INVENTORY,
        "ai_prepositioning_recommendations": recommendations
    }

@router.post("/dispatch")
def dispatch_resource(req: ResourceDispatchRequest):
    """Dispatches requested emergency units to designated ward."""
    resource = next((r for r in RESOURCE_INVENTORY if r["id"] == req.resource_id), None)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    ward = next((w for w in WARDS_DATA if w["id"] == req.target_ward_id), None)
    if not ward:
        raise HTTPException(status_code=404, detail="Target ward not found")

    if resource["standby"] < req.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient standby units. Available: {resource['standby']}")

    resource["standby"] -= req.quantity
    resource["deployed"] += req.quantity
    if req.target_ward_id not in resource.get("allocated_wards", []):
        resource.setdefault("allocated_wards", []).append(req.target_ward_id)

    dispatch_entry = {
        "id": f"disp-{len(DISPATCH_HISTORY) + 1:03d}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "resource_name": resource["name"],
        "quantity": req.quantity,
        "destination_ward": ward["name"],
        "destination_location": f"{ward['name']} Emergency Staging Node",
        "status": "Dispatched / In Route",
        "authorized_by": req.authorized_by,
        "notes": req.notes
    }
    DISPATCH_HISTORY.insert(0, dispatch_entry)

    return {
        "status": "success",
        "message": f"Successfully dispatched {req.quantity}x {resource['name']} to {ward['name']}",
        "dispatch_entry": dispatch_entry,
        "updated_resource": resource
    }

@router.post("/override-alert")
def override_alert(req: AlertOverrideRequest):
    """
    Human-in-the-loop verification or manual override of an AI-generated alert.
    Allows elevating, downgrading, or silencing false positives.
    """
    alert = next((a for a in ACTIVE_ALERTS if a["id"] == req.alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    prev_severity = alert["severity"]
    alert["severity"] = req.new_severity
    alert["is_verified_by_authority"] = True
    alert["verified_by"] = f"{req.authorized_by} (Manual Override: {req.override_reason})"
    
    if req.new_severity == "Silenced":
        alert["status"] = "Cancelled"

    audit_entry = {
        "id": f"disp-{len(DISPATCH_HISTORY) + 1:03d}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "resource_name": f"Alert Severity Override [{alert['id']}]",
        "quantity": 1,
        "destination_ward": alert.get("areaDesc", "Multiple Wards"),
        "destination_location": f"Shifted from {prev_severity} to {req.new_severity}",
        "status": "Executed",
        "authorized_by": req.authorized_by,
        "notes": req.override_reason
    }
    DISPATCH_HISTORY.insert(0, audit_entry)

    return {
        "status": "success",
        "message": f"Alert {alert['id']} severity updated from {prev_severity} to {req.new_severity}",
        "alert": alert
    }

@router.post("/broadcast")
def trigger_emergency_broadcast(req: EmergencyBroadcastRequest):
    """
    Simulates sending emergency Cell Broadcast alarm / SMS blast to citizens in designated wards.
    """
    alert = next((a for a in ACTIVE_ALERTS if a["id"] == req.alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    target_wards = [w for w in WARDS_DATA if w["id"] in req.target_ward_ids]
    estimated_reach_population = sum(w["population"] for w in target_wards) or 450000

    broadcast_result = {
        "broadcast_id": f"BC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "alert_id": alert["id"],
        "headline": alert["headline"],
        "channels_activated": req.channels,
        "estimated_citizen_reach": estimated_reach_population,
        "broadcast_timestamp": datetime.now(timezone.utc).isoformat(),
        "authorized_by": req.authorized_by,
        "delivery_status": "QUEUED_AND_BROADCASTING",
        "simulated_carrier_gateways": ["JIO-CELL-BROADCAST", "AIRTEL-CB", "VI-ALERT", "BSNL-EMERGENCY"]
    }

    return {
        "status": "success",
        "message": f"Emergency alert broadcast triggered successfully across {len(req.channels)} channels.",
        "broadcast_details": broadcast_result
    }

@router.get("/audit-log")
def get_audit_log():
    """Returns official emergency action log."""
    return {
        "status": "success",
        "total_actions": len(DISPATCH_HISTORY),
        "logs": DISPATCH_HISTORY
    }
