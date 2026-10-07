@echo off
title VayuNetra (वायुNetra) AI-C2 System Launcher
color 0A

echo =========================================================================
echo  VayuNetra (वायुNetra) v3.0 -- Autonomous Counter-UAS C2 System
echo =========================================================================
echo.
echo Starting backend server on http://localhost:8000/ ...
echo.

cd /d "%~dp0"

start http://localhost:8000/

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

pause
