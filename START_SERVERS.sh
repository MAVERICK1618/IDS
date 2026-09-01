#!/bin/bash

echo "🚀 Starting IDS Project..."
echo ""
echo "This script will help you start the frontend and backend."
echo ""
echo "Choose what to start:"
echo "1) Backend only"
echo "2) Frontend only"
echo "3) Both (in separate terminals)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
  1)
    echo "Starting backend..."
    cd backend
    source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
    pip install flask flask-cors python-dotenv >/dev/null 2>&1
    python3 app.py
    ;;
  2)
    echo "Starting frontend..."
    cd frontend
    npm install >/dev/null 2>&1
    npm run dev
    ;;
  3)
    echo "To start both, open 2 terminals and run:"
    echo ""
    echo "Terminal 1:"
    echo "  cd backend"
    echo "  source venv/bin/activate"
    echo "  python3 app.py"
    echo ""
    echo "Terminal 2:"
    echo "  cd frontend"
    echo "  npm run dev"
    echo ""
    echo "Then open: http://localhost:5173"
    ;;
  *)
    echo "Invalid choice"
    exit 1
    ;;
esac
