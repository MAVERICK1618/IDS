# 🚀 Complete Run Guide - Frontend, Backend & Systems

## Prerequisites

```bash
# Check Python version (need 3.9+)
python3 --version

# Check Node version (need 18+)
node --version

# Check npm version (need 8+)
npm --version
```

---

## 📋 Option 1: FASTEST START (4 Terminals)

### Terminal 1: Backend Server
```bash
cd /home/test/IDS/backend
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors python-dotenv
python3 app.py
```

**Expected output:**
```
============================================================
  IDS BACKEND API SERVER
  Environment: development
  CORS Origins: *
============================================================
  Development URL   : http://localhost:8000
  API Index         : http://localhost:8000/
============================================================
 * Running on http://localhost:8000
```

---

### Terminal 2: Frontend Dashboard
```bash
cd /home/test/IDS/frontend
npm install  # Only first time
npm run dev
```

**Expected output:**
```
  ✓ built in 234ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

---

### Terminal 3: Live Traffic Monitor
```bash
cd /home/test/IDS/systems
python3 -m venv venv
source venv/bin/activate
pip install scapy psutil numpy

python3 live-traffic-montior.py
```

**Expected output:**
```
[*] Auto-detecting interface for 10.10.10.x...
[+] Found interface: br-xxxxxxxx (10.10.10.1)
[*] Starting packet capture...
[*] Writing to: /home/test/IDS/ML/data/live-traffic.csv
[*] Press Ctrl+C to stop
```

---

### Terminal 4: ML Detectors (One at a time)
```bash
cd /home/test/IDS/systems/ML
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # If exists, else: pip install pandas scikit-learn

# Run one detector:
python3 Portscan-Detection.py
```

**Expected output:**
```
[+] Loading data from: /home/test/IDS/ML/data/
[+] Running port scan detection...
[+] Alerts written to: /home/test/IDS/ML/alerts/
```

---

## 📊 What You'll See

### Frontend (http://localhost:5173)
- **Agent Feed Panel**: Messages from orchestration
- **Packet Monitor Panel**: Live traffic from traffic monitor
- **Attack Timeline Panel**: Alerts from ML detectors
- **Metrics Panel**: Evaluation metrics

### Backend (http://localhost:8000)
- API endpoints responding with system data
- Test: `curl http://localhost:8000/api/status`

---

## ⚙️ Option 2: Simplified Setup (Fewer Terminals)

If you want just **Frontend + Backend** (no real data from systems):

### Terminal 1: Backend
```bash
cd /home/test/IDS/backend
source venv/bin/activate
python3 app.py
```

### Terminal 2: Frontend
```bash
cd /home/test/IDS/frontend
npm run dev
```

**Result:** Dashboard loads but shows empty/mock data (systems not running)

---

## 🎯 Option 3: Run All Systems (One Command)

Create `/home/test/IDS/RUN_ALL.sh`:

```bash
#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  IDS Full Stack Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Start Backend
echo -e "${GREEN}[1/4] Starting Backend...${NC}"
cd /home/test/IDS/backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install flask flask-cors python-dotenv >/dev/null 2>&1
nohup python3 app.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}  ✓ Backend PID: $BACKEND_PID${NC}"
sleep 2

# Start Frontend
echo -e "${GREEN}[2/4] Starting Frontend...${NC}"
cd /home/test/IDS/frontend
npm install >/dev/null 2>&1
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}  ✓ Frontend PID: $FRONTEND_PID${NC}"
sleep 3

# Start Live Traffic Monitor
echo -e "${GREEN}[3/4] Starting Live Traffic Monitor...${NC}"
cd /home/test/IDS/systems
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install scapy psutil numpy >/dev/null 2>&1
nohup python3 live-traffic-montior.py > /tmp/traffic-monitor.log 2>&1 &
TRAFFIC_PID=$!
echo -e "${GREEN}  ✓ Traffic Monitor PID: $TRAFFIC_PID${NC}"

# Start ML Detector
echo -e "${GREEN}[4/4] Starting ML Detector...${NC}"
cd /home/test/IDS/systems/ML
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install pandas scikit-learn >/dev/null 2>&1
nohup python3 Portscan-Detection.py > /tmp/ml-detector.log 2>&1 &
ML_PID=$!
echo -e "${GREEN}  ✓ ML Detector PID: $ML_PID${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ All Services Started${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}URLs:${NC}"
echo -e "  Frontend: ${BLUE}http://localhost:5173${NC}"
echo -e "  Backend:  ${BLUE}http://localhost:8000${NC}"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Backend:        tail -f /tmp/backend.log"
echo -e "  Frontend:       tail -f /tmp/frontend.log"
echo -e "  Traffic Mon:    tail -f /tmp/traffic-monitor.log"
echo -e "  ML Detector:    tail -f /tmp/ml-detector.log"
echo ""
echo -e "${YELLOW}Stop All:${NC}"
echo -e "  kill $BACKEND_PID $FRONTEND_PID $TRAFFIC_PID $ML_PID"
echo ""
```

**Make it executable:**
```bash
chmod +x /home/test/IDS/RUN_ALL.sh
bash /home/test/IDS/RUN_ALL.sh
```

---

## 🔍 Verification Steps

### Step 1: Check Backend
```bash
curl http://localhost:8000/api/status
```

Expected response:
```json
{
  "status": "running",
  "pipeline_running": true,
  "total_alerts": 0,
  "total_packets": 0
}
```

### Step 2: Check Frontend
Open in browser: **http://localhost:5173**

### Step 3: Check API Endpoints
```bash
# Alerts
curl http://localhost:8000/api/alerts

# Live traffic
curl http://localhost:8000/api/traffic/live

# Agent messages
curl http://localhost:8000/api/agent/messages

# Metrics
curl http://localhost:8000/api/metrics
```

### Step 4: Check Frontend Console
Open DevTools (F12) → Console tab
- Should see successful API calls
- Should see **0 errors**

---

## 📡 Data Flow Verification

### Is Backend Reading From Systems?
```bash
# Check if ML alerts folder has data
ls -la /home/test/IDS/systems/ML/alerts/

# Check if traffic CSV exists
ls -la /home/test/IDS/systems/ML/data/live-traffic.csv

# Check if orchestration logs exist
ls -la /home/test/IDS/systems/orchestration/logs/
```

### Is Frontend Getting Data?
1. Open http://localhost:5173
2. Open DevTools (F12)
3. Go to Network tab
4. Look for requests to:
   - `/api/alerts`
   - `/api/traffic/live`
   - `/api/agent/messages`
   - `/api/metrics`
5. Click on each request to see response

---

## ⚠️ Troubleshooting

### Problem: Backend won't start (Port 8000 in use)
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Then start backend again
cd /home/test/IDS/backend && python3 app.py
```

### Problem: Frontend won't start (Port 5173 in use)
```bash
# Find process using port 5173
lsof -i :5173

# Kill it
kill -9 <PID>

# Then start frontend again
cd /home/test/IDS/frontend && npm run dev
```

### Problem: API calls returning 404
```bash
# Check if backend is running
curl http://localhost:8000/api/status

# Check if VITE_API_BASE_URL is correct
cat /home/test/IDS/frontend/.env.local
# Should be: VITE_API_BASE_URL=http://localhost:8000
```

### Problem: No data in frontend (shows empty panels)
```bash
# Check if systems are producing data
ls -la /home/test/IDS/systems/ML/alerts/
ls -la /home/test/IDS/systems/ML/data/

# If folders are empty, systems aren't running
# Start the ML detectors and traffic monitor in separate terminals
```

### Problem: CORS errors in console
```
Access to XMLHttpRequest at 'http://localhost:8000/...' has been blocked by CORS policy
```

**Solution:** Restart backend with CORS enabled
```bash
cd /home/test/IDS/backend
# Kill current backend
pkill -f "python3 app.py"

# Restart
python3 app.py
```

### Problem: "Module not found" errors
```bash
# Frontend
cd /home/test/IDS/frontend
rm -rf node_modules package-lock.json
npm install
npm run dev

# Backend
cd /home/test/IDS/backend
source venv/bin/activate
pip install flask flask-cors python-dotenv
python3 app.py

# Systems
cd /home/test/IDS/systems
source venv/bin/activate
pip install scapy psutil numpy pandas scikit-learn
```

---

## 📊 Full System Diagram

```
┌─────────────────────────────────────────────────────┐
│           FRONTEND (React + Vite)                   │
│          http://localhost:5173                      │
│  ┌─────────────────────────────────────────────┐   │
│  │ Agent Feed  │ Packet Monitor│  Attack Timeline │  │
│  │             │               │    Metrics       │  │
│  └─────────────────────────────────────────────┘   │
└──────────────┬──────────────────────────────────────┘
               │ HTTP Requests
               ▼
┌─────────────────────────────────────────────────────┐
│         BACKEND (Flask API Server)                  │
│          http://localhost:8000                      │
│                                                     │
│  Routes data from systems → HTTP responses          │
└──────────────┬──────────────────────────────────────┘
               │ Reads files from systems
               ▼
┌─────────────────────────────────────────────────────┐
│              SYSTEMS (Data Producers)               │
│         /home/test/IDS/systems/                     │
│                                                     │
│  ┌─────────────────┐ ┌──────────────────────┐      │
│  │  ML Detectors   │ │ Live Traffic Monitor  │      │
│  │ Port Scan       │ │ Captures packets →   │      │
│  │ Brute Force     │ │ ML/data/live-traffic │      │
│  │ Lateral Move    │ │      .csv            │      │
│  │ Exfiltration    │ └──────────────────────┘      │
│  │ C2 Detection    │                               │
│  └────────┬────────┘                               │
│           │ Write alerts                           │
│           ▼                                         │
│  /ML/alerts/*.json                                 │
│                                                     │
│  ┌─────────────────┐ ┌──────────────────────┐      │
│  │  Orchestration  │ │   Red Team           │      │
│  │ Logs events →   │ │ Simulates attacks    │      │
│  │ /orchestration  │ │ → /Red-Team/ground   │      │
│  │   /logs/        │ └──────────────────────┘      │
│  └─────────────────┘                               │
└─────────────────────────────────────────────────────┘
```

---

## 📋 Checklist: Full Integration Running

- [ ] Terminal 1: Backend running (http://localhost:8000)
- [ ] Terminal 2: Frontend running (http://localhost:5173)
- [ ] Terminal 3: Traffic monitor running (writing to ML/data/)
- [ ] Terminal 4: ML detector running (writing to ML/alerts/)
- [ ] Browser: Dashboard loads at http://localhost:5173
- [ ] Browser: Panels show live data (not empty)
- [ ] Console: No CORS errors
- [ ] Console: Successful API calls logged
- [ ] Backend: API endpoints responding (curl test)
- [ ] Systems: Folders have data files

---

## 🎉 Success Indicators

1. **Frontend Dashboard** shows live data
2. **Network tab** shows successful API calls
3. **No red errors** in browser console
4. **Panels populate** with real data from systems
5. **Backend responds** to all API requests
6. **Systems folders** have data (JSON, CSV, logs)

---

## Next Steps

1. Read: **DATA_FLOW_ARCHITECTURE.md** (understand flow)
2. Run: **Backend + Frontend** (core stack)
3. Run: **Traffic Monitor + ML Detectors** (data producers)
4. Verify: All green checks in checklist above
5. Explore: http://localhost:5173 dashboard
