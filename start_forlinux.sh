#!/bin/bash

# Change the working directory to the directory where the script is located
cd "$(dirname "$0")" || exit

echo "==============================================="
echo "  PPDSBAC one-click startup (.sh) for Linux/Mac"
echo "==============================================="
echo

echo "[1/3] Starting backend in the background..."
(cd backend && python3 app.py) &
backend_pid=$!

echo "[2/3] Starting frontend in the background..."
(cd frontend && npm run dev) &
frontend_pid=$!

echo "[3/3] Opening frontend in default browser..."
sleep 2 # Give the server a moment to start
if command -v xdg-open > /dev/null; then
  xdg-open "http://localhost:3000" &> /dev/null
elif command -v open > /dev/null; then
  open "http://localhost:3000" &> /dev/null
else
  echo "Could not automatically open a browser. Please open http://localhost:3000 manually."
fi

echo
echo "Startup commands sent."
echo "Frontend: http://localhost:3000"
echo "Backend : http://localhost:5000"
echo
echo "Press [CTRL+C] to stop both frontend and backend."

# This trap will kill both background processes when the user presses Ctrl+C
trap 'echo -e "\nStopping backend and frontend..."; kill $backend_pid $frontend_pid; exit 0' SIGINT SIGTERM

# Wait indefinitely for background processes
wait $backend_pid $frontend_pid
