"""
AquaAlert AI - Main FastAPI Application
Smart India Hackathon 2026 (Problem Statement SIH26071)
Theme: Disaster Management / Climate Resilience
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from backend.routes.forecasts import router as forecasts_router
from backend.routes.alerts import router as alerts_router
from backend.routes.sensors import router as sensors_router
from backend.routes.admin import router as admin_router
from backend.routes.auth import router as auth_router
from backend.routes.location import router as location_router
from backend.routes.carto import router as carto_router
from backend.ingestion import ingestion_manager

app = FastAPI(
    title="AquaAlert AI - Hyperlocal Early Warning & Flood Inundation Prediction Platform",
    description="Fuses Satellite (INSAT-3D), Doppler Radar, AWS Stations, CWC River Gauges, and GIS DEM elevation layers for Smart India Hackathon 2026 (SIH26071).",
    version="1.0.0"
)

# Enable CORS for all frontend development and deployment origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(forecasts_router)
app.include_router(alerts_router)
app.include_router(sensors_router)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(location_router)
app.include_router(carto_router)

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    assets_path = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

@app.get("/")
def root():
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "platform": "AquaAlert AI",
        "hackathon": "Smart India Hackathon 2026",
        "api_docs": "/docs",
        "status": "OPERATIONAL"
    }

@app.get("/favicon.svg")
def favicon():
    fav_file = os.path.join(frontend_dist, "favicon.svg")
    if os.path.exists(fav_file):
        return FileResponse(fav_file)
    return FileResponse(os.path.join(frontend_dist, "index.html"))

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "ml_engine": "online",
            "ingestion_simulator": "online",
            "gis_store": "online",
            "cap_alert_generator": "online"
        }
    }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
