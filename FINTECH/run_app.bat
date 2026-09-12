@echo off
echo Starting CrediFair AI Backend (FastAPI)...
start "CrediFair Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo Starting CrediFair AI Frontend (React + Vite)...
start "CrediFair Frontend" cmd /k "cd /d %~dp0frontend && npm run dev -- --port 3000"

echo.
echo ========================================================
echo CrediFair AI Application Started Successfully!
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo ========================================================
