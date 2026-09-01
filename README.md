# IDS (Intrusion Detection System) - Full-Stack Project

## 📁 Project Structure

```
IDS/
├── frontend/              # React + Vite dashboard
│   ├── src/
│   ├── package.json
│   ├── vite.config.ts
│   ├── .env.local          (API config for dev)
│   └── .env.production     (API config for prod)
│
├── backend/               # Flask REST API
│   ├── app.py
│   ├── .env               (optional - for backend config)
│   └── venv/
│
└── systems/               # Supporting services & tools
    ├── emulator/          # Containerlab network emulation
    ├── ML/                # ML-based anomaly detection
    ├── Red-Team/          # Red team attack tools
    ├── orchestration/     # Orchestration logic
    ├── live-traffic-montior.py
    ├── alert_dashboard.py
    ├── docs/              # Documentation
    └── venv/              # Python virtualenv for tools
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ (frontend)
- Python 3.9+ (backend)
- pip (Python package manager)

### Step 1: Start Backend (Terminal 1)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)
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

### Step 2: Start Frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

**Expected output:**
```
  ✓ built in 234ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

### Step 3: Access the Dashboard

Open your browser: **http://localhost:5173**

---

## 🛠️ Available Commands

### Frontend
```bash
cd frontend

npm install       # Install dependencies
npm run dev       # Start development server
npm run build     # Build for production
npm run preview   # Preview production build
```

### Backend
```bash
cd backend

# First time setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run development
python3 app.py

# Run production (with Gunicorn)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Systems & Tools
```bash
cd systems

# Network emulator
cd emulator
# Follow emulator setup in systems/docs/

# Red team tools
cd Red-Team

# ML detector
cd ML

# Orchestration
cd orchestration

# Traffic monitor
python3 live-traffic-montior.py

# Alert dashboard
python3 alert_dashboard.py
```

---

## 📝 Configuration

### Development (.env.local - Frontend)
```
VITE_API_BASE_URL=http://localhost:8000
```

### Production (.env.production - Frontend)
```
VITE_API_BASE_URL=https://api.your-domain.com
```

### Backend (.env - Optional)
```
FLASK_ENV=production
ALLOWED_ORIGINS=https://your-domain.com
```

---

## 📚 Documentation

All documentation is in `systems/docs/`:

- **QUICK_START.md** - Detailed quick start guide
- **BACKEND_CONFIG.md** - Backend configuration guide
- **DEPLOYMENT.md** - Production deployment guide
- **INTEGRATION_SUMMARY.md** - API integration overview
- **API_INTEGRATION.md** - Frontend API details

---

## ✅ Verification

After starting both frontend and backend:

```bash
# Test backend
curl http://localhost:8000/api/status

# Open frontend
# http://localhost:5173

# Check console (F12 → Console tab)
# Should show successful API calls, no errors
```

---

## 🔗 API Endpoints

- `/api/status` - Health check
- `/api/alerts` - Security alerts feed
- `/api/agent/messages` - Agent communication
- `/api/traffic/live` - Live network traffic
- `/api/metrics` - System metrics

For full API documentation, see: `systems/docs/API_INTEGRATION.md`

---

## 🚨 Troubleshooting

### Backend won't start
```bash
# Make sure Python 3.9+ is installed
python3 --version

# Clear venv and reinstall
rm -rf backend/venv
cd backend
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors python-dotenv
python3 app.py
```

### Frontend won't start
```bash
# Make sure Node.js 18+ is installed
node --version

# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### API calls failing
- Check backend is running: `curl http://localhost:8000/api/status`
- Check frontend VITE_API_BASE_URL in `.env.local`
- Check browser console (F12) for error messages
- Check backend console for error logs

---

## 📞 Support

For issues or questions:
1. Check documentation in `systems/docs/`
2. Review API logs in browser console (F12)
3. Check backend console output
4. See troubleshooting section above

# IDS
