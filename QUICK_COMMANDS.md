# 🚀 Quick Commands Reference

## Terminal 1: Start Backend

```bash
cd backend
source venv/bin/activate
python3 app.py
```

**URL:** http://localhost:8000
**First time?** Run `pip install flask flask-cors python-dotenv`

---

## Terminal 2: Start Frontend

```bash
cd frontend
npm run dev
```

**URL:** http://localhost:5173
**First time?** Run `npm install`

---

## Full Setup (First Time)

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install flask flask-cors python-dotenv
python3 app.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Production Build

```bash
cd frontend

# Set production API URL
echo "VITE_API_BASE_URL=https://api.your-domain.com" > .env.production

# Build
npm run build

# Output: frontend/dist/
```

---

## Run with Gunicorn (Production Backend)

```bash
cd backend
source venv/bin/activate
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

---

## Test API

```bash
# Test backend is running
curl http://localhost:8000/api/status

# Get alerts
curl http://localhost:8000/api/alerts

# Get agent messages
curl http://localhost:8000/api/agent/messages
```

---

## Project Structure

```
IDS/
├── frontend/        # React app (http://localhost:5173)
├── backend/         # Flask API (http://localhost:8000)
└── systems/         # Tools, ML, emulator, orchestration
    ├── emulator/
    ├── ML/
    ├── Red-Team/
    ├── orchestration/
    └── docs/
```

---

## Environment Variables

### Development (frontend/.env.local)
```
VITE_API_BASE_URL=http://localhost:8000
```

### Production (frontend/.env.production)
```
VITE_API_BASE_URL=https://api.your-domain.com
```

### Backend (backend/.env - Optional)
```
FLASK_ENV=production
ALLOWED_ORIGINS=https://your-domain.com
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend port 8000 in use | `lsof -i :8000` then kill process |
| Frontend port 5173 in use | `lsof -i :5173` then kill process |
| Module not found (frontend) | `rm -rf node_modules && npm install` |
| Module not found (backend) | `source venv/bin/activate && pip install flask flask-cors` |
| API calls failing | Check `VITE_API_BASE_URL` in `.env.local` |

---

## Documentation

- **README.md** - Main project overview
- **systems/docs/QUICK_START.md** - Detailed guide
- **systems/docs/DEPLOYMENT.md** - Production deployment
- **systems/docs/BACKEND_CONFIG.md** - Backend configuration
- **systems/docs/API_INTEGRATION.md** - API endpoints
- **systems/docs/INTEGRATION_SUMMARY.md** - Integration overview

