@echo off
rem One-click DEV mode: backend (auto-reload) + frontend (HMR) in two windows.
setlocal
cd /d "%~dp0"

if not exist "backend\.venv\Scripts\python.exe" (
  echo [ERROR] backend venv missing.
  echo         Run:  cd backend ^&^& python -m venv .venv ^&^& .venv\Scripts\python -m pip install -e ".[dev]"
  pause
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo [INFO] frontend dependencies missing - installing once...
  call npm install --prefix frontend
  if errorlevel 1 (
    echo [ERROR] npm install failed.
    pause
    exit /b 1
  )
)

start "hindsight-backend :8000" cmd /k "backend\.venv\Scripts\python.exe -m uvicorn hindsight.api.app:app --port 8000 --reload"
start "hindsight-frontend :5173" cmd /k "npm run dev --prefix frontend"

rem give vite a moment, then open the browser
timeout /t 3 /nobreak >nul
start "" http://localhost:5173

echo.
echo Launched two windows:
echo   backend  http://localhost:8000  (uvicorn --reload, watches backend code)
echo   frontend http://localhost:5173  (vite HMR, watches frontend code)
echo Close those windows (or Ctrl+C inside them) to stop.
endlocal
