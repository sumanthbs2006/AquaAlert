@echo off
title AquaAlert AI - Cloudflare Public Tunnel
echo ===================================================
echo   AquaAlert AI - Launching High-Speed Public Link
echo ===================================================
echo.
echo Starting Cloudflare Tunnel on http://127.0.0.1:8000...
echo.
cloudflared.exe tunnel --protocol http2 --url http://127.0.0.1:8000
pause
