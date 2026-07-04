@echo off
rem One-click OFFLINE demo: single server, zero network, zero API key.
rem Serves the built frontend + replayed runs at http://localhost:8000
setlocal
cd /d "%~dp0"

if not exist "backend\.venv\Scripts\python.exe" (
  echo [ERROR] backend venv missing.
  echo         Run:  cd backend ^&^& python -m venv .venv ^&^& .venv\Scripts\python -m pip install -e ".[dev]"
  pause
  exit /b 1
)

if not exist "frontend\dist\index.html" (
  echo [INFO] built frontend missing - building once...
  call npm install --prefix frontend
  if errorlevel 1 ( echo [ERROR] npm install failed. & pause & exit /b 1 )
  call npm run build --prefix frontend
  if errorlevel 1 ( echo [ERROR] npm run build failed. & pause & exit /b 1 )
)

set HINDSIGHT_OFFLINE=1

rem open the browser shortly after the server comes up
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000"

echo Offline demo at http://localhost:8000  (Ctrl+C here to stop)
backend\.venv\Scripts\python.exe -m uvicorn hindsight.api.app:app --port 8000
endlocal
