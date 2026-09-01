# 📊 Data Flow Architecture - IDS Full Stack

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + Vite)                         │
│                      http://localhost:5173                              │
│  - Agents Panel    - Packet Monitor   - Attack Timeline   - Metrics    │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ HTTP Requests (VITE_API_BASE_URL)
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BACKEND (Flask API Server)                           │
│                      http://localhost:8000                              │
│  ✓ Polls systems   ✓ Aggregates data   ✓ Serves API endpoints         │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ Reads from systems
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SYSTEMS (Tools & Services)                      │
│                      /home/test/IDS/systems/                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. FRONTEND (React Dashboard)
**Location:** `/frontend/`
**Port:** 5173
**Technology:** React + Vite + TypeScript

**Displays:**
- Agent communications (from `/api/agent/messages`)
- Live network packets (from `/api/traffic/live`)
- Security alerts/attacks (from `/api/alerts`)
- System metrics (from `/api/metrics`)

---

### 2. BACKEND (Flask API Server)
**Location:** `/backend/app.py`
**Port:** 8000
**Technology:** Flask + Python

**Reads from SYSTEMS folders:**
- `/systems/ML/alerts/` → Serves as `/api/alerts`
- `/systems/ML/data/live-traffic.csv` → Serves as `/api/traffic/live`
- `/systems/orchestration/logs/` → Serves as `/api/logs`
- `/systems/Red-Team/ground/` → Serves as `/api/ground-truth`
- `/systems/orchestration/agent_messages.log` → Serves as `/api/agent/messages`

---

### 3. SYSTEMS (Data Producers)
**Location:** `/systems/`

| Component | Folder | Output | Purpose |
|-----------|--------|--------|---------|
| **ML Detectors** | `ML/` | Alerts JSON files | Detects attacks |
| **Live Traffic Monitor** | `live-traffic-montior.py` | `ML/data/live-traffic.csv` | Captures network traffic |
| **Red Team** | `Red-Team/` | Ground truth files | Simulates attacks |
| **Orchestration** | `orchestration/` | Logs, agent messages | Controls pipeline |
| **Emulator** | `emulator/` | Network topology | Containerlab setup |

---

## Data Flow Diagram

### Flow 1: Alerts
```
ML Detectors (systems/ML/*.py)
    ↓ Write JSON alerts
systems/ML/alerts/*.json
    ↓ Read by Backend
Backend: GET /api/alerts
    ↓ HTTP Response
Frontend: Display in Attack Timeline Panel
```

### Flow 2: Live Traffic
```
Live Traffic Monitor (systems/live-traffic-montior.py)
    ↓ Writes CSV rows
systems/ML/data/live-traffic.csv
    ↓ Read by Backend
Backend: GET /api/traffic/live
    ↓ HTTP Response
Frontend: Display in Packet Monitor Panel
```

### Flow 3: Agent Messages
```
Orchestration (systems/orchestration/ids_graph.py)
    ↓ Writes log file
systems/orchestration/agent_messages.log
    ↓ Read by Backend
Backend: GET /api/agent/messages
    ↓ HTTP Response
Frontend: Display in Agent Feed Panel
```

### Flow 4: Metrics
```
ML Models (systems/ML/outputs/*.csv)
    ↓ Evaluation results
systems/ML/outputs/
    ↓ Read by Backend
Backend: GET /api/metrics
    ↓ HTTP Response
Frontend: Display in Metrics Panel
```

---

## Backend Endpoints & Data Sources

| Endpoint | Source File/Folder | System Component |
|----------|-------------------|-----------------|
| `/api/status` | `orchestration/STOP`, `orchestration.pid` | Orchestration |
| `/api/alerts` | `ML/alerts/*.json` | ML Detectors |
| `/api/predictions` | `ML/processed/*.json` | ML Results |
| `/api/ground-truth` | `Red-Team/ground/*.json` | Red Team |
| `/api/metrics` | `ML/outputs/*.csv` | Evaluation |
| `/api/traffic/live` | `ML/data/live-traffic.csv` | Traffic Monitor |
| `/api/agent/messages` | `orchestration/agent_messages.log` | Orchestration |
| `/api/logs` | `orchestration/logs/*.log` | Orchestration |
| `/api/lab/hosts` | `emulator/hosts.json` | Emulator |
| `/api/lab/topology` | `emulator/topology.json` | Emulator |

---

## Folder Structure Overview

```
/home/test/IDS/
│
├── frontend/                    # React Dashboard
│   └── Reads from: Backend API (http://localhost:8000)
│
├── backend/                     # Flask API Server
│   ├── Reads from: systems/
│   ├── Port: 8000
│   └── Serves: REST API to frontend
│
└── systems/                     # Data Producer Services
    ├── ML/
    │   ├── alerts/             → Backend reads for /api/alerts
    │   ├── data/               → Backend reads for /api/traffic/live
    │   ├── outputs/            → Backend reads for /api/metrics
    │   ├── Bonet-Detection.py
    │   ├── C-2-Detection.py
    │   ├── Data-Exfilration-Detection.py
    │   ├── Lateral-Movenment.py
    │   ├── Portscan-Detection.py
    │   └── Ssh-Bruteforce-Detector.py
    │
    ├── Red-Team/
    │   ├── ground/             → Backend reads for /api/ground-truth
    │   └── Attack scripts
    │
    ├── orchestration/
    │   ├── agent_messages.log  → Backend reads for /api/agent/messages
    │   ├── logs/               → Backend reads for /api/logs
    │   ├── orchestration.pid   → Backend reads for /api/status
    │   └── ids_graph.py
    │
    ├── emulator/
    │   ├── topology.json       → Backend reads for /api/lab/topology
    │   ├── hosts.json          → Backend reads for /api/lab/hosts
    │   └── Containerlab files
    │
    ├── live-traffic-montior.py → Outputs to ML/data/live-traffic.csv
    └── alert_dashboard.py      → Standalone Flask app
```

---

## Data Integration Status

### ✅ CONFIGURED (Backend → Systems)
- [x] ML alerts reading
- [x] Live traffic CSV reading
- [x] Agent messages log reading
- [x] Orchestration logs reading
- [x] Ground truth reading
- [x] Metrics CSV reading

### ✅ NOT YET ACTIVE (Need Systems Running)
- [ ] ML detectors producing alerts (need to run detectors)
- [ ] Live traffic monitor capturing packets
- [ ] Orchestration producing agent messages
- [ ] Red team generating attacks

### 📝 HOW IT WORKS
1. **Systems produce data** → Write to folders (CSV, JSON, logs)
2. **Backend polls systems** → Reads files every request
3. **Frontend requests data** → Gets from backend via HTTP
4. **Frontend displays** → Real-time dashboard updates

---

## Example Data Flow (Complete Cycle)

```
Step 1: ML Detector runs
└─ systems/ML/Portscan-Detection.py runs
   └─ Writes: systems/ML/alerts/portscan_alert_2024_09_01.json
      {
        "timestamp": "2024-09-01T15:35:00Z",
        "attack_type": "PORT_SCAN",
        "severity": "HIGH",
        "source_ip": "10.10.10.5"
      }

Step 2: Frontend requests alerts
└─ GET http://localhost:5173/api/alerts
   (Frontend's VITE_API_BASE_URL = http://localhost:8000)

Step 3: Frontend makes HTTP request to backend
└─ GET http://localhost:8000/api/alerts

Step 4: Backend reads alert files
└─ reads_csv_rows(ALERTS_DIR / "*.json")
   └─ Returns: [{ timestamp, attack_type, severity, source_ip }]

Step 5: Backend returns HTTP response
└─ 200 OK with JSON array of alerts

Step 6: Frontend updates UI
└─ Attack Timeline Panel displays new alert
   └─ Shows: "PORT_SCAN - 10.10.10.5 - HIGH"
```

---

## Verification Checklist

- [ ] Frontend starts on port 5173
- [ ] Backend starts on port 8000
- [ ] Backend reads from systems folders
- [ ] ML detectors are running
- [ ] Live traffic monitor is running
- [ ] Orchestration is running
- [ ] Frontend shows real data (not mocks)
- [ ] No 404 errors in API calls
- [ ] CORS is working (no CORS errors in console)

---

## Next: How to Start Everything

See: **COMPLETE_RUN_GUIDE.md**
