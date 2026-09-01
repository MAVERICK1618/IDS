# Frontend-Backend API Integration

## Overview

This document describes the integration between the React frontend and Flask backend for the IDS Dashboard.

## API Base Configuration

The frontend uses environment variables to configure the API base URL:

- **Development**: `VITE_API_BASE_URL=http://localhost:8000`
- **Production**: `VITE_API_BASE_URL=https://api.YOUR_DOMAIN`

Configuration files:
- `.env.local` - Development environment (git-ignored)
- `.env.production` - Production environment (git-ignored)
- `.env.example` - Template for environment configuration

## Architecture

### API Client (`src/services/api.ts`)

Centralized API service providing:
- Automatic base URL injection from environment variables
- Error handling and status code validation
- JSON serialization/deserialization
- Cross-origin credentials support (for authentication)

All API functions return typed responses matching backend endpoints.

### Data Flow

```
Component
  ↓
Panel (e.g., AgentFeedPanel)
  ↓
Hook (e.g., useAgentFeed) 
  ↓
API Service (api.ts)
  ↓
Backend Flask API
```

## Backend Endpoints

### Pipeline Status
- `GET /api/status` - Current pipeline state
- `GET /api/pipeline/checkpoints` - Pipeline execution checkpoints

### Agent Communication
- `GET /api/agent/messages` - Agent log messages
- `GET /api/agent/nodes` - Agent workflow nodes and status

### Alerts
- `GET /api/alerts` - All detector alerts
- `GET /api/alerts/<detector_name>` - Alerts for specific detector

### ML Predictions
- `GET /api/predictions` - All detector predictions
- `GET /api/predictions/<detector_name>` - Predictions for specific detector

### Ground Truth
- `GET /api/ground-truth` - Ground truth summary
- `GET /api/ground-truth/<attack_type>` - Ground truth for specific attack type

### Metrics
- `GET /api/metrics` - Evaluation metrics
- `GET /api/metrics/chart/<chart_name>` - Metric chart images (PNG)

### Live Traffic
- `GET /api/traffic/summary` - Traffic statistics
- `GET /api/traffic/live` - Last 100 packets from live traffic

### Logs
- `GET /api/logs` - List available log files
- `GET /api/logs/<log_name>` - Read log file content (last 200 lines)

### Feedback/Retraining
- `GET /api/feedback/status` - Feedback system status
- `GET /api/feedback/missed-attacks` - Missed attacks requiring retraining

### Lab/Emulator
- `GET /api/lab/hosts` - Active lab container hosts
- `GET /api/lab/topology` - Network topology configuration

### Dashboard
- `GET /api/dashboard` - Combined dashboard data (recommended for performance)

## Frontend Hooks

### useAgentFeed(active: boolean)
Polls `/api/agent/messages` every 3 seconds when active.

Returns: `{ messages, error }`

### usePacketStream(active: boolean)
Polls `/api/traffic/live` every 2 seconds when active.
Transforms CSV rows to Packet format.

Returns: `{ packets, error, clearPackets }`

### useAttackFeed(active: boolean)
Polls `/api/alerts` every 4 seconds when active.
Transforms alerts to Attack format.

Returns: `{ attacks, error, acknowledge }`

### useEvaluation(active: boolean)
Polls `/api/metrics` immediately and then every 8 seconds when active.

Returns: `{ evaluation, error }`

### useRLTraining(active: boolean)
Generates mock RL training data (no backend endpoint).

Returns: `{ points, latest }`

## Error Handling

Each hook returns an `error` state:
```typescript
const { messages, error } = useAgentFeed(active)

if (error) {
  // Handle error
  console.error("Failed to fetch agent messages:", error)
}
```

API errors include:
- Network errors
- HTTP error responses (4xx, 5xx)
- JSON parsing errors

## HTTPS Configuration

### Development
Development mode uses HTTP on localhost. No HTTPS configuration needed.

### Production
1. Backend must be accessible via HTTPS
2. Update `.env.production` with HTTPS URL:
   ```
   VITE_API_BASE_URL=https://api.YOUR_DOMAIN
   ```
3. Build production bundle:
   ```bash
   npm run build
   ```

### CORS Configuration
Backend CORS is configured in `app.py`:
```python
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,OPTIONS"
```

For production with specific origins, update backend:
```python
ALLOWED_ORIGINS = ["https://YOUR_DOMAIN"]
response.headers["Access-Control-Allow-Origin"] = request.origin if request.origin in ALLOWED_ORIGINS else ""
```

## Running the Application

### Backend
```bash
cd backend
source ~/IDS/venv/bin/activate
pip install flask flask-cors
python3 app.py
# Server runs on http://localhost:8000
```

### Frontend (Development)
```bash
cd frontend
npm install
npm run dev
# Development server on http://localhost:5173
# API requests proxied to http://localhost:8000
```

### Frontend (Production Build)
```bash
cd frontend
npm run build
# Generates optimized build in dist/
# Configure .env.production before building
```

## Frontend ↔ Backend API Mapping

| Frontend Component | Hook | Backend Endpoint | HTTP Method | Purpose |
|---|---|---|---|---|
| PacketMonitorPanel | usePacketStream | /api/traffic/live | GET | Live network packets |
| AgentFeedPanel | useAgentFeed | /api/agent/messages | GET | Agent log messages |
| AttackTimelinePanel | useAttackFeed | /api/alerts | GET | Detected attacks |
| MetricsPanelWrapper | useEvaluation | /api/metrics | GET | Model evaluation metrics |
| RLProgressPanel | useRLTraining | (mock) | - | RL training progress |

## Debugging

### Check API Connectivity
```bash
# From terminal
curl http://localhost:8000/api/status
curl http://localhost:8000/api/alerts
```

### Monitor Network Requests
Open browser DevTools → Network tab
Filter by `/api` to see all requests

### Enable Verbose Logging
The API service can be enhanced with logging:
```typescript
// In src/services/api.ts
console.log(`[API] GET ${endpoint}`)
```

## Future Enhancements

- [ ] Add POST/PUT/DELETE endpoints for system control
- [ ] Implement WebSocket for real-time updates (instead of polling)
- [ ] Add request cancellation for improved performance
- [ ] Implement API response caching
- [ ] Add request/response interceptors
- [ ] Add authentication/JWT token handling
