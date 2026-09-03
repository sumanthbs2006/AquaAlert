@echo off
title AquaAlert AI - Full System Launcher
echo ========================================================
echo   AquaAlert AI - SIH26071 Disaster Early Warning System
echo ========================================================
echo.
echo Starting FastAPI & Production GIS Engine...
start /b python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
timeout /t 3 /nobreak >nul
echo Starting High-Speed Cloudflare Tunnel...
cloudflared.exe tunnel --protocol http2 --url http://127.0.0.1:8000
pause
