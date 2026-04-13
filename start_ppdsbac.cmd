@echo off
setlocal

cd /d "%~dp0"

echo ===============================================
echo   PPDSBAC one-click startup
echo ===============================================
echo.

if not exist "backend\requirements.txt" (
  echo [Error] backend\requirements.txt not found.
  pause
  exit /b 1
)

if not exist "frontend\package.json" (
  echo [Error] frontend\package.json not found.
  pause
  exit /b 1
)

echo [1/2] Starting backend in a new cmd window...
start "PPDSBAC Backend" cmd /k "cd /d ""%~dp0backend"" && pip install -r requirements.txt && python app.py"

echo [2/2] Starting frontend in a new cmd window...
start "PPDSBAC Frontend" cmd /k "cd /d ""%~dp0frontend"" && if not exist node_modules npm install && npm run dev"

echo.
echo Startup commands sent. Close this window if you do not need it.
echo Frontend: http://localhost:3000
echo Backend : http://localhost:5000
echo.
pause
