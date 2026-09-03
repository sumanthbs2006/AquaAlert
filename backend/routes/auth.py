"""
AquaAlert AI - Authentication & Role-Based Access Control
Provides citizen and disaster authority login tokens.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/api/auth", tags=["Authentication & Roles"])

class LoginRequest(BaseModel):
    username: str
    password: str
    role_hint: str = "citizen"  # "citizen" or "authority"

DEMO_USERS = {
    "officer@sdma.gov.in": {
        "id": "usr-admin-01",
        "name": "Dr. R. K. Sharma",
        "designation": "Deputy Municipal Commissioner (Disaster Management)",
        "agency": "State Disaster Management Authority (SDMA)",
        "role": "authority",
        "token": "token-sdma-authority-verified-2026"
    },
    "citizen@aquaalert.in": {
        "id": "usr-cit-02",
        "name": "Arun Kumar",
        "role": "citizen",
        "ward_pref": "ward-L-kurla-w",
        "token": "token-citizen-public-2026"
    }
}

@router.post("/login")
def login(req: LoginRequest):
    """Logs in user or creates immediate demo session for reviewer."""
    # Check if known demo user
    user = DEMO_USERS.get(req.username.lower())
    if user:
        return {
            "status": "success",
            "access_token": user["token"],
            "token_type": "bearer",
            "user": user
        }
    
    # Reviewer ad-hoc login fallback
    role = req.role_hint if req.role_hint in ["authority", "citizen"] else "citizen"
    return {
        "status": "success",
        "access_token": f"token-adhoc-{role}-2026",
        "token_type": "bearer",
        "user": {
            "id": "usr-adhoc-reviewer",
            "name": req.username.split("@")[0].capitalize() or "Authorized Reviewer",
            "role": role,
            "agency": "Disaster Response Division" if role == "authority" else "Citizen User"
        }
    }

@router.get("/me")
def get_current_user_profile(role: str = "citizen"):
    """Quick profile lookup helper."""
    if role == "authority":
        return DEMO_USERS["officer@sdma.gov.in"]
    return DEMO_USERS["citizen@aquaalert.in"]
