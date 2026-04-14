@echo off
setlocal

cd /d "%~dp0"

echo ===============================================
echo   PPDSBAC one-click startup (.bat)
echo ===============================================
echo.

echo [1/3] Starting backend in a new cmd window...
start "PPDSBAC Backend" cmd /k "cd /d ""%~dp0backend"" && python app.py"

echo [2/3] Starting frontend in a new cmd window...
start "PPDSBAC Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"

echo [3/3] Opening frontend in default browser...
start "" "http://localhost:3000"

echo.
echo Startup commands sent.
echo Frontend: http://localhost:3000
echo Backend : http://localhost:5000
echo.
pause