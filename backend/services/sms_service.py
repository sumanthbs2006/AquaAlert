"""
AquaAlert AI - Infobip SMS Gateway Service
Integrates with Infobip REST API (https://api.infobip.com) for:
1. Citizen authentication OTP dispatch during signup & login
2. Automated emergency flood and heavy rainfall warnings to citizen handsets
3. Concurrent automated dispatch to nearby rescue authorities (NDRF/SDRF/DEOC)
"""

import re
import logging
from typing import List, Dict, Any, Union, Optional
import requests
from backend.config import (
    INFOBIP_API_KEY, 
    INFOBIP_BASE_URL, 
    INFOBIP_SENDER,
    EMERGENCY_RESCUE_AUTHORITY_PHONE
)

logger = logging.getLogger("aquaalert.sms_service")
logging.basicConfig(level=logging.INFO)

def normalize_phone_for_infobip(phone: Union[str, int]) -> str:
    """
    Normalizes an Indian phone number to Infobip's required E.164 format (without '+').
    Example inputs:
      '+91 98765 43210' -> '919876543210'
      '9876543210'       -> '919876543210'
      '09876543210'      -> '919876543210'
      '919876543210'     -> '919876543210'
    """
    digits = re.sub(r"\D", "", str(phone or ""))
    if len(digits) == 12 and digits.startswith("91"):
        return digits
    elif len(digits) == 11 and digits.startswith("0"):
        return "91" + digits[1:]
    elif len(digits) == 10:
        return "91" + digits
    elif len(digits) > 10:
        return digits
    return digits

def send_infobip_sms(
    destinations: Union[List[str], str],
    text: str,
    sender: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends one or more SMS messages via Infobip's outbound SMS API endpoint:
    POST /sms/2/text/advanced
    """
    if isinstance(destinations, str):
        dest_list = [destinations]
    else:
        dest_list = list(destinations)

    cleaned_dests = []
    for d in dest_list:
        norm = normalize_phone_for_infobip(d)
        if norm:
            cleaned_dests.append(norm)

    if not cleaned_dests:
        return {
            "success": False,
            "error": "No valid destination phone numbers provided",
            "messages": []
        }

    api_key = INFOBIP_API_KEY or "0d284b36ba0d3329b79388f979fa71c7-aeb70f1e-960c-4bfc-ad1e-e81896bbfd0b"
    base_url = (INFOBIP_BASE_URL or "https://api.infobip.com").rstrip("/")
    endpoint = f"{base_url}/sms/2/text/advanced"

    headers = {
        "Authorization": f"App {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Infobip payload structure
    sender_id = sender or INFOBIP_SENDER or "AquaAlert"
    payload = {
        "messages": [
            {
                "from": sender_id,
                "destinations": [{"to": d} for d in cleaned_dests],
                "text": text
            }
        ]
    }

    try:
        logger.info(f"Dispatching Infobip SMS to {cleaned_dests} via {endpoint} (Sender: {sender_id})")
        response = requests.post(endpoint, json=payload, headers=headers, timeout=3.5)
        
        status_code = response.status_code
        try:
            resp_json = response.json()
        except Exception:
            resp_json = {"raw": response.text}

        if 200 <= status_code < 300:
            logger.info(f"Infobip dispatch successful ({status_code}): {resp_json}")
            return {
                "success": True,
                "status_code": status_code,
                "bulk_id": resp_json.get("bulkId"),
                "messages": resp_json.get("messages", []),
                "raw_response": resp_json
            }
        else:
            logger.error(f"Infobip API error ({status_code}): {resp_json}")
            return {
                "success": False,
                "status_code": status_code,
                "error": resp_json.get("requestError", {}).get("serviceException", {}).get("text") or str(resp_json),
                "raw_response": resp_json
            }
    except requests.RequestException as ex:
        logger.error(f"Infobip network request exception: {ex}")
        return {
            "success": False,
            "error": str(ex),
            "messages": []
        }

def send_otp_sms(phone: str, otp_code: str) -> Dict[str, Any]:
    """
    Dispatches a 6-digit verification OTP to a citizen during signup / mobile authentication.
    Uses the configured Infobip API key.
    """
    clean_phone = normalize_phone_for_infobip(phone)
    formatted_display = f"+{clean_phone[:2]} {clean_phone[2:7]} {clean_phone[7:]}" if len(clean_phone) == 12 else clean_phone
    
    otp_text = (
        f"AquaAlert: Your disaster warning verification code is {otp_code}. "
        f"Valid for 5 minutes. Do not share this OTP with anyone for emergency system security."
    )
    
    res = send_infobip_sms(
        destinations=[clean_phone],
        text=otp_text,
        sender="AquaAlert"
    )
    
    msg_id = None
    if res.get("success") and res.get("messages"):
        msg_id = res["messages"][0].get("messageId")
        
    return {
        "success": res.get("success", False),
        "phone": clean_phone,
        "formatted_phone": formatted_display,
        "message_id": msg_id,
        "otp": otp_code,
        "raw": res
    }

def send_dual_flood_sms(
    citizen_phone: str,
    authority_phone: str,
    sms_text: str,
    area_name: str,
    authority_name: str
) -> Dict[str, Any]:
    """
    Dispatches the emergency flood / heavy rainfall SMS to BOTH:
    1. The citizen's phone in the affected area
    2. The nearby rescue authority / concerned emergency authority (NDRF / SDRF / DEOC)
    
    Returns the dispatch tracking details for both destinations.
    """
    clean_citizen = normalize_phone_for_infobip(citizen_phone)
    clean_authority = normalize_phone_for_infobip(authority_phone or EMERGENCY_RESCUE_AUTHORITY_PHONE)
    
    # Send simultaneously to both destinations
    destinations = [clean_citizen]
    if clean_authority and clean_authority != clean_citizen:
        destinations.append(clean_authority)
        
    res = send_infobip_sms(
        destinations=destinations,
        text=sms_text,
        sender="AquaAlert"
    )
    
    citizen_msg_id = None
    authority_msg_id = None
    
    if res.get("success") and res.get("messages"):
        for m in res["messages"]:
            to_num = m.get("to")
            if to_num == clean_citizen:
                citizen_msg_id = m.get("messageId")
            elif to_num == clean_authority:
                authority_msg_id = m.get("messageId")
                
    return {
        "success": res.get("success", False),
        "citizen_phone": clean_citizen,
        "citizen_message_id": citizen_msg_id,
        "authority_phone": clean_authority,
        "authority_message_id": authority_msg_id,
        "authority_name": authority_name,
        "bulk_id": res.get("bulk_id"),
        "raw": res
    }
